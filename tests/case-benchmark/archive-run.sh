#!/usr/bin/env bash
# archive-run.sh — Archive results after an interactive CASE run.
#
# Usage:
#   ./archive-run.sh CASE1 03 [exit_code]
#
# Copies analysis/ to results dir, writes meta.json with timing.

set -eo pipefail

DATA_DIR="${CASE_DATA_DIR:-/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects}"
RESULTS_DIR="${CASE_RESULTS_DIR:-$(cd "$(dirname "$0")" && pwd)/results}"

COMPOUND="${1:?Usage: $0 <compound> <run_number> [exit_code]}"
RUN_NUM="${2:?Usage: $0 <compound> <run_number> [exit_code]}"
RUN_NUM=$(printf "%02d" "$RUN_NUM")
EXIT_CODE="${3:-0}"

COMPOUND_DIR="$DATA_DIR/$COMPOUND"
FORMULA=$(cat "$COMPOUND_DIR/molecular-formula.txt" | tr -d '[:space:]')
RUN_DIR="$RESULTS_DIR/$COMPOUND/run-$RUN_NUM"

if [[ ! -d "$RUN_DIR" ]]; then
    echo "ERROR: Run dir not found: $RUN_DIR" >&2
    echo "Did you run prepare-run.sh first?" >&2
    exit 1
fi

# Calculate duration
END_EPOCH=$(date +%s)
if [[ -f "$RUN_DIR/.start_epoch" ]]; then
    START_EPOCH=$(cat "$RUN_DIR/.start_epoch")
    DURATION=$((END_EPOCH - START_EPOCH))
else
    DURATION="?"
fi

TIMESTAMP="?"
if [[ -f "$RUN_DIR/.start_time" ]]; then
    TIMESTAMP=$(cat "$RUN_DIR/.start_time")
fi

# Archive analysis
if [[ -d "$COMPOUND_DIR/analysis/" ]]; then
    cp -r "$COMPOUND_DIR/analysis/" "$RUN_DIR/analysis/"
    echo "Archived analysis/ → $RUN_DIR/analysis/"
else
    echo "WARNING: No analysis/ directory found"
fi

# Write metadata
cat > "$RUN_DIR/meta.json" <<METAEOF
{
    "compound": "$COMPOUND",
    "formula": "$FORMULA",
    "run": ${RUN_NUM#0},
    "timestamp": "$TIMESTAMP",
    "duration_s": $DURATION,
    "exit_code": $EXIT_CODE
}
METAEOF

# Clean up temp files
rm -f "$RUN_DIR/.start_time" "$RUN_DIR/.start_epoch"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  $COMPOUND run $RUN_NUM archived"
echo "  Duration: ${DURATION}s  │  Exit: $EXIT_CODE"
echo "  Location: $RUN_DIR"
echo "═══════════════════════════════════════════════════════════════"
