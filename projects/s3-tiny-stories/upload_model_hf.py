#!/usr/bin/env python3
"""Upload trained or quantized ESP32-S3 models to Hugging Face Hub.

Uploads the 5 core artifacts:
  - README.md (Model Card with metadata)
  - LICENSE (Apache 2.0 or repository license)
  - metadata.json (Architecture, quantization, and hardware specifications)
  - *.bin (Quantized/packed model weights)
  - tokenizer.json (Vocabulary and tokenizer configuration)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from huggingface_hub import HfApi
except ImportError:
    print(
        "Error: huggingface_hub is not installed. Run 'uv add huggingface-hub' or 'uv run upload_model_hf.py'.",
        file=sys.stderr,
    )
    sys.exit(1)


def generate_model_card(repo_id: str, bin_filenames: List[str], is_ple: bool = False) -> str:
    """Generate a clean model card README.md with YAML metadata for Hugging Face."""
    title = "TinyStories 15M (INT4 Quantized for ESP32-S3)" if not is_ple else "TinyLM PLE Model for ESP32-S3"
    desc = (
        "Quantized INT4 weights designed to run locally on ESP32-S3 with 16MB Flash and Octal PSRAM."
        if not is_ple
        else "Custom trained TinyLM PLE model exported for direct mmap inference on ESP32-S3."
    )
    primary_bin = bin_filenames[0] if bin_filenames else "stories15M_q4.bin"

    card = f"""---
language:
- en
license: apache-2.0
tags:
- esp32
- esp32-s3
- tinystories
- edge-ai
- quantized
- int4
- embedded
pipeline_tag: text-generation
---

# {title}

{desc}

This model repository contains the binary weights, metadata, license, and tokenizer assets for the **[esp32-sandbox](https://github.com/nicholaswilde/esp32-sandbox)** project (`projects/s3-tiny-stories`).

## Model Details

- **Target Hardware**: ESP32-S3 (e.g., ESP32-S3-DevKitC-1-N16R8)
- **Flash Memory Required**: ≥ 16MB
- **PSRAM Required**: ≥ 8MB (Octal SPI recommended)
- **Quantization**: INT4 grouped quantization (`group_size = 64` or `128`) with FP16 scales
- **Partition Offset**: `0x110000` (mapped via `esp_partition_mmap`)
- **Included Files**:
  - `README.md` - Model Card and documentation
  - `LICENSE` - Apache 2.0 License
  - `metadata.json` - Hardware, quantization, and model architecture metadata
  - `*.bin` - Compiled INT4 model weights
  - `tokenizer.json` - SentencePiece / BPE vocabulary configuration

## Quick Flashing to ESP32-S3

Download the binary file (`{primary_bin}`) and flash it directly to your ESP32-S3:

```bash
# 1. Download model binary
hf download {repo_id} {primary_bin} --local-dir .

# 2. Flash to model partition (0x110000)
esptool --baud 921600 --port /dev/ttyACM0 write-flash 0x110000 {primary_bin}
```

## Running Inference

Refer to the [esp32-sandbox repository](https://github.com/nicholaswilde/esp32-sandbox/tree/main/projects/s3-tiny-stories) for firmware building, flashing, and serial monitoring.
"""
    return card


def generate_default_metadata(bin_name: str, is_ple: bool = False) -> dict:
    """Generate default metadata dictionary if metadata.json is not present."""
    if is_ple:
        return {
            "model_name": bin_name,
            "architecture": "TinyLM-PLE",
            "quantization": "int4_group_128",
            "target_hardware": {
                "mcu": "ESP32-S3",
                "flash_required_mb": 16,
                "psram_required_mb": 8,
                "flash_partition_offset": "0x110000",
            },
            "vocab_size": 32768,
            "inference_engine": "llama2.c compatible (esp_partition_mmap)",
        }
    return {
        "model_name": bin_name,
        "architecture": "TinyStories-15M",
        "base_model": "karpathy/tinyllamas",
        "quantization": "int4",
        "group_size": 64,
        "dim": 288,
        "hidden_dim": 768,
        "n_layers": 6,
        "n_heads": 6,
        "n_kv_heads": 6,
        "vocab_size": 32000,
        "seq_len": 256,
        "shared_classifier": True,
        "target_hardware": {
            "mcu": "ESP32-S3",
            "recommended_module": "ESP32-S3-DevKitC-1-N16R8",
            "flash_required_mb": 16,
            "psram_required_mb": 8,
            "flash_partition_offset": "0x110000",
        },
        "inference_engine": "llama2.c compatible (esp_partition_mmap)",
    }


def get_default_repo(api: HfApi, repo_name: str = "esp32-s3-tinystories") -> str:
    """Get default repo_id based on logged-in user."""
    try:
        user_info = api.whoami()
        username = user_info.get("name")
        if username:
            return f"{username}/{repo_name}"
    except Exception:
        pass
    return f"your-username/{repo_name}"


def collect_artifacts(
    target_path: Path, repo_root: Path, is_ple: bool = False
) -> Dict[str, Tuple[Optional[Path], Optional[str]]]:
    """Collect the 5 required files: README.md, LICENSE, metadata.json, *.bin, tokenizer.json.

    Returns dict mapping repo_dest_path -> (local_path_or_None, content_str_or_None).
    """
    artifacts: Dict[str, Tuple[Optional[Path], Optional[str]]] = {}

    if target_path.is_dir():
        base_dir = target_path
        bin_files = sorted(list(base_dir.glob("*.bin")))
    else:
        base_dir = target_path.parent
        bin_files = [target_path] if target_path.suffix == ".bin" else sorted(list(base_dir.glob("*.bin")))

    # 1. Model binary file(s) (*.bin)
    if not bin_files:
        print(f"Warning: No *.bin files found in {base_dir}", file=sys.stderr)
    for b in bin_files:
        artifacts[b.name] = (b, None)

    # 2. Tokenizer (tokenizer.json)
    tok_candidates = [
        base_dir / "tokenizer.json",
        repo_root / "projects" / "s3-tiny-stories" / "pc_tools" / "tokenizer.json",
        repo_root / "projects" / "s3-tiny-stories" / "data" / "tinystories" / "vocab-32768" / "tokenizer.json",
    ]
    for cand in tok_candidates:
        if cand.exists():
            artifacts["tokenizer.json"] = (cand, None)
            break
    if "tokenizer.json" not in artifacts:
        print("Warning: tokenizer.json not found in expected locations.", file=sys.stderr)

    # 3. Metadata (metadata.json)
    meta_candidate = base_dir / "metadata.json"
    if not meta_candidate.exists():
        meta_candidate = repo_root / "projects" / "s3-tiny-stories" / "pc_tools" / "metadata.json"

    if meta_candidate.exists():
        artifacts["metadata.json"] = (meta_candidate, None)
    else:
        primary_name = bin_files[0].name if bin_files else "model.bin"
        meta_data = generate_default_metadata(primary_name, is_ple=is_ple)
        artifacts["metadata.json"] = (None, json.dumps(meta_data, indent=2))

    # 4. License (LICENSE)
    license_candidate = base_dir / "LICENSE"
    if not license_candidate.exists():
        license_candidate = repo_root / "LICENSE"

    if license_candidate.exists():
        artifacts["LICENSE"] = (license_candidate, None)
    else:
        print("Warning: LICENSE file not found.", file=sys.stderr)

    # 5. README.md (Model Card)
    readme_candidate = base_dir / "README.md"
    if readme_candidate.exists() and readme_candidate != (repo_root / "projects" / "s3-tiny-stories" / "README.md"):
        artifacts["README.md"] = (readme_candidate, None)
    else:
        bin_names = [b.name for b in bin_files] if bin_files else ["stories15M_q4.bin"]
        card_content = generate_model_card("REPO_ID_PLACEHOLDER", bin_names, is_ple=is_ple)
        artifacts["README.md"] = (None, card_content)

    return artifacts


def main():
    parser = argparse.ArgumentParser(
        description="Upload ESP32-S3 model artifacts (README.md, LICENSE, metadata.json, *.bin, tokenizer.json) to Hugging Face Hub."
    )
    parser.add_argument(
        "--path",
        "-p",
        "--bin",
        type=str,
        default="pc_tools/stories15M_q4.bin",
        help="Local path to model binary or directory (default: pc_tools/stories15M_q4.bin)",
    )
    parser.add_argument(
        "--repo-id",
        "-r",
        type=str,
        default=None,
        help="Hugging Face repository ID (<username>/<repo_name>). Defaults to <current_user>/esp32-s3-tinystories",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Make repository private if newly created",
    )
    parser.add_argument(
        "--commit-message",
        "-m",
        type=str,
        default=None,
        help="Custom commit message for Hugging Face git history",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate upload without uploading files or creating repositories",
    )

    args = parser.parse_args()

    api = HfApi()

    # Verify authentication
    try:
        user_info = api.whoami()
        username = user_info.get("name")
        print(f"✓ Authenticated as Hugging Face user: {username} ({user_info.get('fullname', '')})")
    except Exception as e:
        print(f"Error: Not authenticated with Hugging Face ({e}).", file=sys.stderr)
        print("Run 'hf auth login' or 'uv run hf auth login' first.", file=sys.stderr)
        sys.exit(1)

    repo_id = args.repo_id or get_default_repo(api)
    print(f"Target repository: https://huggingface.co/{repo_id}")

    upload_path = Path(args.path).resolve()
    if not upload_path.exists():
        print(f"Error: Specified path does not exist: {upload_path}", file=sys.stderr)
        sys.exit(1)

    # Locate repo root
    # Search upwards for LICENSE or .git
    curr = upload_path
    repo_root = curr
    for parent in [curr] + list(curr.parents):
        if (parent / ".git").exists() or (parent / "LICENSE").exists():
            repo_root = parent
            break

    is_ple = "ple" in upload_path.name.lower() or "ple" in str(upload_path).lower()
    artifacts = collect_artifacts(upload_path, repo_root, is_ple=is_ple)

    # Replace repo_id placeholder in README if generated
    if "README.md" in artifacts:
        local_path, content = artifacts["README.md"]
        if content and "REPO_ID_PLACEHOLDER" in content:
            artifacts["README.md"] = (local_path, content.replace("REPO_ID_PLACEHOLDER", repo_id))

    print("\n📦 Files prepared for Hugging Face Hub upload:")
    print(f"{'File':<20} | {'Source':<50} | {'Size'}")
    print("-" * 80)
    for dest_name, (local_file, content) in artifacts.items():
        if local_file and local_file.exists():
            size_str = f"{local_file.stat().st_size / 1024:.1f} KB"
            if local_file.stat().st_size > 1024 * 1024:
                size_str = f"{local_file.stat().st_size / (1024*1024):.2f} MB"
            print(f"{dest_name:<20} | {str(local_file):<50} | {size_str}")
        else:
            size_str = f"{len(content.encode('utf-8'))} B" if content else "0 B"
            print(f"{dest_name:<20} | {'<auto-generated>':<50} | {size_str}")

    commit_msg = args.commit_message or f"Upload model artifacts for ESP32-S3 ({', '.join(artifacts.keys())})"

    if args.dry_run:
        print(f"\n[DRY-RUN] Would create/verify repo: {repo_id} (private={args.private})")
        print(f"[DRY-RUN] Would commit with message: '{commit_msg}'")
        print("[DRY-RUN] No files were uploaded.")
        return

    # Ensure repository exists
    try:
        api.create_repo(repo_id=repo_id, repo_type="model", private=args.private, exist_ok=True)
        print(f"\n✓ Verified repository: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"Warning: could not create or verify repo {repo_id}: {e}", file=sys.stderr)

    # Upload files
    print(f"\nUploading {len(artifacts)} files to {repo_id}...")
    for dest_name, (local_file, content) in artifacts.items():
        if local_file and local_file.exists():
            api.upload_file(
                path_or_fileobj=str(local_file),
                path_in_repo=dest_name,
                repo_id=repo_id,
                repo_type="model",
                commit_message=f"Upload {dest_name}",
            )
        elif content:
            api.upload_file(
                path_or_fileobj=content.encode("utf-8"),
                path_in_repo=dest_name,
                repo_id=repo_id,
                repo_type="model",
                commit_message=f"Add {dest_name}",
            )
        print(f"  ✓ Uploaded {dest_name}")

    print(f"\n✨ All files uploaded! View your model at: https://huggingface.co/{repo_id}")


if __name__ == "__main__":
    main()
