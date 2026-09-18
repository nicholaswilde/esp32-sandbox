#!/usr/bin/env python3
"""Export trained TinyStories PLE model to INT4 packed binary format for ESP32-S3.

Outputs:
  - pc_tools/model.bin (Packed INT4 weights + FP16 scales with PLE header)
  - pc_tools/golden.txt (Golden prompt logits for C/C++ verification)
"""

import argparse
import hashlib
import os
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
import torch
from tokenizers import Tokenizer

# Add project directory to sys.path to import research.model
PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from research.model import Config, TinyLM

MAGIC = 0x00454C50  # "PLE\0"
FORMAT_VERSION = 1
HEADER_BYTES = 56
FLAG_TIED_HEAD = 1 << 0
GROUP_DEFAULT = 128
PROMPT = "Once upon a time"


def quant_pack(w: torch.Tensor, group: int = GROUP_DEFAULT):
    """Group-wise symmetric int4, ragged (no padding) with fp16 scales.

    Returns (packed_uint8, scales_fp16, dequantized_fp32).
    """
    w = w.float()
    out_shape = w.shape
    x = w.reshape(-1, out_shape[-1])
    rows, cols = x.shape
    n_groups = (cols + group - 1) // group
    q = torch.zeros(rows, cols)
    dq = torch.zeros(rows, cols)
    scales = torch.zeros(rows, n_groups)

    for gi in range(n_groups):
        a, b = gi * group, min((gi + 1) * group, cols)
        seg = x[:, a:b]
        sc = (seg.abs().amax(dim=1, keepdim=True) / 7.0).clamp_min(1e-8)
        sc = sc.half().float()  # Round scale to IEEE fp16
        scales[:, gi] = sc.squeeze(1)
        qi = torch.clamp(torch.round(seg / sc), -7, 7)
        q[:, a:b] = qi
        dq[:, a:b] = qi * sc
    dq = dq.reshape(out_shape)

    codes = (q.to(torch.int16) + 8).to(torch.uint8).numpy()
    row_bytes = (cols + 1) // 2
    packed = np.zeros((rows, row_bytes), dtype=np.uint8)
    lo = codes[:, 0::2]
    hi = codes[:, 1::2]
    packed[:, : lo.shape[1]] = lo
    packed[:, : hi.shape[1]] |= (hi << 4)
    scales16 = scales.numpy().astype(np.float16)
    return packed.reshape(-1), scales16.reshape(-1), dq


def main():
    parser = argparse.ArgumentParser(description="Export TinyStories PLE checkpoint to INT4 binary.")
    parser.add_argument(
        "--ckpt",
        type=Path,
        default=PROJECT_DIR / "runs" / "tinystories" / "ple-model.pt",
        help="Path to trained checkpoint (.pt)",
    )
    parser.add_argument(
        "--tokenizer",
        type=Path,
        default=PROJECT_DIR / "pc_tools" / "tokenizer.json",
        help="Path to tokenizer.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=PROJECT_DIR / "pc_tools",
        help="Destination directory for exported artifacts (default: pc_tools/)",
    )
    parser.add_argument(
        "--out-name",
        type=str,
        default="model.bin",
        help="Output binary filename (default: model.bin)",
    )
    parser.add_argument(
        "--group",
        type=int,
        default=GROUP_DEFAULT,
        help=f"Quantization group size (default: {GROUP_DEFAULT})",
    )
    args = parser.parse_args()

    if not args.ckpt.exists():
        sys.exit(f"Error: checkpoint {args.ckpt} not found.")
    if not args.tokenizer.exists():
        sys.exit(f"Error: tokenizer {args.tokenizer} not found.")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading checkpoint: {args.ckpt.name}")
    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    cfg = Config(**ck["cfg"])

    if cfg.arm != "ple":
        sys.exit(f"Error: checkpoint arm={cfg.arm}, expected 'ple'")

    out_vocab = cfg.resolved_out_vocab_size
    print(f"input_vocab={cfg.vocab_size} | output_vocab={out_vocab}")

    model = TinyLM(cfg)
    model.load_state_dict(ck["state"])
    model.eval()

    sd = model.state_dict()
    plan = []

    def add_tensor(name: str, quant: bool):
        plan.append((name, sd[name], quant))

    # Strict tensor order matching C runtime
    add_tensor("tok_emb.weight", True)
    add_tensor("ple_model_proj.weight", True)
    add_tensor("ple_proj_norm.weight", False)
    add_tensor("ple_table.weight", True)

    for i in range(cfg.n_layers):
        p = f"blocks.{i}."
        add_tensor(p + "attn_norm.weight", False)
        add_tensor(p + "attn.qkv.weight", True)
        add_tensor(p + "attn.proj.weight", True)
        add_tensor(p + "ffn_norm.weight", False)
        add_tensor(p + "ffn.gate.weight", True)
        add_tensor(p + "ffn.up.weight", True)
        add_tensor(p + "ffn.down.weight", True)
        add_tensor(p + "ple_norm.weight", False)

    add_tensor("out_norm.weight", False)
    if not cfg.head_is_tied:
        add_tensor("head.weight", True)

    blobs = []
    dq_dict = {}
    total_unquant = 0
    total_packed = 0

    for name, tensor, quant in plan:
        t = tensor.detach().cpu()
        if not quant:
            arr = t.numpy().astype(np.float32)
            blobs.append(("F", name, t.shape, arr.reshape(-1), None))
            total_unquant += arr.nbytes
            dq_dict[name] = t
        else:
            packed, scales, dq = quant_pack(t, group=args.group)
            blobs.append(("Q", name, t.shape, packed, scales))
            total_packed += len(packed) + scales.nbytes
            dq_dict[name] = dq

    out_bin = args.out_dir / args.out_name
    flags = FLAG_TIED_HEAD if cfg.head_is_tied else 0

    with open(out_bin, "wb") as f:
        # 56-byte header
        f.write(struct.pack("<IIII", MAGIC, FORMAT_VERSION, HEADER_BYTES, flags))
        f.write(struct.pack("<II", cfg.vocab_size, out_vocab))
        for v in [
            cfg.d_model,
            cfg.n_layers,
            cfg.n_heads,
            cfg.ffn_hidden,
            cfg.ple_dim,
            cfg.seq_len,
            args.group,
        ]:
            f.write(struct.pack("<i", v))
        f.write(struct.pack("<f", cfg.rope_theta))

        for entry in blobs:
            kind, name, shape, data, scales = entry
            if kind == "F":
                f.write(data.tobytes())
            else:
                f.write(struct.pack("<i", args.group))
                f.write(data.tobytes())
                f.write(scales.tobytes())

    bin_size = out_bin.stat().st_size
    print(f"Exported: {out_bin} ({bin_size / (1024 * 1024):.2f} MB)")


if __name__ == "__main__":
    main()
