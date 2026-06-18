---
type: source
title: "MQTT Protocol Overview"
slug: mqtt-protocol-overview
date_ingested: 2026-05-25
original_file: raw/legacy/mqtt-protocol-overview.md
tags: [protocol, messaging, publish-subscribe, m2m, iot]
provenance: legacy-import
---

# MQTT Protocol Overview

> **Type:** documentation
> **Domain:** IoT
> **Ref:** https://mqtt.org/getting-started/
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** protocol, messaging, publish-subscribe, M2M

## Abstract

MQTT (Message Queuing Telemetry Transport) is a lightweight publish-subscribe messaging protocol designed for constrained devices and low-bandwidth, high-latency networks. It runs over TCP/IP with TLS encryption, supports three Quality of Service levels (0: at-most-once, 1: at-least-once, 2: exactly-once), and maintains persistent connections via a central broker. MQTT v5.0 adds session expiry, user properties, and reason codes. It is the de facto standard for IoT telemetry.

## Key Concepts

- **MQTT Broker** — Central server that routes messages between publishers and subscribers
- **Quality of Service (QoS)** — Three delivery guarantee levels: 0 (fire-and-forget), 1 (acknowledged), 2 (handshake)
- **Last Will Testament (LWT)** — Message sent by broker when client disconnects unexpectedly
- **Topic Tree** — Hierarchical namespace (e.g., `sensor/temperature/room1`) with wildcard support (`+`, `#`)
- **Retained Messages** — Last message kept by broker for new subscribers

## Related Links

- https://mqtt.org/getting-started/
- https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html
- https://www.hivemq.com/blog/mqtt-essentials-part-1-introducing-mqtt/

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/mqtt-protocol]] — entity page this source documents
- [[concepts/iot/mqtt-qos]] — QoS levels described here
- [[concepts/iot/publish-subscribe]] — the messaging pattern MQTT implements

---
*Legacy sister-wiki import — provenance reconstructed 2026-06-18 (raw stub: `raw/legacy/mqtt-protocol-overview.md`).*