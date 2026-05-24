---
type: source
title: "นี่คือข้อมูล datasheet ของ DX-LR02"
slug: ข้อมูล-datasheet-ของ-dx-lr02
date_ingested: 2026-05-24
original_file: raw/ข้อมูล datasheet ของ DX-LR02 .md
tags: []
---

นี่คือข้อมูล datasheet ของ DX-LR02 

1. Chip Manufacturer Links：https://www.semtech.cn/products/wireless-rf/lora-connect/llcc68#talk-with-us-today
2. Module manufacturer link：http://en.szdx-smart.com/EN/zlxz/lymk.html（Select the required model or contact customer service to obtain the information you need）

Development Environment：Keil uVision5

File Description:
CH341SER driver.EXE is the driver software and must be installed before using UartAssist.exe.

Since the LR20/30 series has two versions, please check your order to confirm the version and refer to the corresponding video for learning how to burn the firmware.

https://youtu.be/hX-SSG80Oh8?si=5gjV5DjxgIYffU_W  《LR20/30 series old model burning tutorial》
https://youtu.be/L_HUamG1tiY?si=bQwIUzYVx_draZ6w  《LR20/30 Series New Burning Tutorial》

Note:
1.This document provides a quick guide on how to quickly verify the functionality of LR20/30 products and a tutorial on burning them.
2.Tutorial for those who cannot enter DFU mode

①Explanation of the issue regarding the inability to use DFU mode:
1. Check if the module is connected to the computer and inspect the USB cable.

②If not connected, please install the corresponding software driver.
1. Open the folder: Testing Tools—PC Serial Assistant—open the website in the file—download—PC test tools.zip—open CH341SER drive.EXE—install the driver.
2.http://en.szdx-smart.com/EN/zlxz/Development%20tools/PC%20serial%20port%20assistant/303.html—You can directly download PC test tools.zip from our official website and install the driver.

③Programming test:
1. Open the folder: Testing Tools—STM32F103 burning tool—mcuisp.exe—refer to the settings below—after setting, you can perform the programming test.
