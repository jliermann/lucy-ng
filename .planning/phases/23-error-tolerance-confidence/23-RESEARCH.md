# Phase 23: Error Tolerance and Confidence - Research

**Researched:** 2026-02-07
**Domain:** NMR spectroscopy error tolerance, ambiguity detection, and confidence assessment for CASE
**Confidence:** MEDIUM-HIGH

## Summary

Phase 23 encodes error detection patterns and confidence-annotated output into SKILL.md to enable AI agents to proactively identify and document ambiguity instead of guessing. The research reveals four distinct ambiguity scenarios requiring different handling strategies: (1) close carbons unresolvable by digital resolution, (2) multiplicity conflicts between DEPT and HSQC, (3) sparse HMBC correlations to quaternary carbons, and (4) confidence scoring at both per-atom and per-structure levels.

The critical insight is that **ambiguity detection is resolution-aware**: whether two peaks are distinguishable depends on the digital resolution (points per ppm) of each spectrum dimension independently. 13C dimension in 2D spectra typically has 2-10 points/ppm, making peaks closer than 0.1-0.5 ppm physically indistinguishable. This is fundamentally different from using arbitrary ppm thresholds—it's a physical limitation of the acquired data.

For multiplicity conflicts, the research shows **context trumps dogma**: DEPT-90 provides near-definitive CH identification when available, but when only DEPT-135 and HSQC exist, the agent must weigh S/N, consistency, and chemical shift expectations rather than blindly trusting one source. Recent literature (2021-2023) shows multiplicity-edited HSQC methods that reduce but don't eliminate conflicts.

Quaternary carbons present a connectivity challenge: they appear in 13C but not HSQC/DEPT, making HMBC their only structural link. When HMBC correlations are sparse (0-1 visible), shift-based constraints (170 ppm → carbonyl, 130 ppm → aromatic) provide fallback guidance, with targeted threshold reduction (20% increments) to search for weak correlations.

Confidence assessment follows a **qualitative multi-factor model**: per-atom confidence combines digital resolution (can peaks be distinguished?), HOSE prediction quality (MAE for that atom), and correlation count. Overall structure confidence is derived from atom-level scores. The DP4 parameter (from computational chemistry) provides a precedent for confidence scoring in NMR assignment, though lucy-ng uses HOSE-based MAE rather than DFT.

**Primary recommendation:** Encode resolution-based ambiguity detection, context-dependent conflict resolution, shift-guided quaternary carbon constraints, and qualitative confidence scoring into SKILL.md. No new Python code—this is pure knowledge authoring building on Phase 22's quality assessment foundation.

---

## Standard Stack

### Core (Existing Infrastructure)

| Component | Current State | Purpose | Why Standard |
|-----------|---------------|---------|--------------|
| SKILL.md | 610 lines, 10 sections | CASE domain knowledge | Extended in Phase 22 with quality assessment |
| Spectrum1D/2D models | Pydantic v2 with ppm_scale | Digital resolution calculation | `len(ppm_scale) / (max - min)` = pts/ppm |
| LSD LIST/PROP/ELEM | v3.5.3 constraint types | Ambiguity encoding | Existing mechanism for flexible constraints |
| HOSE prediction | C13Predictor with MAE | Per-atom confidence input | Already returns prediction quality metrics |

### Supporting (No New Libraries Required)

This phase is **pure skill authoring**—no new Python packages, no new MCP tools, no code changes. All ambiguity detection and confidence scoring can be described conceptually using existing spectrum metadata and tool outputs.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Resolution-based detection | Fixed 0.3-0.5 ppm threshold | User explicitly rejected; resolution varies across instruments |
| LIST/PROP for ambiguity | Separate LSD variant files | User rejected; single file with flexible constraints preferred |
| Context-dependent DEPT/HSQC | "DEPT always wins" rule | Rejected as too rigid; S/N and DEPT-90 availability matter |
| Qualitative confidence | Computed percentage formula | User specified qualitative assessment with judgment |
| 20% threshold reduction | Aggressive 50% halving | User rejected aggressive approach as too risky |

---

## Architecture Patterns

### Recommended SKILL.md Structure Additions

Current structure (610 lines, 10 sections from Phase 22):

```
1. NMR Background
2. Spectral Quality Assessment ← Phase 22
3. Peak Picking Strategy
4. Symmetry Detection
5. Dereplication
6. LSD Reference
7. Incremental HMBC Constraint Strategy ← Phase 22
8. Ranking and Prediction
9. CASE Workflow
10. Quick Reference
```

**Add new content within existing sections:**

- **Section 2 (Spectral Quality Assessment)**: Add resolution calculation formulas (3-4 paragraphs)
- **Section 3 (Peak Picking Strategy)**: Add close carbon detection guidance (10-15 lines)
- **Section 6 (LSD Reference)**: Add LIST/PROP ambiguity encoding examples (20-30 lines)
- **NEW Section 11 (Error Tolerance and Ambiguity Detection)**: ~150 lines
  - Close Carbon Detection (resolution-based)
  - DEPT/HSQC Multiplicity Conflicts
  - Quaternary Carbon HMBC Sparsity
  - Ambiguities Detected Output Section
- **NEW Section 12 (Confidence Scoring)**: ~80 lines
  - Per-Atom Confidence Factors
  - Per-Structure Confidence Derivation
  - Confidence-Annotated Output Format
  - Suggesting Additional Experiments

**Estimated addition:** ~250 lines total to SKILL.md (from 610 → ~860 lines)

---

### Pattern 1: Resolution-Based Close Carbon Detection

**What:** Calculate digital resolution independently for 1D 13C, HSQC F1, and HMBC F1 dimensions. If two carbons are closer than the resolution allows to distinguish, they are ambiguous by definition.

**When to use:** After peak picking 13C, before building LSD constraints. Check all carbon pairs.

**Calculation:**
```
# For 1D 13C spectrum
resolution_13C = len(ppm_scale) / (ppm_max - ppm_min)  # points per ppm
peak_spacing_limit = 1.5 / resolution_13C  # ppm (1.5 points minimum separation)

# For 2D HSQC/HMBC F1 dimension (carbon axis)
resolution_F1 = len(f1_ppm_scale) / (f1_ppm_max - f1_ppm_min)
peak_spacing_limit_2D = 1.5 / resolution_F1

# Two carbons are unresolvable if:
abs(carbon_A_shift - carbon_B_shift) < peak_spacing_limit
```

**Quality tiers from Phase 22 Research:**
- > 10 pts/ppm: Excellent → 0.15 ppm minimum spacing
- 5-10 pts/ppm: Good → 0.3 ppm minimum spacing
- 2-5 pts/ppm: Moderate → 0.75 ppm minimum spacing
- < 2 pts/ppm: Poor → 1.5+ ppm minimum spacing

**When carbons are unresolvable:**
1. **Document in "Ambiguities Detected" section**: "Carbons at 155.08 and 155.32 ppm are within 0.24 ppm. Digital resolution of HMBC F1 dimension is 4.2 pts/ppm (0.36 ppm minimum spacing). These positions cannot be distinguished."
2. **Use LSD LIST/PROP mechanism** (not separate variant files):
   ```
   MULT 5 C 2 0   ; could be 155.08 or 155.32
   MULT 6 C 2 0   ; could be 155.08 or 155.32
   LIST L1 5 6    ; these two carbons
   ; HMBC shows correlation to one of them - encode as property constraint
   ; Use PROP to express "one of these carbons must connect to proton X"
   ```

**Source:** [Digital resolution fundamentals](https://cores.research.asu.edu/sites/default/files/2018-07/NMR%20Digital%20Resolution.pdf) and Phase 22 research on 13C HSQC/HMBC limitations showing typical resolution 2-10 pts/ppm.

---

### Pattern 2: Context-Dependent DEPT/HSQC Multiplicity Resolution

**What:** When DEPT and HSQC disagree on multiplicity (e.g., DEPT-135 says CH2, HSQC pattern suggests CH), examine context to choose ground truth.

**When to use:** During HSQC guided picking when multiplicities conflict.

**Decision factors:**

1. **DEPT-90 availability** (highest priority):
   - DEPT-90 shows only CH → near-definitive CH identification
   - DEPT-90 absence + DEPT-135 positive → could be CH or CH3
   - **If DEPT-90 available**: Trust it over HSQC pattern-based inference

2. **S/N ratio comparison**:
   - DEPT-135 SNR > 50, HSQC SNR < 20 → trust DEPT
   - HSQC SNR > 50, DEPT-135 SNR < 20 → trust HSQC
   - Both low SNR → mark as ambiguous, prefer CH/CH3 ambiguous label

3. **Chemical shift expectations**:
   - Shift < 30 ppm → likely CH3 (aliphatic methyl)
   - Shift 100-160 ppm → likely aromatic CH
   - Shift 50-90 ppm with negative DEPT-135 → likely O-CH2

4. **Consistency with other data**:
   - HMBC correlation count: CH typically shows 2-4 HMBC, CH2 shows 2-3, CH3 shows 1-2
   - Molecular formula hydrogen budget: does total H count support assignment?

**Resolution strategy:**
- **Resolve to ONE multiplicity** based on weight of evidence
- **Document the conflict** in "Ambiguities Detected" section:
  ```
  Carbon at 28.5 ppm: DEPT-135 positive (CH or CH3), HSQC intensity
  suggests CH3, but no DEPT-90 available. Assigned as CH3 based on
  chemical shift (< 30 ppm aliphatic region) and HSQC intensity.
  Alternative: could be CH. DEPT-90 acquisition would resolve.
  ```
- Do NOT create separate LSD runs for both possibilities (user rejected branching)

**Source:** [Multiplicity-edited HSQC](https://magritek.com/2015/09/10/two-experiments-for-the-price-of-one-the-multiplicity-edited-hsqc-experiment/) showing edited HSQC provides DEPT-135-equivalent info but with phase anomalies for certain functional groups. [DEPT/HSQC correlation guide](https://nmr.sdsu.edu/index.php/nmr-seminar/7-common-2d-cosy-hsqc-hmbc/) shows DEPT-90 as definitive for CH.

---

### Pattern 3: Quaternary Carbon HMBC Sparsity Handling

**What:** When a quaternary carbon has 0-1 HMBC correlations, use shift-based constraints and targeted threshold reduction.

**When to use:** After initial HMBC guided picking, during LSD constraint building.

**Shift-based constraint mapping** (replaceability design for future atom environment database):

| Shift Range (ppm) | Likely Environment | LSD Constraint |
|-------------------|-------------------|----------------|
| 160-180 | Carboxylic acid/ester/amide C=O | BOND to oxygen: `BOND Quat_idx O_idx` |
| 180-220 | Ketone/aldehyde C=O | BOND to oxygen: `BOND Quat_idx O_idx` |
| 120-160 (aromatic) | Aromatic quaternary | Likely ring junction, use LIST/PROP to constrain to aromatic carbons |
| < 50 | Quaternary aliphatic | Rare, likely tert-butyl or similar |

**Targeted HMBC threshold reduction:**

```
IF quaternary_carbon HMBC_count <= 1:
    original_threshold = 0.05  # from guided picking
    current_threshold = original_threshold

    WHILE HMBC_count <= 1 AND current_threshold > reasonable_floor:
        current_threshold = current_threshold * 0.8  # 20% reduction

        # Re-examine HMBC in ±5 ppm window around quaternary carbon shift
        new_peaks = pick_hmbc_in_region(
            carbon_range=(quat_shift - 2.5, quat_shift + 2.5),
            threshold=current_threshold
        )

        HMBC_count = validate_new_peaks_against_13C_and_HSQC(new_peaks)

        IF HMBC_count > 1:
            STOP → correlations found

    reasonable_floor = noise_floor * 2  # Claude determines based on spectrum
```

**Incremental 20% reduction rationale:** User rejected aggressive 50% halving as "too aggressive." 20% allows finer control with 5-7 steps before reaching 1/3 original threshold.

**Single correlation confidence:** When quaternary carbon has exactly 1 HMBC correlation, treat with **higher confidence** (it's the only connectivity info—precious). Do NOT treat as suspicious.

**Source:** [HMBC challenges with quaternary carbons](https://www.nature.com/articles/s41467-023-37289-z) showing proton-deficient compounds require advanced methods. Incremental threshold approach based on Phase 22 adaptive quality strategy.

---

### Pattern 4: Qualitative Confidence Scoring Model

**What:** Assign High/Medium/Low confidence to each carbon atom, derive overall structure confidence from atom-level scores.

**When to use:** After ranking LSD solutions, before presenting results to user.

**Per-atom confidence factors:**

1. **Digital resolution** (can peak be distinguished?):
   - High: No other carbon within 2× resolution limit
   - Medium: Another carbon within 2-3× resolution limit
   - Low: Peaks overlapping or within 1× resolution limit

2. **HOSE prediction quality** (MAE for that atom):
   - High: MAE < 2.0 ppm (excellent match)
   - Medium: MAE 2.0-3.5 ppm (good match)
   - Low: MAE > 3.5 ppm (poor match or unusual environment)

3. **Number of supporting correlations**:
   - High: 3+ HMBC correlations + HSQC
   - Medium: 1-2 HMBC correlations + HSQC
   - Low: 0 HMBC correlations (quaternary with shift-only constraint) OR HSQC ambiguous

**Qualitative assessment (not formula):** Agent evaluates factors and assigns High/Medium/Low using judgment. The >90% / 60-90% / <60% thresholds from requirements are **guidelines for interpretation**, not computed percentages.

**Example reasoning:**
```
Carbon 5 (155.08 ppm): MEDIUM confidence
- Resolution: GOOD (nearest carbon 4.3 ppm away, well-resolved)
- HOSE MAE: 2.8 ppm (GOOD, within normal aromatic range)
- Correlations: 1 HMBC (MEDIUM, single quaternary correlation)
→ Overall MEDIUM due to sparse correlations despite good resolution/prediction
```

**Per-structure confidence derivation (Claude's discretion):** Options include:
- Weighted average: `(high_count * 1.0 + medium_count * 0.5 + low_count * 0.0) / total_carbons`
- Worst-case: If any carbon is Low, structure is at most Medium
- Threshold-based: Structure is High if ≥80% carbons are High/Medium

**Ambiguity documentation format** (table recommended but Claude's discretion):

```markdown
## Ambiguities Detected

| Carbon Pair/Issue | Type | Resolution | Impact on Constraints |
|-------------------|------|------------|----------------------|
| 155.08 / 155.32 ppm | Close carbons | HMBC F1: 4.2 pts/ppm, 0.36 ppm spacing limit. Peaks 0.24 ppm apart. | Cannot distinguish in HMBC. Used LIST/PROP to encode "one of these two carbons" in constraint C7-H12 |
| 28.5 ppm | DEPT/HSQC conflict | DEPT-135: positive (CH/CH3), HSQC: CH3 pattern, no DEPT-90 | Assigned CH3, but CH possible. DEPT-90 would resolve. |
| 172.4 ppm (C=O) | Sparse HMBC | 0 correlations after threshold reduction to 0.025 | Used shift constraint: BOND to oxygen based on 172 ppm carbonyl region |
```

**Suggesting additional NMR experiments** (actionable for spectroscopist):

```markdown
## Recommended Additional Experiments

1. **DEPT-90**: Would resolve CH/CH3 ambiguity at 28.5 ppm (currently assigned as
   CH3 based on shift, but pattern-based inference uncertain)

2. **HMBC with optimized nJCH delay**: Current HMBC optimized for 8 Hz (3-bond).
   Re-acquire with 5 Hz delay to enhance quaternary carbon correlations,
   specifically targeting C=O at 172.4 ppm which shows no correlations.

3. **Higher-resolution HSQC (F1 dimension)**: Current resolution 4.2 pts/ppm in
   13C dimension. Acquire with 2× F1 points to distinguish 155.08/155.32 ppm pair.
```

**Source:** [DP4 confidence parameter for NMR assignment](https://pubs.acs.org/doi/10.1021/acs.jnatprod.6b00799) shows precedent for confidence scoring. [HOSE code prediction confidence](https://sciencesolutions.wiley.com/wp-content/uploads/2025/09/15_Training-NMR_Predictor.pdf) shows coefficients 1-4 representing shell match depth.

---

### Anti-Patterns to Avoid

- **Hard-coded ppm thresholds**: "Carbons within 0.5 ppm are close" fails—0.5 ppm may be 5× resolution or 0.5× resolution depending on spectrum.
- **Separate LSD variant files for ambiguity**: User explicitly rejected. Use LIST/PROP in single file.
- **DEPT always wins / HSQC always wins**: Context matters—S/N, DEPT-90 availability, chemical shift expectations.
- **Aggressive threshold halving**: User rejected 50% reduction as too risky. Use 20% increments.
- **Confidence formula worship**: User specified qualitative judgment, not rigid weighted scoring.
- **Ignoring atom environment database future**: Shift→constraint mapping should be modular and explicit for future replacement.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Digital resolution calculation | Complex Nyquist limit estimator | Simple `len(ppm_scale) / (max - min)` | One-line calculation sufficient for ambiguity detection |
| LIST/PROP constraint generation | Custom Python generator | Conceptual guidance in SKILL.md | Constraints are problem-specific, AI agent composes them |
| Confidence scoring | Weighted ML classifier | Qualitative tier-based assessment | User explicitly chose qualitative over computed percentages |
| Ambiguity documentation | Structured JSON schema | Markdown table in analysis output | Human-readable audit trail more valuable than machine format |

**Key insight:** This phase teaches the AI agent *how to think about* ambiguity and confidence, not *how to compute* them algorithmically. The agent observes spectral characteristics, applies decision criteria, and documents reasoning—expert spectroscopist workflow, not automated pipeline.

---

## Common Pitfalls

### Pitfall 1: Treating Resolution as Fixed Threshold

**What goes wrong:** Agent uses "carbons within 0.5 ppm are ambiguous" rule uniformly, flagging false ambiguities in high-resolution spectra or missing real ambiguities in low-resolution spectra.

**Why it happens:** Confusing chemical shift tolerance (±1.5 ppm for matching known peaks) with resolution limit (physical distinguishability in acquired data).

**How to avoid:**
- **Calculate resolution for each spectrum independently**: 1D 13C, HSQC F1, HMBC F1
- **Use resolution-relative threshold**: `1.5 / (pts_per_ppm)` for minimum spacing
- **Document the math**: "HMBC F1 has 256 points across 60 ppm = 4.27 pts/ppm = 0.35 ppm minimum spacing"

**Warning signs:**
- Agent claims "all carbons in aromatic region are ambiguous" (likely using fixed threshold on low-res spectrum)
- Agent never detects ambiguity even with 2 pts/ppm resolution (not calculating resolution at all)

---

### Pitfall 2: DEPT/HSQC Conflict Loops

**What goes wrong:** Agent oscillates between DEPT and HSQC assignments, changing multiplicity of same carbon across iterations without convergence.

**Why it happens:** No decision criteria—agent "guesses" based on whichever tool output it reads most recently.

**How to avoid:**
- **Decision tree with priority order**: DEPT-90 (if available) → S/N comparison → chemical shift → consistency check
- **Resolve ONCE and document**: Make one assignment, note the alternative in Ambiguities section, do NOT revisit unless new data acquired
- **Confidence downgrade, not flip-flop**: If conflict is irresolvable, assign Medium/Low confidence, keep one multiplicity

**Warning signs:**
- LSD iterations show changing MULT hydrogen counts for same carbon (3 → 2 → 3)
- Agent says "HSQC suggests CH3, so I'll change it" followed by "but DEPT says CH2, so I'll change back"

---

### Pitfall 3: Threshold Reduction Runaway

**What goes wrong:** Agent reduces HMBC threshold to 0.001 (near noise floor), finds 200+ "correlations," most of which are noise.

**Why it happens:** No reasonable floor defined, agent pursues "find correlations" goal blindly.

**How to avoid:**
- **Establish floor before starting**: `reasonable_floor = noise_floor * 2` (or *3 for very noisy spectra)
- **Validate new peaks**: Each threshold reduction MUST validate new peaks against 13C and HSQC (guided picking logic)
- **Stop at diminishing returns**: If 3 consecutive reductions yield 0 new validated peaks, stop

**Warning signs:**
- Threshold reaches 0.01 or lower (10× lower than starting 0.05-0.10)
- Validated HMBC count jumps from 15 to 80 after one threshold reduction (likely noise leakage)
- Agent reports "lowered threshold to find correlations" without mentioning validation

---

### Pitfall 4: Confidence Inflation

**What goes wrong:** Agent assigns High confidence to all atoms despite ambiguities, poor HOSE predictions, or sparse correlations.

**Why it happens:** Optimism bias—agent wants to present confident results, downplays uncertainty.

**How to avoid:**
- **Explicit confidence downgrade rules**:
  - Any ambiguity → at most Medium confidence
  - MAE > 3.5 ppm → Low confidence
  - 0 HMBC correlations on quaternary → Low confidence
- **Audit question**: "Would an expert spectroscopist agree this assignment is >90% certain?"
- **Err on side of honesty**: Better to under-promise and deliver certainty than over-promise and be wrong

**Warning signs:**
- All carbons rated High despite multiple ambiguities in detection report
- Structure confidence is High despite MAE > 3.0 ppm overall
- Agent says "confident" but also lists 5 ambiguities in same breath

---

## Code Examples

**No code examples this phase.** All patterns are conceptual guidance for SKILL.md authoring. The AI agent will apply these patterns during CASE workflow using existing tools.

For reference, how the agent would use existing data:

**Digital resolution calculation (conceptual, not code):**
```python
# Agent reads spectrum metadata via read_spectrum_2d tool
# Tool returns: f1_points, f1_ppm_min, f1_ppm_max
# Agent computes: pts_per_ppm = f1_points / (f1_ppm_max - f1_ppm_min)
# Agent computes: min_spacing = 1.5 / pts_per_ppm
# Agent documents: "HSQC F1 dimension has 5.2 pts/ppm, minimum spacing 0.29 ppm"
```

**HOSE prediction confidence (conceptual):**
```python
# Agent runs rank_lsd_solutions tool
# Tool returns per-solution MAE and per-atom deviations
# Agent extracts per-atom MAE from deviations list
# Agent assigns High (< 2.0), Medium (2-3.5), Low (> 3.5) per atom
# Agent summarizes: "8/10 carbons High confidence, 2/10 Medium"
```

---

## State of the Art

| Old Approach | Current Approach (Phase 23) | When Changed | Impact |
|--------------|----------------------------|--------------|--------|
| Fixed 0.5 ppm "close carbon" threshold | Resolution-dependent spacing limit | User insight 2026-02-06 | Physically grounded ambiguity detection, no false flags |
| DEPT always trusted over HSQC | Context-dependent resolution (DEPT-90, S/N, shift) | User decision 2026-02-06 | More robust multiplicity assignment, handles edge cases |
| Separate LSD files for ambiguous cases | LIST/PROP in single file | User decision 2026-02-06 | Simpler workflow, LSD built-in ambiguity support |
| Manual correlation hunting at fixed threshold | Incremental 20% threshold reduction | User preference 2026-02-06 | Controlled risk, finer granularity than 50% halving |
| No confidence scoring | Per-atom qualitative + per-structure derived | Phase 23 requirements | Transparent uncertainty, actionable experiment suggestions |

**Recent NMR developments (2021-2025):**
- [i-HMBC methodology (2023)](https://www.nature.com/articles/s41467-023-37289-z): Isotope shift detection to distinguish 2-bond from 3-bond HMBC correlations—addresses quaternary carbon challenge at sub-mg scale
- [Multiplicity-edited HSQC improvements](https://www.nature.com/articles/s41598-021-01041-8): Complete removal of proton multiplet structure in HSQC cross-peaks (2021)
- [DP4/mix-J-DP4 confidence scoring](https://pubs.acs.org/doi/abs/10.1021/acs.jnatprod.6b00799): 100% confidence in stereochemical assignments for complex molecules

**Future-aware design:**
- Shift→constraint mapping explicitly documented for replacement by atom environment database (user noted)
- Resolution-based detection compatible with future learned models of peak distinguishability
- Qualitative confidence framework can incorporate DFT predictions, RDC/RCSA data when available

---

## Open Questions

### 1. Overall Structure Confidence Derivation

**What we know:** Per-atom confidence uses three factors (resolution, HOSE MAE, correlations). Multiple carbons with varying confidence levels.

**What's unclear:** How to combine atom-level scores into single structure-level confidence (High/Medium/Low).

**Recommendation:** Claude's discretion in SKILL.md. Suggest three options:
- **Weighted average**: `sum(atom_confidence_score) / n_carbons` with High=1, Medium=0.5, Low=0
- **Worst-case**: Structure confidence = lowest atom confidence (conservative)
- **Threshold-based**: Structure is High if ≥80% atoms are High/Medium, else Medium if ≥50%, else Low

User approved "Claude's discretion" for this decision (CONTEXT.md).

---

### 2. Threshold Reduction Floor for Quaternary Carbon Search

**What we know:** Start at 0.05, reduce by 20% per step. User rejected aggressive 50% halving.

**What's unclear:** When to stop? What is "reasonable_floor"?

**Recommendation:** Claude determines floor based on noise characteristics. Suggest:
- **Conservative**: `noise_floor × 3` (ensure 3× signal over noise)
- **Moderate**: `noise_floor × 2` (standard 2:1 S/N)
- **Aggressive** (only if spectral quality is excellent): `noise_floor × 1.5`

Additionally stop if:
- 3 consecutive reductions yield 0 new validated peaks (diminishing returns)
- Threshold reaches 0.01 absolute (10× below starting point, likely futile)

User approved "Claude determines the floor based on noise characteristics" (CONTEXT.md).

---

### 3. Edge Case: DEPT and HSQC Both Poor S/N

**What we know:** Decision tree prioritizes DEPT-90 → S/N comparison → shift expectations.

**What's unclear:** When both DEPT-135 and HSQC have S/N < 20, which is ground truth?

**Recommendation:** Mark as **explicitly ambiguous**:
- Document: "Both DEPT-135 and HSQC show S/N < 20 for peak at X ppm. Cannot confidently assign multiplicity."
- Assign **Low confidence** to this carbon
- Suggest additional experiment: "Re-acquire DEPT-135 or HSQC with longer acquisition time to improve S/N"
- Use shift-based heuristic as last resort (< 30 ppm → likely CH3, 100-160 → likely CH, etc.)

User approved "how to handle edge cases where DEPT and HSQC both have poor S/N" as Claude's discretion (CONTEXT.md).

---

### 4. Ambiguities Detected Section Format

**What we know:** Dedicated section in analysis output listing unresolvable pairs with resolution details and impact.

**What's unclear:** Table vs prose vs hybrid format?

**Recommendation:** **Table format preferred** for structured audit trail:

| Element | Content |
|---------|---------|
| Carbon Pair/Issue | "155.08 / 155.32 ppm" or "28.5 ppm" |
| Type | "Close carbons" / "DEPT/HSQC conflict" / "Sparse HMBC" |
| Resolution | Quantitative detail: "HMBC F1: 4.2 pts/ppm, 0.36 ppm limit, 0.24 ppm apart" |
| Impact on Constraints | "Used LIST/PROP to encode..." or "Assigned CH3 with Medium confidence..." |

Prose alternative acceptable if user prefers narrative style. Hybrid (table for close carbons, prose for conflicts) also valid.

User approved format as Claude's discretion (CONTEXT.md).

---

### 5. Shift-to-Constraint Mapping Completeness

**What we know:** 160-180 ppm → carboxylic, 180-220 ppm → ketone/aldehyde, 120-160 aromatic → ring junction, < 50 → quaternary aliphatic.

**What's unclear:** Are these ranges sufficient? What about edge cases (nitrile 115-120 ppm, conjugated carbonyls 170-180 ppm overlap)?

**Recommendation:** Start with broad categories in SKILL.md (as listed above). Document as **heuristic guidelines, not rigid rules**. Agent should:
- Apply shift constraint when 0 HMBC correlations AND shift clearly in one region
- **Flag ambiguous shift ranges** in Ambiguities section: "Quaternary at 175 ppm could be carboxylic acid or conjugated ketone. Used BOND to oxygen but structure may require refinement."
- Note this mapping is **designed for future replacement** by atom environment database (user noted in CONTEXT.md)

User approved specific shift→constraint mapping as Claude's discretion (CONTEXT.md).

---

## Sources

### Primary (HIGH confidence)

- [Digital Resolution in NMR](https://cores.research.asu.edu/sites/default/files/2018-07/NMR%20Digital%20Resolution.pdf) - Calculation methods and impact on peak distinguishability
- [LSD Software Documentation](https://nuzillard.github.io/LSD/index_ENG.html) - LIST, PROP, ELEM constraint types and usage
- [Phase 22 HMBC Strategy Research](../../22-hmbc-strategy-quality/22-RESEARCH.md) - Quality tiers, S/N calculation, digital resolution impact
- [lucy-ng Spectrum Models](../../../../src/lucy_ng/models/spectrum.py) - Pydantic models with ppm_scale for resolution calculation

### Secondary (MEDIUM confidence)

- [Multiplicity-Edited HSQC Methods](https://magritek.com/2015/09/10/two-experiments-for-the-price-of-one-the-multiplicity-edited-hsqc-experiment/) - HSQC provides DEPT-135-equivalent info with phase anomalies
- [HMBC and HSQC Guide](https://nmr.chem.columbia.edu/content/hsqc-and-hmbc) - Practical NMR correlation experiments
- [i-HMBC for Quaternary Carbons (2023)](https://www.nature.com/articles/s41467-023-37289-z) - Recent advance for proton-deficient compounds
- [DP4 Confidence Parameter](https://pubs.acs.org/doi/abs/10.1021/acs.jnatprod.6b00799) - NMR assignment confidence scoring precedent
- [HOSE Code Prediction Confidence](https://sciencesolutions.wiley.com/wp-content/uploads/2025/09/15_Training-NMR_Predictor.pdf) - Shell match depth coefficients 1-4
- [Computer-Assisted Structure Elucidation Review (2021)](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/mrc.5115) - Current and future CASE perspectives

### Tertiary (LOW confidence - general background)

- [Chemistry LibreTexts: C-13 NMR](https://chem.libretexts.org/Bookshelves/Organic_Chemistry/Introduction_to_Organic_Spectroscopy/06:_Carbon-13_NMR_Spectroscopy/6.05:_Interpreting_C-13_NMR_Spectra) - Wide chemical shift range aids peak separation
- [NMR Resolution Enhancement (2021)](https://www.nature.com/articles/s41598-021-01041-8) - Complete removal of proton multiplet structure in HSQC
- [DEPT/HSQC/HMBC Overview](https://nmr.sdsu.edu/index.php/nmr-seminar/7-common-2d-cosy-hsqc-hmbc/) - Standard 2D NMR experiments

---

## Metadata

**Confidence breakdown:**
- Digital resolution detection: **HIGH** - well-established physics, simple calculation
- DEPT/HSQC conflict resolution: **MEDIUM** - context-dependent, requires judgment, literature shows ongoing challenges
- Quaternary carbon constraints: **MEDIUM** - shift heuristics are approximate, i-HMBC shows advanced solutions exist but not in lucy-ng scope
- Confidence scoring model: **MEDIUM** - qualitative framework well-justified, but no quantitative validation for this specific approach
- Overall: **MEDIUM-HIGH** - core patterns are sound, open questions noted for Claude's discretion

**Research date:** 2026-02-07
**Valid until:** 60 days (stable domain knowledge, but NMR methodology evolves slowly)

**Phase 22 dependencies:** This research builds directly on Phase 22's spectral quality assessment (S/N tiers, digital resolution concept, artifact recognition). The quality→strategy adjustments from Phase 22 become inputs to ambiguity detection and confidence scoring in Phase 23.

**Future phases:** Phase 24+ may build Python tools for automated ambiguity detection or confidence calculation if patterns prove consistent, but Phase 23 focuses on teaching the AI agent to perform these assessments conceptually.
