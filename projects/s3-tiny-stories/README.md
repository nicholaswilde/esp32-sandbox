# :book: S3 Tiny Stories :robot:

This project runs a quantized language model locally on an ESP32-S3. It utilizes a C-based inference engine (based on `llama2.c`) to generate text from the TinyStories dataset entirely offline.

Due to the size of the model weights, this project requires an ESP32-S3 with at least 16MB of Flash and PSRAM enabled. The weights are stored in a custom Flash partition and are accessed iteratively during inference to bypass RAM limitations.

## :clipboard: Prerequisites

Ensure you have the following tools installed on your host machine:
*   [PlatformIO Core (CLI)](https://docs.platformio.org/en/latest/core/index.html)
*   [go-task](https://taskfile.dev/)
*   [uv](https://github.com/astral-sh/uv) (for Python dependency management)
*   [esptool.py](https://docs.espressif.com/projects/esptool/en/latest/esp32/)

## :gear: Setup Workflow

The build and deployment process is split into two phases: preparing the model weights and flashing the firmware.

### :arrow_down: 1. Fetch and Export the Model

The model weights must be downloaded and quantized into a binary format that the ESP32 can read. We use `uv` to handle the Python environment automatically.

```bash
task fetch-model
```

### :zap: 2. Flash the Model Partition

The custom `partitions.csv` allocates a large model partition starting at `0x1F0000`. The exported .bin file must be flashed directly to this address.

```bash
task flash-model
```

### :hammer: 3. Build and Flash the Firmware

Once the model weights are situated in Flash, compile and upload the inference engine.

```bash
task build
task flash
```

### :rocket: 4. Run

Open the serial monitor to interact with the model.

```bash
task monitor 
```

## :link: References

- https://github.com/slvDev/esp32-ai
