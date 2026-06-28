#!/bin/bash
# Check Bitcoin node sync status

output=$(docker exec bitcoin_app_1 bitcoin-cli getblockchaininfo 2>/dev/null) || exit 1

synced=$(echo "$output" | jq -r '.synced_to_chain // false')

if [[ "$synced" == "true" ]]; then
    echo "Bitcoin is fully synced"
    exit 0
else
    progress=$(echo "$output" | jq -r '.verification_progress // 0')
    pct=$(echo "$progress * 100" | bc -l 2>/dev/null | cut -c1-5)
    echo "Bitcoin is syncing: ${pct}%"
    exit 0
fi
