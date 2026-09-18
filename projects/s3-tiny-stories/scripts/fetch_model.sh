#!/usr/bin/env bash
# Download the released TinyStories model and tokenizer, verified against pinned SHA-256 hashes.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$ROOT/pc_tools"
mkdir -p "$TARGET_DIR"

REPO="slvDev/esp32-ai-tinystories"
MODEL_SHA="1d8326c05c383ccfa615f5455575802817cb453dbc7ab28875d41a9dbb45477e"
MODEL_BYTES="14912348"
TOK_SHA="4e28163669f2249af31a528a54fc25064dcbd0a34edbfa7bedb16d2d600ec7ae"
TOK_BYTES="1788896"

echo "Fetching model.bin from $REPO..."
uv run --no-project --with 'huggingface-hub' python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='$REPO', filename='model.bin', local_dir='$TARGET_DIR')"

echo "Fetching tokenizer.json from $REPO..."
uv run --no-project --with 'huggingface-hub' python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='$REPO', filename='tokenizer.json', local_dir='$TARGET_DIR')"

# Verify SHA256
echo "$MODEL_SHA  $TARGET_DIR/model.bin" | sha256sum -c -
echo "$TOK_SHA  $TARGET_DIR/tokenizer.json" | sha256sum -c -

echo "Model and tokenizer verified successfully in $TARGET_DIR"
