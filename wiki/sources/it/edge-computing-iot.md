---
type: source
title: "Edge Computing Architectures for IoT"
slug: edge-computing-iot
date_ingested: 2026-05-25
original_file: raw/legacy/edge-computing-iot.md
tags: [edge-computing, iot, fog, processing, latency]
provenance: legacy-import
---

# Edge Computing Architectures for IoT

> **Type:** article
> **Domain:** IT
> **Ref:** https://www.ibm.com/topics/edge-computing
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** edge-computing, IoT, fog, processing, latency

## Abstract

Edge computing moves data processing closer to IoT devices to reduce latency, bandwidth consumption, and cloud dependency. Architectures follow a three-tier model: device edge (sensors/actuators with onboard MCU processing), gateway edge (local aggregation and protocol translation), and near edge (micro-datacenters or cloudlets within 10-20 ms latency). Key technologies include AWS Greengrass, Azure IoT Edge, EdgeX Foundry (open-source middleware), and WebAssembly for portable edge workloads. Data reduction techniques (filtering, aggregation, compression) at the edge can reduce cloud upload by 80-95%. Challenges include device heterogeneity, offline operation, secure OTA updates, and distributed ML model inference.

## Key Concepts

- **Three-Tier Edge** — Device edge → Gateway edge → Near edge / cloud continuum
- **AWS Greengrass** — Lambda execution and ML inference on IoT gateways with local MQTT broker
- **EdgeX Foundry** — Vendor-neutral edge middleware with device, core, and export microservices
- **Data Reduction** — On-edge filtering and aggregation before cloud transmission
- **Distributed ML Inference** — Model partitioning across edge and cloud (e.g., early exit DNNs)

## Related Links

- https://www.edgexfoundry.org/
- https://aws.amazon.com/greengrass/

## หน้า Wiki ที่ได้รับการอัปเดต

- [[concepts/iot/tinyml]] — on-device ML inference at the device edge
- [[entities/iot/raspberry-pi]] — common gateway-edge hardware for local aggregation
- [[concepts/iot/data-logger]] — edge data reduction / aggregation before cloud upload

---
*Legacy sister-wiki import — provenance reconstructed 2026-06-18 (raw stub: `raw/legacy/edge-computing-iot.md`).*