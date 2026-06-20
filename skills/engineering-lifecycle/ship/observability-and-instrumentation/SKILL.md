---
name: observability-and-instrumentation
description: Structured logging, RED metrics, OpenTelemetry tracing, symptom-based alerting — instrument as you build. Use when adding telemetry, or shipping anything that runs in production.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Observability and Instrumentation

## Overview

Observability means you can understand what a system is doing without deploying new code. Every feature should be instrumented as it's built — not after. The three pillars — logging, metrics, tracing — answer different questions: logs say *why*, metrics say *that*, traces say *where*.

## When to Use

- Building any feature that will run in production
- Adding an API endpoint or background job
- Setting up monitoring for a new service
- Debugging an issue where telemetry is missing
- Auditing existing observability gaps

## Structured Logging

- **Format**: JSON with stable event names (not free-form strings)
- **Fields**: timestamp, level, event, service, request_id, duration_ms, error
- **Levels**: `error` = invariant broken, `warn` = degraded but handled, `info` = significant event, `debug` = off in production
- **No secrets**: never log passwords, tokens, PII, or full request bodies
- **Correlation ID**: propagated on every outbound call via HTTP headers

## RED Metrics

Every endpoint and dependency gets:
- **Rate** — requests per second
- **Errors** — failed requests per second (by error type)
- **Duration** — latency histogram (p50, p95, p99)

## Distributed Tracing

- OpenTelemetry initialized at service startup
- Auto-instrumentation for HTTP, gRPC, DB clients
- Manual spans for meaningful internal units of work
- Trace context propagated on every outbound call

## Symptom-Based Alerting

- **Page**: user-facing issue, act now (error rate > 1%, p99 > 1s, queue > 1000)
- **Ticket**: degradation, act this week (p95 > 500ms, disk > 80%)
- Every alert links to a runbook
- No alerts that fire daily and get acknowledged without action

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll add logging if we need it" | When you need it, you needed it yesterday. Log from day one. |
| "Metrics are overkill for a simple endpoint" | Simple endpoints in aggregate make up system behavior. Every endpoint gets RED. |
| "Tracing is for microservices, this is a monolith" | Traces help even in a monolith — they show how a single request flows through modules. |
| "Users will report issues if something breaks" | Users report symptoms, not causes. Telemetry lets you find the cause without relying on user reports. |

## Red Flags

- Production issue debugging with no logs available
- Error messages that say "something went wrong" with no details
- No correlation IDs across service boundaries
- Average latency reported instead of percentiles
- Alerts that require SSH access to diagnose
- Dashboard that shows everything except the answer to the on-call question

## Verification

- [ ] Structured JSON logging with correlation ID
- [ ] RED metrics for every endpoint and dependency
- [ ] Trace context propagated on outbound calls
- [ ] At least one symptom-based alert per new feature
- [ ] No secrets or PII in logs
- [ ] Runbook exists for each alert
