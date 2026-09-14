import argparse
import hashlib
import json
import math
import os
import signal
import sys
import time
import tracemalloc

if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)


def safe_print(*a, **kw):
    try:
        print(*a, **kw)
    except BrokenPipeError:
        pass

import numpy as np
import torch

from research.model import Config, TinyLM, make_model

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# A vocabulary variant keeps its tokenizer and token bins together.
DATA = ROOT / "data" / "tinystories"
RUNS = str(ROOT / "runs")


def variant_dir(vocab_size):
    return DATA / f"vocab-{vocab_size}"


def get_device():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class Batcher:
    """Generator-based batch provider that streams micro-batches from memmapped data.
    Avoids holding large batch lists or giant tensors in memory."""
    def __init__(self, split, batch_size, seq_len, device, dataset, seed=0):
        self.data = np.memmap(dataset / f"{split}.bin", dtype=np.uint16, mode="r")
        self.bs, self.sl, self.device = batch_size, seq_len, device
        self.rng = np.random.default_rng(1234 if split == "val" else seed)

    def stream(self):
        """Infinite generator yielding (x, y) micro-batches on demand."""
        max_idx = len(self.data) - self.sl - 1
        while True:
            ix = self.rng.integers(0, max_idx, self.bs)
            # Allocate contiguous 2D array directly to minimize fragmentation
            x_arr = np.empty((self.bs, self.sl), dtype=np.int64)
            y_arr = np.empty((self.bs, self.sl), dtype=np.int64)
            for row_idx, i in enumerate(ix):
                x_arr[row_idx] = self.data[i : i + self.sl]
                y_arr[row_idx] = self.data[i + 1 : i + 1 + self.sl]
            yield (
                torch.from_numpy(x_arr).to(self.device, non_blocking=True),
                torch.from_numpy(y_arr).to(self.device, non_blocking=True),
            )

    def __call__(self):
        return next(self.stream())


@torch.no_grad()
def evaluate(model, batcher, iters):
    model.eval()
    batcher.rng = np.random.default_rng(1234)  # same val batches for every arm
    losses = []
    gen = batcher.stream()
    for _ in range(iters):
        x, y = next(gen)
        _, loss = model(x, y)
        losses.append(loss.item())
        del x, y, _
    model.train()
    return sum(losses) / len(losses)


def lr_at(step, total, peak, warmup):
    if step < warmup:
        return peak * (step + 1) / warmup
    p = (step - warmup) / max(1, total - warmup)
    return 0.1 * peak + 0.9 * peak * 0.5 * (1 + math.cos(math.pi * p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--arm",
        required=True,
        choices=["baseline", "ple", "ple_notable", "fatembed", "bigcore"],
    )
    ap.add_argument("--target-core", type=int, default=1_500_000)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--micro-batch-size", type=int, default=4,
                    help="chunk size processed per forward/backward pass (keeps peak RAM low)")
    ap.add_argument("--seq-len", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--warmup", type=int, default=200)
    ap.add_argument("--eval-every", type=int, default=250)
    ap.add_argument("--eval-iters", type=int, default=40)
    ap.add_argument("--ple-dim", type=int, default=64)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--n-layers", type=int, default=6)
    ap.add_argument("--n-heads", type=int, default=4)
    ap.add_argument("--fixed-ffn", type=int, default=None,
                    help="pin ffn_hidden and skip the core solver (table-scaling sweep)")
    # Published experiments always pass --vocab; the default is for ad-hoc runs.
    ap.add_argument("--vocab", type=int, default=32768)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--profile-memory", action="store_true",
                    help="enable tracemalloc memory profiling and leak detection")
    args = ap.parse_args()

    if args.profile_memory:
        tracemalloc.start()
        safe_print("[mem-profile] tracemalloc profiling enabled.")

    # Before anything expensive: the tokenizer that produced these bins. Its
    # hash is what lets the exporter and sampler refuse a mismatched tokenizer
    # later, and a checkpoint written without it cannot be tied to one. Failing
    # here costs nothing; failing after a 30-minute run costs the run.
    if not 0 < args.vocab <= 65536:
        raise SystemExit(f"--vocab must be 1..65536; the token bins are uint16 "
                         f"and are memmapped as uint16")

    dataset = variant_dir(args.vocab)
    tok_path = dataset / "tokenizer.json"
    if not os.path.exists(tok_path):
        raise SystemExit(
            f"{tok_path} missing. The bins this run trains on came from it, and "
            f"without its hash the checkpoint cannot be tied to a tokenizer. "
            f"Run: python -m research.tinystories.prepare --vocab {args.vocab}")
    tok_sha = hashlib.sha256(open(tok_path, "rb").read()).hexdigest()

    torch.manual_seed(args.seed)
    device = get_device()
    os.makedirs(RUNS, exist_ok=True)

    base = Config(seq_len=args.seq_len, ple_dim=args.ple_dim, vocab_size=args.vocab,
                  d_model=args.d_model, n_layers=args.n_layers, n_heads=args.n_heads)
    model = make_model(args.arm, args.target_core, base, fixed_ffn=args.fixed_ffn).to(device)
    budget = model.param_budget()
    cfg = model.cfg

    # No weight decay on 1-D params (norms) or on lookup tables.
    decay, no_decay = [], []
    for n, p in model.named_parameters():
        (no_decay if p.ndim < 2 or "table" in n or "tok_emb" in n else decay).append(p)
    opt = torch.optim.AdamW(
        [{"params": decay, "weight_decay": 0.1}, {"params": no_decay, "weight_decay": 0.0}],
        lr=args.lr,
        betas=(0.9, 0.95),
    )

    # Micro-batch chunking & gradient accumulation:
    # Keeps total effective batch size identical while slashing peak RAM by (batch_size / micro_batch_size)
    micro_bs = min(args.micro_batch_size, args.batch_size)
    accum_steps = max(1, args.batch_size // micro_bs)

    train_b = Batcher("train", micro_bs, args.seq_len, device, dataset, seed=args.seed)
    val_b = Batcher("val", micro_bs, args.seq_len, device, dataset)
    train_stream = train_b.stream()

    name = f"{args.arm}{'-' + args.tag if args.tag else ''}-s{args.seed}"
    history, best = [], float("inf")
    t0 = time.time()

    safe_print(f"[{args.arm}] batch_size={args.batch_size} (micro_batch={micro_bs}, accum={accum_steps})")

    for step in range(args.steps):
        lr = lr_at(step, args.steps, args.lr, args.warmup)
        for g in opt.param_groups:
            g["lr"] = lr

        opt.zero_grad(set_to_none=True)
        step_loss = 0.0

        # Generator-based chunk processing
        for _ in range(accum_steps):
            x, y = next(train_stream)
            _, loss = model(x, y)
            loss_scaled = loss / accum_steps
            loss_scaled.backward()
            step_loss += loss.item() / accum_steps
            del x, y, _, loss, loss_scaled

        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if args.profile_memory and (step == 0 or (step + 1) % 50 == 0):
            current, peak = tracemalloc.get_traced_memory()
            safe_print(f"[mem-profile] step {step:4d} | current: {current / 1024**2:6.1f} MB | peak: {peak / 1024**2:6.1f} MB", flush=True)

        if step % args.eval_every == 0 or step == args.steps - 1:
            vl = evaluate(model, val_b, args.eval_iters)
            best = min(best, vl)
            tok = (step + 1) * args.batch_size * args.seq_len
            history.append({"step": step, "tokens": tok, "train": step_loss, "val": vl})
            safe_print(
                f"{name} step {step:5d} | tok {tok / 1e6:6.1f}M | train {step_loss:.4f} "
                f"| val {vl:.4f} | ppl {math.exp(vl):7.2f} | {time.time() - t0:5.0f}s",
                flush=True,
            )

    result = {
        "arm": args.arm,
        "seed": args.seed,
        "tag": args.tag,
        "config": {k: v for k, v in cfg.__dict__.items()},
        "training": {
            "batch_size": args.batch_size,
            "steps": args.steps,
            "lr": args.lr,
            "warmup": args.warmup,
            "eval_every": args.eval_every,
            "eval_iters": args.eval_iters,
            "target_core": args.target_core,
            "fixed_ffn": args.fixed_ffn,
            "seed": args.seed,
        },
        "tokenizer_sha256": tok_sha,
        "params": budget,
        "final_val": history[-1]["val"],
        "best_val": best,
        "final_ppl": math.exp(history[-1]["val"]),
        "tokens_seen": args.steps * args.batch_size * args.seq_len,
        "steps": args.steps,
        "wall_seconds": time.time() - t0,
        "history": history,
    }
    with open(os.path.join(RUNS, f"{name}.json"), "w") as f:
        json.dump(result, f, indent=2)
    # Identity and schedule live only in the filename and the sidecar JSON
    # otherwise, so a checkpoint copied over another name, or trained on a
    # different schedule, would pass every content check.
    torch.save({"cfg": cfg.__dict__, "state": model.state_dict(),
                "tokenizer_sha256": tok_sha,
                "seed": args.seed, "tag": args.tag, "name": name,
                "training": result["training"]},
                os.path.join(RUNS, f"{name}.pt"))
    safe_print(f"{name} DONE core={budget['core']:,} table={budget['table']:,} "
               f"val={result['final_val']:.4f} ppl={result['final_ppl']:.2f}")


if __name__ == "__main__":
    try:
        main()
        try:
            sys.stdout.flush()
        except BrokenPipeError:
            pass
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
