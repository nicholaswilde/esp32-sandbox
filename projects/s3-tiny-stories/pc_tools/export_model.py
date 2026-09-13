#!/usr/bin/env python3
"""
Export karpathy/tinyllamas stories15M to llama2.c v1 binary format.

karpathy/tinyllamas on HuggingFace stores NATIVE llama2.c .pt checkpoints,
NOT HuggingFace-format models. We download stories15M.pt directly and load
it with torch.load(). No HF rotary permutation needed.

Binary layout (v1):
  [0..3]   magic   = 0x616b3432  ("ak42")
  [4..7]   version = 1
  [8..11]  dim
  [12..15] hidden_dim
  [16..19] n_layers
  [20..23] n_heads
  [24..27] n_kv_heads
  [28..31] vocab_size
  [32..35] seq_len
  [36]     shared_classifier (uint8)
  [37..40] group_size (int32, 0 = fp32)
  [41..255] zero padding
  [256..]  FP32 weights in order:
             token_embedding_table, rms_att_weight,
             wq, wk, wv, wo,
             rms_ffn_weight, w1, w2, w3,
             rms_final_weight, [wcls if not shared]
"""

import os
import struct
import sys

import numpy as np
import torch
from huggingface_hub import hf_hub_download

HEADER_SIZE = 256
MAGIC = 0x616B3432
VERSION = 1

# stories15M config (from karpathy/llama2.c params)
DIM = 288
HIDDEN_DIM = 768
N_LAYERS = 6
N_HEADS = 6
N_KV_HEADS = 6
VOCAB_SIZE = 32000
SEQ_LEN = 256
SHARED_CLASSIFIER = True
GROUP_SIZE = 64  # 64 = INT4


def serialize(f, tensor: torch.Tensor) -> int:
    """Write tensor as FP32 little-endian bytes, return byte count."""
    data = tensor.detach().float().cpu().contiguous().numpy().astype(np.float32)
    f.write(data.tobytes())
    return data.nbytes




def quantize_q4(tensor: torch.Tensor, group_size: int):
    # Flatten all dimensions except the last one
    cols = tensor.size(-1)
    tensor = tensor.view(-1, cols)
    rows = tensor.size(0)
    n_groups = (cols + group_size - 1) // group_size
    row_bytes = (cols + 1) // 2
    
    # Pad to multiple of group_size
    pad_len = (n_groups * group_size) - cols
    if pad_len > 0:
        tensor = torch.nn.functional.pad(tensor, (0, pad_len))
        
    # Reshape to [rows, n_groups, group_size]
    w = tensor.view(rows, n_groups, group_size).detach().cpu().numpy()
    
    # Calculate amax and scales
    amax = np.max(np.abs(w), axis=2)  # [rows, n_groups]
    scales = np.where(amax > 1e-8, amax / 7.0, 0.0).astype(np.float16)
    
    # Quantize
    inv_scales = np.where(scales > 0, 1.0 / scales, 0.0)
    q = np.round(w * inv_scales[:, :, np.newaxis])
    q = np.clip(q, -8, 7).astype(np.int8)
    q_packed = q + 8  # 0 to 15
    
    # Flatten back to [rows, cols] (handling padding if we want, but we just take cols)
    q_packed = q_packed.reshape(rows, -1)[:, :cols].astype(np.uint8)
    
    # Pack nibbles
    # Even indices go to lower nibble, odd indices go to upper nibble
    q_even = q_packed[:, 0::2]
    q_odd = q_packed[:, 1::2]
    
    codes = np.zeros((rows, row_bytes), dtype=np.uint8)
    codes[:, :q_even.shape[1]] |= (q_even & 0xF)
    codes[:, :q_odd.shape[1]] |= ((q_odd & 0xF) << 4)
    
    return codes, scales

def serialize_q4(f, tensor: torch.Tensor, group_size: int) -> int:
    codes, scales = quantize_q4(tensor, group_size)
    f.write(codes.tobytes())
    f.write(scales.tobytes())
    return codes.nbytes + scales.nbytes

def write_header(f):
    header = struct.pack(
        "<IiiiiiiiiBi",
        MAGIC,
        VERSION,
        DIM,
        HIDDEN_DIM,
        N_LAYERS,
        N_HEADS,
        N_KV_HEADS,
        VOCAB_SIZE,
        SEQ_LEN,
        int(SHARED_CLASSIFIER),
        GROUP_SIZE,
    )
    pad = HEADER_SIZE - len(header)
    assert pad >= 0, f"Header too large: {len(header)} bytes"
    header += b"\x00" * pad
    assert len(header) == HEADER_SIZE
    f.write(header)
    print(f"  Header written ({HEADER_SIZE} bytes)")


def load_checkpoint(pt_path: str) -> dict:
    """Load a llama2.c native .pt checkpoint. Returns the state dict."""
    print(f"  Loading checkpoint from {pt_path} …")
    checkpoint = torch.load(pt_path, map_location="cpu", weights_only=True)
    # karpathy/tinyllamas checkpoints are saved as {"model": state_dict, ...}
    # or directly as a state_dict.
    if isinstance(checkpoint, dict) and "model" in checkpoint:
        sd = checkpoint["model"]
    else:
        sd = checkpoint
    print(f"  Loaded {len(sd)} tensors.")
    return sd


def export_model(out_path: str = "stories15M.bin"):
    # ------------------------------------------------------------------ #
    # 1. Download the native .pt checkpoint                               #
    # ------------------------------------------------------------------ #
    print("Downloading karpathy/tinyllamas (stories15M) from HuggingFace …")
    pt_path = hf_hub_download(
        repo_id="karpathy/tinyllamas",
        filename="stories15M.pt",
        local_dir=".",
    )
    print(f"  Downloaded to: {pt_path}")

    sd = load_checkpoint(pt_path)

    # Print available keys to help debug if structure ever changes
    print("  State dict keys (first 10):", list(sd.keys())[:10])

    # ------------------------------------------------------------------ #
    # 2. Write binary                                                      #
    # ------------------------------------------------------------------ #
    print(f"\nWriting binary to: {out_path}")
    total_bytes = 0

    with open(out_path, "wb") as f:
        write_header(f)

        # Native llama2.c state dict key names:
        #   tok_embeddings.weight         (vocab_size, dim)
        #   layers.{i}.attention_norm.weight  (dim,)
        #   layers.{i}.attention.wq.weight    (dim, dim)
        #   layers.{i}.attention.wk.weight    (dim, dim)
        #   layers.{i}.attention.wv.weight    (dim, dim)
        #   layers.{i}.attention.wo.weight    (dim, dim)
        #   layers.{i}.ffn_norm.weight        (dim,)
        #   layers.{i}.feed_forward.w1.weight (hidden_dim, dim)
        #   layers.{i}.feed_forward.w2.weight (dim, hidden_dim)
        #   layers.{i}.feed_forward.w3.weight (hidden_dim, dim)
        #   norm.weight                   (dim,)
        #   output.weight                 (vocab_size, dim)  -- if not shared

        # 1. token_embedding_table  [vocab_size × dim]
        print("  Writing token_embedding_table …")
        total_bytes += serialize_q4(f, sd["tok_embeddings.weight"], GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, sd["tok_embeddings.weight"])

        # 2. rms_att_weight  [n_layers × dim]
        print("  Writing rms_att_weight …")
        rms_att = torch.stack(
            [sd[f"layers.{i}.attention_norm.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize(f, rms_att)

        # 3. wq  [n_layers × dim × dim]  — no permutation needed for native format
        print("  Writing wq …")
        wq = torch.stack(
            [sd[f"layers.{i}.attention.wq.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, wq, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, wq)

        # 4. wk  [n_layers × dim × dim]
        print("  Writing wk …")
        wk = torch.stack(
            [sd[f"layers.{i}.attention.wk.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, wk, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, wk)

        # 5. wv  [n_layers × dim × dim]
        print("  Writing wv …")
        wv = torch.stack(
            [sd[f"layers.{i}.attention.wv.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, wv, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, wv)

        # 6. wo  [n_layers × dim × dim]
        print("  Writing wo …")
        wo = torch.stack(
            [sd[f"layers.{i}.attention.wo.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, wo, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, wo)

        # 7. rms_ffn_weight  [n_layers × dim]
        print("  Writing rms_ffn_weight …")
        rms_ffn = torch.stack(
            [sd[f"layers.{i}.ffn_norm.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize(f, rms_ffn)

        # 8. w1  [n_layers × hidden_dim × dim]
        print("  Writing w1 …")
        w1 = torch.stack(
            [sd[f"layers.{i}.feed_forward.w1.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, w1, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, w1)

        # 9. w2  [n_layers × dim × hidden_dim]
        print("  Writing w2 …")
        w2 = torch.stack(
            [sd[f"layers.{i}.feed_forward.w2.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, w2, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, w2)

        # 10. w3  [n_layers × hidden_dim × dim]
        print("  Writing w3 …")
        w3 = torch.stack(
            [sd[f"layers.{i}.feed_forward.w3.weight"] for i in range(N_LAYERS)]
        )
        total_bytes += serialize_q4(f, w3, GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, w3)

        # 11. rms_final_weight  [dim]
        print("  Writing rms_final_weight …")
        total_bytes += serialize(f, sd["norm.weight"])

        # 12. wcls  [vocab_size × dim]  — only if classifier not shared with embeddings
        if not SHARED_CLASSIFIER:
            print("  Writing wcls …")
            total_bytes += serialize_q4(f, sd["output.weight"], GROUP_SIZE) if GROUP_SIZE > 0 else serialize(f, sd["output.weight"])

    file_size = os.path.getsize(out_path)
    print(f"\nExport complete!")
    print(f"  File : {out_path}")
    print(f"  Size : {file_size / 1024 / 1024:.2f} MB  ({file_size:,} bytes)")
    expected = HEADER_SIZE + total_bytes
    print(f"  Check: {file_size} == {expected} → {'OK' if file_size == expected else 'MISMATCH'}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "stories15M.bin"
    export_model(out)
