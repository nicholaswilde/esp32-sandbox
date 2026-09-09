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

Refer directly to the [CYD W5500 wiring diagram](https://wiki.bruce.computer/external-modules/w5500-ethernet-module/) on the Bruce wiki for the exact pinout. 

> [!NOTE]
> The W5500 communicates over SPI. Ensure that your Chip Select (CS), INT, and reset pins match the firmware expectations so they do not conflict with the CYD's internal display or touchscreen SPI buses.*

## :rocket: Building and Flashing

If compiling Bruce from source to modify the pinout or enable the module natively, ensure the W5500 flag is enabled in your build environment. 

```bash
# Example task runner command
task build
task flash
```
