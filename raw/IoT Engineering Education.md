---
title: "IoT Engineering Education"
source: "https://iot-kmutnb.github.io/blogs/"
author:
  - "[[RSP]]"
published:
created: 2026-04-18
description: "None"
tags:
  - "clippings"
---
## รายการบทความ

รายการบทความที่จัดทำขึ้นเพื่อเผยแพร่นี้ เป็นเนื้อหาทางวิชาที่เกี่ยวข้องกับวิศวกรรมไฟฟ้า-อิเล็กทรอนิกส์และคอมพิวเตอร์ ซึ่งเกิดจากการศึกษา ค้นคว้า และลงมือปฏิบัติด้วยตนเอง รวมทั้งบางส่วนมาจากประสบการณ์การสอนของผู้เขียนในอดีต และเผยแพร่ในลักษณะอิสระ โดยไม่เกี่ยวข้องหรือสังกัดสถาบันการศึกษา องค์กร หรือหลักสูตรใดเป็นการเฉพาะ

หวังเป็นอย่างยิ่งว่าจะเป็นประโยชน์แก่ผู้ที่สนใจและกำลังศึกษาเรียนรู้ในสาขาที่เกี่ยวข้องครับ

---

### ▹ การเรียนรู้ไมโครคอนโทรลเลอร์และระบบสมองกลฝังตัวด้วย Arduino Hardware & Software

หากสนใจการเรียนรู้การเขียนโปรแกรมสำหรับบอร์ดไมโครคอนโทรลเลอร์ (**Microcontroller: MCU**) เช่น ภาษา **C/C++** ซึ่งเป็นพื้นฐานที่สำคัญสำหรับการพัฒนาระบบสมองกลฝังตัว ([**Embedded Systems Development**](https://iot-kmutnb.github.io/blogs/embed-sys-dev/)) เราจะพบว่า มีตัวเลือกหลากหลายทั้งซอฟต์แวร์และฮาร์ดแวร์ และกล่าวได้ว่า **Arduino** เป็นหนึ่งในตัวเลือกที่น่าสนใจและเป็นตัวเลือกแรกสำหรับผู้เริ่มต้น → มีบทความที่เกี่ยวข้องดังนี้

- [**Arduino Ecosystem:**](https://iot-kmutnb.github.io/blogs/arduino/) กล่าวถึงภาพรวมของ **Arduino** การพัฒนาจากอดีตมาถึงปัจจุบัน ซอฟต์แวร์และฮาร์ดแวร์ที่เกี่ยวข้องกับ **Arduino** เป็นต้น
- [**CPU Chips on Arduino Boards:**](https://iot-kmutnb.github.io/blogs/arduino/cpu_chips_on_arduino_boards/) กล่าวถึง ตัวเลือกชิปในประเภทไมโครคอนโทรลเลอร์ (**MCU**) สำหรับบอร์ด **Arduino** หลายรุ่น
- บทบาทของบอร์ดไมโครคอนโทรลเลอร์ [**Arduino Uno / Nano (8-bit MCU)**](https://iot-kmutnb.github.io/blogs/arduino/arduino_avr/) ต่อการเรียนรู้ระบบสมองกลฝังตัวในปัจจุบัน
- [บอร์ด **Arduino Nano**](https://iot-kmutnb.github.io/blogs/arduino/arduino_nano/): ความแตกต่างของบอร์ดจากต่างผู้ผลิตและการเลือกใช้งาน
- [**Single Board Computers (SBCs) with Arduino Support**](https://iot-kmutnb.github.io/blogs/arduino/sbc_with_arduino/): คอมพิวเตอร์บอร์ดเดี่ยวที่รองรับการเขียนโปรแกรมด้วย **Arduino**
- แนะนำการใช้งาน [**VS Code IDE + Wokwi**](https://iot-kmutnb.github.io/blogs/wokwi/wokwi-vscode/)
- การใช้งานซอฟต์แวร์ [**VS Code IDE + PlatformIO**](https://iot-kmutnb.github.io/blogs/arduino/vscode_pio_arduino/) เพื่อเขียนโค้ด **Arduino** สำหรับบอร์ด เช่น **Arduino Uno Rev.3** หรือ **Nano v3.0**
- การใช้งาน [**Arduino CLI**](https://iot-kmutnb.github.io/blogs/arduino/arduino_cli/): การทำคำสั่งแบบ **Command Line**
- ตัวอย่างการสร้าง **C++ Class** เพื่อใช้งานเป็นไลบรารีสำหรับ **Arduino**: [**RGB LED**](https://iot-kmutnb.github.io/blogs/arduino/arduino_cpp_class_rgb_led/) และ [**4x4 Membrane Keypad**](https://iot-kmutnb.github.io/blogs/arduino/arduino_cpp_class_keypad/)
- [การกระเด้งของปุ่มกด (**Switch Bouncing**)](https://iot-kmutnb.github.io/blogs/arduino/arduino_avr_io_follower/) การแก้ปัญหาและทดลองเขียนโค้ดด้วย **Arduino (ATmega328P)**
- [การใช้โมดูล **8-bit LED Bar**](https://iot-kmutnb.github.io/blogs/arduino/arduino_ledbar/) เพื่อการฝึกเขียนโค้ด **Arduino Sketch** โดยใช้ **Wokwi Simulator** และใช้บอร์ด **Arduino Nano** และ **ESP32**
- [การสื่อสารข้อมูลด้วยบัส **SPI**](https://iot-kmutnb.github.io/blogs/arduino/arduino-spi-master-slave/) และเขียนโปรแกรมด้วย **Arduino**
- [การใช้งานไมโครคอนโทรลเลอร์ **ATtiny85**](https://iot-kmutnb.github.io/blogs/arduino/arduino_attiny85/) การเขียนโปรแกรม **Arduino** และจำลองการทำงานด้วย **Wokwi AVR Simulator**
- การเขียนโปรแกรมภาษา **C**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/training/c_tutorial_part-1/) | [2](https://iot-kmutnb.github.io/blogs/training/c_tutorial_part-2/) | [3](https://iot-kmutnb.github.io/blogs/training/c_tutorial_part-3/)
- ตัวอย่างการเขียนโค้ดภาษา **C** แบบ **Bare-Metal** และใช้งานซอฟต์แวร์ **GCC AVR Toolchain / Arduino IDE** สำหรับชิป **AVR / ATmega328P**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-1/) | [2](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-2/) | [3](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-3/) | [4](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-4/) | [5](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-5/) | [6](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-6/) | [7](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-7/) | [8](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-8/) | [9](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-9/) | [10](https://iot-kmutnb.github.io/blogs/arduino/avr_gcc_part-10/)
- [**Arduino LED Blink**](https://iot-kmutnb.github.io/blogs/arduino/arduino_led_blink/): ตัวอย่างการเขียนโค้ดที่ทำให้ **LED** กระพริบได้ด้วยวิธีที่แตกต่างกันหลายวิธี โดยใช้บอร์ด **Uno / Nano**
- [**Arduino I/O Toggle**](https://iot-kmutnb.github.io/blogs/arduino/avr_io_toggle/): ตัวอย่างการเขียนโค้ดเพื่อสร้างและวัดสัญญาณแบบพัลส์ โดยใช้บอร์ด **Uno / Nano**
- [**GCC AVR - Inline Assembly**](https://iot-kmutnb.github.io/blogs/arduino/avr_asm_io/): ตัวอย่างการเขียนโค้ดและการจำลองการทำงานด้วย **Wokwi AVR Simulator**
- การใช้งาน [**Arduino TimerOne Library**](https://iot-kmutnb.github.io/blogs/arduino/arduino_timerone_lib/) สำหรับบอร์ดไมโครคอนโทรลเลอร์ **Arduino Uno / Nano**
- ตัวอย่างการเขียนโค้ดเพื่อวัดความถี่ของสัญญาณที่มีคาบโดยใช้บอร์ด **Uno / Nano**: [**Frequency Measurement with Arduino**](https://iot-kmutnb.github.io/blogs/arduino/arduino_atmega328p_freq_counter/)
- การอ่านค่าจาก **ADC** เพื่อปรับความกว้างพัลส์ของสัญญาณ **PWM**: [**ADC Reading and PWM Output with Arduino**](https://iot-kmutnb.github.io/blogs/arduino/arduino_adc_pwm/): โดยใช้บอร์ด **Uno / Nano** และ **ESP32**
- ตัวเลือกในการดีบักโค้ดสำหรับชิปไมโครคอนโทรลเลอร์ **AVR**: [**AVR Debugging Tools**](https://iot-kmutnb.github.io/blogs/arduino/avr_debugger/)
- การใช้งานบอร์ด [**Arduino Due Rev.3**](https://iot-kmutnb.github.io/blogs/due/) (**ATSAM3x8e, 32-bit Arm Cortex-M3 CPU**)
- การใช้งานบอร์ด [**Arduino Uno R4 WiFi**](https://iot-kmutnb.github.io/blogs/arduino/arduino_uno_r4_wifi/) ในเบื้องต้น

---

### ▹ ไมโครคอนโทรลเลอร์ตระกูล Arm Cortex-M Series และซอฟต์แวร์ที่เกี่ยวข้อง

ไมโครคอนโทรลเลอร์ที่ใช้ซีพียูเป็น **32-bit Arm Cortex-M Series** ถือว่าเป็นตัวเลือกที่ได้รับความนิยม มีการใช้งานแพร่หลาย ดังนั้นความรู้เกี่ยวกับการใช้งานชิปตระกูลนี้ จึงเป็นพื้นฐานที่สำคัญ

- ทำความรู้จัก [**Arm CMSIS** สำหรับซีพียู **Arm Cortex-M Series**](https://iot-kmutnb.github.io/blogs/arm_cmsis/) โดยเลือกชิป **STM32F4 (Arm Cortex-M4F)** มาเป็นกรณีศึกษา
- การเขียนโปรแกรม **Arduino** โดยใช้ซอฟต์แวร์ [**Arduino IDE** + **STM32duino** สำหรับ **STM32**](https://iot-kmutnb.github.io/blogs/arduino/arduino_nucleo_stm32/) พร้อมโค้ดตัวอย่างสำหรับบอร์ด **STM32 NUCLEO-L432KC (Arm Cortex-M4)**
- แนะนำการใช้งานบอร์ด [**Black Pill STM32F4 (Arm Cortex-M4F)**](https://iot-kmutnb.github.io/blogs/stm32/stm32f4-blackpill/) ซึ่งเป็นบอร์ดไมโครคอนโทรลเลอร์ ที่มีราคาไม่แพง ใช้ชิป **STM32F411CEU6** เป็นตัวประมวลผลหลัก
- การเขียนโปรแกรม **Arduino** โดยใช้ซอฟต์แวร์ [**Microsoft VS Code IDE + PlatformIO**](https://iot-kmutnb.github.io/blogs/arduino/vscode_pio_arduino_stm32/) สำหรับบอร์ด **Black Pill STM32F4**
- การเขียนโปรแกรม **Arduino** สำหรับบอร์ดไมโครคอนโทรลเลอร์ [**Seeeduino XIAO - SAMD21**](https://iot-kmutnb.github.io/blogs/seeed_xiao/xiao_samd21/) (**Arm Cortex-M0+**)
- การเขียนโปรแกรมและดีบักโค้ดด้วย **Arduino API** โดยใช้ [**VS Code IDE + PlatformIO + SWD Debug Probe + STM32F4 (BlackPill Board)**](https://iot-kmutnb.github.io/blogs/stm32/stm32f4_pio_arduino_freertos/)
- การเขียนโปรแกรมและดีบักโค้ดด้วย **Arm CMSIS API** โดยใช้ [**VS Code IDE + PlatformIO + SWD Debug Probe + STM32F4 (BlackPill Board)**](https://iot-kmutnb.github.io/blogs/stm32/stm32f4-blackpill_vscode_cmsis/)
- แนะนำการใช้งาน [**STM32CubeIDE**](https://iot-kmutnb.github.io/blogs/stm32/stm32f4-blackpill_stm32cube_linux/) สำหรับบอร์ด **BlackPill STM32F411**
- แนะนำการใช้งาน [**STM32Cube for VS Code: Nucleo F446RE Board**](https://iot-kmutnb.github.io/blogs/stm32/vscode_stm32cube/)
- การทดลองใช้งานบอร์ดไมโครคอนโทรลเลอร์ [**Teensy 4.0 & 4.1**](https://iot-kmutnb.github.io/blogs/teensy/) ด้วย **Arduino** ในเบื้องต้น
- แนะนำชิปไมโครคอนโทรลเลอร์ของบริษัท [**Nordic Semiconductor - nRF SoCs**](https://iot-kmutnb.github.io/blogs/nrf_soc/)
- การเขียนโปรแกรม **C/C++** โดยใช้ [**CODAL v2** สำหรับบอร์ด **Micro:bit V2**](https://iot-kmutnb.github.io/blogs/microbit/microbit_codal_v2/) ในเบื้องต้น
- ตัวอย่างการรับส่งข้อมูลระหว่างบอร์ด **Micro:bit** แบบไร้สาย: [**Wireless Data Communication with Micro:bits**](https://iot-kmutnb.github.io/blogs/microbit/microbit_radio_share_emotional_icon/)
- การสร้างเกม [**Digital Bingo**](https://iot-kmutnb.github.io/blogs/microbit/microbit_radio_bingo/) สำหรับบอร์ด **Micro:bit**

---

### ▹ การใช้งานไมโครคอนโทรลเลอร์ Raspberry Pi MCU และซอฟต์แวร์ที่เกี่ยวข้อง

- แนวทางการใช้งานบอร์ด [**Raspberry Pi Pico - RP2040** สำหรับการเรียนรู้ระบบสมองกลฝังตัว](https://iot-kmutnb.github.io/blogs/rpi-rp2040/) ซึ่งใช้ชิป **RP2040 SoC (Dual-Core Arm Cortex-M0+)** เป็นตัวประมวลผลหลัก
- การเขียนโปรแกรม **Arduino Sketch** โดยใช้งาน **Arduino IDE** สำหรับบอร์ด **Raspberry Pi Pico**: [**Arduino Pico Core (by Earle F. Philhower)**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/arduino_rp2040_core/) และตัวอย่างการจำลองการทำงานโดยใช้ [**WokWi Simulator**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/arduino_pico/)
- การติดตั้งและใช้งานซอฟต์แวร์ [**Pico C/C++ SDK for RP2040**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/pico_sdk_vscode_wsl2/) เพื่อใช้งานร่วมกับ **VS Code IDE / WSL 2 Ubuntu**
- การเขียนโปรแกรมด้วย [**FreeRTOS Kernel + Pico C/C++ SDK + VS Code IDE**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/pico_sdk_freertos/) สำหรับบอร์ด **Raspberry Pi Pico**
- การเขียนโปรแกรมและดีบักโค้ดด้วย **Arduino API** โดยใช้ [**VS Code IDE + PlatformIO + SWD Debug Probe + RP2040 (Pico Board)**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/vscode_pio_rp2040/)
- แนะนำชิปไมโครคอนโทรลเลอร์ [**Raspberry Pi RP253x**](https://iot-kmutnb.github.io/blogs/rpi-rp253x/) สำหรับบอร์ด **Pico 2 / Pico 2 W**
- การใช้งานบอร์ด **RP2040** เป็นอุปกรณ์ [**CMSIS-DAP Debug Probe**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/rp2040_cmsis-dap/)

---

### ▹ การใช้งานฮาร์ดแวร์และซอฟต์แวร์ของบริษัท Atmel / Microchip

หากต้องการใช้ไมโครคอนโทรลเลอร์ของบริษัท **Atmel / Microchip** เช่น ตระกูล **AVR**, **SAM**, **PIC** แนะนำให้ลองใช้ซอฟต์แวร์ **Microchip MPLAB-X IDE** และมีบทความที่เกี่ยวข้องดังนี้

- แนะนำการใช้งานซอฟต์แวร์ [**MPLAB-X IDE**](https://iot-kmutnb.github.io/blogs/arduino/mplab-x_ide_avr/) สำหรับ **AVR (ATmega328P)**
- แนะนำการใช้งานซอฟต์แวร์ [**MPLAB Xpress Cloud IDE**](https://iot-kmutnb.github.io/blogs/arduino/mplab_xpress_avr/) สำหรับการเขียนโค้ดภาษา **C** สำหรับชิป **AVR (ATmega328P)**
- การนำเข้าไฟล์ [**Arduino Sketch** เพื่อใช้งานกับ **MPLAB-X IDE**](https://iot-kmutnb.github.io/blogs/arduino/mplab-x_ide_arduino_avr/) สำหรับ **AVR (ATmega328P)**
- แนะนำการใช้งานซอฟต์แวร์ [**MPLAB-X IDE** + **Harmony Framework v3**](https://iot-kmutnb.github.io/blogs/mplab-x/samd21_intro/) สาธิตการเขียนโค้ดสำหรับ **ATSAMD21 (Arm Cortex-M0+)**

---

### ▹ ระบบปฏิบัติการเวลาจริงสำหรับการเขียนโปรแกรมไมโครคอนโทรลเลอร์

ระบบปฏิบัติการเวลาจริง หรือ **RTOS (Real-Time OS)** เป็นประเภทหนึ่งของระบบปฏิบัติการ (**OS**) ถือว่าเป็นซอฟต์แวร์ที่มีความสำคัญสำหรับการพัฒนาระบบสมองกลฝังตัว-ไมโครคอนโทรลเลอร์ ดังนั้นความรู้และทักษะเกี่ยวกับการเขียนโปรแกรมแบบมัลติเธรด (**Multi-Threading**) หรือแบ่งการทำงานแบบหลายงาน จึงเป็นสิ่งสำคัญสำหรับนักพัฒนาในระดับมืออาชีพ → แนะนำให้ลองศึกษาจากบทความต่อไปนี้

- สำหรับผู้ที่สนใจเรียนรู้และใช้งาน **RTOS**: [แนวทางการเรียนรู้ **RTOS**](https://iot-kmutnb.github.io/blogs/rtos/)
- แนวทางการเรียนรู้ [**Arm Mbed OS for 32-bit Arm Cortex-M Series MCUs**](https://iot-kmutnb.github.io/blogs/mbedos/)
- การใช้งาน **FreeRTOS** จำแนกตามบอร์ดไมโครคอนโทรลเลอร์ต่อไปนี้
	- บอร์ด **Arduino Classic** (**Uno, Nano, Mega2560**): ตอนที่ [1](https://iot-kmutnb.github.io/blogs/freertos/arduino_avr_part-1/) | [2](https://iot-kmutnb.github.io/blogs/freertos/arduino_avr_part-2/) | [3](https://iot-kmutnb.github.io/blogs/freertos/arduino_avr_part-3/) | [4](https://iot-kmutnb.github.io/blogs/freertos/arduino_avr_part-4/) | [5](https://iot-kmutnb.github.io/blogs/freertos/arduino_avr_part-5/)
		- บอร์ด **STM32F411CE BlackPill**: [**STM32duino + FreeRTOS**](https://iot-kmutnb.github.io/blogs/stm32/stm32f4_arduino_freertos/)
- แนะนำการใช้งาน [**Zephyr RTOS**](https://iot-kmutnb.github.io/blogs/zephyr/):
	- แนะนำการใช้งานและตัวอย่างการเขียนโค้ด [**BBC Micro:bit v2 + Zephyr RTOS**](https://iot-kmutnb.github.io/blogs/zephyr/zephyr_cli_west/) ในรูปแบบ **CLI**
		- การเริ่มต้นใช้งาน [**Zephyr IDE**](https://iot-kmutnb.github.io/blogs/zephyr/zephyr_ide/) สำหรับ **VS Code IDE**
		- การใช้งาน **Zephyr RTOS** สำหรับ **ESP32**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/zephyr/zephyr_esp32_part-1/)
		- การใช้งาน **Zephyr RTOS** สำหรับ **RP2040**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/zephyr/zephyr_pico_part-1/)
- การเขียนโปรแกรมแบบ [**Multi-Tasking: TinyGo Goroutines vs. FreeRTOS**](https://iot-kmutnb.github.io/blogs/go/tinygo_vs_freertos_pico/)

---

### ▹ ไมโครคอนโทรลเลอร์สำหรับงาน IoT: ESP32 SoCs

หากต้องการเลือกใช้ไมโครคอนโทรลเลอร์ที่ไม่ได้ใช้สถาปัตยกรรมของซีพียูตระกูล **Arm** ก็แนะนำให้ลองใช้ชิป **ESP32 Series** ของบริษัท **Espressif** ซึ่งมีจุดเด่นคือ สามารถเชื่อมต่อ **Wi-Fi** และ **Bluetooth / BLE** ได้

- แนะนำ [**Espressif ESP32 SoCs**](https://iot-kmutnb.github.io/blogs/esp32/): ตัวเลือกสำหรับฮาร์ดแวร์และซอฟต์แวร์
- แนวทางการเรียนรู้: [**Guidelines for ESP32 Programming**](https://iot-kmutnb.github.io/blogs/training/mcu_programming_with_esp32/)
- ขั้นตอนการติดตั้งและใช้งานซอฟต์แวร์ [**Espressif ESP-IDF**](https://iot-kmutnb.github.io/blogs/esp32/esp-idf_linux_wsl/) สำหรับ **WSL2 Ubuntu**
- แนะนำการใช้งาน [**VS Code IDE + PlatformIO**](https://iot-kmutnb.github.io/blogs/esp32/esp32_vscode_pio/) สำหรับบอร์ด **ESP32**
- การใช้งาน [**PlatformIO (PIO) Core**](https://iot-kmutnb.github.io/blogs/esp32/linux_pio_esp32/) สำหรับ **WSL2 Ubuntu** ในเบื้องต้น
- การใช้งาน [**VS Code IDE + Espresssif IDF Extension**](https://iot-kmutnb.github.io/blogs/esp32/esp-idf_vscode/) สำหรับ **Windows**
- การเขียนโปรแกรม [**ESP32-C6 / ESP-IDF (WSL2 Ubuntu)**](https://iot-kmutnb.github.io/blogs/esp32/esp32-c6_esp-idf/)
- การเขียนโปรแกรม [**ESP32-C6 / Arduino-ESP32 Core**](https://iot-kmutnb.github.io/blogs/esp32/esp32-c6_arduino/)
- การใช้งาน [**VS Code IDE + PlatformIO + ESP-IDF** (สำหรับ **Linux**)](https://iot-kmutnb.github.io/blogs/esp32/pio_esp32_esp-idf/)
- แนะนำการใช้งานชิป [**Espressif ESP32-C3 (RISC-V)**](https://iot-kmutnb.github.io/blogs/esp32/esp32-c3_intro/)
- แนะนำการใช้บอร์ดไมโครคอนโทรลเลอร์ **ESP32-C3** ที่เป็นตัวเลือกและแตกต่างกันจากหลายผู้ผลิต
	- [**Ai Thinker NodeMCU ESP32-C3 DevKits**](https://iot-kmutnb.github.io/blogs/esp32/esp32_c3_ai_thinker/)
		- [**AirM2M CORE-ESP32C3**](https://iot-kmutnb.github.io/blogs/esp32/esp32-luatos_core_c3/)
		- [**WeAct Studio ESP32-C3FH4 Mini Core**](https://iot-kmutnb.github.io/blogs/esp32/esp32_c3_weact_studio/)
		- [**WeMos LOLIN C3 Mini**](https://iot-kmutnb.github.io/blogs/esp32/esp32-c3_lolin_mini/)
		- [**WeMos LOLIN C3 Pico**](https://iot-kmutnb.github.io/blogs/esp32/esp32_c3_wemos_pico/)
		- [**Maker Go ESP32 C3 Super-Mini**](https://iot-kmutnb.github.io/blogs/esp32/esp32_c3_super-mini/)
		- [**Seeed Studio XIAO ESP32-C3**](https://iot-kmutnb.github.io/blogs/esp32/esp32_c3_xiao/)
		- [**M5Stamp (Pico / C3 / C3U)**](https://iot-kmutnb.github.io/blogs/esp32/esp32_m5stamp/)
- การเขียนโค้ด **Arduino** และดีบักการทำงานของชิป **Espressif ESP32-C3** ด้วย [**PIO Debug / USB-JTAG**](https://iot-kmutnb.github.io/blogs/esp32/pio_esp32c3_debug/)
- แนะนำการใช้งานชิป [**Espressif ESP32-S3**](https://iot-kmutnb.github.io/blogs/esp32/esp32-s3_intro/)
- การใช้งานโมดูล [**ESP01S (ESP8285) WiFi-Serial**](https://iot-kmutnb.github.io/blogs/rpi-rp2040/rp2040_wifi_esp-at/) สำหรับบอร์ด **Raspberry Pi Pico**
- การติดตั้งเฟิร์มแวร์ [**Espressif ESP-AT**](https://iot-kmutnb.github.io/blogs/esp32/esp_at_firmware/) เพื่อใช้งานกับโมดูล **WiFi-to-Serial (ESP8266 / ESP8285 / ESP32-C3)**
- การทำความเข้าใจผังวงจรสำหรับบอร์ดไมโครคอนโทรลเลอร์ [**WeMos Lolin32 Lite ESP32 Board**](https://iot-kmutnb.github.io/blogs/esp32/esp32-wemos_lolin/)
- การเขียนโปรแกรม **Arduino** สำหรับ **ESP32** ด้วย **Wokwi Simulator**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/esp32/arduino-esp32-wokwi-part1/) | [2](https://iot-kmutnb.github.io/blogs/esp32/arduino-esp32-wokwi-part2/)
- การเขียนโปรแกรม **Arduino-ESP32** เพื่อใช้งาน **Hardware SPI**: [**Using Arduino-ESP32 as SPI Master**](https://iot-kmutnb.github.io/blogs/esp32/esp32_spi/)
- การเขียนโค้ด **Arduino-ESP32** เพื่อการใช้เชื่อมต่อด้วยบัส **SPI Master-Slave**: [**SPI Master-Slave Demo with ESP32**](https://iot-kmutnb.github.io/blogs/esp32/esp32-spi-master-slave/)
- การสร้างสัญญาณพัลส์และวัดความกว้างพัลส์ด้วย **ESP32**: [**Pulse Generation using ESP32**](https://iot-kmutnb.github.io/blogs/esp32/arduino_esp32_pulse_counter/)
- การทดสอบหาระยะเวลาในการทำคำสั่งสำหรับ **Arduino ESP32**: [**Execution Time Measurement for ESP32**](https://iot-kmutnb.github.io/blogs/esp32/arduino_esp32_code_instrumentation/)
- การสร้างสัญญาณแอนะล็อกด้วยวงจร **DAC** ภายในชิป **ESP32**: [**Analog Signal Generation using ESP32's built-in DAC**](https://iot-kmutnb.github.io/blogs/esp32/arduino_esp32_dac/)
- การใช้งาน **ESP32** เพื่อประมวลผลข้อมูลด้วย **FFT (Fast-Fourier Transform)**: [**ESP32-based FFT Processing**](https://iot-kmutnb.github.io/blogs/esp32/esp32_fft/)
- การอ่านค่าสัญญาณเสียงแอนะล็อกด้วย **ESP32** และแสดงผลกราฟสัญญาณด้วย **Python**: [**Analog Signal Capture with ESP32's built-in ADC & Python-based Visualization**](https://iot-kmutnb.github.io/blogs/esp32/esp32_adc_python/)
- การอ่านข้อมูลเสียงจากโมดูลเซนเซอร์ [**INMP441**](https://iot-kmutnb.github.io/blogs/esp32/esp32_inmp441/) ด้วย **ESP32**
- การใช้งานโมดูลขยายเสียง [**MAX9835A**](https://iot-kmutnb.github.io/blogs/esp32/esp32_max98357a_i2s/) ร่วมกับ **ESP32**
- การสื่อสารไร้สายด้วยโพรโทคอล [**ESPNOW**](https://iot-kmutnb.github.io/blogs/esp32/espnow_intro/) สำหรับชิป **Espressif ESP32 SoC**
- ตัวอย่างการเขียนโปรแกรมด้วย **Arduino** สำหรับใช้งาน [**ESP32 Bluetooth LE**](https://iot-kmutnb.github.io/blogs/esp32/esp32_ble_intro/)
- การทำงานของชิป **ESP32-C3** ในโหมดประหยัดพลังงาน: [**Low-Power Mode**](https://iot-kmutnb.github.io/blogs/esp32/esp32-c3_low_power/)
- การเขียนโปรแกรม **ESP32-C3** ด้วย **Arduino** ทำงานในโหมด [**Sleep / Wakeup**](https://iot-kmutnb.github.io/blogs/esp32/esp32-c3_sleep_wakeup/) และวิเคราะห์การใช้พลังงาน
- การเขียนโปรแกรม **ESP32** เพื่อใช้งาน **BLE** ด้วยไลบรารี **NimBLE-Arduino**: ตอนที่ [**1**](https://iot-kmutnb.github.io/blogs/esp32/esp32_nimble_part-1/) | [**2**](https://iot-kmutnb.github.io/blogs/esp32/esp32_nimble_part-2/) | [**3**](https://iot-kmutnb.github.io/blogs/esp32/esp32_nimble_part-3/)
- [**DIY ESP32-Based IR Remote Web Server**](https://iot-kmutnb.github.io/blogs/mini-projects/esp32_ir_remote/)
- [**Treasure-Hunt Game using Bluetooth LE & QR Code Technologies**](https://iot-kmutnb.github.io/blogs/mini-projects/ble_qr_code_game/)

---

### ▹ ภาษาคอมพิวเตอร์ที่ไม่ใช่ C/C++ สำหรับไมโครคอนโทรลเลอร์

ภาษา **C/C++** เป็นภาษาคอมพิวเตอร์ที่สำคัญสำหรับการพัฒนาโปรแกรมสำหรับระบบสมองกลฝังตัว แต่ในปัจจุบัน **Python** ก็เป็นอีกหนึ่งภาษาที่ได้รับความนิยม และได้เริ่มมีการนำมาใช้งานสำหรับไมโครคอนโทรลเลอร์ → มีบทความที่เกี่ยวข้องต่อไปนี้

- [**Python for Hardware Programming**](https://iot-kmutnb.github.io/blogs/python/): การใข้งาน **MicroPython** และ **CircuitPython** ในเบื้องต้น
- แนะนำการเขียนโค้ดสำหรับไมโครคอนโทรลเลอร์ด้วย [**MicroPython**](https://iot-kmutnb.github.io/blogs/micropython/)
- แนะนำการเริ่มต้นฝึกเขียนโปรแกรมด้วย **MicroPython** จำแนกตามบอร์ดไมโครคอนโทรลเลอร์
	- [**Raspberry Pi Pico / Pico-W**](https://iot-kmutnb.github.io/blogs/micropython/micropython_rpi_pico/)
		- [**BBC Micro:bit V2**](https://iot-kmutnb.github.io/blogs/micropython/micropython_microbit_v2/)
		- [**Espressif ESP32**](https://iot-kmutnb.github.io/blogs/micropython/micropython_esp32/)
- ตัวอย่างการเขียนโค้ด **MicroPython for ESP32**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/micropython/micropython_esp32_part-1/) | [2](https://iot-kmutnb.github.io/blogs/micropython/micropython_esp32_part-2/) | [3](https://iot-kmutnb.github.io/blogs/micropython/micropython_esp32_part-3/)
- แนะนำการใช้งาน **TinyGo** สำหรับการเขียนโปรแกรมไมโครคอนโทรลเลอร์: [**TinyGo for MCU Programming**](https://iot-kmutnb.github.io/blogs/go/tinygo_intro/)
- แนะนำการใช้งาน **TinyGo** สำหรับบอร์ด **Raspberry Pico**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/go/tinygo_pico_part-1/) | [2](https://iot-kmutnb.github.io/blogs/go/tinygo_pico_part-2/)

---

### ▹ การใช้งานระบบปฏิบัติการ Linux และการเขียนโปรแกรมที่เกี่ยวข้อง

ความรู้และทักษะทางด้านคอมพิวเตอร์ที่เกี่ยวข้องกับระบบปฏิบัติการ **Linux** และการเขียนโปรแกรมภาษา **C/C++** ก็ถือว่าเป็นพื้นฐานที่สำคัญมาตั้งแต่อดีตจนถึงปัจจุบัน ในส่วนนี้มีบทความและหัวข้อมาแนะนำให้ลองศึกษาและปฏิบัติ

- การใช้ [**GNU C/C++ Toolchain**](https://iot-kmutnb.github.io/blogs/training/gcc_linux/) สำหรับการคอมไพล์โค้ดในเบื้องต้น
- การใช้ซอฟต์แวร์ [**Geany** เพื่อการเขียนโปรแกรมภาษา **C/C++**](https://iot-kmutnb.github.io/blogs/training/geany_editor/) (สำหรับ **Linux / Ubuntu**)
- การใช้งาน [**VS Code IDE** สำหรับ **Remote Development**](https://iot-kmutnb.github.io/blogs/training/vscode_remote/) (ใช้ **Windows** เป็น **Local OS** และ **Linux / Ubuntu** เป็น **Remote OS**)
- การเขียนโปรแกรมภาษา **C**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/training/c_tutorial_part-1/) | [2](https://iot-kmutnb.github.io/blogs/training/c_tutorial_part-2/) | [3](https://iot-kmutnb.github.io/blogs/training/c_tutorial_part-3/)
- การเขียนโค้ดภาษา **C/C++** ให้ทำงานแบบ **Multi-Threading** ด้วยไลบรารี [**Pthreads**](https://iot-kmutnb.github.io/blogs/pthreads/) สำหรับ **Linux**
- **MQTT** และการใช้งานสำหรับ **Linux**: ตอนที่ [1](https://iot-kmutnb.github.io/blogs/training/mqtt_linux_part-1/) | [2](https://iot-kmutnb.github.io/blogs/training/mqtt_linux_part-2/) | [3](https://iot-kmutnb.github.io/blogs/training/mqtt_linux_part-3/) | [4](https://iot-kmutnb.github.io/blogs/training/mqtt_linux_part-4/) | [5](https://iot-kmutnb.github.io/blogs/training/mqtt_linux_part-5/)
- การติดตั้ง [**Zigbee2MQTT**](https://iot-kmutnb.github.io/blogs/zigbee/zigbee2mqtt_linux/) (สำหรับ **Linux**) และใช้งานในเบื้องต้น

---

### ▹ การใช้งานคอมพิวเตอร์บอร์ดเดี่ยว

ปัจจุบันคอมพิวเตอร์บอร์ดเดี่ยว (**Single-Board Computer: SBC**) มีขนาดเล็ก ใช้กำลังไฟฟ้าไม่มาก มีตัวประมวลผลทั้ง 32 บิต หรือ 64 บิต ให้เลือกใช้ และมีหลายแกนอยู่ภายในชิป (**Multi-Core**) ดังนั้นจึงมีความสามารถมากกว่าไมโครคอนโทรลเลอร์ทั่วไป รองรับระบบปฏิบัติการ เช่น **Linux** และ **Android** เป็นต้น สามารถนำมาใช้งานได้ทั้งแบบตั้งโต๊ะ หรือเป็นเครื่องแม่ข่าย และงานทางด้านระบบสมองกลฝังตัว ดังนั้นความรู้และทักษะในการใช้งานฮาร์ดแวร์และซอฟต์แวร์สำหรับอุปกรณ์ประเภทนี้ ก็ถือว่าเป็นพื้นฐานที่สำคัญด้าน **IoT**

- [**Raspberry Pi 4 Model B + Raspberry Pi OS (64-bit)**](https://iot-kmutnb.github.io/blogs/rpi/rpi4b_headless/): การใช้งานแบบ **Headless** (โดยไม่ต่อจอแสดงผลและอุปกรณ์อินพุตจากผู้ใช้)

---

### ▹ การใช้งานโมดูลอิเล็กทรอนิกส์

การประยุกต์ใช้งานไมโครคอนโทรลเลอร์ เกี่ยวข้องกับการใช้งานวงจรอิเล็กทรอนิกส์ ไอซี และโมดูลเซนเซอร์ประเภทต่าง ๆ รายการบทความต่อไปนี้นำเสนอการใช้งานโมดูลอิเล็กทรอนิกส์และเขียนโปรแกรมด้วย **Arduino** ในเบื้องต้น

- โมดูลเซนเซอร์วัดความเข้มแสง:
	- [**BH1750**](https://iot-kmutnb.github.io/blogs/sensors/bh1750/)
		- [**MAX44009**](https://iot-kmutnb.github.io/blogs/sensors/max44009/)
		- [**VEML6070**](https://iot-kmutnb.github.io/blogs/sensors/veml6070/)
		- [**TEMT6000**](https://iot-kmutnb.github.io/blogs/sensors/temt6000/)
- โมดูลเซนเซอร์วัดอุณหภูมิและความชื้นสัมพัทธ์:
	- [**AHT10 / AHT2x (I2C)**](https://iot-kmutnb.github.io/blogs/sensors/aht2x/)
		- [**XY-MD02 (SHT40, RS485, Modbus-RTU)**](https://iot-kmutnb.github.io/blogs/sensors/xy-md02/)
- โมดูลเซนเซอร์อัลตราโซนิกสำหรับวัดระยะห่างจากวัตถุกีดขวาง:
	- [**HC-SR04**](https://iot-kmutnb.github.io/blogs/sensors/hc-sr04/)
		- [**GY-US042V2**](https://iot-kmutnb.github.io/blogs/sensors/gy-us042v2/)
- โมดูลรับสัญญาณอินฟราเรด
	- การรับค่าจากอุปกรณ์รีโมตคอนโทรล-อินฟราเรด: [**NEC Decoder**](https://iot-kmutnb.github.io/blogs/sensors/ir_receiver/)
- โมดูลจอภาพสำหรับการแสดงผลข้อความและเชิงกราฟิก
	- [**OLED Display (I2C / SPI)**](https://iot-kmutnb.github.io/blogs/displays/i2c_oled/)
		- [**TFT LCD (SPI)**](https://iot-kmutnb.github.io/blogs/displays/spi_tft_lcd/)
- โมดูล **RGB LED**
	- [**RGB LED**](https://iot-kmutnb.github.io/blogs/displays/rgb_led/)
		- [**MAX7219**](https://iot-kmutnb.github.io/blogs/displays/max7219/)
		- [**WS2812(B) / NeoPixel**](https://iot-kmutnb.github.io/blogs/displays/neopixel_rgb_leds/)
- โมดูลไมโครโฟนเสียง
	- [**MAX4466 Analog Sound Sensor**](https://iot-kmutnb.github.io/blogs/sensors/max4466/)
- โมดูล **ADC / DAC**
	- [**MCP3201 SPI ADC**](https://iot-kmutnb.github.io/blogs/electronics/mcp3201_adc_spi/)
		- [**MCP4725 I2C DAC**](https://iot-kmutnb.github.io/blogs/electronics/mcp4725_dac_i2c/)
		- [**MCP4921 SPI DAC**](https://iot-kmutnb.github.io/blogs/electronics/mcp4921_dac_spi/)
- ไอซีตัวต้านทานปรับค่าได้แบบดิจิทัล (**Digital Potentiometer**)
	- [**MCP41010**](https://iot-kmutnb.github.io/blogs/electronics/digi_pot/)
- โมดูลสื่อสาร
	- [**RS485 Transceiver**](https://iot-kmutnb.github.io/blogs/electronics/rs485_modules/)
- โมดูลเซนเซอร์วัดกระแสและพลังงาน
	- แนะนำการใช้งาน [**MAX4080 Current Sensor**](https://iot-kmutnb.github.io/blogs/electronics/max4080/)
		- แนะนำการใช้งาน [**INA169 Current Shunt Monitor**](https://iot-kmutnb.github.io/blogs/electronics/ina169/)

---

### ▹ วงจรไฟฟ้าและอิเล็กทรอนิกส์

นอกเหนือจากความรู้เกี่ยวกับการเขียนโปรแกรมแล้ว ความรู้ทางไฟฟ้าและอิเล็กทรอนิกส์และทักษะที่เกี่ยวข้อง ก็มีความสำคัญเช่นกัน → มีบทความที่เกี่ยวข้องต่อไปนี้

- การใช้งานบอร์ด **Arduino** ควบคู่กับการทดลองไฟฟ้าและอิเล็กทรอนิกส์: [**Using Arduino for Circuits & Electronics Labs**](https://iot-kmutnb.github.io/blogs/electronics/electronics_labs_with_arduino/)
- การต่อวงจรไฟฟ้าและอิเล็กทรอนิกส์พื้นฐานบนแผงต่อวงจร: [**Breadboards & Circuit Prototyping**](https://iot-kmutnb.github.io/blogs/electronics/breadboard_prototyping/)
- แนะนำซอฟต์แวร์: [**Autodesk Tinkercad Circuits**](https://iot-kmutnb.github.io/blogs/tinkercad/)
- ซอฟต์แวร์สำหรับการวิเคราะห์และจำลองการทำงานของวงจรไฟฟ้า-อิเล็กทรอนิกส์: [**Circuits and Electronics Simulation Software**](https://iot-kmutnb.github.io/blogs/electronics/circuit_simulation_software/)
- แนะนำการต่อวงจรเสมือนจริงร่วมกับบอร์ด **Arduino Uno** ด้วยซอฟต์แวร์ **AUTODESK Tinkercad Circuits**: [**Arduino & Circuit Virtual Prototyping**](https://iot-kmutnb.github.io/blogs/electronics/tinkercad_uno_breadboard/)
- การฝึกต่อตัวต้านทานหลายตัวบนเบรดบอร์ดและวัดค่าความต้านทานรวม: [**Resistor-Only Circuit Lab**](https://iot-kmutnb.github.io/blogs/electronics/resistor_network_lab/)
- โครงข่ายของตัวต้านทานแบบ **Binary Tree** และ **Ladder Structure** และการหาค่าความต้านทานรวม: [**Resistor Network and Resistance Measurement**](https://iot-kmutnb.github.io/blogs/electronics/resistor_networks_ladder_binary_tree/)
- [**R-2R DAC Lab**](https://iot-kmutnb.github.io/blogs/electronics/r2r_lab/): การฝึกต่อวงจร บนเบรดบอร์ดร่วมกับบอร์ด **Arduino Uno**
- [**Voltage Divider Lab**](https://iot-kmutnb.github.io/blogs/electronics/voltage_divider_lab/): การฝึกต่อวงจรแบ่งแรงดันบนเบรดบอร์ดร่วมกับบอร์ด **Arduino Uno**
- [**Voltage Measurement with Micro:bit**](https://iot-kmutnb.github.io/blogs/electronics/tinkercad_microbit_resistance_mesurement/): การวัดค่าความต้านทานด้วยบอร์ด **Micro:bit** และจำลองการทำงานด้วย **AUTODESK Tinkercad**
- ตัวอย่างการใช้ซอฟต์แวร์เพื่อการวิเคราะห์วงจรไฟฟ้าพื้นฐาน (มีตัวอย่างการใช้ซอฟต์แวร์ **EasyEDA** การเขียนโค้ด **MATLAB** และ **Python**):
	- การวิเคราะห์และจำลองการทำงานของวงจรไฟฟ้ากระแสตรง: [**DC Circuit Analysis**](https://iot-kmutnb.github.io/blogs/electronics/dc_circuit_analysis/)
		- การวิเคราะห์และจำลองการทำงานของวงจรไฟฟ้ากระแสสลับ: [**AC Circuit Analysis**](https://iot-kmutnb.github.io/blogs/electronics/ac_circuit_analysis/)
		- การใช้วิธีโหนดและเมชเพื่อวิเคราะห์วงจรไฟฟ้าพื้นฐาน: [**Mesh and Nodal Circuit Analysis**](https://iot-kmutnb.github.io/blogs/electronics/mesh_and_nodal_analysis/)
		- การใช้แหล่งจ่ายไฟฟ้ากระแสตรงและวิเคราะห์วงจร: [**Constant DC Sources & Circuit Analysis**](https://iot-kmutnb.github.io/blogs/electronics/dc_sources_analysis/)
		- การวิเคราะห์วงจรไฟฟ้าพื้นฐานที่มี **R**, **L**, **C**: [**RLC Circuit Analysis**](https://iot-kmutnb.github.io/blogs/electronics/rlc_circuits/)
		- วงจรกรองความถี่แบบพาสซีฟสำหรับสัญญาณทางไฟฟ้า: [**Passive Filter Analysis**](https://iot-kmutnb.github.io/blogs/electronics/filter_circuits/)
- การทดลองหาค่าความจุของตัวเก็บประจุไฟฟ้าโดยใช้วงจร **RC** และบอร์ด **Arduino Uno / Nano**: [**Capacitance Measurement with Arduino**](https://iot-kmutnb.github.io/blogs/electronics/capacitance_measurement/)
- วิธีการวัดค่าของตัวเหนี่ยวนำหรือคอยล์โดยใช้วงจร **RLC** การวัดสัญญาณด้วยออสซิลโลสโคป: [**Inductance Measurement**](https://iot-kmutnb.github.io/blogs/electronics/inductance_measurement/) + [**Arduino Sketch Demo**](https://iot-kmutnb.github.io/blogs/electronics/arduino_inductance_measurement/)
- ตัวอย่างวงจรอิเล็กทรอนิกส์: [การสร้างสัญญาณพัลส์เมื่อกดปุ่มแล้วปล่อยโดยใช้ลอจิกเกตพื้นฐาน](https://iot-kmutnb.github.io/blogs/electronics/pulse_gen_logic_gates/)
- ความรู้พื้นฐานเกี่ยวกับไอซีลอจิกมาตรฐาน: [**Standard Logic ICs**](https://iot-kmutnb.github.io/blogs/electronics/std_logic_gates/)
- ความรู้พื้นฐานเกี่ยวกับไอซีลอจิกประเภทแลตช์: [**Latches**](https://iot-kmutnb.github.io/blogs/electronics/latches/)
- การสร้าวงจรตัวนับโดยใช้ฟลิปฟลอป **JK-FF** และการจำลองการทำงาน: [**4-bit Ripple-Carry Counter**](https://iot-kmutnb.github.io/blogs/electronics/ripple_carry_counter_jkff/)
- การใช้บอร์ด **Arduino** เลียนแบบการทำงานของวงจร [**Successive Approximation ADC**](https://iot-kmutnb.github.io/blogs/electronics/adc_successive_approx/)
- การเลือกใช้ไอซีประเภท [**Current-Sense Amplifier (CSA)**](https://iot-kmutnb.github.io/blogs/electronics/csa/) สำหรับการวัดกระแสในวงจรไฟฟ้า-อิเล็กทรอนิกส์
- การทดลองวัดกระแสโดยใช้โมดูล [**Current Sense Amplifier - MAX4080S**](https://iot-kmutnb.github.io/blogs/electronics/max4080_test/)
- การสร้างสัญญาณทดสอบด้วยบอร์ด **Arduino Uno / Nano** เพื่อการฝึกใช้ออสซิลโลสโคป ([**Arduino-based Test Signal Generation**](https://iot-kmutnb.github.io/blogs/electronics/arduino_test_signals/))

---

### ▹ เครื่องมือวัดและทดสอบทางอิเล็กทรอนิกส์

- มัลติมิเตอร์
	- การใช้งานมัลติมิเตอร์สำหรับการวัดปริมาณทางไฟฟ้าในเบื้องต้น: [**Multimeters**](https://iot-kmutnb.github.io/blogs/electronics/multimeters/)
- ออสซิลโลสโคปดิจิทัลและเครื่องวิเคราะห์สัญญาณดิจิทัล
	- สิ่งที่ควรรู้เกี่ยวกับการใช้งาน ["ออสซิลโลสโคป" (**Oscilloscopes**)](https://iot-kmutnb.github.io/blogs/electronics/oscilloscopes/)
		- แนะนำการใช้งานออสซิลโลสโคป [**RIGOL DS1054Z**](https://iot-kmutnb.github.io/blogs/electronics/rigol_ds1054z_basic/) ในเบื้องต้น
		- การใช้งานออสซิลโลสโคปและการเขียนโปรแกรมเชื่อมต่อ: [**RIGOL DS1054Z**](https://iot-kmutnb.github.io/blogs/electronics/rigol_scope_lxi/)
		- [**RIGOL DS1054Z + PulseView**](https://iot-kmutnb.github.io/blogs/tools/pulseview_rigol_ds1054z): แนะนำการใช้งานเพื่อการบันทึกและวิเคราะห์สัญญาณแอนะล็อก-ดิจิทัล
		- การเขียนโปรแกรม **Python** เชื่อมต่อผ่านเครือข่าย **LAN / LXI** สำหรับสโคป [**Rigol DS2072A**](https://iot-kmutnb.github.io/blogs/electronics/rigol_scope_ds2000_lxi/)
		- [**USB Logic Analyzer + PulseView**](https://iot-kmutnb.github.io/blogs/tools/logic_analyzer_pulseview/): แนะนำการใช้งานเพื่อการบันทึกและวิเคราะห์สัญญาณดิจิทัล
		- แนะนำการใช้งานเครื่องมือสร้างและวัดสัญญาณแบบพกพา [**ADALM2000**](https://iot-kmutnb.github.io/blogs/electronics/adalm2000_intro/) ในเบื้องต้น (สำหรับ **Windows 10 / 11**)
- แหล่งไฟ **DC Power Supply** แบบโปรแกรมได้
	- การเขียนโปรแกรม **Python** สำหรับ [**Rigol DP832 Programmable DC Power Supply**](https://iot-kmutnb.github.io/blogs/electronics/python_dp832/)
		- ตัวอย่างการโปรแกรม **Rigol DP832** เพื่อทดสอบไดโอดและทรานซิสเตอร์-มอสเฟต (**I-V Curve Tracing:**) [**Diode**](https://iot-kmutnb.github.io/blogs/electronics/dp832_diode_testing/) | [**MOSFET**](https://iot-kmutnb.github.io/blogs/electronics/dp832_mosfet_testing/)
		- การเขียนโปรแกรมด้วยภาษา **Python** ควบคุม [**FNIRSI DPS-150 DC Supply**](https://iot-kmutnb.github.io/blogs/electronics/dps150_dc_supply/)
- มิเตอร์ไฟฟ้าเชื่อมต่อด้วย **RS485/Modbus**: การอ่านค่าจากเพาเวอร์มิเตอร์ไฟฟ้าเฟสเดียวและสามเฟส
	- [**SDM120-Modbus**](https://iot-kmutnb.github.io/blogs/sensors/power_meter_sdm120_modbus/) | [**ZM194-D9Y (ZJZM)**](https://iot-kmutnb.github.io/blogs/sensors/power_meter_zm194-d9y/) | [**CJ-3D3YS (ZGCJ)**](https://iot-kmutnb.github.io/blogs/sensors/power_meter_cj-3d3ys/)

---

### ▹ การออกแบบวงจรดิจิทัลด้วย FPGA

การออกแบบวงจรดิจิทัลโดยใช้ชิป **FPGA** (*Field-Programmable Gate Array*) ซึ่งผู้ใช้สามารถโปรแกรมฮาร์ดแวร์ได้ในเชิงลอจิก ถือว่าเป็นอีกหนึ่งตัวเลือกที่สำคัญสำหรับนักพัฒนาระบบสมองกลฝังตัว → บทความสำหรับการเรียนรู้ที่เกี่ยวข้องในหัวข้อนี้

- หัวข้อในการเรียนรู้สำหรับการออกแบบวงจรลอจิก: [**Logic Design**](https://iot-kmutnb.github.io/blogs/fpga/logic_design_circuits_topics/)
- แนวทางการเรียนรู้การออกแบบวงจรดิจิทัลด้วยชิป **FPGA**: [**Guidelines for Learning FPGA Design**](https://iot-kmutnb.github.io/blogs/fpga/intro_fpga_learning/)
- การจำลองการทำงานของโค้ด **VHDL** ด้วย [**GHDL Simulator**](https://iot-kmutnb.github.io/blogs/fpga/ghdl_vhdl_sim/)
- การทดลองใช้งานซอฟต์แวร์ [**Intel FPGA Prime Lite Edition**](https://iot-kmutnb.github.io/blogs/fpga/intel_prime_lite_cyc4/) พร้อมตัวอย่างโค้ด **VHDL / Verilog** สาธิตการใช้บอร์ด **Cyclone IV FPGA** ในเบื้องต้น
- แนะนำการใช้งานบอร์ด [**Terasic DE10 Lite (MAX 10 FPGA)**](https://iot-kmutnb.github.io/blogs/fpga/de10_lite_intro/)
- แนะนำการใช้งานบอร์ด [**QMTECH Cyclone 10 LP Starter Kit**](https://iot-kmutnb.github.io/blogs/fpga/qmtech_cyclone10_intro/)
- การติดตั้งซอฟต์แวร์ [**AMD / Xilinx Vivado Design Suite**](https://iot-kmutnb.github.io/blogs/fpga/xilinx_vivado_linux/): สำหรับ **Ubuntu**
- การทดลองใช้งานบอร์ด [**Mojo v3 - Xilinx Spartan 6 FPGA** (*legacy*)](https://iot-kmutnb.github.io/blogs/fpga/mojo_v3/): สำหรับ **Ubuntu**
- แนะนำการใช้งานบอร์ด [**Sipeed Tang FPGA**](https://iot-kmutnb.github.io/blogs/fpga/tang_nano_boards/)
- การติดตั้งและใช้งานซอฟต์แวร์ [**Gowin IDE Standard Edition**](https://iot-kmutnb.github.io/blogs/fpga/tang_nano/): สำหรับ **Ubuntu** และบอร์ด **Sipeed Tang Nano (Gowin FPGA)**
- การใช้งานซอฟต์แวร์ **Open Source FPGA Design Tools**: สำหรับบอร์ด [**Sipeed Tang Nano (Gowin FPGA)**](https://iot-kmutnb.github.io/blogs/fpga/gowin_fpga_tools/) และ [**Lattice iCE40 FPGA**](https://iot-kmutnb.github.io/blogs/fpga/ice40_foss_tools/)
- ตัวอย่างการทดลองใช้งานบอร์ด [**Sipeed Tang Nano 1K FPGA**](https://iot-kmutnb.github.io/blogs/fpga/tang_nano_1k_demo/) โดยใช้ภาษา **VHDL**
- การใช้งานซอฟต์แวร์ [**Lattice Radiant**](https://iot-kmutnb.github.io/blogs/fpga/lattice_radiant_ice40/) สำหรับการออกแบบวงจรดิจิทัลด้วย **Lattice iCE40 FPGA**
- การทดลองใช้งาน [**PicoRV32 CPU Core**](https://iot-kmutnb.github.io/blogs/fpga/ice40_picorv32/) ในเบื้องต้น สำหรับบอร์ด **Lattice iCE40 FPGA**
- แนะนำการใช้งานซอฟต์แวร์: [**Signal Tap Logic Analyzer**](https://iot-kmutnb.github.io/blogs/fpga/signaltap_intro/)
- ตัวอย่างการออกแบบวงจรดิจิทัลสำหรับ **FPGA** ด้วยภาษา **VHDL / Verilog**
	- การใช้งานโมดูล [**AC Dimmer**](https://iot-kmutnb.github.io/blogs/fpga/fpga_ac_dimmer/) ปรับความสว่างของหลอดไฟ
		- การสร้างสัญญาณรูปไซน์ด้วยวิธี [**DDS (Direct Digital Synthesis)**](https://iot-kmutnb.github.io/blogs/fpga/fpga_dds_r2r_dac/) และการใช้วงจร **R-2R DAC** สร้างสัญญาณเอาต์พุต-แอนะล็อก
		- การใช้งานโมดูล [**MCP4725 I2C DAC**](https://iot-kmutnb.github.io/blogs/fpga/fpga_mcp4725_dac/) เพื่อสร้างสัญญาณเอาต์พุต-แอนะล็อก
		- การใช้งานไอซีตัวต้านทานปรับค่าได้แบบดิจิทัล [**MCP41010**](https://iot-kmutnb.github.io/blogs/fpga/fpga_mcp41010/)
		- การใช้งานไอซีแปลงข้อมูลดิจิทัลให้เป็นสัญญาณแอนะล็อก [**MCP4921 SPI DAC**](https://iot-kmutnb.github.io/blogs/fpga/fpga_mcp4921_dac/)
		- การอ่านค่าสัญญาณแอนะล็อกด้วยไอซี [**12-bit SPI ADC**](https://iot-kmutnb.github.io/blogs/fpga/fpga_adc_spi/)
		- การสร้างสัญญาณสำหรับ [**VGA: 800x600 @72Hz**](https://iot-kmutnb.github.io/blogs/fpga/vga_demo/)
		- การใช้งานวงจร [**On-chip ADC Core / Intel FPGA IP**](https://iot-kmutnb.github.io/blogs/fpga/max10_adc_pwm/) (ทดลองใช้กับบอร์ด **Terasic DE10-Lite FPGA**)
		- [**Getting Started with the Low-Cost Cyclone IV EP4CE6E22C8N FPGA Board**](https://iot-kmutnb.github.io/blogs/fpga/fpga_ep4ce6_board/)

---

ผู้ที่สนใจยังสามารถติดตามข่าวสารในอีกช่องทางหนึ่งผ่านทาง **Facebook Page**  
→ " **IoT Engineering Education** " ([https://fb.me/iot.kmutnb](https://fb.me/iot.kmutnb))

![](https://iot-kmutnb.github.io/blogs/assets/images/qrcode_fb.png)

---

## สัญญาอนุญาตการเผยแพร่

เผยแพร่ภายใต้สัญญาอนุญาตครีเอทีฟคอมมอนส์ (Creative Commons License): **CC BY-SA 4.0**

"อนุญาตให้ผู้อื่นสามารถนำผลงานไปใช้ ทำซ้ำ แจกจ่าย หรือดัดแปลงงานนั้นได้ แต่ผลงานที่ดัดแปลงนั้นจะต้องกำกับด้วยสัญญาอนุญาตเงื่อนไขเดียวกันกับต้นฉบับ เว้นแต่ว่าจะได้รับอนุญาตจากเจ้าของผลงานก่อน"

This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.