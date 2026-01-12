# Phase 8: LSD Solution Ranking — Context

## Vision

Rank LSD solutions by how well their predicted 13C spectrum matches the experimental 13C spectrum. When LSD produces multiple candidate structures, this helps identify which solutions are most chemically plausible.

## How It Works

1. Take LSD solution structures (SMILES or MOL)
2. Predict 13C chemical shifts for each candidate using a **local prediction method**
3. Compare predicted shifts against experimental 13C peaks
4. Score each solution by similarity (e.g., MAE, RMSE)
5. Return solutions sorted by score (best match first)

## What's Essential

- **Score and sort** — the core functionality
- **Local prediction** — no external API dependencies
- **13C only** — proton prediction is out of scope

## Research Needed

- Investigate what prediction tools exist
- Check if pyLSD has built-in prediction capability
- Evaluate HOSE code-based approaches (used by nmrshiftdb)
- Consider ML-based alternatives if appropriate

## Out of Scope

- 1H spectrum prediction
- Visual output / spectrum plots
- External prediction services / APIs
- Detailed peak assignment output (just scores for now)
- Filtering solutions (user decides what score threshold matters)

## Integration Points

- Input: LSD solutions from Phase 5 (`LSDSolution` objects with SMILES)
- Input: Experimental 13C peaks from Phase 2.1 (peak list with ppm values)
- Output: Ranked list of solutions with similarity scores

---
*Captured: 2026-01-11*
