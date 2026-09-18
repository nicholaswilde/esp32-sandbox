#!/usr/bin/env python3
"""Validate and test Sourdough dataset integrity without training the model.

Features:
1. Validation Checks:
   - Tokenizer round-trip fidelity (Encode -> Decode == original)
   - Sequence length distribution vs context window (128 tokens)
   - Vocabulary ID boundaries (< vocab size)
   - Binary bin integrity (train.bin, val.bin)
   - Category distribution balance

2. Interactive Retrieval / Matcher Test:
   - Queries dataset using TF-IDF / token similarity to verify how questions match
     expected answers before training the neural network.
"""

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "sourdough"


def run_checks(vocab_size: int = 2048, seq_len: int = 128):
    qa_file = DATA_ROOT / "raw" / "sourdough_qa.jsonl"
    tok_file = DATA_ROOT / f"vocab-{vocab_size}" / "tokenizer.json"
    train_bin = DATA_ROOT / f"vocab-{vocab_size}" / "train.bin"
    val_bin = DATA_ROOT / f"vocab-{vocab_size}" / "val.bin"

    if not qa_file.exists():
        print(f"Error: {qa_file} not found. Run 'task generate' first.")
        return False
    if not tok_file.exists() or not train_bin.exists():
        print(f"Error: Tokenizer or bin files not found in {DATA_ROOT / f'vocab-{vocab_size}'}. Run 'task prepare' first.")
        return False

    print("=== Sourdough Dataset Validation ===")
    records = [json.loads(line) for line in qa_file.read_text().splitlines() if line]
    print(f"Total Q&A pairs in JSONL: {len(records):,}")

    tok = Tokenizer.from_file(str(tok_file))
    print(f"Tokenizer vocabulary size: {tok.get_vocab_size():,}")

    # Check token lengths and roundtrip
    lengths = []
    roundtrip_errors = 0
    categories = Counter()

    for r in records:
        categories[r.get("category", "unknown")] += 1
        text = f"User: {r['prompt']}\nAssistant: {r['completion']}<|endoftext|>"
        enc = tok.encode(text)
        lengths.append(len(enc.ids))
        dec = tok.decode(enc.ids, skip_special_tokens=False)
        if dec != text:
            roundtrip_errors += 1

    max_len = max(lengths)
    min_len = min(lengths)
    avg_len = sum(lengths) / len(lengths)
    exceeds = sum(1 for l in lengths if l > seq_len)

    print("\n--- Sequence Lengths ---")
    print(f"  Target context window (seq_len): {seq_len} tokens")
    print(f"  Max sequence length:             {max_len} tokens")
    print(f"  Min sequence length:             {min_len} tokens")
    print(f"  Avg sequence length:             {avg_len:.1f} tokens")
    print(f"  Exceeding context window:        {exceeds} (must be 0)")

    print("\n--- Tokenizer Fidelity ---")
    print(f"  Round-trip decode errors:        {roundtrip_errors} (must be 0)")

    print("\n--- Category Breakdown ---")
    for cat, count in sorted(categories.items()):
        pct = (count / len(records)) * 100
        print(f"  - {cat:<22}: {count:5d} ({pct:5.1f}%)")

    # Binary bin validation
    print("\n--- Binary Token Bins ---")
    train_tokens = np.fromfile(train_bin, dtype=np.uint16)
    val_tokens = np.fromfile(val_bin, dtype=np.uint16)

    print(f"  train.bin: {len(train_tokens):,} tokens ({train_bin.stat().st_size:,} bytes)")
    print(f"             ID range: [{train_tokens.min()}, {train_tokens.max()}] (limit: < {vocab_size})")
    print(f"  val.bin:   {len(val_tokens):,} tokens ({val_bin.stat().st_size:,} bytes)")
    print(f"             ID range: [{val_tokens.min()}, {val_tokens.max()}] (limit: < {vocab_size})")

    all_passed = (
        exceeds == 0
        and roundtrip_errors == 0
        and train_tokens.max() < vocab_size
        and val_tokens.max() < vocab_size
    )

    if all_passed:
        print("\n✓ ALL DATASET INTEGRITY CHECKS PASSED!")
    else:
        print("\n✗ SOME CHECKS FAILED.")
    return all_passed


def query_dataset(query_text: str, top_k: int = 3):
    """Simple token-overlap / similarity search over dataset."""
    qa_file = DATA_ROOT / "raw" / "sourdough_qa.jsonl"
    if not qa_file.exists():
        print(f"Error: {qa_file} not found.")
        return

    records = [json.loads(line) for line in qa_file.read_text().splitlines() if line]
    query_tokens = set(query_text.lower().replace("?", "").replace(",", "").split())

    scored = []
    for r in records:
        prompt_tokens = set(r["prompt"].lower().replace("?", "").replace(",", "").split())
        overlap = query_tokens.intersection(prompt_tokens)
        if not overlap:
            continue
        # Jaccard similarity score
        score = len(overlap) / len(query_tokens.union(prompt_tokens))
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\nQuery: \"{query_text}\"")
    if not scored:
        print("No matching QA entry found in dataset.")
        return

    print(f"Top {min(top_k, len(scored))} matches in training dataset:\n")
    seen_answers = set()
    count = 0
    for score, r in scored:
        if r["completion"] in seen_answers:
            continue
        seen_answers.add(r["completion"])
        count += 1
        print(f"Match #{count} (Score: {score:.2f} | Category: {r['category']}):")
        print(f"  Prompt:     {r['prompt']}")
        print(f"  Answer:     {r['completion']}\n")
        if count >= top_k:
            break


def main():
    parser = argparse.ArgumentParser(description="Test and validate Sourdough dataset without training.")
    parser.add_argument("--query", "-q", type=str, default=None, help="Test query against the dataset")
    parser.add_argument("--vocab", type=int, default=2048, help="Vocabulary size (default: 2048)")
    parser.add_argument("--seq-len", type=int, default=128, help="Context length (default: 128)")
    args = parser.parse_args()

    if args.query:
        query_dataset(args.query)
    else:
        run_checks(vocab_size=args.vocab, seq_len=args.seq_len)


if __name__ == "__main__":
    main()
