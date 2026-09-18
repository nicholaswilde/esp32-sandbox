---
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

# TinyStories 15M (INT4 Quantized for ESP32-S3)

Quantized INT4 weights designed to run locally on ESP32-S3 with 16MB Flash and Octal PSRAM.

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

Download the binary file (`stories15M_q4.bin`) and flash it directly to your ESP32-S3:

```bash
# 1. Download model binary
hf download nicholascwilde/esp32-s3-tinystories stories15M_q4.bin --local-dir .

# 2. Flash to model partition (0x110000)
esptool --baud 921600 --port /dev/ttyACM0 write-flash 0x110000 stories15M_q4.bin
```

## Running Inference

Refer to the [esp32-sandbox repository](https://github.com/nicholaswilde/esp32-sandbox/tree/main/projects/s3-tiny-stories) for firmware building, flashing, and serial monitoring.
