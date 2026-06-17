---
tags: [iot, wearable, lora, node, battery, long]
type: source
title: "IoTThinks/EasyLoRaNode_Tracker: A wearable LoRa node with battery for long range wearable projects"
slug: iotthinkseasyloranodetracker-a-wearable-lora-node-with-battery-for-long-range-we
date_ingested: 2026-05-24
original_file: raw/IoTThinksEasyLoRaNode_Tracker A wearable LoRa node with battery for long range wearable projects.md
---

```yaml
---
title: "IoTThinks/EasyLoRaNode_Tracker: A wearable LoRa node with battery for long range wearable projects"
source: "https://github.com/IoTThinks/EasyLoRaNode_Tracker"
author: ""
published: ""
created: "2026-04-18"
description: "A wearable LoRa node with battery for long range wearable projects - IoTThinks/EasyLoRaNode_Tracker"
tags: ""
---
```

## Easy LoRa Node - Tracker

A wearable LoRa node with battery and less than 15uA deepsleep.

## 1\. Specifications

## 1.1 Overview

[]()

## 1.2 Components

[]()

## 1.3 Design overview

[]()## 2\. Usage guides

## 2.1 Pin mappingVIN

- 3.6-5v only!!!

LED

- LED 22 // LOW is off, HIGH is on.

Button

- BTN 39 // Pressed is HIGH. Keep LOW.

LoRa

- LORA\_POWER 21 // LOW to off, HIGH to power on LoRa module
- LORA\_SS 25 // Have pull up resistor
- LORA\_SCK 18
- LORA\_MOSI 23
- LORA\_MISO 19
- LORA\_DIO0 26
- LORA\_DIO1 35
- LORA\_DIO2 34
- LORA\_RESET 27

Battery

- BAT\_METER 36 // To measure battery voltage

Special GPIOs

- GPIO 16 is used by internal flash by Pico. And should not be used in program.

Other GPIOs

- Connect directly to ESP32-Pico-D4: [https://www.espressif.com/sites/default/files/documentation/esp32-pico-d4\_datasheet\_en.pdf](https://www.espressif.com/sites/default/files/documentation/esp32-pico-d4_datasheet_en.pdf)

## 2.2 Upload sketch

- To install UART driver for CP2012: [https://github.com/IoTThinks/EasyLoRaGateway\_v2.1/wiki/Install-USB-UART-driver](https://github.com/IoTThinks/EasyLoRaGateway_v2.1/wiki/Install-USB-UART-driver)
- To install Arduino IDE: [https://www.arduino.cc/en/software](https://www.arduino.cc/en/software)
- To install ESP32 for Arduino IDE: [https://github.com/IoTThinks/EasyLoRaGateway\_v2.1/wiki/Setup-Arduino-IDE-and-ESP32](https://github.com/IoTThinks/EasyLoRaGateway_v2.1/wiki/Setup-Arduino-IDE-and-ESP32)
- To install LoRa library: [https://github.com/sandeepmistry/arduino-LoRa](https://github.com/sandeepmistry/arduino-LoRa)

[]()

## 2.3 Sample codes

- Test code for receiver: [https://github.com/IoTThinks/EasyLoRaNode\_Tracker/tree/main/ESP32SimpleReceiver\_920Mhz](https://github.com/IoTThinks/EasyLoRaNode_Tracker/tree/main/ESP32SimpleReceiver_920Mhz)
- Test code for sender: [https://github.com/IoTThinks/EasyLoRaNode\_Tracker/tree/main/EasyLoRaMiniNodeTest-Batch1](https://github.com/IoTThinks/EasyLoRaNode_Tracker/tree/main/EasyLoRaMiniNodeTest-Batch1)

## 2.4 LoRa Power

To turn on/off LoRa power

- Be sure LoRa power is on before sending LoRa messages
- To turn off LoRa power if not in use or in deep sleep to save power. []()

## 2.5 Battery

### 2.5.1 No battery

The node can be powered via usb port 5v or Vin (3.6v-5v)

- The charge LED will be blinked.

### 2.5.2 Connect battery

Recommended battery:

- Lipo battery 4.2v with under-voltage protection is recommended.
- 18650 battery is NOT recommended as it does not have under-voltage protection.

### 2.5.3 Charge battery

To connect the battery and plug the USB jack into 5v USB

- You can still use the node during the charging
- It takes around 2 hours to fully charge

### 2.5.4 Battery protection

Over-charging protection

- The node has IC to limit the charge to 4.2v.

Under-discharge protection

- The node has no IC to prevent under-discharge.
- The Lipo battery must have protection circuit.

### 2.5.5 Measure battery voltage

Sample code to measure battery voltage is in [https://github.com/IoTThinks/EasyLoRaNode\_Tracker/blob/main/EasyLoRaMiniNodeTest-Batch1/55\_battery.ino](https://github.com/IoTThinks/EasyLoRaNode_Tracker/blob/main/EasyLoRaMiniNodeTest-Batch1/55_battery.ino)

- If the USB or VIN is connected, the voltage may be read over 4.2v.
- Accuracy is around +/- 0.1v

[]()

### 2.5.6 Measure battery current during deepsleep

To use VOM to measure current directly from the Lipo battery to Vin GPIO or battery pins.

- To use as short wire as possible
- The voltage may drop.

To wait until the node goes into deepsleep

[]()

## 2.6 Assemble everything

TO SOLDER THE BATTERY TO BATTERY PADS FIRST

- WRONG +/- WILL KILL THE BOARD

[]()

To put battery on the bottom

[]()

To put in board

[]()
