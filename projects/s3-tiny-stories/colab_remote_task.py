#!/usr/bin/env python3
"""
Remote execution script for building/training s3-tiny-stories on Google Colab (Free Tier).

This script runs inside the Colab VM environment. It handles:
1. Environment validation (verifying T4 GPU or CPU free-tier runtime).
2. Dependency installation (tokenizers, huggingface_hub, requests, numpy).
3. Workspace setup (unpacking uploaded payload or cloning repository).
4. Running the selected action (quantize, train-test, or train-full).
5. Staging output artifacts to /content/output/ for download back to host.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


def log(msg: str):
    print(f"[colab-task] {msg}", flush=True)


def check_environment():
    log("=== Checking Environment ===")
    try:
        import torch
        log(f"PyTorch version: {torch.__version__}")
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            log(f"GPU detected: {gpu_name} (Free Tier T4 recommended)")
        else:
            log("No CUDA GPU detected; running on CPU (Free Tier).")
    except ImportError:
        log("PyTorch not imported yet.")


def install_dependencies():
    log("=== Installing Dependencies ===")
    pkgs = ["tokenizers", "huggingface_hub", "requests", "numpy"]
    cmd = [sys.executable, "-m", "pip", "install", "-q"] + pkgs
    subprocess.run(cmd, check=True)
    log("Dependencies installed successfully.")


def setup_workspace(base_dir: Path) -> Path:
    log("=== Setting up Workspace ===")
    payload_tar = Path("/content/payload.tar.gz")
    work_dir = base_dir / "s3-tiny-stories"

    if payload_tar.exists():
        log(f"Extracting uploaded payload from {payload_tar}...")
        work_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(payload_tar, "r:gz") as tar:
            tar.extractall(path=work_dir)
        log(f"Extracted payload into {work_dir}")
        return work_dir

    repo_dir = Path("/content/esp32-sandbox")
    if not repo_dir.exists():
        log("Cloning repository from GitHub...")
        subprocess.run(
            ["git", "clone", "https://github.com/nicholaswilde/esp32-sandbox.git", str(repo_dir)],
            check=True,
        )
    target = repo_dir / "projects" / "s3-tiny-stories"
    if target.exists():
        return target
    return repo_dir


def run_quantize(work_dir: Path, output_dir: Path):
    log("=== Action: Quantize Pre-trained TinyStories 15M (INT4) ===")
    pc_tools = work_dir / "pc_tools"
    export_script = pc_tools / "export_model.py"
    generate_vocab_script = pc_tools / "generate_vocab.py"

    out_bin = pc_tools / "stories15M_q4.bin"
    log(f"Running {export_script} ...")
    subprocess.run(
        [sys.executable, str(export_script), str(out_bin)],
        cwd=str(pc_tools),
        check=True,
    )

    if generate_vocab_script.exists():
        log("Generating vocab header...")
        subprocess.run(
            [sys.executable, str(generate_vocab_script)],
            cwd=str(work_dir),
            check=True,
        )

    # Stage artifacts
    if out_bin.exists():
        dest = output_dir / "stories15M_q4.bin"
        shutil.copy2(out_bin, dest)
        log(f"Staged {dest} ({dest.stat().st_size / (1024*1024):.2f} MB)")

    vocab_h = work_dir / "src" / "generated" / "vocab.h"
    if vocab_h.exists():
        shutil.copy2(vocab_h, output_dir / "vocab.h")
        log(f"Staged {output_dir / 'vocab.h'}")

    tok_json = pc_tools / "tokenizer.json"
    if tok_json.exists():
        shutil.copy2(tok_json, output_dir / "tokenizer.json")
        log(f"Staged {output_dir / 'tokenizer.json'}")


def run_train(work_dir: Path, output_dir: Path, is_full: bool):
    target_core = 15000000 if is_full else 1500000
    steps = 5000 if is_full else 500
    tag = f"baseline_v32768_c{target_core}_s0"
    log(f"=== Action: Train Custom TinyLM Model (Full={is_full}, Steps={steps}) ===")

    # Step 1: Prepare data and tokenizer
    log("Preparing dataset slice and BPE tokenizer...")
    subprocess.run(
        [sys.executable, "-m", "research.tinystories.prepare", "--vocab", "32768"],
        cwd=str(work_dir),
        check=True,
    )

    # Step 2: Train model
    log(f"Training model ({target_core:,} params, {steps} steps) on GPU...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "research.tinystories.train",
            "--arm",
            "baseline",
            "--vocab",
            "32768",
            "--target-core",
            str(target_core),
            "--steps",
            str(steps),
            "--seed",
            "0",
            "--micro-batch-size",
            "8",
        ],
        cwd=str(work_dir),
        check=True,
    )

    # Step 3: Export model
    log("Exporting checkpoint to packed binary format...")
    tok_path = work_dir / "data" / "tinystories" / "vocab-32768" / "tokenizer.json"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "research.tinystories.export",
            "--tokenizer",
            str(tok_path),
            tag,
        ],
        cwd=str(work_dir),
        check=True,
    )

    # Stage artifacts
    art_dir = work_dir / "artifacts" / "tinystories"
    if art_dir.exists():
        for f in art_dir.glob("*.bin"):
            dest = output_dir / f.name
            shutil.copy2(f, dest)
            log(f"Staged model binary {dest} ({dest.stat().st_size / (1024*1024):.2f} MB)")
    if tok_path.exists():
        shutil.copy2(tok_path, output_dir / "tokenizer.json")
        log(f"Staged {output_dir / 'tokenizer.json'}")


def main():
    parser = argparse.ArgumentParser(description="Google Colab Remote Task Runner for s3-tiny-stories")
    parser.add_argument(
        "--action",
        choices=["quantize", "train-test", "train-full"],
        default="quantize",
        help="Build/training action to perform",
    )
    args = parser.parse_args()

    base_dir = Path("/content")
    output_dir = base_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    check_environment()
    install_dependencies()
    work_dir = setup_workspace(base_dir)

    if args.action == "quantize":
        run_quantize(work_dir, output_dir)
    elif args.action == "train-test":
        run_train(work_dir, output_dir, is_full=False)
    elif args.action == "train-full":
        run_train(work_dir, output_dir, is_full=True)

    log("=== Task Complete ===")
    log("Artifacts available in /content/output/:")
    for item in output_dir.iterdir():
        log(f"  - {item.name} ({item.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
