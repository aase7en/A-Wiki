#!/bin/bash
# Container Recovery Daemon v2.0 - FIXED
# Durable UmbrelOS container monitoring & recovery with Hermes model auto-restore
# Location: runs on Pi5 HOST (not inside container)
# State persists in recovery/ subdir (survives Umbrel app updates)
set -euo pipefail

# ===== CONFIGURATION =====
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BASE_DIR="$SCRIPT_DIR"
readonly LOG_FILE="${BASE_DIR}/recovery/recovery.log"
readonly DB_FILE="${BASE_DIR}/recovery/recovery.db"
readonly STATE_FILE="${BASE_DIR}/recovery/recovery-state.json"
readonly MODEL_STATE="${BASE_DIR}/model-state.json"
readonly CONTAINER_CONF="${BASE_DIR}/containers.conf"
readonly HEALTH_DIR="${BASE_DIR}/recovery/health-checks"

# Hermes CLI container (mode-switch.sh must docker exec here)
readonly HERMES_CLI_CONTAINER="hermes-agent_web_1"
readonly MODE_SWITCH_IN_CONTAINER="/opt/data/scripts/hermes/mode-switch.sh"

# Telegram config (from environment)
readonly TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
readonly TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Tier intervals (seconds)
readonly CRITICAL_INTERVAL=120   # 2 minutes
readonly IMPORTANT_INTERVAL=600  # 10 minutes
readonly WATCH_INTERVAL=1800     # 30 minutes

# ===== LOGGING =====
log() {
    local level="$1"
    shift
    local msg="$*"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $msg" | tee -a "$LOG_FILE"
}

rotate_log() {
    local max_size=$((10 * 1024 * 1024))  # 10MB
    if [[ -f "$LOG_FILE" ]]; then
        local file_size
        file_size=$(stat -c%s "$LOG_FILE" 2>/dev/null || stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)
        if [[ $file_size -gt $max_size ]]; then
            local backup="${LOG_FILE}.$(date +%Y%m%d_%H%M%S).bak"
            mv "$LOG_FILE" "$backup"
            gzip "$backup" 2>/dev/null || true
            log INFO "Log rotated: $backup.gz"
        fi
    fi
}

# ===== DATABASE =====
init_db() {
    if [[ ! -f "$DB_FILE" ]]; then
        sqlite3 "$DB_FILE" <<'EOF'
CREATE TABLE IF NOT EXISTS recovery_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    container TEXT NOT NULL,
    event_type TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    tier TEXT,
    priority INTEGER
);

CREATE TABLE IF NOT EXISTS model_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    expected_model TEXT,
    actual_model TEXT,
    success INTEGER,
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON recovery_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_container ON recovery_events(container);
CREATE INDEX IF NOT EXISTS idx_model_timestamp ON model_events(timestamp DESC);
EOF
        log INFO "Database initialized: $DB_FILE"
    fi
}

log_event() {
    local container="$1"
    local event_type="$2"
    local status="$3"
    local message="${4:-}"
    local tier="${5:-}"
    local priority="${6:-0}"

    sqlite3 "$DB_FILE" <<EOF
INSERT INTO recovery_events (container, event_type, status, message, tier, priority)
VALUES ('$container', '$event_type', '$status', '$message', '$tier', $priority);
EOF
}

log_model_event() {
    local event_type="$1"
    local expected_model="${2:-}"
    local actual_model="${3:-}"
    local success="${4:-0}"
    local message="${5:-}"

    sqlite3 "$DB_FILE" <<EOF
INSERT INTO model_events (event_type, expected_model, actual_model, success, message)
VALUES ('$event_type', '$expected_model', '$actual_model', $success, '$message');
EOF
}

# ===== STATE MANAGEMENT =====
load_state() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo '{}'
    fi
}

update_stats() {
    local state
    state=$(load_state)

    local total_checks total_recoveries model_restores
    total_checks=$(jq -r '.total_checks // 0' <<< "$state")
    total_recoveries=$(jq -r '.total_recoveries // 0' <<< "$state")
    model_restores=$(jq -r '.model_restores // 0' <<< "$state")

    jq \
        --argjson checks "$((total_checks + 1))" \
        --argjson recoveries "$total_recoveries" \
        --argjson restores "$model_restores" \
        --arg last_check "$(date -Iseconds)" \
        '{
            last_check: $last_check,
            daemon_version: "2.0",
            total_checks: $checks,
            total_recoveries: $recoveries,
            model_restores: $restores,
            last_recovery: .last_recovery,
            version: "2.0"
        }' <<< "$state" > "$STATE_FILE"
}

record_recovery() {
    local container="$1"
    local tier="$2"

    local state
    state=$(load_state)
    jq \
        --arg container "$container" \
        --arg timestamp "$(date -Iseconds)" \
        --arg tier "$tier" \
        '.last_recovery = {container: $container, timestamp: $timestamp, tier: $tier}' \
        <<< "$state" | jq '.total_recoveries += 1' > "$STATE_FILE"
}

record_model_restore() {
    local state
    state=$(load_state)
    jq '.model_restores += 1' <<< "$state" > "$STATE_FILE"
}

# ===== CONTAINER CHECKS =====
get_container_status() {
    local container="$1"
    docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found"
}

run_health_check() {
    local container="$1"
    local health_script="$2"

    if [[ -z "$health_script" ]]; then
        return 0
    fi

    local script_path="${HEALTH_DIR}/${health_script}"
    if [[ -x "$script_path" ]]; then
        "$script_path"
        return $?
    fi

    log WARN "Health check script not found or not executable: $script_path"
    return 0
}

check_container() {
    local container="$1"
    local tier="$2"
    local health_script="${3:-}"

    local status
    status=$(get_container_status "$container")

    if [[ "$status" == "running" ]]; then
        if ! run_health_check "$container" "$health_script"; then
            log WARN "Deep health check FAILED for $container"
            log_event "$container" "health_check_failed" "running" "Deep check failed" "$tier"
            return 1
        fi

        log DEBUG "$container is healthy (tier: $tier)"
        log_event "$container" "check" "healthy" "" "$tier"
        return 0
    fi

    log WARN "$container is NOT running: $status"
    log_event "$container" "detected" "$status" "Container not running" "$tier"
    return 1
}

recover_container() {
    local container="$1"
    local tier="$2"

    log WARN "Attempting to recover $container..."

    if docker start "$container" >/dev/null 2>&1; then
        log INFO "Successfully recovered $container"
        log_event "$container" "recovered" "running" "Docker start successful" "$tier"

        record_recovery "$container" "$tier"

        send_alert "Container **$container** recovered at $(date '+%Y-%m-%d %H:%M:%S')"
        return 0
    else
        log ERROR "Failed to recover $container"
        log_event "$container" "recovery_failed" "failed" "Docker start failed" "$tier"
        send_alert "CRITICAL: Failed to recover **$container**"
        return 1
    fi
}

# ===== HERMES MODEL RECOVERY (FIXED - docker exec into CLI container) =====
check_and_restore_hermes_model() {
    log INFO "Checking Hermes model routing..."

    local expected_mode
    expected_mode=$(jq -r '.mode // "unknown"' "$MODEL_STATE" 2>/dev/null || echo "unknown")

    log INFO "Expected mode: $expected_mode"

    if [[ "$expected_mode" != "freeforall" ]]; then
        log INFO "Mode is $expected_mode, no model restore needed"
        return 0
    fi

    log INFO "Running mode-switch.sh to restore FREE-FOR-ALL mode..."

    for i in $(seq 1 30); do
        if docker exec "$HERMES_CLI_CONTAINER" test -f "$MODE_SWITCH_IN_CONTAINER" 2>/dev/null; then
            break
        fi
        sleep 2
    done

    if docker exec "$HERMES_CLI_CONTAINER" bash "$MODE_SWITCH_IN_CONTAINER" freeforall >> "$LOG_FILE" 2>&1; then
        log INFO "Hermes model restored to FREE-FOR-ALL"
        send_alert "Hermes model restored to FREE-FOR-ALL (free models)"
        log_model_event "restored" "freeforall" "freeforall" 1 "mode-switch via docker exec"
        record_model_restore
        return 0
    else
        log ERROR "Failed to restore Hermes model via mode-switch.sh"
        log_model_event "restored" "freeforall" "unknown" 0 "docker exec mode-switch.sh failed"
        return 1
    fi
}

# ===== TELEGRAM ALERTING =====
send_alert() {
    local message="$1"

    mkdir -p "$BASE_DIR/recovery/alerts"
    local alert_file="${BASE_DIR}/recovery/alerts/alert_$(date +%s).txt"
    echo "$message" > "$alert_file"

    if [[ -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        local response
        response=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${message}" \
            -d "parse_mode=Markdown" 2>&1)

        if echo "$response" | jq -e '.ok' >/dev/null 2>&1; then
            log INFO "Telegram alert sent"
        else
            log WARN "Failed to send Telegram alert: $response"
        fi
    fi
}

# ===== TIER SCHEDULING =====
should_check_container() {
    local container="$1"
    local tier="$2"
    local now
    now=$(date +%s)

    local last_check_file="${BASE_DIR}/recovery/.last_check_${container}"
    local last_check=0

    if [[ -f "$last_check_file" ]]; then
        last_check=$(cat "$last_check_file")
    fi

    local interval
    case "$tier" in
        CRITICAL) interval=$CRITICAL_INTERVAL ;;
        IMPORTANT) interval=$IMPORTANT_INTERVAL ;;
        WATCH) interval=$WATCH_INTERVAL ;;
        *) interval=$CRITICAL_INTERVAL ;;
    esac

    local elapsed=$((now - last_check))

    if [[ $elapsed -ge $interval ]]; then
        echo "$now" > "$last_check_file"
        return 0
    fi

    return 1
}

# ===== MAIN RECOVERY LOOP =====
main() {
    log INFO "=== Container Recovery v2.0 Started ==="
    rotate_log
    init_db

    local recovered_hermes=false

    while IFS='|' read -r tier container priority description health_script; do
        [[ -z "$tier" || "$tier" =~ ^#.* ]] && continue

        if ! should_check_container "$container" "$tier"; then
            log DEBUG "Skipping $container (tier $tier not due yet)"
            continue
        fi

        log INFO "Checking $container (tier: $tier, priority: $priority)"

        if ! check_container "$container" "$tier" "$health_script"; then
            if recover_container "$container" "$tier"; then
                if [[ "$container" == "$HERMES_CLI_CONTAINER" ]]; then
                    recovered_hermes=true
                    log INFO "Hermes CLI container recovered, waiting 10s for service init..."
                    sleep 10
                fi
            fi
        fi
    done < "$CONTAINER_CONF"

    if [[ "$recovered_hermes" == true ]]; then
        log INFO "Restoring Hermes model routing..."
        check_and_restore_hermes_model
    fi

    update_stats
    log INFO "=== Recovery cycle completed ==="
}

main "$@"
