#!/usr/bin/env bash
# run-one.sh — Run /lucy-ng:case N times on a single compound, archiving each run.
#
# Usage:
#   ./run-one.sh CASE1 [--runs N] [--dry-run]
#
# Reads molecular formula from $DATA_DIR/$compound/molecular-formula.txt

set -eo pipefail

# ── Configuration ──────────────────────────────────────────────────────
DATA_DIR="${CASE_DATA_DIR:-/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects}"
PROJECT_DIR="${CASE_PROJECT_DIR:-/Users/steinbeck/Dropbox/develop/lucy-ng}"
RESULTS_DIR="${CASE_RESULTS_DIR:-$(cd "$(dirname "$0")" && pwd)/results}"
NUM_RUNS=5
DRY_RUN=false

# ── Argument parsing ──────────────────────────────────────────────────
COMPOUND=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --runs)   NUM_RUNS="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -*)       echo "Unknown option: $1" >&2; exit 1 ;;
        *)        COMPOUND="$1"; shift ;;
    esac
done

if [[ -z "$COMPOUND" ]]; then
    echo "Usage: $0 <compound> [--runs N] [--dry-run]" >&2
    exit 1
fi

# ── Validate compound ─────────────────────────────────────────────────
COMPOUND_DIR="$DATA_DIR/$COMPOUND"
if [[ ! -d "$COMPOUND_DIR" ]]; then
    echo "ERROR: Compound directory not found: $COMPOUND_DIR" >&2
    exit 1
fi

FORMULA_FILE="$COMPOUND_DIR/molecular-formula.txt"
if [[ ! -f "$FORMULA_FILE" ]]; then
    echo "ERROR: No molecular-formula.txt in $COMPOUND_DIR" >&2
    exit 1
fi
FORMULA=$(cat "$FORMULA_FILE" | tr -d '[:space:]')

echo "═══════════════════════════════════════════════════════════════"
echo "  $COMPOUND  │  $FORMULA  │  $NUM_RUNS runs"
echo "═══════════════════════════════════════════════════════════════"

# ── Run loop ──────────────────────────────────────────────────────────
for ((i = 1; i <= NUM_RUNS; i++)); do
    RUN_NUM=$(printf "%02d" "$i")
    RUN_DIR="$RESULTS_DIR/$COMPOUND/run-$RUN_NUM"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    echo ""
    echo "── $COMPOUND run $RUN_NUM/$NUM_RUNS [$TIMESTAMP] ──"

    if $DRY_RUN; then
        echo "[DRY-RUN] Would clean: $COMPOUND_DIR/analysis/"
        echo "[DRY-RUN] Would clean: ~/.claude/teams/case-* ~/.claude/tasks/case-*"
        echo "[DRY-RUN] Would run:"
        echo "  claude -p \"/lucy-ng:case $COMPOUND_DIR $FORMULA\" \\"
        echo "    --permission-mode bypassPermissions \\"
        echo "    --add-dir \"$DATA_DIR\" \\"
        echo "    --model opus"
        echo "[DRY-RUN] Would archive to: $RUN_DIR/analysis/"
        echo "[DRY-RUN] Would write:      $RUN_DIR/meta.json"
        continue
    fi

    # 1. Clean previous analysis
    rm -rf "$COMPOUND_DIR/analysis/"

    # 2. Clean leftover team state
    rm -rf ~/.claude/teams/case-* 2>/dev/null || true
    rm -rf ~/.claude/tasks/case-* 2>/dev/null || true

    # 3. Create run directory
    mkdir -p "$RUN_DIR"

    # 4. Invoke CASE (unset CLAUDECODE to allow nested invocation)
    START_EPOCH=$(date +%s)
    EXIT_CODE=0
    env -u CLAUDECODE claude -p "/lucy-ng:case $COMPOUND_DIR $FORMULA" \
        --permission-mode bypassPermissions \
        --add-dir "$DATA_DIR" \
        --model opus \
        > "$RUN_DIR/claude-output.txt" 2>&1 || EXIT_CODE=$?
    END_EPOCH=$(date +%s)
    DURATION=$((END_EPOCH - START_EPOCH))

    # 5. Archive results
    if [[ -d "$COMPOUND_DIR/analysis/" ]]; then
        cp -r "$COMPOUND_DIR/analysis/" "$RUN_DIR/analysis/"
    else
        echo "  WARNING: No analysis/ directory produced"
    fi

    # 6. Write metadata
    cat > "$RUN_DIR/meta.json" <<METAEOF
{
    "compound": "$COMPOUND",
    "formula": "$FORMULA",
    "run": $i,
    "timestamp": "$TIMESTAMP",
    "duration_s": $DURATION,
    "exit_code": $EXIT_CODE
}
METAEOF

    # 7. Log progress
    echo "  Done: exit=$EXIT_CODE  duration=${DURATION}s  archived=$RUN_DIR"
done

echo ""
echo "All $NUM_RUNS runs for $COMPOUND complete."
