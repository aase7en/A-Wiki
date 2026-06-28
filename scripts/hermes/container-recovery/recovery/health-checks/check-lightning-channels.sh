#!/bin/bash
# Check Lightning channels

channels=$(docker exec lightning_lnd_1 lncli listchannels 2>/dev/null) || exit 1

count=$(echo "$channels" | jq -r '.channels | length' 2>/dev/null || echo 0)

if [[ "$count" -gt 0 ]]; then
    echo "Lightning: $count channels active"
    exit 0
else
    echo "Lightning: No channels (or node not ready)"
    exit 0
fi
