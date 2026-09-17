# :bread: ESP32-S3 Sourdough Baker Assistant :robot:

An offline, on-device AI assistant for sourdough bread baking and troubleshooting that runs locally on an **ESP32-S3** microcontroller.

Inspired by [slvDev/esp32-ai-barista](https://huggingface.co/slvDev/esp32-ai-barista), this model uses a lightweight **Per-Layer Embeddings (PLE)** architecture and a compact 2,048-token vocabulary to fit entirely into flash and PSRAM without requiring internet access or external APIs.

---

## :sparkles: Features

*   **Architecture**: Per-Layer Embeddings (PLE) micro-LLM (~2.3M params).
*   **Target Hardware**: ESP32-S3 with ≥ 16MB Flash and Octal PSRAM (e.g. `ESP32-S3-DevKitC-1-N16R8`).
*   **Vocabulary**: 2,048-token ByteLevel BPE tokenizer tailored for baking terms.
*   **Quantization**: INT4 grouped quantization (`group_size = 128`) mapped directly from flash via `esp_partition_mmap` at offset `0x110000`.
*   **Troubleshooting Domains**:
    1.  **Starter Health**: Hooch, sluggish rising, acetone/nail polish smell, mold detection, feeding ratios (1:1:1 vs 1:5:5), refrigeration.
    2.  **Bulk Fermentation**: Volume rise indicators, under-fermentation (fool's crumb), over-fermentation, poke test, stretch & folds, dough temperature.
    3.  **Hydration & Shaping**: Sticky dough handling, banneton sticking (50/50 rice flour dusting), cold retard benefits, autolyse, beginner hydrations.
    4.  **Scoring & Baking**: Blade angle (30–45° for ears), steam importance, Dutch oven temps & times, gummy crumb prevention, burnt bottom deflection.
    5.  **Baker's Math**: Baker's percentages, standard 100/70/20/2 sourdough formula, salt functions.

---

## :clipboard: Prerequisites

Ensure you have the following tools installed:
*   [PlatformIO Core (CLI)](https://docs.platformio.org/en/latest/core/index.html)
*   [go-task](https://taskfile.dev/)
*   [uv](https://github.com/astral-sh/uv) (Python dependency manager)
*   [huggingface-hub](https://huggingface.co/docs/huggingface_hub/en/guides/cli) (`hf` CLI)
*   [esptool.py](https://docs.espressif.com/projects/esptool/en/latest/esp32/)

---

## :gear: Setup & Training Workflow

### 0. Navigation & Active Project
Navigate to the project directory:
```bash
cd projects/s3-sourdough
```
*(Or set `CURRENT_PROJECT=s3-sourdough` in the root `.env` file).*

### 1. Generate the Q&A Dataset
Expands the 28 curated sourdough troubleshooting topics into 2,500 conversational Q&A training pairs with varied prefixes and phrasings:
```bash
task generate
```
Outputs in `data/sourdough/raw/`:
* `sourdough_qa.jsonl` (Structured JSON lines dataset)
* `sourdough_corpus.txt` (Text corpus formatted with `<|endoftext|>` delimiters, ~93k words)

### 2. Train Tokenizer and Prepare Binary Bins
Trains a compact 2,048-token ByteLevel BPE tokenizer and encodes the corpus into `uint16` memmapped arrays:
```bash
task prepare
```
Outputs in `data/sourdough/vocab-2048/`:
* `tokenizer.json` (BPE vocabulary and merge table)
* `train.bin` (95% training split, ~115k tokens)
* `val.bin` (5% validation split, ~6k tokens)

### 3. Train the Model
Trains the **Per-Layer Embeddings (PLE)** micro-LLM (~2.3M parameters):
```bash
task train
```
*   **Speed**: ~2–3 minutes on CPU (or seconds on CUDA GPU).
*   **Metrics**: Logs training loss, validation loss, and perplexity (PPL) every 100 steps.
*   **Checkpoint**: Saved to `runs/sourdough/ple-sourdough-v1-s0.pt`.

*Advanced Options:*
```bash
# Train for additional steps or custom learning rates:
uv run python -m research.sourdough.train --steps 1000 --eval-every 100 --arm ple --lr 1e-3
```

### 4. Interactive Test (Prompt Sampling)
Query the trained model with baking troubleshooting questions directly in your terminal:
```bash
# Question 1: Starter liquid / hooch
task sample PROMPT="Why is there liquid on top of my sourdough starter?"

# Question 2: Scoring & ears
task sample PROMPT="Why didn't my sourdough bread develop an ear?"

# Question 3: Gummy crumb
task sample PROMPT="Why is the inside of my loaf gummy?"

# Question 4: Fermentation timing
task sample PROMPT="How do I know when bulk fermentation is finished?"

# Question 5: Sticky dough
task sample PROMPT="My dough is too sticky to shape. What should I do?"
```

### 5. Run Native Host Firmware Tests
Verify the C++ firmware compilation and unit tests against Unity:
```bash
# From within projects/s3-sourdough/
pio test -e native

# Or from repository root:
task test:s3-sourdough
```

---

## :cloud: Hugging Face Model Hub

Upload the trained weights and the 5-file bundle (`README.md`, `LICENSE`, `metadata.json`, `*.bin`, `tokenizer.json`) to Hugging Face Hub:

```bash
# Preview upload files and sizes without pushing (Dry Run)
uv run python upload_model_hf.py --dry-run

# Upload to your Hugging Face account (<username>/esp32-s3-sourdough)
task upload-model
```

---

## :zap: Flashing to the ESP32-S3

1. **Flash Model Weights Partition (`0x110000`)**:
   ```bash
   task flash-model
   ```

2. **Compile and Upload Firmware**:
   ```bash
   task build
   task flash
   ```

3. **Open Serial Monitor**:
   ```bash
   task monitor
   ```

---

## :link: References

*   [slvDev/esp32-ai-barista](https://huggingface.co/slvDev/esp32-ai-barista) - Dedicated espresso troubleshooting LLM for ESP32
*   [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - Minimalist C inference engine
