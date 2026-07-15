#!/usr/bin/env bash
# scripts/eval/trigger_ci.sh — Trigger the subagent-eval GitHub workflow and watch it.
#
# Helper for the R1 "first-run verification" gate: checks `gh` CLI + auth + that
# the workflow exists on the default branch, then triggers it and watches the
# run. When the run is green, prints the exact one-line edit needed to enable
# the weekly schedule (uncomment the `schedule:` block).
#
# Usage:
#   bash scripts/eval/trigger_ci.sh                  # trigger + watch (default inputs)
#   bash scripts/eval/trigger_ci.sh --dry-run        # print the plan, do NOT trigger
#   bash scripts/eval/trigger_ci.sh --domains medical,finance --k 2
#   bash scripts/eval/trigger_ci.sh --no-watch       # trigger but do not block on watch
#
# Exit: 0=ok (run triggered / dry-run plan printed), 1=preflight failure
#
# This is a thin wrapper around `gh workflow run` + `gh run watch`. It makes
# zero API calls itself; the actual eval runs in GitHub Actions.

set -euo pipefail

WORKFLOW="subagent-eval.yml"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WF_PATH="$REPO_ROOT/.github/workflows/$WORKFLOW"

# ---- arg parsing ----
DRY_RUN=0
NO_WATCH=0
DOMAINS=""
K="2"
CREATE_ISSUE="true"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)    DRY_RUN=1; shift ;;
    --no-watch)   NO_WATCH=1; shift ;;
    --domains)    DOMAINS="$2"; shift 2 ;;
    --domains=*)  DOMAINS="${1#--domains=}"; shift ;;
    --k)          K="$2"; shift 2 ;;
    --k=*)        K="${1#--k=}"; shift ;;
    --no-issue)   CREATE_ISSUE="false"; shift ;;
    -h|--help)
      sed -n '2,16p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

echo "════════════════════════════════════════════════════════════════"
echo "  Subagent Eval CI — Trigger Helper (R1)"
echo "════════════════════════════════════════════════════════════════"
echo ""

# ---- preflight ----
echo "[1/4] Checking gh CLI..."
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ 'gh' CLI not found. Install: https://cli.github.com/"
  exit 1
fi
echo "  ✓ gh found: $(gh --version 2>/dev/null | head -1)"

echo "[2/4] Checking gh auth..."
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ Not authenticated. Run: gh auth login"
  gh auth status || true
  exit 1
fi
echo "  ✓ authenticated as: $(gh api user --jq .login 2>/dev/null || echo '(user lookup failed)')"

echo "[3/4] Checking workflow exists on default branch..."
if [ ! -f "$WF_PATH" ]; then
  echo "❌ Workflow file not found locally: $WF_PATH"
  exit 1
fi
# Confirm it's pushed to the remote default branch.
DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name 2>/dev/null || echo "main")"
REMOTE_WF_CHECK="$(gh api "repos/{owner}/{repo}/contents/.github/workflows/$WORKFLOW?ref=$DEFAULT_BRANCH" \
  --jq '.name' 2>/dev/null || echo "")"
if [ -z "$REMOTE_WF_CHECK" ]; then
  echo "❌ Workflow not found on remote '$DEFAULT_BRANCH'. Push the workflow file first."
  echo "   (Local copy exists at $WF_PATH but it may not be committed/pushed.)"
  exit 1
fi
echo "  ✓ workflow on $DEFAULT_BRANCH: $REMOTE_WF_CHECK"

echo "[4/4] Checking prior results (evals/subagents/results/)..."
RESULTS_DIR="$REPO_ROOT/evals/subagents/results"
if [ -d "$RESULTS_DIR" ] && ls "$RESULTS_DIR"/results-*.json >/dev/null 2>&1; then
  COUNT=$(ls -1 "$RESULTS_DIR"/results-*.json 2>/dev/null | wc -l | tr -d ' ')
  echo "  ℹ️  $COUNT prior result file(s) — a regression baseline exists."
else
  echo "  ℹ️  No prior results — this will be the FIRST run (no regression baseline)."
fi

echo ""
echo "Plan:"
echo "  Workflow:   $WORKFLOW"
echo "  Branch:     $DEFAULT_BRANCH"
echo "  domains:    '${DOMAINS:-(all)}'"
echo "  k:          $K"
echo "  create_issue: $CREATE_ISSUE"

if [ "$DRY_RUN" -eq 1 ]; then
  echo ""
  echo "[dry-run] Not triggering. Remove --dry-run to run for real."
  exit 0
fi

echo ""
echo "────────────────────────────────────────────────────────────────"
echo "  Triggering workflow..."
echo "────────────────────────────────────────────────────────────────"

# Build `gh workflow run` args (only pass --field for non-defaults).
RUN_ARGS=(workflow run "$WORKFLOW" -f "k=$K" -f "create_issue=$CREATE_ISSUE")
if [ -n "$DOMAINS" ]; then
  RUN_ARGS+=(-f "domains=$DOMAINS")
fi
gh "${RUN_ARGS[@]}"

echo "  ✓ Triggered."

# gh workflow run doesn't return the run URL directly. Find the newest run.
sleep 3  # let GitHub register the run
RUN_ID="$(gh run list --workflow="$WORKFLOW" --limit 1 --json databaseId --jq '.[0].databaseId' 2>/dev/null || echo "")"
RUN_URL="$(gh run list --workflow="$WORKFLOW" --limit 1 --json url --jq '.[0].url' 2>/dev/null || echo "")"

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ -n "$RUN_URL" ]; then
  echo "  Run URL: $RUN_URL"
fi
if [ -n "$RUN_ID" ]; then
  echo "  Run ID:  $RUN_ID"
fi
echo "════════════════════════════════════════════════════════════════"

if [ "$NO_WATCH" -eq 1 ]; then
  echo ""
  echo "Watch later with:"
  echo "  gh run watch $RUN_ID   # or open the URL above"
  exit 0
fi

echo ""
echo "Watching run (this blocks until completion; eval takes ~10-30 min)..."
if [ -n "$RUN_ID" ]; then
  # gh run watch exits non-zero if the run fails — don't let set -e kill us,
  # we want to print the post-run guidance either way.
  if gh run watch "$RUN_ID" --exit-status; then
    RUN_CONCLUSION="success"
  else
    RUN_CONCLUSION="failure"
  fi
else
  echo "  ⚠️  Could not resolve run ID — open the Actions tab to watch manually."
  RUN_CONCLUSION="unknown"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
if [ "$RUN_CONCLUSION" = "success" ]; then
  echo "  ✅ Run GREEN — next step: enable the weekly schedule."
  echo "════════════════════════════════════════════════════════════════"
  echo ""
  echo "Edit .github/workflows/subagent-eval.yml — uncomment the schedule block"
  echo "(currently lines 32-34):"
  echo ""
  echo "    # schedule:"
  echo "    #   # Mon 3:23 UTC (after agent-model-scan 2:41 + cross-platform 3:17)"
  echo "    #   - cron: \"23 3 * * 1\""
  echo ""
  echo "becomes:"
  echo ""
  echo "    schedule:"
  echo "      # Mon 3:23 UTC (after agent-model-scan 2:41 + cross-platform 3:17)"
  echo "      - cron: \"23 3 * * 1\""
  echo ""
  echo "Then commit:"
  echo "  git add .github/workflows/subagent-eval.yml"
  echo "  git commit -m 'docs(ci): enable weekly subagent-eval schedule'"
  echo ""
  echo "Results file: evals/subagents/results/results-<timestamp>.json (auto-committed by CI)"
  echo "Regression issue: check Actions tab for '🚨 Subagent eval regression detected'"
else
  echo "  ❌ Run did NOT finish green ($RUN_CONCLUSION)."
  echo "════════════════════════════════════════════════════════════════"
  echo ""
  echo "Do NOT enable the schedule yet. Debug first:"
  echo "  gh run view $RUN_ID --log-failed"
  echo ""
  echo "Common causes:"
  echo "  - OPENROUTER_API_KEY not set (hard requirement)"
  echo "  - Free-tier rate limit hit (reduce k=1, or run fewer domains)"
  echo "  - delegate.sh AWIKI_FORCE_MODEL routing bug"
fi
