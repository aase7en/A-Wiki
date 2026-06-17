---
tags: [iot, lorawan, fuota, rak3172, rui3, chirpstackos]
type: source
title: "LoRaWAN® FUOTA on RAK3172 (RUI3 v5) with ChirpStackOS – Full Step-by-Step Demo"
slug: lorawan-fuota-on-rak3172-rui3-v5-with-chirpstackos-full-step-by-step-demo
date_ingested: 2026-05-24
original_file: raw/LoRaWAN® FUOTA on RAK3172 (RUI3 v5) with ChirpStackOS – Full Step-by-Step Demo.md
---

```yaml
---
title: "LoRaWAN® FUOTA on RAK3172 (RUI3 v5) with ChirpStackOS – Full Step-by-Step Demo"
source: "https://www.youtube.com/watch?v=uqUSpXV8yVM"
author: ""
published: "2026-03-03"
created: "2026-04-18"
description: "Learn how LoRaWAN® FUOTA (Firmware Update Over-the-Air) works on the RAK3172 using RUI3 v5 and ChirpStackOS. This step-by-step demo shows device setup, OTAA join, and multicast firmware updates.In t"
tags: ""
---
```

Learn how LoRaWAN® FUOTA (Firmware Update Over-the-Air) works on the RAK3172 using RUI3 v5 and ChirpStackOS. This step-by-step demo shows device setup, OTAA join, and multicast firmware updates.  
  
In this video, we walk through a pre-release LoRaWAN FUOTA demo on the RAK3172 using RUI3 v5 and ChirpStackOS.  
  
You’ll see the complete LoRaWAN FUOTA workflow, from creating an application in ChirpStackOS to configuring OTAA, joining the LoRaWAN® network using AT commands, and starting a LoRaWAN FUOTA session. We also demonstrate how firmware fragments are delivered using multicast once the device switches to Class C.  
  
This feature is in early beta. It is shared for testing and learning purposes only and is not ready for production use.  
  
What you’ll learn  
\- How to set up ChirpStackOS and the LNS  
\- How to add and configure a LoRaWAN device  
\- How OTAA join works using RUI3 AT commands  
\- Why uplink timing matters for LoRaWAN FUOTA  
\- How to create and start a LoRaWAN FUOTA session  
\- How multicast is used during firmware updates  
  
Timestamps  
0:00 Introduction and demo overview  
0:32 ChirpStackOS setup  
0:41 Creating an application  
0:45 Adding a LoRaWAN device  
0:53 OTAA configuration and keys  
1:07 Uplink interval considerations  
1:24 Joining the network with AT commands  
1:52 Why uplinks matter for LoRaWAN FUOTA downlinks  
2:12 Preparing a LoRaWAN FUOTA session  
2:31 Uploading firmware  
2:49 Starting the LoRaWAN FUOTA session  
3:38 Switching to Class C  
3:42 Multicast fragment delivery  
4:15 Verifying firmware update  
  
If this video helps you, like and subscribe for more LoRaWAN and RUI3 tutorials.  
Have questions or want to see a specific topic next? Leave a comment below.  
  
#FUOTA #RAK3172 #RUI3 #ChirpStackOS #LoRaWAN #FirmwareUpdate #Multicast #ClassC #IoTDevelopment #rakwireless  
  
RAKwireless Official website ➡ https://www.rakwireless.com  
Buy it here ➡ https://store.rakwireless.com  
Have a question ➡ https://forum.rakwireless.com  
Documentation ➡ https://docs.rakwireless.com  
Latest Updates ➡ https://news.rakwireless.com  
Join RAKwireless Affiliate Program ➡ https://bit.ly/RAK-Affiliate  
  
For the latest updates from RAK follow us:  
https://www.facebook.com/RakwirelessIoT  
https://www.instagram.com/rak\_wireless  
https://www.linkedin.com/company/rakwireless  
https://twitter.com/RAKwireless  
http://www.youtube.com/c/RAKwireless  
https://pinterest.com/rakwireless

## Transcript

### Introduction and demo overview

**0:00** · In this video, we're going to walk through a pre-release demo of FOTA on the Rack 3172 using RUI 3V5 and Chirp Stack OS. I'll guide you step by step from setting up your application, configuring the device, and joining the network all the way to starting a FUDA session and seeing the fragments come in. This is an early beta feature and it's a good chance to explore how the workflow actually looks. If you're testing FUD or just curious about how the process works, this tutorial will help you follow along easily.

**0:30** · Let's get started with the Chirpstack OS setup.

### ChirpStackOS setup

**0:36** · Open your Chirpstack OS. Run the LNS and login.

### Creating an application

**0:41** · Start by creating an application.

### Adding a LoRaWAN device

**0:45** · Add a Laurowan device inside the application. Set up the name and OTAA parameters including device profile. For the OTAA key, you can generate it and make sure that the application key is the same as gen app key which is needed for remote multiccast setup. Before proceeding, you can check if the MAC version in the device profile is correct as well as expected uplink interval which is 30 seconds.

### OTAA configuration and keys

### Uplink interval considerations

**1:13** · Connect your rack 3172 evaluation board and open serial terminal software.

**1:19** · Prepare the OTAA parameters including band and join settings. Input the AT commands and command the device to join the network.

### Joining the network with AT commands

**1:44** · Once joined successfully, it is very important to set up the uplink interval to 10 seconds.

### Why uplinks matter for LoRaWAN FUOTA downlinks

**1:52** · When FOD session started, the down link needs to be captured which RX window happens after an uplink.

**1:59** · Observe the successful uplink events.

### Preparing a LoRaWAN FUOTA session

**2:12** · Go to fuota tab to prepare for fuota session. Create a new fuota deployment.

**2:19** · You can follow these fuota settings or adjust as necessary.

### Uploading firmware

**2:31** · Select and submit the firmware to be uploaded via FOD.

**2:38** · Add the device to the FOD session created.

### Starting the LoRaWAN FUOTA session

**2:50** · Go to the FOD session tab. After adding the device, select the device and start the FOD session.

**3:08** · Open the serial terminal and you can see the down link going towards F-Port 2020.

**3:28** · This will be a long process and wait until the unit switches to class C and FOD session starts.

### Switching to Class C

**3:38** · Device moves to class C and FOD sessions begin. You can see the fragments being sent to the device. While waiting, you can check on the multiccast group tab for the fragments being uploaded as multiccast.

### Multicast fragment delivery

**4:00** · Check the uplink fragments shows FUTA is finished and the device reboots.

### Verifying firmware update

**4:15** · Observe successful uplinks on the new firmware.

**4:20** · Thanks for sticking with the FOD demo.

**4:23** · If this helped, hit like, subscribe, and let me know what you want to see next.

**4:28** · See you in the next video.
