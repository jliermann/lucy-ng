# Phase 23: Error Tolerance and Confidence - Context

**Gathered:** 2026-02-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Encode error detection patterns and confidence-annotated output into SKILL.md so the AI agent proactively identifies and documents ambiguity (close carbons, multiplicity conflicts, sparse quaternary carbons) instead of guessing through it. Confidence levels are assigned per-atom and per-structure.

No new Python code or tools -- this phase is pure skill/knowledge authoring into existing SKILL.md.

</domain>

<decisions>
## Implementation Decisions

### Close carbon detection (ETOL-01, ETOL-03)
- Use **digital resolution** of each spectrum to determine whether two peaks are physically distinguishable -- NOT a hard-coded ppm threshold
- Check resolution in **all dimensions independently**: 1D 13C, HSQC F1 (carbon axis), HMBC F1 (carbon axis) -- each may have different digital resolution
- The criterion: if two peaks are closer than the spectral resolution allows to distinguish, they are **ambiguous by definition**
- When carbons are unresolvable: use LSD's **LIST/PROP mechanism** to encode ambiguity in a single LSD file (NOT separate LSD variant files)
- All detected ambiguities go in a **dedicated "Ambiguities Detected" section** in the analysis output, listing each unresolvable pair with resolution details and impact on constraints
- **Future-aware**: Design the resolution-based detection so that a future atom environment database can augment or replace hardcoded shift-region heuristics

### DEPT vs HSQC multiplicity conflicts (ETOL-02)
- Resolution is **context-dependent**: agent examines S/N of both experiments, consistency with other data, and chemical shift expectations to choose ground truth
- No blanket "DEPT always wins" or "HSQC always wins" rule
- **DEPT-90 upgrades confidence**: When DEPT-90 is available, its CH identification is near-definitive and should override HSQC pattern-based guesses
- **Document ALL disagreements**, even minor ones -- builds a complete audit trail
- When a conflict is found: **resolve to one multiplicity** based on context, note the alternative in ambiguity documentation (do NOT branch into separate LSD runs)

### Quaternary carbon HMBC sparsity (ETOL-04)
- When a quaternary carbon has 0 HMBC correlations: use **shift-based constraints** to add LSD constraints (e.g., 170 ppm -> BOND to oxygen, 130 ppm -> must be aromatic)
- Design shift-region constraints so a **future atom environment database** can replace them -- keep the mapping explicit and modular
- Single HMBC correlation to a quaternary carbon: treat with **higher confidence** (it's the only connectivity info -- precious, not suspicious)
- **Targeted search** for missing quaternary HMBC correlations: if 0-1 correlations found, re-examine HMBC at lower threshold around that carbon's shift
- Threshold lowering is **incremental**: reduce by 20% per step, check for new peaks, repeat -- NOT aggressive halving
- Continue lowering until correlations appear or a reasonable lower limit is reached (Claude determines the floor based on noise characteristics)

### Confidence scoring model (CONF-01, CONF-02, CONF-03)
- Confidence levels at **both granularities**: per-atom (each carbon gets High/Medium/Low) AND per-structure (overall confidence derived from atom-level scores)
- Per-atom confidence factors: **digital resolution** (can peaks be distinguished?) + **HOSE prediction quality** (MAE for that atom) + **number of supporting correlations**
- Confidence assessment is **qualitative**: agent evaluates factors and assigns High/Medium/Low based on judgment -- no rigid formula or weighted scoring function
- The >90% / 60-90% / <60% thresholds from requirements are **qualitative guidelines**, not computed percentages
- Ambiguous assignments **explicitly documented with reasoning** in a dedicated section
- When additional NMR experiments might help: suggest **specific experiments** with explanation of what they would resolve (e.g., "acquire DEPT-90 to resolve CH/CH3 ambiguity at 28.5 ppm") -- actionable for the spectroscopist

### Claude's Discretion
- Exact format of the "Ambiguities Detected" section (table vs prose vs hybrid)
- How to derive overall structure confidence from per-atom scores (weighted average, worst-case, or other)
- The lower limit for incremental threshold reduction on quaternary carbon targeted search
- Which chemical shift regions map to which functional group constraints (the specific shift->constraint mapping table)
- How to handle edge cases where DEPT and HSQC both have poor S/N (both unreliable)

</decisions>

<specifics>
## Specific Ideas

- The resolution-based close-carbon detection emerged from the user's insight: "There must be rigorous scientific ways to decide whether, given the digital resolution of both the 1D carbon and the 2D HSQC and HMBC, a distinction of two peaks is possible in principle. This is better than hard-coding a ppm distance."
- Incremental 20% threshold reduction for quaternary carbon search was explicitly preferred over aggressive halving: "The two suggested options are too aggressive, IMHO."
- A future atom environment database will augment the shift-based constraint heuristics -- design for replaceability
- DEPT-90 as near-definitive for CH identification -- its availability should materially upgrade confidence in multiplicity assignments

</specifics>

<deferred>
## Deferred Ideas

- Atom environment database for quaternary carbon constraint lookup -- future phase/milestone
- Automatic re-acquisition recommendations (requesting the spectroscopist to re-run experiments with better parameters) -- out of scope, but confidence flagging enables this workflow

</deferred>

---

*Phase: 23-error-tolerance-confidence*
*Context gathered: 2026-02-06*
