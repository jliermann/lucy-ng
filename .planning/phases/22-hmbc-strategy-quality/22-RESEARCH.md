# Phase 22: HMBC Strategy and Spectral Quality - Research

**Researched:** 2026-02-06
**Domain:** NMR spectroscopy knowledge for Computer-Assisted Structure Elucidation (CASE)
**Confidence:** MEDIUM

## Summary

This phase adds two critical knowledge areas to SKILL.md for AI-driven structure elucidation: (1) incremental HMBC constraint strategy and (2) spectral quality assessment. The research reveals that both domains rely on relative assessment rather than fixed thresholds, and both require teaching the AI agent to adapt its strategy based on observations.

The incremental HMBC strategy is an adaptive convergence approach where the AI agent adds small batches of constraints (3-5 correlations) and observes solution count changes, continuing until reaching ≤10 solutions or exhausting correlations. This mirrors the LSD software's constraint satisfaction paradigm and expert spectroscopist practice of building structure proposals iteratively.

Spectral quality assessment focuses on three measurable parameters: S/N ratio (relative to noise floor), digital resolution (points per ppm in 13C dimension), and artifacts (1J leakage, t1 noise, baseline distortions). Quality findings actively modify peak picking thresholds, correlation confidence, and constraint-building caution.

**Primary recommendation:** Encode knowledge as adaptive decision trees and relative metrics, not fixed rules. The AI agent should observe, assess, and adjust—mimicking expert spectroscopist reasoning.

---

## Standard Stack

### Core (Existing Infrastructure)

| Component | Current State | Purpose | Why Standard |
|-----------|---------------|---------|--------------|
| LSD | v3.5.3 | Structure generation via constraint satisfaction | Jean-Marc Nuzillard's validated solver, 20+ years academic use |
| lucy-ng MCP tools | 15 tools | AI agent interface to NMR processing | Already operational in Phase 20 audit |
| SKILL.md | 418 lines, 8 sections | Domain knowledge document | Established in Phase 21 |
| Spectrum1D/2D models | Pydantic v2 | Access to raw spectral data | Contains `data` and `ppm_scale` for quality assessment |

### Supporting (No New Libraries Required)

This phase is **pure knowledge authoring**—no new Python packages, no new MCP tools. All spectral quality metrics can be computed from existing Spectrum1D/2D `.data` arrays using basic NumPy operations the AI agent can describe conceptually.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Iterative 3-5 batch | Fixed 3-phase recipe | User rejected; too rigid, doesn't adapt to solution count trends |
| Relative S/N thresholds | Absolute dB cutoffs | Fixed thresholds fail across different instruments/samples |
| Teaching quality assessment | Building quality checker tool | Phase scope is skill authoring, not code; tools come in Phase 23+ if needed |

---

## Architecture Patterns

### Recommended SKILL.md Structure Additions

Based on existing 8-section structure (418 lines), add:

```
9. Spectral Quality Assessment (NEW)
   ├── S/N Ratio Evaluation
   ├── Digital Resolution Impact
   ├── Common Artifacts (1J, t1 noise, baseline)
   └── Strategy Adjustments Based on Quality

10. Incremental HMBC Constraint Strategy (NEW)
    ├── Adaptive Batch Loop (3-5 correlations)
    ├── High-Confidence Correlation Identification
    ├── Solution Count Convergence
    ├── Stopping Conditions
    └── Failure Decision Tree
```

Alternatively, expand existing sections:
- **Section 2 (Peak Picking Strategy)**: Add quality assessment before picking guidance
- **Section 7 (CASE Workflow)**: Insert incremental HMBC loop into Step 4-5

**Recommendation:** New sections for clarity, as both topics are substantial (estimated 80-120 lines each).

### Pattern 1: Adaptive Iteration Loop

**What:** Continuous refinement cycle where the AI agent adds small constraint batches, observes solution count change, and decides whether to continue or stop.

**When to use:** When LSD produces >10 solutions after first HMBC batch.

**Conceptual flow:**
```
WHILE solution_count > 10 AND hmbc_remaining AND iterations < 10:
    SELECT next 3-5 high-confidence HMBC correlations
    ADD correlations to LSD file
    RUN LSD
    OBSERVE solution_count_new

    IF solution_count_new ≤ 10:
        STOP → proceed to ranking
    IF solution_count_new == solution_count_old (stalled):
        DIAGNOSE → may need different correlations or ELIM consideration
    IF solution_count_new > solution_count_old (increased):
        ERROR → rollback last batch, diagnose conflict

    iterations += 1

IF iterations >= 10 OR hmbc_remaining == 0:
    RANK ANYWAY with caveats
```

**Source:** Conceptual synthesis from LSD constraint satisfaction paradigm ([Nuzillard's LSD tutorial](https://nuzillard.github.io/LSD/index_ENG.html)) and user-specified batch size (CONTEXT.md).

### Pattern 2: High-Confidence Correlation Selection

**What:** Prioritize HMBC correlations where carbon assignment is unambiguous (no close shifts within ±1.5 ppm tolerance).

**When to use:** When selecting which 3-5 correlations to add in next iteration.

**Criteria:**
1. **Unique carbon assignment**: Carbon shift has no neighbors within 2× tolerance (±3.0 ppm)
2. **Unique proton assignment**: Proton shift has no neighbors within 2× tolerance (±0.2 ppm)
3. **Strong peak intensity**: HMBC peak is in top quartile of validated correlations

**Why:** Ambiguous assignments can introduce conflicting constraints, leading to 0 solutions or wrong solutions. Starting with high-confidence correlations builds a solid structural core.

**Source:** Derived from HMBC assignment best practices ([Leveraging the HMBC to Facilitate Metabolite Identification](https://pmc.ncbi.nlm.nih.gov/articles/PMC10948112/)) and chemical shift tolerance research (isotope shift difference ≥0.3 ppb for confident two-bond identification).

### Pattern 3: Relative Spectral Quality Metrics

**What:** Compute quality metrics relative to the spectrum itself, not fixed thresholds.

**When to use:** Before peak picking (Section 2 in SKILL.md workflow).

**Metrics:**

1. **S/N Ratio** (1D spectra):
   ```
   noise_floor = median(abs(data)) in quiet regions (e.g., -5 to -2 ppm)
   tallest_peak = max(abs(data)) in signal region
   SNR = tallest_peak / noise_floor

   Quality tiers:
   - SNR > 100: Excellent (trust threshold 0.05)
   - SNR 30-100: Good (trust threshold 0.05-0.08)
   - SNR 10-30: Moderate (threshold 0.10, wider tolerances)
   - SNR < 10: Poor (increase tolerances, reduce trusted correlations)
   ```

2. **Digital Resolution** (13C dimension in 2D):
   ```
   points_per_ppm = len(f1_ppm_scale) / (max(f1_ppm_scale) - min(f1_ppm_scale))

   Resolution tiers:
   - > 10 pts/ppm: Excellent (standard ±1.5 ppm tolerance)
   - 5-10 pts/ppm: Good (standard tolerance acceptable)
   - 2-5 pts/ppm: Moderate (increase tolerance to ±2.0 ppm)
   - < 2 pts/ppm: Poor (±3.0 ppm, expect aliasing)
   ```

   **Source:** Based on [digital resolution fundamentals](https://cores.research.asu.edu/sites/default/files/2018-07/NMR%20Digital%20Resolution.pdf) and [13C HSQC/HMBC limitations](https://nmr.chem.columbia.edu/content/hsqc-and-hmbc) showing typical resolution is 10.8 Hz/pt (poor) vs optimized 0.09 Hz/pt.

3. **Artifacts** (visual inspection guidance):
   - **1J leakage**: Strong diagonal/near-diagonal HMBC peaks at ±1 ppm offset → exclude from constraints
   - **t1 noise**: Horizontal streaks in 2D spectrum → gradient-selected HMBC preferred, but if present, require higher validation threshold
   - **Baseline roll**: Distortion in 1D 13C causing peaks to shift ±0.5-1 ppm → increase tolerances

   **Source:** [Common NMR artifacts reference](https://onlinelibrary.wiley.com/doi/epdf/10.1002/cmr.a.21387), [t1 noise suppression methods](https://pubmed.ncbi.nlm.nih.gov/37143296/), [baseline correction algorithms](https://pmc.ncbi.nlm.nih.gov/articles/PMC2516527/).

**Strategy adjustments:**
```
IF SNR < 30 AND digital_resolution < 5 pts/ppm:
    - Trust only top 50% of HMBC correlations (by intensity)
    - Increase 13C tolerance to ±2.5 ppm
    - Batch size: 3 correlations (not 5) for finer control
    - Document quality caveats in final report
```

### Anti-Patterns to Avoid

- **Dumping all HMBC at once**: User explicitly prohibited (CONTEXT.md). Leads to over-constraint or under-constraint without diagnostic insight.
- **Fixed SNR thresholds**: "SNR must be > 50" fails—different instruments, concentrations, nuclei have vastly different baselines.
- **Ignoring solution count trends**: If 3 iterations show 500 → 450 → 420 solutions (slow decline), continuing to 10 iterations is futile. Stop and diagnose.
- **Blind ELIM usage**: Never add `ELIM 1 0` without understanding WHY 0 solutions occurred (sp2 parity, hydrogen count, etc.).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Baseline correction | Custom peak shift adjuster | Conceptual guidance only (no code this phase) | [Model-free algorithms exist](https://pubmed.ncbi.nlm.nih.gov/22911463/) but building one is Phase 23+ scope |
| Noise floor estimation | Iterative outlier removal | Median of quiet regions | Statistical robustness, one-line NumPy |
| Convergence detection | Complex ML predictor | Simple trend analysis (3-iteration window) | Over-engineering for CASE domain |
| Quality scoring | Weighted multi-factor formula | Tier-based thresholds | Easier for AI to reason about |

**Key insight:** This phase encodes *what the AI should look for* and *how to respond*, not *code to automate it*. Future phases may build tools if patterns emerge, but premature tooling creates maintenance burden.

---

## Common Pitfalls

### Pitfall 1: Confusing Solution Count Reduction with Progress

**What goes wrong:** Agent sees 1000 → 800 solutions and considers it "good progress," continues adding correlations blindly until hitting iteration cap with 300 solutions remaining.

**Why it happens:** Lack of convergence rate awareness. 20% reduction in one iteration vs 2% reduction signals different dynamics.

**How to avoid:**
- Teach **convergence rate threshold**: If reduction < 10% for 2 consecutive iterations AND solution_count > 50, stop and diagnose.
- Teach **plateau detection**: If 3 iterations show < 5% change each, structure is under-determined—request more NMR data or rank current solutions with strong caveats.

**Warning signs:**
- Solution count oscillates (500 → 450 → 480)
- Solution count increases after adding "high-confidence" correlations
- Solution count stuck at round numbers (500 → 500 → 500)

### Pitfall 2: Over-Trusting Low-Quality Spectra

**What goes wrong:** Agent picks 50 HMBC peaks from noisy spectrum (SNR = 15), generates LSD file with all 50, gets 0 solutions, blindly adds `ELIM 10 0`, gets 10,000 nonsense solutions.

**Why it happens:** No quality gate before peak picking. Garbage in, garbage out.

**How to avoid:**
- **Quality gate**: If SNR < 20 OR digital_resolution < 3 pts/ppm, document limitations FIRST, then adjust strategy:
  - Use only top 25% of HMBC peaks (by intensity)
  - Start with 3 correlations, not 5
  - Warn user that low quality may prevent definitive answer
- **Never auto-ELIM on low-quality spectra**: If 0 solutions, diagnose manually with user input.

**Warning signs:**
- Noise floor is > 20% of tallest peak
- 13C dimension has < 50 total points (severe under-sampling)
- HMBC shows > 200 "validated" correlations (likely noise leakage)

### Pitfall 3: Ignoring 1J Artifact Leakage

**What goes wrong:** HMBC picker validates a peak at (155 ppm C, 7.2 ppm H) as "long-range correlation," but it's actually a 1JCH direct coupling that leaked through the filter. LSD interprets this as "C-155 correlates to distant H-7.2" and generates impossible structures.

**Why it happens:** HMBC experiments suppress but don't fully eliminate 1JCH. Peaks near the HSQC diagonal are suspect.

**How to avoid:**
- **1J exclusion zone**: If HMBC peak is within ±1.5 ppm of ANY HSQC correlation, flag as potential 1J artifact.
- **Cross-reference with HSQC**: If HMBC(C1, H2) exists AND HSQC(C1, H1) exists AND H1 ≈ H2 (±0.3 ppm), likely 1J—exclude.

**Warning signs:**
- Strong HMBC peaks cluster along expected 1JCH positions
- Symmetry: HMBC(C1, H2) and HMBC(C2, H1) both present (mutual 1J)
- Agent reports "unusual HMBC correlation from aromatic C to its own H" (red flag phrasing)

### Pitfall 4: Iteration Cap as Default Outcome

**What goes wrong:** Agent always hits 10-iteration maximum, presents solutions with "reached iteration limit" caveat, never investigates why convergence failed.

**Why it happens:** Treating iteration cap as acceptable stopping condition instead of failure mode.

**How to avoid:**
- **Iteration cap is a SAFETY**, not a strategy. If hit, treat as diagnostic failure:
  - Review correlation selection logic—were they truly high-confidence?
  - Check for systematic issue (wrong molecular formula, missing heteroatom constraints)
  - Document "structure elucidation incomplete, requires manual review"
- **Target 3-5 iterations for success**: If taking >7 iterations, something is wrong with correlation quality or molecular formula.

**Warning signs:**
- Always hitting iteration 9-10
- Solution count still > 100 at iteration 8
- Agent says "adding more correlations" without assessing why previous ones were ineffective

---

## Code Examples

**Note:** This phase has NO code examples—it's pure knowledge authoring. However, here are conceptual patterns the AI agent should understand to describe in natural language:

### Quality Assessment (Conceptual)

```python
# What the AI should UNDERSTAND (not write):
# 1. Compute noise floor from quiet region
noise_floor = np.median(np.abs(spectrum.data[quiet_region_mask]))

# 2. Find tallest signal peak
tallest_peak = np.max(np.abs(spectrum.data[signal_region_mask]))

# 3. Calculate SNR
snr = tallest_peak / noise_floor

# 4. Assess digital resolution
points_per_ppm = len(spectrum.f1_ppm_scale) / ppm_range

# 5. Make strategy decisions
if snr < 30:
    recommended_threshold = 0.08  # Higher threshold for noisy data
    trusted_fraction = 0.5  # Use top 50% of correlations
else:
    recommended_threshold = 0.05
    trusted_fraction = 1.0
```

**Teaching point:** The AI should explain this logic to users, not generate this code. Example: "The spectrum's signal-to-noise ratio is approximately 25 (tallest peak / noise floor), which is moderate quality. I'll increase the peak picking threshold to 0.08 to avoid noise peaks."

### High-Confidence Correlation Selection (Conceptual)

```python
# What the AI should REASON ABOUT:
# For each HMBC correlation (C_ppm, H_ppm):
#   1. Find nearest other carbons
#   2. If nearest_carbon_distance < 2 * tolerance (3.0 ppm), mark AMBIGUOUS
#   3. Same for protons (0.2 ppm threshold)
#   4. If both unique AND intensity > median, mark HIGH_CONFIDENCE

# Sort correlations by confidence score, take top 3-5
# Document why chosen: "C-155.2 ppm is isolated (nearest carbon 4.3 ppm away)"
```

**Teaching point:** The agent should document reasoning: "I'm starting with the correlation between C-155.2 and H-7.8 because the carbon shift is well-isolated from other signals (nearest carbon is 4.3 ppm away), reducing assignment ambiguity."

---

## State of the Art

| Domain | Old Approach | Current Approach | When Changed | Impact |
|--------|--------------|------------------|--------------|--------|
| HMBC constraint building | Dump all correlations into LSD | Iterative refinement with high-confidence first | Conceptual best practice (no dated publication) | Reduces over-constraint failures, provides diagnostic feedback |
| S/N assessment | Fixed dB thresholds (e.g., 50:1 minimum) | Relative to spectrum's own noise floor | Ongoing in deep learning era ([DN-Unet 2020](https://pubs.acs.org/doi/abs/10.1021/acs.analchem.0c03087)) | Generalizes across instruments |
| Digital resolution | Ignored in automated workflows | Explicitly assessed, tolerances adjusted | Recent (2025 [JTF-Net](https://www.nature.com/articles/s41467-025-57721-w) quality metrics) | Prevents false negatives from aliasing |
| t1 noise handling | Manual spectrum cleanup | Gradient-selected pulse sequences + algorithmic suppression ([2023 method](https://pubmed.ncbi.nlm.nih.gov/37143296/)) | 2023 | Cleaner HMBC data for automation |

**Deprecated/outdated:**
- **"Always use ELIM for zero solutions"**: Modern approach diagnoses first (sp2 parity, formula errors) before resorting to ELIM
- **"3-phase HMBC strategy" (high/medium/low confidence)**: Too rigid; user wants continuous iteration with 3-5 batch size
- **"Trust all HMBC correlations equally"**: Artifact awareness (1J leakage) now standard

---

## Open Questions

### 1. Zero-Solution Recovery Strategy

**What we know:** User wants diagnosis before ELIM, but didn't specify exact diagnostic order.

**What's unclear:** Should the AI agent check in a specific sequence (sp2 parity → H-count → formula → correlations → ELIM) or use a decision tree?

**Recommendation:** Encode as a checklist-style decision tree in SKILL.md:
```
IF 0 solutions:
    1. Verify sp2 atom count is EVEN (most common cause)
    2. Verify hydrogen count matches formula
    3. Review most recent batch for conflicts (try removing last batch)
    4. Check molecular formula correctness
    5. ONLY THEN consider ELIM 1 0 (eliminate 1 correlation)
```

### 2. Convergence Stall Detection

**What we know:** User wants agent to detect when solution count reduction stalls.

**What's unclear:** Exact threshold—2 iterations with <5% change? 3 iterations with <10%? Absolute vs relative change?

**Recommendation:** Use 3-iteration sliding window with <10% relative change:
```
IF last_3_iterations show < 10% reduction each:
    STOP adding correlations
    RANK current solutions with caveat: "structure is under-determined"
```

**Confidence:** MEDIUM—heuristic threshold, not validated by literature.

### 3. Artifact Recognition Specificity

**What we know:** 1J leakage, t1 noise, baseline roll are common artifacts.

**What's unclear:** How specific should the guidance be? Should we teach visual recognition patterns or just impact on data?

**Recommendation:** Focus on **impact and mitigation**, not visual recognition (AI agent can't "see" spectra directly):
- 1J leakage: "Strong peaks within ±1.5 ppm of HSQC diagonal—exclude from HMBC constraints"
- t1 noise: "If spectrum metadata indicates non-gradient HMBC, expect horizontal streaks—validate fewer correlations"
- Baseline roll: "If 13C peaks shift by >0.5 ppm between experiments, increase tolerances"

**Confidence:** MEDIUM—practical guidance, not comprehensive artifact taxonomy.

### 4. Quality Tier Thresholds

**What we know:** User wants relative thresholds, not absolute.

**What's unclear:** Exact SNR and digital resolution tier boundaries (e.g., is SNR=30 "good" or "moderate"?).

**Recommendation:** Use quartile-based tiers with domain-informed anchors:
- SNR: 100 (excellent), 30 (good), 10 (moderate), <10 (poor)
- Digital resolution: 10 pts/ppm (excellent), 5 (good), 2 (moderate), <2 (poor)

These are **pragmatic defaults** based on typical NMR facility data, not rigorously validated thresholds.

**Confidence:** LOW—thresholds are heuristic, not evidence-based. Mark as "subject to refinement based on real-world usage."

---

## Sources

### Primary (HIGH confidence)

- **LSD Software Documentation**: [https://nuzillard.github.io/LSD/index_ENG.html](https://nuzillard.github.io/LSD/index_ENG.html) - Official LSD manual, constraint satisfaction paradigm
- **Tutorial for LSD structure elucidation**: [PubMed 28543725](https://pubmed.ncbi.nlm.nih.gov/28543725/) - Iterative constraint building methodology
- **Common NMR artifacts**: [Wiley Online Library](https://onlinelibrary.wiley.com/doi/epdf/10.1002/cmr.a.21387) - 1J leakage, t1 noise, baseline issues
- **HMBC correlation confidence**: [Leveraging the HMBC PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10948112/) - Assignment best practices
- **Digital resolution fundamentals**: [ASU NMR Core](https://cores.research.asu.edu/sites/default/files/2018-07/NMR%20Digital%20Resolution.pdf) - Points per ppm calculations

### Secondary (MEDIUM confidence)

- **13C HSQC/HMBC resolution limits**: [Columbia NMR Facility](https://nmr.chem.columbia.edu/content/hsqc-and-hmbc) - Typical digital resolution issues
- **t1 noise suppression**: [PubMed 37143296](https://pubmed.ncbi.nlm.nih.gov/37143296/) - 2023 algorithmic methods
- **Baseline correction review**: [PMC 2516527](https://pmc.ncbi.nlm.nih.gov/articles/PMC2516527/) - Artifact detection and correction
- **iPick automated peak picking**: [PMC 8767925](https://pmc.ncbi.nlm.nih.gov/articles/PMC8767925/) - SNR-based validation methods
- **Deep learning for NMR quality**: [Nature Communications 2025](https://www.nature.com/articles/s41467-025-57721-w) - JTF-Net quality assessment

### Tertiary (LOW confidence)

- **SNR thresholds for quantitative NMR**: [Various web sources](https://www.sciencedirect.com/science/article/abs/pii/S1064185884711600) - Suggests 250:1 for <1% integration error, but NOT validated for CASE workflows
- **Convergence stopping criteria**: [Wikipedia CSP](https://en.wikipedia.org/wiki/Constraint_satisfaction_problem) - General CSP theory, not NMR-specific

---

## Metadata

**Confidence breakdown:**
- **Incremental HMBC strategy**: MEDIUM - Based on LSD constraint satisfaction paradigm and user requirements, but specific batch size (3-5) and iteration cap (~10) are pragmatic choices, not validated
- **Spectral quality metrics**: MEDIUM - S/N and digital resolution calculations are standard, but tier thresholds are heuristic
- **Artifact identification**: MEDIUM - 1J leakage and t1 noise are well-documented, but mitigation strategies for AI agents are novel
- **Failure decision trees**: LOW - Diagnostic sequences are reasoned from first principles, not literature-validated workflows

**Research date:** 2026-02-06
**Valid until:** 60 days (stable domain—NMR spectroscopy fundamentals don't change rapidly, but AI agent best practices may evolve)

**Key uncertainties:**
1. Optimal convergence stall threshold (currently 3 iterations with <10% change)
2. SNR/resolution tier boundaries (currently quartile-based heuristics)
3. Zero-solution diagnostic sequence (currently checklist-ordered, not decision-tree validated)

**Recommendations for Phase 23+ validation:**
- Collect real-world CASE session logs to validate iteration counts (is 3-5 typical? do successful cases need <7 iterations?)
- Benchmark SNR thresholds against expert spectroscopist decisions
- Build diagnostic tool to automate sp2 parity / H-count checks (reduces cognitive load on AI agent)
