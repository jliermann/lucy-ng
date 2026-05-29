#!/usr/bin/env bash
# run-benchmark.sh — Run the full CASE benchmark across all (or selected) compounds.
#
# Usage:
#   ./run-benchmark.sh                  # All 8 compounds
#   ./run-benchmark.sh CASE4 CASE8      # Subset
#   ./run-benchmark.sh --dry-run        # Preview only
#   ./run-benchmark.sh --runs 3 CASE1   # 3 runs instead of 5

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ALL_COMPOUNDS=(CASE1 CASE2 CASE3 CASE4 CASE5 CASE6 CASE7 CASE8)

# ── Argument parsing ──────────────────────────────────────────────────
COMPOUNDS=()
PASSTHROUGH_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)  PASSTHROUGH_ARGS+=("--dry-run"); shift ;;
        --runs)     PASSTHROUGH_ARGS+=("--runs" "$2"); shift 2 ;;
        CASE*)      COMPOUNDS+=("$1"); shift ;;
        *)          echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

if [[ ${#COMPOUNDS[@]} -eq 0 ]]; then
    COMPOUNDS=("${ALL_COMPOUNDS[@]}")
fi

# ── Banner ────────────────────────────────────────────────────────────
BENCH_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  CASE Benchmark — ${#COMPOUNDS[@]} compound(s)                             ║"
echo "║  Started: $BENCH_START                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ── Run each compound ─────────────────────────────────────────────────
FAILED=()
for COMPOUND in "${COMPOUNDS[@]}"; do
    if ! "$SCRIPT_DIR/run-one.sh" "$COMPOUND" "${PASSTHROUGH_ARGS[@]}"; then
        echo "WARNING: $COMPOUND had failures"
        FAILED+=("$COMPOUND")
    fi
    echo ""
done

# ── Extract results ───────────────────────────────────────────────────
BENCH_END=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Benchmark complete: $BENCH_END                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

if [[ ${#PASSTHROUGH_ARGS[@]} -eq 0 ]] || ! printf '%s\n' "${PASSTHROUGH_ARGS[@]}" | grep -q -- '--dry-run'; then
    echo ""
    echo "Extracting results..."
    "$SCRIPT_DIR/extract-results.sh"
fi

if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo ""
    echo "WARNING: These compounds had failures: ${FAILED[*]}"
fi
