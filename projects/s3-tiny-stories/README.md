# :book: S3 Tiny Stories :robot:

This project runs a quantized language model locally on an ESP32-S3. It utilizes a lightweight C inference engine (adapted from `llama2.c`) to generate text from the TinyStories dataset entirely offline.

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
*   [esptool.py](https://docs.espressif.com/projects/esptool/en/latest/esp32/)

## :gear: Setup Workflow

The build and deployment process involves preparing the quantized model weights, flashing them to the custom flash partition, and flashing the firmware.

### :arrow_down: 1. Fetch and Quantize the Model

Download the pre-trained TinyStories 15M weights and quantize them to the INT4 format:

```bash
task quantize
```

*(Alternatively, pre-exported weights can be downloaded with `task fetch-model`)*.

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

## :wrench: Troubleshooting

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

## :link: References

*   [karpathy/llama2.c](https://github.com/karpathy/llama2.c) - Inference Llama 2 in one file of pure C
*   [slvDev/esp32-ai](https://github.com/slvDev/esp32-ai) - On-device AI inference on ESP32
