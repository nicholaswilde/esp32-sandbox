# :zap: CYD Ethernet Bruce

Integration and testing environment for the W5500 Ethernet module on the ESP32 Cheap Yellow Display (CYD) running the Bruce firmware.

## :mag_right: Overview

This sub-project houses the configurations, setup notes, and wiring references required to add physical Ethernet support to the CYD. By leveraging the W5500 SPI Ethernet module, the CYD can utilize Bruce's Layer 2 and Layer 3 network capabilities (like NetCut ARP spoofing and raw packet injection).

## :link: References

- [Bruce Firmware W5500 Ethernet Wiki](https://wiki.bruce.computer/external-modules/w5500-ethernet-module/) - Official documentation and wiring diagrams for the W5500 module (includes CYD specifics).
- [Bruce Firmware GitHub Repository](https://github.com/BruceDevices/firmware)

## :hammer_and_wrench: Hardware Required

- ESP32 Cheap Yellow Display (CYD)
- W5500 Ethernet Module (Standard or Mini)
- Jumper wires / custom PCB shield

## :electric_plug: Wiring

The W5500 communicates with the ESP32 over SPI. According to the repository's central pinout reference in [`docs/pinouts.md`](../../docs/pinouts.md), the wiring connects via an SD card sniffer/breakout ribbon adapter for SPI lines and the CYD extended header for control pins:

| W5500 Pin | CYD / ESP32 Pin | Connection Point / Notes |
| :--- | :--- | :--- |
| **GND** | GND | SD Sniffer / CYD GND |
| **3V3** | 3V3 / VCC | SD Sniffer / CYD 3.3V power |
| **SCLK** | 14 (CLK) | SD Sniffer CLK line |
| **MOSI** | 13 (CMD) | SD Sniffer CMD line |
| **MISO** | 12 (DAT0) | SD Sniffer DAT0 line |
| **SCS (CS)** | 27 | CYD Extended Header (CN1) - Dedicated Ethernet Chip Select |
| **INT** | 22 | CYD Extended Header (CN1) - Hardware Interrupt |
| **RST** | NC | Not Connected (internally pulled up or tied to EN) |

### Wiring Details & Tips

1. **SD Card Sniffer**:
   - Using a MicroSD sniffer or breakout ribbon inserted into the CYD's TF card slot exposes the SPI bus (`SCLK`, `MOSI`, `MISO`) along with power (`3V3`, `GND`) without needing to solder directly to surface-mount display pins.
2. **Dedicated Chip Select & Interrupt**:
   - Connect **SCS (CS)** to **GPIO 27** and **INT** to **GPIO 22** on the CYD's 4-pin expansion connector (CN1/P3).
3. **Bus Contention Prevention**:
   - If using a board setup where the onboard SD slot shares SPI lines, ensure SD Card CS (**GPIO 5**) is held `HIGH` so it does not conflict with W5500 Ethernet SPI traffic.

> [!NOTE]
> Refer directly to [`docs/pinouts.md`](../../docs/pinouts.md) and the [CYD W5500 wiring diagram](https://wiki.bruce.computer/external-modules/w5500-ethernet-module/) on the Bruce wiki for additional hardware details.

## :rocket: Building and Flashing

If compiling Bruce from source to modify the pinout or enable the module natively, ensure the W5500 flag is enabled in your build environment. 

```bash
# Example task runner command
task build
task flash
```

## :wrench: Troubleshooting