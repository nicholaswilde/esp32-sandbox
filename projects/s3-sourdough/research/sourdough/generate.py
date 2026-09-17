#!/usr/bin/env python3
"""Generate curated and expanded Q&A dataset for sourdough bread baking.

Outputs:
  - data/sourdough/raw/sourdough_qa.jsonl
  - data/sourdough/raw/sourdough_corpus.txt (formatted for language model pretraining / instruction tuning)
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Dict

from research.sourdough.knowledge import QA_ENTRIES, CATEGORIES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "sourdough" / "raw"

PROMPT_PREFIXES = [
    "",
    "Hi, ",
    "Hello, ",
    "Hey baker, ",
    "Quick question: ",
    "I have a problem: ",
    "Troubleshooting sourdough: ",
    "Can you help me? ",
    "Help, ",
]


def expand_dataset(entries: List[Dict], target_samples: int = 2500, seed: int = 42) -> List[Dict]:
    """Expand seed QA pairs with realistic user conversational variations."""
    rng = random.Random(seed)
    dataset = []

    # First add all canonical questions exactly as written
    for entry in entries:
        for q in entry["questions"]:
            dataset.append({
                "prompt": q,
                "completion": entry["answer"],
                "category": entry["category"],
            })

    # Now synthetically expand with prefixes, minor casing/punctuation changes, and combinations
    while len(dataset) < target_samples:
        entry = rng.choice(entries)
        base_q = rng.choice(entry["questions"])
        prefix = rng.choice(PROMPT_PREFIXES)

        # Style variants
        q_variant = base_q
        rand_style = rng.random()
        if rand_style < 0.2:
            q_variant = q_variant.lower()
        elif rand_style < 0.4 and q_variant.endswith("?"):
            q_variant = q_variant[:-1]

        # Combine with prefix
        if prefix:
            # lower first character if after prefix
            if prefix.endswith(": ") or prefix.endswith("? ") or prefix.endswith(", "):
                q_variant = prefix + q_variant[0].upper() + q_variant[1:]
            else:
                q_variant = prefix + q_variant

        dataset.append({
            "prompt": q_variant,
            "completion": entry["answer"],
            "category": entry["category"],
        })

    rng.shuffle(dataset)
    return dataset


def main():
    parser = argparse.ArgumentParser(description="Generate Sourdough Q&A dataset.")
    parser.add_argument(
        "--samples",
        type=int,
        default=2500,
        help="Target number of Q&A samples to generate (default: 2500)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for repeatable expansion (default: 42)",
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = OUTPUT_DIR / "sourdough_qa.jsonl"
    txt_path = OUTPUT_DIR / "sourdough_corpus.txt"

    print(f"Expanding seed QA pairs ({len(QA_ENTRIES)} topics) to ~{args.samples} samples...")
    dataset = expand_dataset(QA_ENTRIES, target_samples=args.samples, seed=args.seed)

    # Write JSONL
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")

    # Write plaintext pretraining / tuning corpus
    # Format with endoftext tokens: <|endoftext|>User: {q}\nAssistant: {a}<|endoftext|>\n
    total_words = 0
    with open(txt_path, "w", encoding="utf-8") as f:
        for item in dataset:
            block = f"<|endoftext|>User: {item['prompt']}\nAssistant: {item['completion']}<|endoftext|>\n"
            f.write(block)
            total_words += len(block.split())

    file_size_kb = txt_path.stat().st_size / 1024
    print(f"\n✓ Generated {len(dataset):,} Q&A pairs:")
    print(f"  JSONL dataset:  {jsonl_path}")
    print(f"  Text corpus:    {txt_path} ({file_size_kb:.1f} KB, ~{total_words:,} words)")

    # Category breakdown
    print("\nCategory distribution:")
    counts = {}
    for item in dataset:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    for cat in CATEGORIES:
        print(f"  - {cat:<22}: {counts.get(cat, 0):4d} samples")


if __name__ == "__main__":
    main()
