#!/usr/bin/env python3
"""Build frozen output vocabulary for Sourdough Baker Assistant.

Follows the asymmetric vocabulary design from slvDev/esp32-ai-barista:
Constrains the model's output predictions to a curated dictionary of full words,
punctuation, and special tokens. Non-dictionary gibberish and broken subwords
are rendered literally unsayable.

Outputs:
  - data/sourdough/vocab.json
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "sourdough"
RAW_QA_PATH = DATA_DIR / "raw" / "sourdough_qa.jsonl"
OUT_VOCAB_PATH = DATA_DIR / "vocab.json"

SPECIALS = ["<pad>", "<bos>", "<eos>", "<unk>"]
PUNCTUATION = [",", ".", ":", ";", "?", "%"]

COMMON_FUNCTION_WORDS = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "just", "me", "more", "most", "must", "my", "myself",
    "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "shouldn't", "so", "some", "such", "than", "that", "the", "their", "theirs",
    "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we",
    "were", "weren't", "what", "when", "where", "which", "while", "who", "whom",
    "why", "will", "with", "won't", "would", "wouldn't", "you", "you're", "your", "yours"
]

NUMBER_WORDS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "twenty", "thirty", "fifty", "half", "double", "triple"
]


def tokenize_answer(text: str) -> List[str]:
    """Tokenize answer text into lowercase words, ASCII digits, and punctuation."""
    text = text.replace("\u00b0", " ").replace("\u00ba", " ").replace("%", " % ")
    raw = re.findall(r"[a-zA-Z0-9]+(?:'[a-zA-Z]+)?|[.,:;?%]", text)
    tokens = []
    for t in raw:
        clean = t.lower()
        if all(0x20 <= ord(c) <= 0x7E for c in clean):
            tokens.append(clean)
    return tokens


def build_vocabulary(qa_path: Path) -> Dict:
    if not qa_path.exists():
        raise FileNotFoundError(f"QA dataset not found: {qa_path}. Run generate task first.")

    existing_answer_words = set()
    with open(qa_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            ans = item.get("completion", "")
            for token in tokenize_answer(ans):
                if token not in SPECIALS and token not in PUNCTUATION:
                    existing_answer_words.add(token)

    tokens = []
    tier_counts = {
        "punctuation": len(SPECIALS) + len(PUNCTUATION),
        "answers_existing": 0,
        "function": 0,
        "numbers": 0,
    }

    # 1. Specials (classes 0..3)
    for s in SPECIALS:
        tokens.append({"token": s, "tier": "punctuation"})

    # 2. Punctuation
    for p in PUNCTUATION:
        tokens.append({"token": p, "tier": "punctuation"})

    # 3. Existing answer words
    for w in sorted(existing_answer_words):
        tokens.append({"token": w, "tier": "answers_existing"})
        tier_counts["answers_existing"] += 1

    # 4. Function words not already present
    function_additions = [w for w in COMMON_FUNCTION_WORDS if w not in existing_answer_words and w not in PUNCTUATION]
    for w in sorted(function_additions):
        tokens.append({"token": w, "tier": "function"})
        tier_counts["function"] += 1

    # 5. Number words not already present
    number_additions = [w for w in NUMBER_WORDS if w not in existing_answer_words and w not in function_additions]
    for w in sorted(number_additions):
        tokens.append({"token": w, "tier": "numbers"})
        tier_counts["numbers"] += 1

    vocab_data = {
        "version": "sourdough-v1",
        "total": len(tokens),
        "tokens": tokens,
        "tier_counts": tier_counts,
    }
    return vocab_data


def main():
    parser = argparse.ArgumentParser(description="Build frozen output vocabulary for Sourdough.")
    parser.add_argument("--qa-path", type=Path, default=RAW_QA_PATH, help="Path to sourdough_qa.jsonl")
    parser.add_argument("--out", type=Path, default=OUT_VOCAB_PATH, help="Output vocab.json path")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    vocab_data = build_vocabulary(args.qa_path)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(vocab_data, f, indent=2)

    print(f"✓ Saved output vocabulary ({vocab_data['total']} tokens) to {args.out}")
    print("  Tier breakdown:")
    for tier, count in vocab_data["tier_counts"].items():
        print(f"    - {tier:18s}: {count}")


if __name__ == "__main__":
    main()
