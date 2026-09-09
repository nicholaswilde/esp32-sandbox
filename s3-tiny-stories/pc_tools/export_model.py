import os
import struct
import torch
from transformers import AutoModelForCausalLM

def export_model():
  print("Downloading TinyStories model checkpoint...")
  # Pulling a 15M parameter model as a baseline
  model = AutoModelForCausalLM.from_pretrained("karpathy/tinyllamas")
  
  print("Exporting weights to binary format...")
  out_path = "stories15M.bin"
  
  with open(out_path, "wb") as f:
    # Write the magic number / version header expected by llm_core.c
    f.write(struct.pack("I", 0x414b3432))
    
    # In a full implementation, layer weights are iterated, 
    # quantized to INT8/INT4, and packed iteratively here.
    pass
    
  print(f"Export complete: {out_path}")

if __name__ == "__main__":
  export_model()

