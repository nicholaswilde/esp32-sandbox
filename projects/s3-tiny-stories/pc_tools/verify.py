import sys
import struct
import numpy as np
import torch
from huggingface_hub import hf_hub_download

# Define model structure matching stories15M
class SimpleModel(torch.nn.Module):
    def __init__(self, vocab_size=32000, dim=288, hidden_dim=768, n_layers=6, n_heads=6):
        super().__init__()
        self.tok_embeddings = torch.nn.Embedding(vocab_size, dim)
        self.layers = torch.nn.ModuleList()
        for _ in range(n_layers):
            layer = torch.nn.ModuleDict({
                'attention_norm': torch.nn.RMSNorm(dim),
                'attention': torch.nn.ModuleDict({
                    'wq': torch.nn.Linear(dim, dim, bias=False),
                    'wk': torch.nn.Linear(dim, dim, bias=False),
                    'wv': torch.nn.Linear(dim, dim, bias=False),
                    'wo': torch.nn.Linear(dim, dim, bias=False),
                }),
                'ffn_norm': torch.nn.RMSNorm(dim),
                'feed_forward': torch.nn.ModuleDict({
                    'w1': torch.nn.Linear(dim, hidden_dim, bias=False),
                    'w2': torch.nn.Linear(hidden_dim, dim, bias=False),
                    'w3': torch.nn.Linear(dim, hidden_dim, bias=False),
                })
            })
            self.layers.append(layer)
        self.norm = torch.nn.RMSNorm(dim)
        self.output = torch.nn.Linear(dim, vocab_size, bias=False)

def dequantize_q4(codes, scales, rows, cols):
    # codes: [rows, ceil(cols/2)] uint8
    # scales: [rows, n_groups] float16
    group_size = 64
    w = np.zeros((rows, cols), dtype=np.float32)
    for r in range(rows):
        for gi in range(scales.shape[1]):
            begin = gi * group_size
            end = min(begin + group_size, cols)
            scale = scales[r, gi]
            for i in range(end - begin):
                j = begin + i
                byte = codes[r, j // 2]
                val_packed = (byte >> 4) if (j % 2 != 0) else (byte & 0xF)
                w[r, j] = (int(val_packed) - 8) * scale
    return w

def load_bin(path):
    with open(path, "rb") as f:
        header_bytes = f.read(256)
        magic, version, dim, hidden_dim, n_layers, n_heads, n_kv_heads, vocab_size, seq_len, shared_class, group_size = struct.unpack("<IiiiiiiiiBi", header_bytes[:41])
        assert magic == 0x616B3432
        
        state_dict = {}
        
        def read_q4(rows, cols):
            n_groups = (cols + group_size - 1) // group_size
            row_bytes = (cols + 1) // 2
            codes = np.frombuffer(f.read(rows * row_bytes), dtype=np.uint8).reshape(rows, row_bytes)
            scales = np.frombuffer(f.read(rows * n_groups * 2), dtype=np.float16).reshape(rows, n_groups)
            return torch.tensor(dequantize_q4(codes, scales, rows, cols), dtype=torch.float32)
            
        def read_f32(size):
            return torch.tensor(np.frombuffer(f.read(size * 4), dtype=np.float32))

        state_dict["tok_embeddings.weight"] = read_q4(vocab_size, dim)
        
        rms_att = read_f32(n_layers * dim).view(n_layers, dim)
        wq = read_q4(n_layers * dim, dim).view(n_layers, dim, dim)
        wk = read_q4(n_layers * dim, dim).view(n_layers, dim, dim)
        wv = read_q4(n_layers * dim, dim).view(n_layers, dim, dim)
        wo = read_q4(n_layers * dim, dim).view(n_layers, dim, dim)
        rms_ffn = read_f32(n_layers * dim).view(n_layers, dim)
        w1 = read_q4(n_layers * hidden_dim, dim).view(n_layers, hidden_dim, dim)
        w2 = read_q4(n_layers * dim, hidden_dim).view(n_layers, dim, hidden_dim)
        w3 = read_q4(n_layers * hidden_dim, dim).view(n_layers, hidden_dim, dim)
        
        for l in range(n_layers):
            state_dict[f"layers.{l}.attention_norm.weight"] = rms_att[l]
            state_dict[f"layers.{l}.attention.wq.weight"] = wq[l]
            state_dict[f"layers.{l}.attention.wk.weight"] = wk[l]
            state_dict[f"layers.{l}.attention.wv.weight"] = wv[l]
            state_dict[f"layers.{l}.attention.wo.weight"] = wo[l]
            state_dict[f"layers.{l}.ffn_norm.weight"] = rms_ffn[l]
            state_dict[f"layers.{l}.feed_forward.w1.weight"] = w1[l]
            state_dict[f"layers.{l}.feed_forward.w2.weight"] = w2[l]
            state_dict[f"layers.{l}.feed_forward.w3.weight"] = w3[l]
            
        state_dict["norm.weight"] = read_f32(dim)
        if not shared_class:
            state_dict["output.weight"] = read_q4(vocab_size, dim)
        else:
            state_dict["output.weight"] = state_dict["tok_embeddings.weight"]
            
        return state_dict

if __name__ == "__main__":
    print("Loading quantized bin...")
    bin_sd = load_bin("pc_tools/stories15M_q4.bin")
    
    print("Downloading FP32 checkpoint...")
    pt_path = hf_hub_download(repo_id="karpathy/tinyllamas", filename="stories15M.pt", local_dir=".")
    pt_checkpoint = torch.load(pt_path, map_location="cpu", weights_only=True)
    pt_sd = pt_checkpoint["model"] if "model" in pt_checkpoint else pt_checkpoint
    
    print("Comparing tensors...")
    err_sum = 0
    total = 0
    for k in bin_sd.keys():
        if k in pt_sd:
            mse = torch.nn.functional.mse_loss(bin_sd[k], pt_sd[k]).item()
            err_sum += mse
            total += 1
    
    print(f"Average MSE across {total} matching tensors: {err_sum/total:.6f}")
    if err_sum/total < 0.05:
        print("SUCCESS: INT4 model closely matches FP32 model!")
    else:
        print("WARNING: High divergence detected.")
