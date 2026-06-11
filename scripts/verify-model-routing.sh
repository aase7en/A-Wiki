#!/usr/bin/env bash
# Verify that CLI agents can infer A-Wiki model-cost switching rules from repo context.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MOCK=0
OUT=""

while [ $# -gt 0 ]; do
    case "$1" in
        --mock)
            MOCK=1
            shift
            ;;
        --out)
            OUT="${2:-}"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--mock] [--out PATH]"
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [ -z "$OUT" ]; then
    mkdir -p "$REPO_ROOT/exports"
    OUT="$REPO_ROOT/exports/model-routing-$(date +%Y%m%d-%H%M%S).md"
else
    mkdir -p "$(dirname "$OUT")"
fi

PROMPT="In this A-Wiki repo, for a new multi-step project, what model-cost switching ladder should the agent use? Answer briefly and mention the tier names."

run_cmd() {
    local timeout_seconds="${AWIKI_VERIFY_MODEL_ROUTING_TIMEOUT:-60}"
    python3 - "$timeout_seconds" "$@" <<'PY'
import subprocess
import sys

timeout = int(sys.argv[1])
cmd = sys.argv[2:]
try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    sys.exit(result.returncode)
except subprocess.TimeoutExpired as exc:
    if exc.stdout:
        sys.stdout.write(exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode())
    if exc.stderr:
        sys.stderr.write(exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode())
    sys.stderr.write(f"timeout after {timeout}s\n")
    sys.exit(124)
PY
}

probe_output() {
    local agent="$1"

    if [ "$MOCK" -eq 1 ]; then
        case "$agent" in
            claude) echo "Use model-cost-switching: tier 4a/4b/4c with effort." ;;
            codex) echo "Default 4b, escalate to 4c, de-escalate to 4a." ;;
            gemini) echo "Use the best available model." ;;
        esac
        return 0
    fi

    case "$agent" in
        claude)
            command -v claude >/dev/null 2>&1 || return 127
            run_cmd claude -p "$PROMPT"
            ;;
        codex)
            command -v codex >/dev/null 2>&1 || return 127
            run_cmd codex exec "$PROMPT"
            ;;
        gemini)
            command -v gemini >/dev/null 2>&1 || return 127
            run_cmd gemini -p "$PROMPT"
            ;;
    esac
}

classify_output() {
    local output="$1"
    if printf '%s' "$output" | grep -Eiq 'session limit|ERROR|failed|timeout after|not authenticated|authentication|command not found'; then
        echo "FAIL"
        return
    fi
    if printf '%s' "$output" | grep -Eiq '4a|4b|4c|model-cost-switching|model-switching|tier'; then
        echo "PASS"
    else
        echo "FAIL"
    fi
}

pass_count=0
rows=""

for agent in claude codex gemini; do
    output=""
    status="FAIL"
    if output="$(probe_output "$agent")"; then
        status="$(classify_output "$output")"
    elif [ $? -eq 127 ]; then
        status="SKIP"
        output="command not found"
    else
        status="FAIL"
        output="probe failed"
    fi

    if [ "$status" = "PASS" ]; then
        pass_count=$((pass_count + 1))
    fi

    summary="$(printf '%s' "$output" | tr '\n' ' ' | sed 's/|/\\|/g' | cut -c 1-180)"
    rows="${rows}| ${agent} | ${status} | ${summary} |\n"
done

if [ "$pass_count" -ge 2 ]; then
    threshold="PASS"
    exit_code=0
else
    threshold="FAIL"
    exit_code=1
fi

{
    echo "# Model Routing Verification"
    echo
    echo "- generated_at: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "- repo: A-Wiki"
    echo "- PASS count: ${pass_count}/3"
    echo "- threshold: ${threshold}"
    echo
    echo "| Agent | Result | Evidence |"
    echo "|---|---|---|"
    printf '%b' "$rows"
} > "$OUT"

echo "wrote $OUT"
exit "$exit_code"
