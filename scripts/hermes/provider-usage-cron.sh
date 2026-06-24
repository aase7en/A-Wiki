#!/usr/bin/env bash
# Wrapper for provider-usage.py — runs with --json flag
cd "$(dirname "$0")"
exec python3 provider-usage.py --json
