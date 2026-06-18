---
type: source
title: "Network Monitoring for IoT Deployments"
slug: network-monitoring-iot
date_ingested: 2026-05-25
original_file: raw/legacy/network-monitoring-iot.md
tags: [network-monitoring, iot, snmp, metrics, observability]
provenance: legacy-import
---

# Network Monitoring for IoT Deployments

> **Type:** article
> **Domain:** IT
> **Ref:** https://www.cisco.com/c/en/us/solutions/internet-of-things/iot-network-monitoring.html
> **Ingested:** 2026-05-25
> **Quality:** curated
> **Tags:** network-monitoring, IoT, SNMP, metrics, observability

## Abstract

Network monitoring in IoT environments differs from traditional IT monitoring due to constrained devices, heterogeneous protocols, variable connectivity, and edge deployments. Key monitoring dimensions include device reachability (ICMP, CoAP ping), link quality (RSSI, SNR, packet loss), bandwidth utilization, message broker health (MQTT queue depth, throughput), and gateway availability. Protocols include SNMP (limited on constrained devices), NETCONF/YANG for configuration monitoring, and CoAP observe for real-time telemetry. Prometheus + Grafana is the dominant open-source stack, with MQTT exporter bridging IoT message brokers to the Prometheus ecosystem. Edge monitoring requires local aggregation with intermittent uplink sync.

## Key Concepts

- **MQTT Queue Depth** — Pending messages in broker, leading indicator of consumer lag
- **RSSI/SNR** — Received Signal Strength Indicator and Signal-to-Noise Ratio for wireless link quality
- **Prometheus Exporter** — Bridge converting IoT protocol metrics to Prometheus scrape format
- **Edge Monitoring** — Local metric aggregation and alerting with offline-first data sync
- **Blackbox Monitoring** — Synthetic probes checking end-to-end IoT pipeline (sensor → broker → app)

## Related Links

- https://prometheus.io/docs/operating/integrations/
- https://www.grafana.com/solutions/iot-monitoring/

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/iot/grafana]] — the dashboarding half of the Prometheus + Grafana stack
- [[entities/iot/influxdb]] — time-series metric store for IoT telemetry
- [[concepts/iot/mqtt-qos]] — MQTT broker queue depth / health monitoring discussed here

---
*Legacy sister-wiki import — provenance reconstructed 2026-06-18 (raw stub: `raw/legacy/network-monitoring-iot.md`).*