# :book: S3 Tiny Stories :robot:

[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-nicholascwilde%2Fesp32--s3--tinystories-ffd21e)](https://huggingface.co/nicholascwilde/esp32-s3-tinystories)

This project runs a quantized language model locally on an ESP32-S3. It utilizes a lightweight C inference engine (adapted from `llama2.c`) to generate text from the TinyStories dataset entirely offline. Pre-quantized model binaries, tokenizers, and metadata are published at [nicholascwilde/esp32-s3-tinystories](https://huggingface.co/nicholascwilde/esp32-s3-tinystories).

Due to the size of the model weights, this project requires an ESP32-S3 with at least 16MB of Flash and Octal PSRAM (such as the ESP32-S3-DevKitC-1-N16R8). The weights are quantized to INT4 (~8.1 MB) and stored in a dedicated Flash partition mapped directly into address space via `esp_partition_mmap`.

## :sparkles: Features

*   **Model**: TinyStories 15M (6 layers, 6 heads, 288 embedding dimension, 768 hidden dimension, 32k vocabulary).
*   **Quantization**: INT4 grouped quantization (`group_size = 64`) with interleaved FP16 scales.
*   **Sampling**: Temperature (`temperature = 0.9`) and Top-P (`top_p = 0.9`) sampling using an efficient in-place random generator and PSRAM probability buffer.
*   **Tokenizer**: SentencePiece 32k vocabulary with full UTF-8 byte-fallback support directly decoded on-device.

## :clipboard: Prerequisites

Ensure you have the following tools installed on your host machine:
*   [PlatformIO Core (CLI)](https://docs.platformio.org/en/latest/core/index.html)
*   [go-task](https://taskfile.dev/)
*   [uv](https://github.com/astral-sh/uv) (for Python dependency management)
*   [huggingface-hub](https://huggingface.co/docs/huggingface_hub/en/guides/cli) (`hf` CLI) - for downloading and uploading model weights and tokenizers
*   [esptool.py](https://docs.espressif.com/projects/esptool/en/latest/esp32/)
*   [google-colab-cli](https://github.com/googlecolab/colab-cli) (`colab`) - optional, for running builds and training on Google Colab Free Tier


## :gear: Setup Workflow

The build and deployment process involves preparing the quantized model weights, flashing them to the custom flash partition, and flashing the firmware.

### :arrow_down: 1. Fetch and Quantize the Model

Download the pre-trained TinyStories 15M weights and quantize them to the INT4 format:

```bash
task quantize
```

*(Alternatively, pre-exported weights can be downloaded with `task fetch-model`)*.

### :cloud: Google Colab Free Tier (Accelerated GPU Build & Training)

You can offload INT4 quantization or custom model training to Google Colab using the **Free Tier** (T4 GPU or CPU), avoiding local CPU/RAM bottlenecks and getting 10x+ training speedups:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nicholaswilde/esp32-sandbox/blob/main/projects/s3-tiny-stories/s3_tiny_stories_colab.ipynb)

#### Option A: Standalone Colab Notebook
Open [`s3_tiny_stories_colab.ipynb`](file:///home/nicholas/git/nicholaswilde/esp32-sandbox/projects/s3-tiny-stories/s3_tiny_stories_colab.ipynb) directly in Google Colab:
1. **Set Hardware Accelerator**: Select **Runtime** > **Change runtime type** > **T4 GPU** (Free Tier).
2. **Execute Steps**:
   - **Track 1 (Quantize)**: Downloads `karpathy/tinyllamas` `stories15M.pt` and quantizes it to 4-bit INT4 (`stories15M_q4.bin`, ~8.1MB).
   - **Track 2 (Train Custom)**: Downloads the TinyStories dataset slice, trains the 32k BPE tokenizer, trains a custom TinyLM model on CUDA, and exports to the packed INT4 binary format.
   - **Test Generation**: Interactively sample text from the model directly within the notebook.
3. **Download**: Run the download cell to save the `.bin` model file locally. Move it to `projects/s3-tiny-stories/pc_tools/` and flash with `task flash-model`.

#### Option B: Automated CLI Workflow (`colab-cli`)
If you have the `colab` CLI installed (`uv tool install google-colab-cli`), you can drive the entire Colab provisioning, build, download, and cleanup process from your terminal:

1. **One-Time Authentication**:
   Verify CLI authentication (launches browser authorization if first time):
   ```bash
   task colab-check
   # or interactive login: colab sessions
   ```
   *(For Application Default Credentials, use: `gcloud auth application-default login --scopes=openid,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/colaboratory`)*.

2. **Build / Quantize Pre-trained Model**:
   ```bash
   task colab-quantize
   ```
   *Automatically provisions a free-tier Colab session (T4 GPU or CPU fallback), quantizes the 15M model, downloads `stories15M_q4.bin` to `pc_tools/`, and stops the VM session.*

3. **Train Custom TinyLM Model on Free T4 GPU**:
   ```bash
   # Quick test run (1.5M params, 500 steps, ~1-2 min on T4 GPU)
   task colab-train-test

   # Full run (15M params, 5000 steps, ~15-20 min on T4 GPU)
   task colab-train-full
   ```
   *Downloads the exported `.bin` model artifact directly into `artifacts/tinystories/`.*

4. **Stop Session**:
   ```bash
   task colab-stop
   ```
   *(Sessions are automatically stopped by default after builds to conserve free-tier quotas).*

5. **Flash Model to ESP32-S3**:
   Once downloaded, flash the model directly to the Flash partition (`0x110000`):
   ```bash
   task flash-model
   ```



### :zap: 2. Flash the Model Partition

The custom `partitions.csv` allocates a large model partition starting at offset `0x110000` (subtype `0x40`, size `0xEE0000`). Flash the quantized binary directly to this address:

```bash
task flash-model
```

### :hammer: 3. Build and Flash the Firmware

Compile and upload the C inference engine to the ESP32-S3:

```bash
task build
task flash
```

### :rocket: 4. Run & Monitor

Open the serial monitor to view text generation:

```bash
task monitor
```

> **Tip:** If the monitor connects after the board finishes its boot priming sequence, press the physical **RST** button on the ESP32-S3 board to restart generation from the beginning.

## :brain: Training a Custom Model

You can train custom models with Hierarchical Softmax (cluster prediction head) directly in the `research/` pipeline and export them for on-device inference.

### 1. Environment & Dependencies
Ensure Python dependencies are synced via `uv`:
```bash
uv sync
```

### 2. Prepare Training Data & Tokenizer
Downloads the TinyStories dataset slice (first 300MB) and builds the 32k vocabulary tokenizer:
```bash
task prepare
```

### 3. Run Training
* **Quick Verification Run (1.5M params, 500 steps)**:
  ```bash
  task train-test
  ```
* **Full Training Run (15M params, 5000 steps)**:
  ```bash
  task train-full
  ```
Checkpoints will be saved to `runs/` as `.pt` files.

> **Tip (Recommended):** Instead of running heavy training on your local CPU machine, you can run training on a free-tier Google Colab T4 GPU via `task colab-train-test` or `task colab-train-full`, or interactively in [`s3_tiny_stories_colab.ipynb`](file:///home/nicholas/git/nicholaswilde/esp32-sandbox/projects/s3-tiny-stories/s3_tiny_stories_colab.ipynb).


### Memory Optimization & Host Protection
Training models with large vocabularies (e.g. 32k) requires substantial memory for intermediate activation tensors during forward/backward passes.

* **Micro-Batching & Gradient Accumulation**:
  `train.py` defaults to `--micro-batch-size 4` with automatic gradient accumulation to match the full `--batch-size 32`. This keeps peak memory under ~1.5GB RAM on constrained machines.
* **Memory Profiling**:
  Pass `--profile-memory` to print `tracemalloc` memory reports at step 0 and every 50 steps.
* **Adding Swap on Linux**:
  ```bash
  sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  ```
  *(Note: On Btrfs filesystems, run `sudo chattr +C /swapfile` before zeroing with `dd`).*
* **Cgroup / Systemd Protection (`systemd-run`)**:
  To protect the host OS from hard freezes or OOM panics if memory spikes, wrap training with a cgroup `MemoryMax` limit:
  ```bash
  systemd-run --user --scope -p MemoryMax=4G -p MemoryHigh=3.5G task train-full
  ```

### 4. Export to Binary
Export the trained PyTorch checkpoint into the packed binary format for the ESP32 partition:
```bash
task export-test
```
*(Or invoke `research.tinystories.export` directly for custom checkpoint tags).* Once exported, flash the binary using `task flash-model`.

### 5. Upload Model to Hugging Face Hub

Pre-trained model artifacts are hosted on Hugging Face Hub at **[nicholascwilde/esp32-s3-tinystories](https://huggingface.co/nicholascwilde/esp32-s3-tinystories)**.

You can publish trained checkpoints, INT4 quantized weights, and tokenizer assets directly to Hugging Face Hub.

#### Uploaded File Bundle
The upload script automatically bundles and stages 5 essential files:
*   **`README.md`**: Model card with metadata tags, hardware requirements (ESP32-S3, 16MB Flash, 8MB PSRAM, `0x110000` flash offset), and `esptool` flashing commands.
*   **`LICENSE`**: Repository Apache 2.0 license.
*   **`metadata.json`**: Model architecture dimensions, INT4 quantization group sizes, and partition offset specifications.
*   **`*.bin`**: Compiled INT4 model weights (e.g. `stories15M_q4.bin`, `model.bin`).
*   **`tokenizer.json`**: BPE / SentencePiece tokenizer vocabulary definition.

#### Authentication
Authenticate your Hugging Face CLI once:
```bash
uv run hf auth login
# or with global hf: hf auth login
```

#### Upload Commands
```bash
# 1. Preview upload files and sizes without pushing (Dry Run)
uv run python upload_model_hf.py --dry-run

# 2. Upload pre-quantized 15M INT4 bundle (stories15M_q4.bin + tokenizer + metadata + license + model card)
task upload-model

# 3. Upload custom PLE trained model artifacts directory
task upload-custom DIR=artifacts/tinystories/ple-v32768_c1500000-s0

# 4. Custom destination repository and commit message
uv run python upload_model_hf.py \
  --path pc_tools/stories15M_q4.bin \
  --repo-id <username>/<custom-repo> \
  --commit-message "Upload 15M INT4 TinyStories weights"
```
*(Tip: You can also use the `.agents/skills/upload-model-hf` agent skill or native `hf upload`).*

### 6. Download Model from Hugging Face Hub

To download pre-trained weights, metadata, and tokenizer directly from Hugging Face:

```bash
# Download from default repository (nicholascwilde/esp32-s3-tinystories)
task download-model

# Or download from a specific Hugging Face repository
task download-model REPO="<username>/esp32-s3-tinystories"

# Or directly via Python with custom options
uv run python download_model_hf.py --repo-id "<username>/esp32-s3-tinystories" --out-dir pc_tools/
```
The download script automatically saves `stories15M_q4.bin`, `tokenizer.json`, and regenerates the C decoding header (`src/generated/vocab.h`) so you can immediately flash with `task flash-model && task flash`.

---

*   **Serial Port Busy (`[Errno 11] Resource temporarily unavailable`)**:
    If `task flash` fails because `/dev/ttyACM0` is locked, close any active `task monitor` or serial terminals:
    ```bash
    pkill -f "pio device monitor"
    ```
*   **Missing or Corrupted Characters**:
    If token strings appear without spaces or with corrupted byte tokens, regenerate the vocabulary header from `pc_tools/tokenizer.json`:
    ```bash
    task generate-vocab
    task flash
    ```
*   **PSRAM Allocation Failures**:
    Ensure `platformio.ini` has `board_build.arduino.memory_type = qio_opi` and `-D BOARD_HAS_PSRAM` enabled. The board must have functional Octal PSRAM.
*   **Colab CLI Execution Error (`AttributeError: module 'jupyter_kernel_client' has no attribute 'KernelClient'`)**:
    If `colab exec` or `task colab-...` fails with this error due to unpinned `jupyter-kernel-client` versions, apply the automated patch:
    ```bash
    task colab-patch
    ```
    *(Refer to [`docs/colab_cli_patch.md`](file:///home/nicholas/git/nicholaswilde/esp32-sandbox/docs/colab_cli_patch.md) for full root cause and manual patch instructions).*


## :link: References

*   [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - Inference Llama 2 in one file of pure C
*   [slvDev/esp32-ai](https://github.com/slvDev/esp32-ai) - On-device AI inference on ESP32
