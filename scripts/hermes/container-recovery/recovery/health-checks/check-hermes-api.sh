#!/bin/bash
# Check Hermes API via host-local curl (follows redirect through Umbrel middleware)
# This is a best-effort deep check; primary signal is container running status.
# Fallback: if curl not available, just indicate "running" (exit 0).

if command -v curl >/dev/null 2>&1; then
  if curl -sfL -m 5 http://localhost:18790/health >/dev/null 2>&1; then
    echo "Hermes API is responding"
    exit 0
  else
    echo "Hermes API is not responding"
    exit 1
  fi
fi

echo "Hermes check: no curl on host, skipping deep check"
exit 0
