# MQTT: The Standard Messaging Protocol for IoT

**Source**: Example article for wiki initialization  
**Date**: 2026-04-18

## What is MQTT?

MQTT (Message Queuing Telemetry Transport) is a lightweight, publish-subscribe network protocol that transports messages between devices. It was designed by Andy Stanford-Clark (IBM) and Arlen Nipper in 1999 for monitoring oil pipelines via satellite. MQTT is now an OASIS standard (v3.1.1 and v5.0).

## How MQTT Works

MQTT uses a broker-based architecture:
- **Broker**: A central server (e.g., Mosquitto, EMQX, HiveMQ) that receives and routes messages
- **Publisher**: A device that sends messages to a topic
- **Subscriber**: A device that listens to one or more topics

Topics are hierarchical strings, e.g. `home/living-room/temperature`. Wildcards: `+` (single level), `#` (multi-level).

## QoS Levels

| QoS | Name | Guarantee |
|-----|------|-----------|
| 0 | At most once | Fire and forget, may lose messages |
| 1 | At least once | Guaranteed delivery, may duplicate |
| 2 | Exactly once | Guaranteed, no duplicates, slowest |

## MQTT vs HTTP

MQTT uses ~2x less battery than HTTP for small payloads. Header overhead: MQTT fixed header is 2 bytes vs HTTP ~500 bytes typical. MQTT maintains persistent TCP connections; HTTP opens/closes per request.

## MQTT 5.0 New Features (2019)

- Reason codes on all ACKs
- User properties (custom key-value headers)
- Message expiry interval
- Shared subscriptions (load balancing)
- Request/response pattern support
- Topic aliases

## Security

MQTT supports TLS/SSL on port 8883 (vs plain 1883). Authentication via username/password or client certificates. Authorization is broker-specific (topic-level ACLs).

## Common IoT Use Cases

1. Home automation (Home Assistant uses MQTT heavily)
2. Industrial sensor monitoring
3. Fleet tracking (vehicles, assets)
4. Smart agriculture
5. Healthcare monitoring

## Popular Brokers

- **Mosquitto** — open source, lightweight, ideal for Raspberry Pi / edge
- **EMQX** — enterprise-grade, high throughput (100M connections claimed)
- **HiveMQ** — enterprise, good Kubernetes support
- **AWS IoT Core** — managed, integrates with AWS ecosystem
- **Mosquitto** supports MQTT 3.1, 3.1.1, and 5.0

## Client Libraries

- Python: `paho-mqtt`
- JavaScript: `mqtt.js`, `MQTTX`
- Arduino/ESP32: `PubSubClient`, `AsyncMqttClient`
- Go: `paho.mqtt.golang`
