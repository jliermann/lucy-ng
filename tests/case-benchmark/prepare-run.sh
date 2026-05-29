#!/usr/bin/env bash
# prepare-run.sh — Clean state before an interactive CASE run.
#
# Usage:
#   ./prepare-run.sh CASE1 03
#
# Cleans analysis dir and team state, then prints the command to run.

set -eo pipefail

DATA_DIR="${CASE_DATA_DIR:-/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects}"
RESULTS_DIR="${CASE_RESULTS_DIR:-$(cd "$(dirname "$0")" && pwd)/results}"

COMPOUND="${1:?Usage: $0 <compound> <run_number>}"
RUN_NUM="${2:?Usage: $0 <compound> <run_number>}"
RUN_NUM=$(printf "%02d" "$RUN_NUM")

COMPOUND_DIR="$DATA_DIR/$COMPOUND"
FORMULA=$(cat "$COMPOUND_DIR/molecular-formula.txt" | tr -d '[:space:]')
RUN_DIR="$RESULTS_DIR/$COMPOUND/run-$RUN_NUM"

# Clean
rm -rf "$COMPOUND_DIR/analysis/"
rm -rf ~/.claude/teams/case-* 2>/dev/null || true
rm -rf ~/.claude/tasks/case-* 2>/dev/null || true

# Create run dir and record start time
mkdir -p "$RUN_DIR"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$RUN_DIR/.start_time"
date +%s > "$RUN_DIR/.start_epoch"

echo "═══════════════════════════════════════════════════════════════"
echo "  $COMPOUND run $RUN_NUM  │  $FORMULA"
echo "  Cleaned: analysis/, teams, tasks"
echo "  Start:   $(cat "$RUN_DIR/.start_time")"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Now open a Claude Code session and run:"
echo ""
echo "  /lucy-ng:case $COMPOUND_DIR $FORMULA"
echo ""
echo "When done, run:"
echo ""
echo "  ./tests/case-benchmark/archive-run.sh $COMPOUND $RUN_NUM"
echo ""
