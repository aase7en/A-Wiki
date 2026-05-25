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

---
*Auto-created by `scripts/ingest-source.py` — review abstract and concepts for accuracy.*