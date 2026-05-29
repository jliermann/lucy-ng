#!/usr/bin/env bash
# extract-results.sh — Parse archived benchmark runs into summary tables.
#
# Reads: results/<COMPOUND>/run-<NN>/
#   - meta.json          (timing, exit code)
#   - analysis/CASE-PROGRESS.md  (iterations, solutions, top SMILES)
#   - claude-output.txt   (fallback for crash detection)
#
# Outputs:
#   results/summary.tsv
#   results/consistency.txt
#   stdout: formatted summary table

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="${CASE_RESULTS_DIR:-$SCRIPT_DIR/results}"

if [[ ! -d "$RESULTS_DIR" ]]; then
    echo "No results directory found at $RESULTS_DIR" >&2
    exit 1
fi

TSV_FILE="$RESULTS_DIR/summary.tsv"
CONSISTENCY_FILE="$RESULTS_DIR/consistency.txt"

# ── TSV header ────────────────────────────────────────────────────────
echo -e "compound\trun\titerations\tsolutions\ttop_smiles\tdiagnostic_spawned\tduration_s\texit_code\tstatus" > "$TSV_FILE"

# ── Helper: extract field from CASE-PROGRESS.md ──────────────────────
extract_from_progress() {
    local progress_file="$1"
    local field="$2"

    case "$field" in
        iterations)
            # Count "## Iteration" headers
            grep -c '^## Iteration' "$progress_file" 2>/dev/null || echo "0"
            ;;
        solutions)
            # Look for final solution count — patterns like "N solutions" or "solutions: N"
            # Take the last occurrence (final iteration result)
            grep -ioE '[0-9]+ solutions?' "$progress_file" 2>/dev/null \
                | tail -1 | grep -oE '^[0-9]+' || echo "?"
            ;;
        top_smiles)
            # Look for SMILES in ranking section — first line matching a SMILES-like pattern
            # after "rank" or "solution" headers
            grep -oE '[A-Za-z0-9@+\-\[\]\\()=#/]{10,}' "$progress_file" 2>/dev/null \
                | grep -E '^[A-Za-z]' \
                | grep -E '[()=]' \
                | head -1 || echo "-"
            ;;
        diagnostic)
            # Check if diagnostic specialist was mentioned
            if grep -qi 'diagnostic\|lucy-diagnostic' "$progress_file" 2>/dev/null; then
                echo "yes"
            else
                echo "no"
            fi
            ;;
    esac
}

# ── Determine run status ─────────────────────────────────────────────
determine_status() {
    local exit_code="$1"
    local solutions="$2"
    local iterations="$3"
    local progress_exists="$4"

    if [[ "$exit_code" -ne 0 ]]; then
        echo "crashed"
    elif [[ "$progress_exists" == "false" ]]; then
        echo "no-progress"
    elif [[ "$solutions" == "?" || "$solutions" == "0" ]]; then
        echo "failed"
    elif [[ "$iterations" -ge 1 ]]; then
        # Check if it seems to have converged (has solutions)
        if [[ "$solutions" -gt 0 ]] 2>/dev/null; then
            echo "converged"
        else
            echo "partial"
        fi
    else
        echo "partial"
    fi
}

# ── Process each run ──────────────────────────────────────────────────
for compound_dir in "$RESULTS_DIR"/CASE*/; do
    [[ -d "$compound_dir" ]] || continue
    COMPOUND=$(basename "$compound_dir")

    for run_dir in "$compound_dir"/run-*/; do
        [[ -d "$run_dir" ]] || continue
        RUN=$(basename "$run_dir" | sed 's/run-//')

        # Read meta.json
        META="$run_dir/meta.json"
        if [[ -f "$META" ]]; then
            DURATION=$(python3 -c "import json; print(json.load(open('$META'))['duration_s'])" 2>/dev/null || echo "?")
            EXIT_CODE=$(python3 -c "import json; print(json.load(open('$META'))['exit_code'])" 2>/dev/null || echo "?")
        else
            DURATION="?"
            EXIT_CODE="?"
        fi

        # Find CASE-PROGRESS.md (may be in analysis/ or analysis/iteration_*/
        PROGRESS=""
        PROGRESS_EXISTS="false"
        for candidate in \
            "$run_dir/analysis/CASE-PROGRESS.md" \
            "$run_dir/analysis/"*/CASE-PROGRESS.md; do
            if [[ -f "$candidate" ]]; then
                PROGRESS="$candidate"
                PROGRESS_EXISTS="true"
                break
            fi
        done

        if [[ -n "$PROGRESS" ]]; then
            ITERATIONS=$(extract_from_progress "$PROGRESS" iterations)
            SOLUTIONS=$(extract_from_progress "$PROGRESS" solutions)
            TOP_SMILES=$(extract_from_progress "$PROGRESS" top_smiles)
            DIAGNOSTIC=$(extract_from_progress "$PROGRESS" diagnostic)
        else
            ITERATIONS="0"
            SOLUTIONS="?"
            TOP_SMILES="-"
            DIAGNOSTIC="?"
        fi

        STATUS=$(determine_status "$EXIT_CODE" "$SOLUTIONS" "$ITERATIONS" "$PROGRESS_EXISTS")

        echo -e "$COMPOUND\t$RUN\t$ITERATIONS\t$SOLUTIONS\t$TOP_SMILES\t$DIAGNOSTIC\t$DURATION\t$EXIT_CODE\t$STATUS" >> "$TSV_FILE"
    done
done

# ── Per-compound consistency ──────────────────────────────────────────
echo "# CASE Benchmark — Consistency Report" > "$CONSISTENCY_FILE"
echo "# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "$CONSISTENCY_FILE"
echo "" >> "$CONSISTENCY_FILE"

for compound_dir in "$RESULTS_DIR"/CASE*/; do
    [[ -d "$compound_dir" ]] || continue
    COMPOUND=$(basename "$compound_dir")

    # Count runs and collect top SMILES
    TOTAL=0
    declare -A SMILES_COUNT=()

    while IFS=$'\t' read -r c r it sol smi diag dur ec st; do
        [[ "$c" == "$COMPOUND" ]] || continue
        TOTAL=$((TOTAL + 1))
        if [[ "$smi" != "-" && "$smi" != "?" ]]; then
            SMILES_COUNT["$smi"]=$(( ${SMILES_COUNT["$smi"]:-0} + 1 ))
        fi
    done < <(tail -n +2 "$TSV_FILE")

    echo "## $COMPOUND ($TOTAL runs)" >> "$CONSISTENCY_FILE"
    if [[ ${#SMILES_COUNT[@]} -eq 0 ]]; then
        echo "  No top SMILES extracted from any run." >> "$CONSISTENCY_FILE"
    else
        for smi in "${!SMILES_COUNT[@]}"; do
            COUNT=${SMILES_COUNT["$smi"]}
            PCT=$(( COUNT * 100 / TOTAL ))
            echo "  $COUNT/$TOTAL ($PCT%) → $smi" >> "$CONSISTENCY_FILE"
        done
    fi
    echo "" >> "$CONSISTENCY_FILE"
    unset SMILES_COUNT
done

# ── Print summary to stdout ──────────────────────────────────────────
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Benchmark Results Summary                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Print TSV as aligned table
if command -v column &>/dev/null; then
    column -t -s $'\t' "$TSV_FILE"
else
    cat "$TSV_FILE"
fi

echo ""
echo "──────────────────────────────────────────────────────────────"
echo "Consistency:"
echo ""
cat "$CONSISTENCY_FILE" | grep -E '^\s|^##'

echo ""
echo "Full data: $TSV_FILE"
echo "Consistency: $CONSISTENCY_FILE"
