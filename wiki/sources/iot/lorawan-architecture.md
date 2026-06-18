---
type: source
title: "LoRaWAN Architecture"
slug: lorawan-architecture
date_ingested: 2026-05-25
original_file: raw/legacy/lorawan-architecture.md
tags: [lpwan, long-range, radio, sensor-network, iot]
provenance: legacy-import
---

# LoRaWAN Architecture

> **Type:** documentation
> **Domain:** IoT
> **Ref:** https://lora-alliance.org/about-lorawan/
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** LPWAN, long-range, radio, sensor-network

## Abstract

LoRaWAN is a Low Power Wide Area Network (LPWAN) protocol designed for battery-powered IoT devices over long distances (2-5 km urban, 15+ km rural). It uses chirp spread spectrum modulation in unlicensed ISM bands (868 MHz EU, 915 MHz US, 923 MHz Asia). The architecture follows a star-of-stars topology: end-devices communicate with gateways via LoRa radio, gateways forward packets to a Network Server over TCP/IP. It supports three device classes (A, B, C) trading off latency for power consumption.

## Key Concepts

- **Spread Spectrum** — Chirp modulation resilient to interference and Doppler shift
- **Adaptive Data Rate (ADR)** — Network server optimizes data rate and power for each device
- **Device Classes** — Class A (lowest power, bidirectional after uplink), B (scheduled receive slots), C (continuous receive)
- **Join Procedure** — Over-the-Air Activation (OTAA) vs Activation by Personalization (ABP)
- **Gateway** — Transparent bridge between LoRa radio and Network Server

## Related Links

- https://lora-alliance.org/about-lorawan/
- https://lora-developers.semtech.com/documentation/tech-papers-and-guides/lora-and-lorawan

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/lorawan]] — the LoRaWAN protocol this source documents
- [[concepts/iot/lora]] — the underlying LoRa physical layer / chirp spread spectrum
- [[entities/iot/chirpstack]] — open-source LoRaWAN Network Server implementation

---
*Legacy sister-wiki import — provenance reconstructed 2026-06-18 (raw stub: `raw/legacy/lorawan-architecture.md`).*