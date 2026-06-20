# Observability Checklist

**source**: addyosmani/agent-skills@v0.6.2 | **adapted**: A-Wiki | **verified**: 2026-06-20

Quick reference for instrumenting production code. Use alongside the `observability-and-instrumentation` skill.

## Table of Contents

- [On-Call Questions (Start Here)](#on-call-questions-start-here)
- [Structured Logging](#structured-logging)
- [Metrics](#metrics)
- [Distributed Tracing](#distributed-tracing)
- [Alerting](#alerting)
- [Dashboards](#dashboards)
- [Verify the Telemetry](#verify-the-telemetry)
- [Pre-Launch Gate](#pre-launch-gate)

## On-Call Questions (Start Here)

- [ ] 2-4 questions an on-call engineer will ask about this feature are written down
- [ ] Every signal below maps to one of those questions
- [ ] Each question is matched to the right signal type: metrics say **that** something is wrong, traces say **where**, logs say **why**

## Structured Logging

- [ ] Logs are structured (JSON) with stable event names
- [ ] Every log line carries a correlation/request ID
- [ ] Correlation ID is propagated on every outbound call
- [ ] Log levels are consistent: `error` = invariant broken, `warn` = degraded but handled, `info` = significant business event, `debug` = off in production
- [ ] No secrets, tokens, passwords, or PII in any log line
- [ ] Fields are allowlisted — no whole request/response bodies

## Metrics

- [ ] **RED** instrumented for every endpoint: Rate, Errors, Duration
- [ ] **USE** instrumented for every resource (queues, pools, hosts): Utilization, Saturation, Errors
- [ ] Latency is a histogram with p50/p95/p99 — never an average
- [ ] All labels come from small, fixed sets (route template, status class, provider name)
- [ ] No unbounded label values (no user IDs, raw URLs)

## Distributed Tracing

- [ ] OpenTelemetry initialized at service startup, before other imports
- [ ] Auto-instrumentation enabled for HTTP, gRPC, and DB clients
- [ ] Trace context propagated on every outbound call
- [ ] Manual spans only around meaningful internal units of work
- [ ] No secrets or PII as span attributes

## Alerting

- [ ] Every alert is symptom-based (error rate, latency, queue age) — causes go to dashboards, not pagers
- [ ] Every alert is actionable
- [ ] Every alert links to a runbook
- [ ] Thresholds justified by an SLO or historical data
- [ ] Two severities only: **page** (user-facing, act now) and **ticket** (degradation, act this week)
- [ ] Each new alert test-fired once

## Dashboards

- [ ] Service health dashboard exists: error rate, latency p99, traffic, saturation
- [ ] Dependency health panel shows per-service error rates and latency
- [ ] Default time range is sensible (1h-6h, not 30d)

## Verify the Telemetry

- [ ] Forced an error in staging → found it in the logs by correlation ID
- [ ] Sent test traffic → metric series appear with expected labels
- [ ] Followed one request end-to-end in the tracing UI → no broken spans

## Pre-Launch Gate

- [ ] Structured logs flowing to the log aggregator
- [ ] RED metrics visible in dashboards for every new endpoint
- [ ] At least one symptom-based alert configured, with runbook, test-fired
- [ ] A request can be traced across every service it touches
