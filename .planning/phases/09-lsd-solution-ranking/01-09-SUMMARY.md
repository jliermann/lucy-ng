# Phase 9 Summary: LSD Solution Ranking

## Outcome

**Successfully implemented** LSD solution ranking by comparing experimental 13C spectrum with predicted spectrum for each candidate structure. Uses the local HOSE-based C13Predictor (from Phase 8) for fast, offline prediction.

## What Was Built

### Core Module: `lucy_ng.ranking`

| Component | Description |
|-----------|-------------|
| `ShiftAssignment` | Pydantic model for predicted→experimental shift mapping |
| `RankedSolution` | Single solution with MAE score and assignments |
| `RankingResult` | Full ranking result with sorted solutions |
| `SolutionRanker` | Main ranker with greedy N:1 matching for symmetry |

### CLI Command

```bash
# Rank solutions using experimental 13C spectrum
lucy lsd rank ./solutions/ data/Ibuprofen/2 --table hose_lookup.json.gz

# Rank using curated peak list (recommended)
lucy lsd rank ./solutions/ --peaks "180.5,140.8,129.4,127.8"

# Top 5 with JSON output
lucy lsd rank ./solutions/ --peaks "180.5,140.8" --top 5 --format json
```

### MCP Tool

- `rank_lsd_solutions(solutions_dir, experimental_shifts, ...)` - Rank solutions for AI agents
- Auto-discovers HOSE table in default locations
- Returns sorted results with MAE scores and shift assignments

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| N:1 matching (not 1:1) | Molecular symmetry: equivalent carbons predict same shift, match single experimental peak |
| MAE as primary score | Simple, interpretable, lower is better |
| Unmatched penalty = 0.5×tolerance | Mild penalty so missing predictions don't dominate |
| 3.0 ppm default tolerance | Balances strictness vs prediction accuracy |
| Curated peaks preferred | Raw spectrum peak picking adds noise; curated list more reliable |

## Architecture

```
src/lucy_ng/ranking/
├── __init__.py       # Public API: SolutionRanker, RankedSolution, RankingResult
├── models.py         # Pydantic models for ranking results
└── ranker.py         # SolutionRanker with N:1 shift matching
```

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 991b0e5 | feat | Add LSD solution ranking by 13C spectrum prediction |
| c5f3ff8 | fix | Correct SMILES indexing and ranked_count in solution ranking |
| c1e3976 | wip | Phase 9 complete, pausing work |
| d23f2d5 | docs | Add solution ranking to USER_GUIDE.md |
| 54f877e | docs | Add predict_c13_shifts and rank_lsd_solutions to documentation |
| 70a8eb1 | fix | Correct AdaptivePeakPicker usage in lsd rank --spectrum |
| cd129d2 | docs | Recommend curated peak list over spectrum for ranking |

## Test Coverage

- **27 tests** covering:
  - ShiftAssignment model (matched and unmatched)
  - RankedSolution with MAE scoring
  - RankingResult sorting and statistics
  - SolutionRanker matching algorithm
  - N:1 matching for molecular symmetry
  - Edge cases (no SMILES, prediction failures)
  - CLI command options

## Algorithm Details

### Shift Matching (N:1)

Unlike typical 1:1 bipartite matching, the ranker allows multiple predicted shifts to match the same experimental peak. This handles molecular symmetry correctly:

```
Para-disubstituted benzene:
  Predicted: C1=129.2, C5=129.4 (equivalent ortho carbons)
  Experimental: 129.3 ppm (single peak)
  → Both C1 and C5 match to 129.3 (correct behavior)
```

### MAE Calculation

```
MAE = (sum of |predicted - experimental| for matched) / matched_count
    + (unmatched_count × tolerance × 0.5) / total_predicted
```

## Usage Example

```python
from lucy_ng import C13Predictor, SolutionRanker
from lucy_ng.lsd import LSDRunner

# Run LSD
result = LSDRunner.run("input.lsd")

# Rank solutions
predictor = C13Predictor.from_table_file("hose_lookup.json.gz")
ranker = SolutionRanker(predictor, tolerance=3.0)

experimental = [180.5, 140.8, 129.4, 127.8, 45.2, 30.1]
ranking = ranker.rank(result.solutions, experimental, top_n=10)

print(f"Best solution: {ranking.solutions[0].smiles}")
print(f"MAE: {ranking.solutions[0].mae:.2f} ppm")
```

## Next Steps

Phase 10: NMRXiv Dataset Fetching - Download NMR datasets from nmrxiv.org

---
*Completed: 2026-01-12*
