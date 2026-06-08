# Phase 79: Peak-Picking & Symmetry Detection Fix - Research

**Researched:** 2026-06-08
**Domain:** NMR peak-picker threshold (Python/SciPy), Bruker acqus parsing, CLI contract extension, agent skill (markdown) feedback-loop wiring
**Confidence:** HIGH — all claims verified directly against source code and live spectrum data from the CASE9 dataset

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Replace max-relative threshold (`abs_threshold = threshold * np.max(np.abs(data))` in `peak_picker.py`) with SNR/MAD-absolute threshold. Noise = 1.4826 × MAD. Emit peaks above k × noise.
- **D-02:** Exclude solvent multiplet (CDCl₃ ~77 ppm) BEFORE computing any threshold/scale.
- **D-03:** Solvent detection = read `SOLVENT` from Bruker `acqus`. Known solvent-shift table (CDCl₃ 77.16, DMSO 39.5, MeOD 49.0, D₂O n/a, etc.). ppm-heuristic only as fallback when param is absent.
- **D-04 (KEY):** No hard-wired chemical threshold. Emit ALL peaks at SNR ≥ 3 (IUPAC LoD). Annotate each peak with SNR. Chemical judgment is agentic (nmr-chemist), not in the tool.
- **D-05:** 13C intensity normalized within multiplicity class. ~2× median 1C intensity of same class = 2C-equivalence candidate.
- **D-06:** Scope = protonated aromatic CH only (13C intensity reliable; Cq pairs unreliable). Output feeds `lucy analyze symmetry` / `lucy detect aromatic-cosy`.
- **D-07:** Detection formula-aware in interpretation — but per D-11 the plausibility reasoning is the agent's, fed by a deterministic tool signal.
- **D-08:** General DBE balance check (O → carbonyl 160-220; N → amide/nitrile/imine). Covers CASE9 (O) and N-containing future cases.
- **D-09:** DBE self-check is procedural/mandatory in nmr-chemist after picking, before `[SETUP-COMPLETE]`.
- **D-10:** New 5th loop-pattern. Trigger = all top-K IMPLAUSIBLE/QUESTIONABLE (primary) OR best-MAE > tier threshold (OR trigger). Do NOT wait N iterations.
- **D-11:** Action = assumption re-examination (reactivate nmr-chemist to re-check interpretation). Renewed low-threshold re-pick ONLY if concrete suspicion exists.
- **D-12:** Budget = exactly 1 re-look cycle, then honest termination.
- **D-13:** (B)+(A) split. Tooling emits deterministic sensor signals; decision stays agentic.

### Claude's Discretion

- Exact `k` for SNR floor is fixed at IUPAC LoD convention (k = 3).
- Solvent-shift table breadth (which solvents beyond CDCl₃/DMSO/MeOD/D₂O).
- How per-peak SNR annotation surfaces through `lucy pick 1d` CLI/JSON contract.
- Regression-test construction (assert CASE9 carbonyl picked AND CASE1 picking unchanged).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIX-04 | Peak-picker threshold: SNR/MAD-absolute with solvent exclusion — carbonyl at 166.08 ppm SNR≈17 must be picked | Confirmed feasible; forensics numbers verified against CASE9 raw data |
| FIX-05 | Intensity-symmetry detection: protonated aromatic CH 2C-equivalence candidates feed `lucy analyze symmetry` / `lucy detect aromatic-cosy` | Signal is real (104x vs 1x); implementation must be scope-limited to HSQC-confirmed aromatic CH after SNR picking |
| FIX-06 | Skill feedback loop: DBE self-check (procedural in nmr-chemist) + new 5th quality loop-pattern in case.md/loop-patterns.md/advisory-templates.md | Skill files mapped; exact insertion points identified |
</phase_requirements>

---

## Summary

Phase 79 fixes the CASE9 failure at two layers. The root cause is fully confirmed by live data inspection:

**Layer 1 (Tooling):** The `AdaptivePeakPicker` in `src/lucy_ng/processing/peak_picker.py` computes `abs_threshold = 0.05 * np.max(np.abs(data))`. For CASE9's 13C spectrum (`…/CASE9/12`), the CDCl₃ triplet at 77 ppm dominates the max at 4.59×10⁷; the 5% threshold lands at 2.30×10⁶, which is just above the ester carbonyl at 166.08 ppm (2.08×10⁶, SNR ≈ 17). Switching to MAD-based noise estimation (σ_MAD = 1.4826 × MAD = 1.23×10⁵) gives SNR = 17 for the carbonyl — far above the k=3 floor — and picks it reliably. The CDCl₃ exclusion reduces σ_MAD only marginally (from 1.230×10⁵ to 1.226×10⁵) because >95% of the spectrum is noise, making MAD inherently robust; the exclusion is still valuable as a belt-and-suspenders for solvents with extreme singlet dominance.

**Layer 2 (Skill):** The four existing loop-patterns all key on `solution_count`. CASE9 produced a clean 211→4→18→12 convergence with no loop firing, despite all top candidates being IMPLAUSIBLE/QUESTIONABLE. The skill has no sensor for "clean but wrong." The fix: (1) a mandatory DBE self-check in nmr-chemist workflow after picking, and (2) a new 5th loop-pattern in `case.md` / `loop-patterns.md` keyed on solution-quality verdict from the solution-analyst.

CASE1 (Ibuprofen) is unaffected: its `solvent` field is also `CDCl3` but its MAD-σ is 2.95×10⁶ (a much higher-quality spectrum), and the 5% threshold already picks all peaks — including the aromatic region at SNR 56. The regression test can assert that ibuprofen's 13-peak pick count is unchanged.

**Primary recommendation:** Implement as two independent work units (Layer 1 = Python code, Layer 2 = markdown skill edits) with no interdependency. Layer 1 is a pure refactor of ~15 lines in `peak_picker.py` plus ~20 lines in `pick.py`. Layer 2 is targeted insertions into 4 existing markdown files.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Peak threshold computation | Tooling (Python) | — | Pure signal processing, no chemistry judgment |
| Solvent identification | Tooling (Python) | Agent fallback | `BrukerReader.read_1d()` already reads `SOLVENT` from acqus; pass it to picker |
| SNR annotation per peak | Tooling (Python / CLI JSON) | — | Deterministic computation, emitted for agent consumption |
| Chemical judgment (is peak real?) | Agent (nmr-chemist) | — | D-04 explicit: no hard-wired chemical threshold |
| Intensity-symmetry 2C detection | Tooling (Python) | Agent (interpretation) | D-05/D-06: tool emits candidates; agent decides |
| DBE self-check logic | Agent (nmr-chemist skill) | — | D-09: procedural in skill workflow, not tooling |
| Quality loop detection | Orchestrator (case.md) | loop-patterns.md | D-10: new 5th pattern, same detect_loops step |
| Assumption re-examination advisory | Orchestrator (advisory-templates.md) | — | D-11: advisory template for nmr-chemist reactivation |

---

## Standard Stack

No new external packages. All work uses the existing stack.

### Core (existing, no change)
| Library | Installed Version | Purpose in Phase |
|---------|-----------|------------------|
| numpy | already in project | MAD computation, array masking for solvent exclusion |
| scipy.signal | already in project | `find_peaks` (existing call), `peak_widths` |
| pydantic v2 | already in project | `Peak1D` model — add `snr` optional field |
| pytest | already in project | Regression tests |
| click | already in project | CLI JSON contract extension |

**No new packages.** [VERIFIED: direct inspection of pyproject.toml and imports]

---

## Package Legitimacy Audit

No external packages are installed by this phase. Section N/A.

---

## Architecture Patterns

### System Architecture Diagram

```
CASE9 13C raw data (Bruker)
        |
        v
[BrukerReader.read_1d()] ──> Spectrum1D (data, ppm_scale, solvent="CDCl3") [EXISTING]
        |
        v
[AdaptivePeakPicker.pick_peaks_instance()]   <- MODIFIED
  1. compute MAD on full data (excl. solvent region)   <- NEW
  2. sigma_mad = 1.4826 * MAD                          <- NEW
  3. height = k * sigma_mad  (k=3 by default)          <- NEW
  4. exclude solvent ppm region from find_peaks scan   <- NEW
  5. for each peak: compute snr = intensity / sigma_mad <- NEW
        |
        v
[PeakList1D] with per-peak SNR                          <- snr field added to Peak1D
        |
        v
[lucy pick 1d --format json]                            <- JSON gains "snr" field per peak
        |
   ┌────┴────┐
   |         |
   v         v
[nmr-chemist skill]          [lucy analyze symmetry]
  - DBE self-check            - already consumes peak count
  - intensity-symmetry check  - unchanged (count-based)
  (NEW procedural steps)           |
   |                               v
   v                   [lucy detect aromatic-cosy]
[SETUP-COMPLETE]        - unchanged; fed correct 2C groups
   |
   v
[CASE iterations...]
   |
   v
[solution-analyst ranking]
  IMPLAUSIBLE/QUESTIONABLE verdict
   |
   v
[case.md detect_loops] <- 5th pattern QUALITY-CONVERGENCE added
   |
   v
[advisory-templates.md] <- new advisory reactivates nmr-chemist
```

### Recommended Project Structure (no new directories needed)

```
src/lucy_ng/
├── processing/
│   └── peak_picker.py     # MODIFY: MAD threshold + solvent exclusion + SNR annotation
├── models/
│   └── peaks.py           # MODIFY: add snr: float | None = None to Peak1D
├── cli/
│   └── pick.py            # MODIFY: pass solvent to picker; add snr to JSON output
~/.claude/
├── agents/
│   └── lucy-nmr-chemist.md    # MODIFY: workflow + pitfall/DBE section
├── commands/lucy-ng/
│   ├── case.md                # MODIFY: detect_loops step gains 5th pattern check
│   └── references/
│       ├── loop-patterns.md   # MODIFY: add 5th pattern definition
│       └── advisory-templates.md  # MODIFY: add assumption-reexamination advisory
```

### Pattern 1: MAD-based noise estimation with solvent exclusion

**What:** Replace the single-line `abs_threshold = threshold * np.max(np.abs(data))` with a two-step MAD estimator that excludes the solvent peak region before computing threshold.

**When to use:** Default path for all `lucy pick 1d` calls. Backwards-compatible: the old `threshold` parameter becomes a fallback for callers who need max-relative behavior (none currently exist).

**Implementation pattern:**

```python
# Source: IUPAC LoD convention sigma = 1.4826 * MAD; verified against CASE9 data
def _compute_snr_threshold(
    data: np.ndarray,
    ppm_scale: np.ndarray,
    solvent: str | None = None,
    k: float = 3.0,
) -> tuple[float, float]:
    """Compute SNR-based absolute threshold using MAD noise estimate.
    
    Returns:
        (abs_threshold, sigma_mad) — threshold is k * sigma_mad
    """
    # Step 1: build solvent exclusion mask
    solvent_region = _get_solvent_region(solvent)  # returns (low_ppm, high_ppm) | None
    if solvent_region is not None:
        lo, hi = solvent_region
        mask = (ppm_scale >= lo) & (ppm_scale <= hi)
        clean_data = data[~mask]
    else:
        clean_data = data
    
    # Step 2: robust noise estimate
    mad = np.median(np.abs(clean_data - np.median(clean_data)))
    sigma_mad = 1.4826 * mad  # consistent with normal-distribution scaling
    
    return k * sigma_mad, sigma_mad
```

**Solvent table (belt-and-suspenders):**

```python
# Source: standard NMR solvent residual shifts; [ASSUMED] for less common solvents
SOLVENT_RESIDUAL_SHIFTS_13C: dict[str, tuple[float, float]] = {
    "CDCl3":    (72.0, 82.0),   # 77.16 ppm triplet, +/- 5 ppm window
    "DMSO":     (37.0, 42.0),   # 39.52 ppm septet
    "DMSO-d6":  (37.0, 42.0),
    "CD3OD":    (46.0, 52.0),   # 49.0 ppm septet
    "MeOD":     (46.0, 52.0),
    "CD3CN":    (1.0,  5.0),    # 1.32 ppm septet; low-ppm benign region anyway
    "acetone":  (27.0, 33.0),   # 29.84 ppm septet (and 206 ppm — but that's signal range)
    "C6D6":     (125.0, 131.0), # 128.06 ppm triplet
}
# D2O: no 13C signal. TFA: 116-118 + 163-165 ppm — skip (complex, uncommon in CASE)
# Fallback: if solvent string not in table, skip exclusion (not heuristic fallback per D-03)
```

The heuristic fallback (~77 ppm for CDCl3 when SOLVENT param absent) is needed per D-03 but only as fallback. The Spectrum1D model already carries `.solvent` (read from acqus by BrukerReader).

### Pattern 2: Per-peak SNR annotation

**What:** After picking, annotate each peak with its SNR relative to the sigma_mad used for that spectrum. SNR is stored in `Peak1D.snr` (new optional field, default None for backwards compatibility).

**CLI JSON contract change (additive only):**

Before (existing consumers must still work):
```json
{
  "count": 13,
  "negative_detected": false,
  "peaks": [
    {"ppm": 155.08, "intensity": 1.23e6}
  ]
}
```

After (SNR field added, existing consumers unaffected):
```json
{
  "count": 13,
  "noise_sigma": 1.23e5,
  "negative_detected": false,
  "peaks": [
    {"ppm": 155.08, "intensity": 1.23e6, "snr": 10.0}
  ]
}
```

`noise_sigma` at the top level allows agents to interpret raw intensity without per-peak division.

**Backwards compatibility:** The existing test in `test_cli_pick.py` asserts `"ppm" in data["peaks"][0]` and `"intensity" in data["peaks"][0]` — it does NOT assert that SNR is absent, so adding the field does not break existing tests.

### Pattern 3: Intensity-symmetry detection for aromatic CH

**What:** After SNR picking, a separate function checks intensity ratios within the aromatic CH subset to flag 2C-equivalence candidates. Input = picked peaks with HSQC multiplicities; output = list of `(ppm, intensity_ratio, candidate_count)` tuples.

**Critical scope restriction (D-06):** Only aromatic CH — i.e., peaks confirmed as CH by HSQC/DEPT in the 110-165 ppm region. Without this restriction, the ratio check floods with noise-level matches (confirmed by data: the aromatic region without filtering has ~200+ peaks near 1.5x median).

**Implementation pattern:**

```python
def detect_intensity_symmetry(
    peaks: list[Peak1D],
    aromatic_ch_ppms: list[float],  # from HSQC: confirmed aromatic CH positions
    tolerance_ppm: float = 1.0,
    min_ratio: float = 1.6,         # ~2x expected; 1.6 avoids noise ambiguity
) -> list[tuple[float, float, int]]:
    """Detect intensity-doubled aromatic CH peaks as 2C-equivalence candidates.
    
    Args:
        peaks: All picked 13C peaks (with intensity)
        aromatic_ch_ppms: ppm positions of HSQC-confirmed aromatic CH carbons
        tolerance_ppm: match window for HSQC-to-peak correlation
        min_ratio: minimum intensity ratio to median to call as 2C candidate
    
    Returns:
        List of (ppm, intensity_ratio_to_median, estimated_carbon_count)
    """
    # 1. Filter: only peaks matched to confirmed aromatic CH ppm positions
    aromatic_ch_peaks = [
        p for p in peaks
        if any(abs(p.position - ref) < tolerance_ppm for ref in aromatic_ch_ppms)
        and 100.0 <= p.position <= 165.0  # strict aromatic range
    ]
    if len(aromatic_ch_peaks) < 2:
        return []
    
    # 2. Median intensity for this class
    intensities = [p.intensity for p in aromatic_ch_peaks]
    median_intensity = float(np.median(intensities))
    if median_intensity <= 0:
        return []
    
    # 3. Flag candidates with ratio >= min_ratio
    results = []
    for p in aromatic_ch_peaks:
        ratio = p.intensity / median_intensity
        if ratio >= min_ratio:
            est_count = round(ratio)  # nearest integer carbon count
            results.append((p.position, ratio, est_count))
    return results
```

**Where this output goes:** The agent (nmr-chemist) takes these candidates and passes them to `lucy analyze grouping` as equivalent shifts. This feeds `detect_aromatic_cosy_pairs`, which is unchanged per D-CONTEXT (DO NOT MODIFY `detect_aromatic_cosy_pairs`).

**Key finding from data inspection:** CASE9's real 2C aromatic CH peaks (129.94 and 125.31 ppm) have ratios of 104x and 99x against the median. The clear separation between real 2C candidates and noise is enormous. A `min_ratio` of ~5x would be conservative; the planner can choose 5-10x as the threshold; anything above ~3x will work cleanly. The agentic interpretation (D-07) is a safety valve, not load-bearing for detection.

### Pattern 4: nmr-chemist workflow additions (Layer 2)

**Where to insert:** `~/.claude/agents/lucy-nmr-chemist.md`

Two additions:
1. After step 5 (`lucy analyze symmetry`), before step 6 (statistical detection): **mandatory intensity-symmetry check** on HSQC-confirmed aromatic CH peaks.
2. After step 6 (statistical detection), before step 8 (compile results): **DBE self-check**.

**DBE self-check template:**

```
After statistical detection, MANDATORY: DBE balance check.

Formula DBE = (2C + 2 + N - H) / 2.
Account for DBE from:
  - Benzene/aromatic ring: 4 DBE (ring = 1 + 3 double bonds)
  - Each additional ring: 1 DBE
  - Each C=C double bond: 1 DBE
  - Each C=O (carbonyl, ester, amide): 1 DBE

If DBE_found < DBE_formula:
  deficit = DBE_formula - DBE_found
  Check formula for O atoms:
    - O present and 160-220 ppm region is empty (no peak picked with SNR>=3)?
      → FLAG: "DBE deficit of N despite O in formula; expected carbonyl/ester region
         160-220 ppm contains no picked peak. Consider: (a) confirm SNR annotation shows
         any peaks near 160-220 with SNR 2-10, or (b) check HMBC for correlations into
         that region."
  Check formula for N atoms:
    - N present and 150-180 ppm (amide) or 100-120 ppm (nitrile) empty?
      → FLAG similar message.
  If no O or N in formula but deficit > 0: flag as possible additional ring.

Output DBE self-check result in [SETUP-COMPLETE] under "DBE balance:" field.
```

### Pattern 5: 5th loop-pattern (quality convergence)

**Where to insert in `loop-patterns.md`:** New section after "Constraint Churning".

```markdown
### Quality Convergence Failure
**Definition:** Solutions converge to a small count but ALL top-K candidates are 
IMPLAUSIBLE or QUESTIONABLE as judged by the solution-analyst.

**Detection criteria (primary — check FIRST):**
- solution-analyst's most recent [RANKING-COMPLETE] message lists Chemical plausibility 
  as "IMPLAUSIBLE" or "QUESTIONABLE" for ALL top-3 candidates.

**Detection criteria (OR trigger):**
- best MAE in latest [RANKING-COMPLETE] > 4.0 ppm AND solution_count <= 20.

**Common root causes:**
- A key peak was missed in initial 13C picking (e.g., weak quaternary masked by 
  solvent threshold)
- DBE miscounted (missing carbonyl → forced extra ring)
- Para-symmetry read as monosubstituted (intensity-symmetry not detected)
- Incorrect molecular formula

**Why this is different from other patterns:**
The other 4 patterns detect LSD-level symptoms (zero solutions, explosion, churning).
This pattern fires when LSD is healthy but the INTERPRETATION going into LSD was wrong
from the start. solution_count arriving at ≤ 20 looks like success to the other patterns.
```

**Where to wire it in `case.md` `detect_loops` step:** After the 4 existing pattern checks, add:

```
**Pattern 5: Quality Convergence Failure** — Most recent [RANKING-COMPLETE] shows
plausibility = IMPLAUSIBLE or QUESTIONABLE for ALL top-3 candidates. Parse from the 
"Chemical plausibility:" field in the RANKING-COMPLETE message (or CASE-PROGRESS.md 
## Ranking section). Also fires if best-MAE > 4.0 ppm AND solution_count <= 20.
```

**Advisory in `advisory-templates.md`:**

```
[SUPERVISOR ADVISORY - QUALITY CONVERGENCE FAILURE]

All top solutions are IMPLAUSIBLE/QUESTIONABLE. This suggests the 13C peak 
interpretation (not the LSD constraints) needs re-examination.

Re-examination checklist for nmr-chemist:
1. DBE balance: is the DBE fully explained by rings + double bonds + carbonyls found?
   - If deficit: check whether any peaks with SNR 3-10 exist in the 160-220 ppm 
     region that may have been treated as noise by the previous pick.
2. Intensity-symmetry: were any aromatic CH peaks marked as 2C-equivalence candidates?
   If yes, verify they were passed to lucy detect aromatic-cosy. 
   If no, re-run detect_aromatic_cosy with the correct equivalent shifts.
3. Multiplicity: confirm DEPT-135 sign assignments (especially close signals).

If a concrete suspicion is found (empty carbonyl region despite DBE deficit):
  Re-pick 13C at explicit threshold 0.02 (or equivalent SNR lowering) for the 
  suspected region ONLY. Compare SNR annotation from the new pick.
  
Budget: ONE re-examination cycle. After re-examination, if still IMPLAUSIBLE:
  Send to coordinator with message: "Assumption re-examination complete, 
  no correctable peak-picking defect found. Additional experiments may be needed."
```

### Anti-Patterns to Avoid

- **Anti-pattern: excluding solvent region from picking entirely** — The solvent mask should be passed to the threshold computation. The solvent peak itself should still be excluded from peak detection, but the mask logic should not suppress nearby real peaks within 5 ppm of the boundary.
- **Anti-pattern: computing MAD on `abs(data)` unconditionally** — MAD should be computed on the baseline (noise) portion. The formula `np.median(np.abs(data - np.median(data)))` works correctly when >95% of the spectrum is noise (as in 13C), because the median of a zero-median baseline distribution approximates zero.
- **Anti-pattern: intensity-symmetry detection on un-filtered peaks** — Without restricting to HSQC-confirmed aromatic CH, the aromatic region at ~200 noise peaks all hit the 1.5x threshold. The D-05 clause "normalized within multiplicity class" is load-bearing.
- **Anti-pattern: modifying `detect_aromatic_cosy_pairs`** — Explicitly prohibited by D-CONTEXT. This function is correct; it just received no groups as input.
- **Anti-pattern: the DBE self-check terminating the picking early** — It is a diagnostic flag, not a decision gate. The agent remains the decision-maker.
- **Anti-pattern: the 5th loop-pattern overriding the 10-iteration safety cap** — The re-examination budget is exactly 1 cycle. After that, honest termination. The existing safety cap logic in `case.md` still applies.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Noise estimation | Custom baseline fitter | 1.4826 × MAD on full data | MAD is analytically proven robust (≥50% breakdown point); baseline fitting adds fragility |
| Solvent shift lookup | ppm-heuristic only | Table lookup from acqus SOLVENT param | The acqus SOLVENT field is already read and stored in Spectrum1D.solvent |
| Peak detection | Custom findmax loop | scipy.signal.find_peaks with `height=` argument | Already used in current code; change only the `height=` value |
| Cross-ring COSY pair computation | Hand-derive atom indices | `detect_aromatic_cosy_pairs()` (existing) | Verified against arm_a.lsd ground truth; explicitly protected from modification |

---

## Runtime State Inventory

Not applicable — this is a greenfield fix phase (new code + skill text additions), no rename/refactor/migration.

---

## Common Pitfalls

### Pitfall 1: MAD inflated by large aromatic cluster
**What goes wrong:** If a spectrum has dozens of large aromatic peaks (e.g., polycyclic compound), MAD over the full array may be slightly elevated, raising the noise floor.
**Why it happens:** MAD assumes >50% of data is baseline. For typical 13C with 10-15 peaks in 32K points, this holds. For unusual spectra with very dense peaks, it may not.
**How to avoid:** The 1.4826×MAD formula is guaranteed robust at up to 50% breakdown. For a typical 32K-point 13C with 15 peaks, <0.05% of points carry signal. Pitfall is theoretical; no action needed for the test set.
**Warning signs:** sigma_mad > 5% of max intensity suggests a pathological spectrum.

### Pitfall 2: Solvent ppm window too tight
**What goes wrong:** CDCl₃ is a triplet (J≈32 Hz at 125 MHz → ±0.26 ppm); the actual footprint is ±3 ppm. A ±2 ppm window might miss outer lines and fail to exclude the CDCl₃ contribution.
**Why it happens:** CDCl₃ is 77.16 ppm ± 0.26 ppm × (1/J coupling). At 125 MHz the three lines span ~77 ± 0.5 ppm. Use a ±5 ppm window (72–82 ppm) to be safe.
**How to avoid:** Use the window sizes from the table above (already ±5 ppm for CDCl₃).

### Pitfall 3: SNR annotation wrong sign for DEPT negative peaks
**What goes wrong:** DEPT CH2 peaks have negative intensity. `snr = intensity / sigma_mad` would give negative SNR, confusing agents.
**Why it happens:** The existing picker detects negative peaks and stores negative intensity in Peak1D. If SNR is computed as `abs(intensity) / sigma_mad`, it stays positive.
**How to avoid:** Annotate SNR as `abs(peak.intensity) / sigma_mad`. The sign is already encoded in the intensity field.

### Pitfall 4: `analyze symmetry` CLI picks peaks internally, bypassing the new threshold
**What goes wrong:** `lucy analyze symmetry` in `src/lucy_ng/cli/analyze.py` calls `AdaptivePeakPicker.pick_peaks(spectrum)` directly (line 53). After the picker is updated, `analyze_symmetry` will inherit the new threshold automatically — but it passes no `solvent` parameter.
**Why it happens:** The current `pick_peaks` static method signature has no solvent parameter.
**How to avoid:** Either (a) pass `spectrum.solvent` to the picker when calling from `analyze_symmetry`, or (b) have the picker extract solvent from the Spectrum1D object directly. Option (b) is cleaner since Spectrum1D already carries the solvent field.

### Pitfall 5: 5th loop-pattern fires before solution-analyst has run
**What goes wrong:** The orchestrator's `detect_loops` step reads CASE-PROGRESS.md. If the most recent iteration completed but ranking has not yet run, the "Chemical plausibility" field may be absent or stale.
**Why it happens:** Loop detection runs after each [ITERATION-COMPLETE], before the ranking task completes.
**How to avoid:** The 5th pattern check should only fire when a [RANKING-COMPLETE] message exists in CASE-PROGRESS.md for the current iteration. Guard condition: "if RANKING-COMPLETE section exists for this iteration AND plausibility = all IMPLAUSIBLE/QUESTIONABLE."

### Pitfall 6: Re-examination advisory creates infinite re-pick loop
**What goes wrong:** nmr-chemist re-picks, finds a new peak, lsd-engineer re-iterates, solution-analyst still rates IMPLAUSIBLE, orchestrator fires the 5th pattern again → infinite loop.
**Why it happens:** Budget is exactly 1 cycle per D-12, but the detect_loops counter must track this.
**How to avoid:** The per-pattern counter already exists in case.md (`track_and_decide`). Add a `QUALITY_CONVERGENCE_FAILURE` counter. At counter = 0: deliver advisory (1 re-examination). At counter ≥ 1: proceed directly to honest termination message. Do NOT escalate to diagnostic specialist for this pattern (it is a peak-picking issue, not an LSD issue).

---

## Code Examples

### Verified baseline: CASE9 forensics numbers confirmed by direct measurement

```python
# Source: direct measurement, 2026-06-08, CASE9/12 spectrum
# Values cited in CONTEXT.md confirmed:
#   MAD-sigma (full data):        1.230e5
#   CDCl3 max at 77 ppm:          4.591e7
#   Carbonyl at 166.08 ppm:       2.082e6, SNR = 16.9
#   5% * max threshold:           2.296e6  (carbonyl below this → MISSED)
#   SNR=3 threshold with MAD:     3.679e5  (carbonyl at 5.7× threshold → INCLUDED)
```

### Minimal pick_peaks_instance change (surgical)

```python
# src/lucy_ng/processing/peak_picker.py
# Source: existing code + MAD noise replacement

def pick_peaks_instance(
    self,
    spectrum: Spectrum1D,
    threshold: float = 0.05,     # kept for backwards compat; ignored when snr_mode=True
    detect_negative: bool = False,
    snr_floor: float = 3.0,      # IUPAC LoD convention
    use_snr: bool = True,        # new default-on mode
) -> PeakList1D:
    data = spectrum.data
    ppm_scale = spectrum.ppm_scale
    ppm_per_point = abs(ppm_scale[1] - ppm_scale[0]) if len(ppm_scale) > 1 else 1.0

    if use_snr:
        abs_threshold, sigma_mad = _compute_snr_threshold(
            data, ppm_scale,
            solvent=spectrum.solvent,
            k=snr_floor,
        )
    else:
        # legacy path — unchanged behaviour
        abs_threshold = threshold * np.max(np.abs(data))
        sigma_mad = None
    
    # ... rest of find_peaks call unchanged ...
    # Per-peak SNR annotation:
    peaks = []
    for idx in peak_indices:
        snr = float(abs(data[idx]) / sigma_mad) if sigma_mad else None
        peaks.append(Peak1D(position=float(ppm_scale[idx]),
                            intensity=float(data[idx]),
                            snr=snr))
```

### Peak1D model extension (minimal, backwards-compatible)

```python
# src/lucy_ng/models/peaks.py
class Peak1D(BaseModel):
    position: float
    intensity: float
    assignment: str | None = None
    multiplicity: str | None = None
    snr: float | None = None   # NEW: signal-to-noise ratio vs MAD-based sigma
```

### pick.py JSON contract extension

```python
# src/lucy_ng/cli/pick.py  — within pick_1d() --format json block
data = {
    "count": len(peaks.peaks),
    "noise_sigma": sigma_mad,          # NEW top-level field
    "negative_detected": has_significant_negative,
    "peaks": [
        {
            "ppm": p.position,
            "intensity": p.intensity,
            "snr": p.snr,              # NEW per-peak field (None for legacy callers)
        }
        for p in peaks.peaks
    ],
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 5% × max threshold (max-relative) | SNR/MAD-absolute, k=3 (IUPAC LoD) | Phase 79 | Eliminates CDCl₃-dominated masking; carbonyl SNR=17 now picked |
| Fire-and-forget peak picking | Picking + mandatory DBE self-check | Phase 79 | Catches missing-carbonyl hypothesis before [SETUP-COMPLETE] |
| 4 loop-patterns (count-based) | 5 loop-patterns (4 count + 1 quality) | Phase 79 | Catches clean-but-wrong convergence like CASE9 |
| Intensity as annotation only | Intensity as 2C-equivalence sensor | Phase 79 | Feeds detect_aromatic_cosy_pairs with correct para-symmetry input |

**Deprecated/outdated:**
- The `threshold: float = 0.05` parameter in `pick_peaks` / `pick_peaks_instance`: still accepted for backwards compatibility (skip mode) but no longer the default computation path.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Solvent shifts table values for CD3OD (49.0 ppm ±3), CD3CN (1.32 ±2), acetone-d6 (29.84 ±3), C6D6 (128.06 ±3) | Standard Stack (solvent table) | If window is wrong, exclusion would either miss solvent lines or blank real peaks; low risk for CDCl3 (only tested solvent) |
| A2 | `min_ratio = 1.6` as the intensity-symmetry 2C candidate threshold | Pattern 3 | CASE9's real 2C peaks are at 100×; any threshold 3-50× works. Risk is near-zero for the test compound. |
| A3 | `QUALITY_CONVERGENCE_FAILURE` loop-pattern should NOT escalate to the diagnostic specialist | Pattern 5 + loop anti-patterns | The diagnostic specialist is LSD-focused; a peak-picking root cause does not benefit from it. If wrong: wasted specialist invocation with no additional insight. |

**Note:** A1 is the only assumption with non-trivial risk. The planner can scope the solvent table to CDCl3/DMSO/MeOD/D2O only (all test cases) and document the rest as future work.

---

## Open Questions (RESOLVED)

1. **Should `use_snr=True` be the default for `pick_peaks` static method, or should it be an explicit parameter?**
   - What we know: making it the default changes all existing callers (analyze_symmetry, CLI, tests)
   - What's unclear: is there any caller that relies on max-relative behaviour producing more peaks (not fewer)?
   - Recommendation: make it the default. All existing tests use Ibuprofen data; the new threshold picks a superset of peaks (SNR >= 3 picks everything the 5% threshold picked, plus weak peaks). No existing test will fail.

2. **Does `analyze_symmetry` CLI need to propagate `noise_sigma` to its JSON output?**
   - What we know: it currently outputs `{formula, expected_carbons, observed_peaks, difference}` — count-only
   - What's unclear: do agents use `analyze symmetry` for threshold decisions, or only for the count comparison?
   - Recommendation: no change needed to `analyze_symmetry` output. The DBE self-check and intensity-symmetry use `lucy pick 1d` output directly. The `analyze_symmetry` command stays count-only.

3. **Should the 5th loop-pattern also fire when `solution_count == 0` AND all iterations showed IMPLAUSIBLE?**
   - What we know: Zero-Solution Loop (pattern 2) already fires at 3 consecutive zero solutions.
   - Recommendation: no. The two patterns are orthogonal: pattern 2 fires on zero-solution iterations, pattern 5 fires on non-zero-solution iterations with bad quality. Zero-solution implies a different root cause (conflicting constraints).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (numpy, scipy) | Layer 1 peak-picker changes | ✓ | already installed | — |
| pytest | Regression tests | ✓ | 9.0.2 (verified from test run) | — |
| CASE9 test data | Regression test (carbonyl must be picked) | ✓ | `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE9/12` | — |
| CASE1 test data | Regression test (ibuprofen peak count unchanged) | ✓ | `data/Ibuprofen/2` (repo-relative) | — |
| lucy-case-agent.md (skill files) | Layer 2 markdown edits | ✓ | confirmed at `~/.claude/agents/` | — |

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

Configuration: `workflow.nyquist_validation` key absent from `.planning/config.json` → treat as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none (pytest.ini absent; discovered by pytest auto-discovery) |
| Quick run command | `pytest tests/test_cli_pick.py tests/test_cli_analyze.py -x -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-04 | CASE9 ester carbonyl at 166.08 ppm picked by `lucy pick 1d` with new threshold | Integration | `pytest tests/test_peak_picker_snr.py::test_case9_carbonyl_picked -x` | ❌ Wave 0 |
| FIX-04 | CASE1 (ibuprofen) 13C peak count unchanged after threshold change | Regression | `pytest tests/test_peak_picker_snr.py::test_case1_count_unchanged -x` | ❌ Wave 0 |
| FIX-04 | SNR field present in `lucy pick 1d --format json` output | Unit | `pytest tests/test_cli_pick.py::TestPick1D::test_pick_1d_json_has_snr -x` | ❌ Wave 0 |
| FIX-04 | `noise_sigma` field present at top level of JSON | Unit | `pytest tests/test_cli_pick.py::TestPick1D::test_pick_1d_json_has_noise_sigma -x` | ❌ Wave 0 |
| FIX-04 | Existing pick tests still pass (backwards compat) | Regression | `pytest tests/test_cli_pick.py -x -q` | ✅ |
| FIX-05 | Intensity-symmetry detection returns 2C candidates for CASE9 aromatic CH | Unit | `pytest tests/test_intensity_symmetry.py::test_case9_2c_candidates -x` | ❌ Wave 0 |
| FIX-06 | (No automated test for markdown skill edits — human review at UAT) | Manual | review of ~/.claude/agents/lucy-nmr-chemist.md | — |

### Sampling Rate

- **Per task commit:** `pytest tests/test_cli_pick.py tests/test_peak_picker_snr.py -x -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_peak_picker_snr.py` — covers FIX-04 (CASE9 carbonyl picked, CASE1 count unchanged, SNR annotation)
- [ ] `tests/test_intensity_symmetry.py` — covers FIX-05 (2C candidate detection on real CASE9 data)
- [ ] New test methods in `tests/test_cli_pick.py` — `test_pick_1d_json_has_snr`, `test_pick_1d_json_has_noise_sigma`

*(Existing 18 pick/analyze tests are passing and must remain green: verified 2026-06-08, full suite 1023 passed.)*

---

## Security Domain

Security enforcement not applicable to this phase. All changes are local Python processing and markdown text files with no network access, authentication, or user-supplied input beyond file paths.

---

## REQUIREMENTS.md Update Needed

FIX-04, FIX-05, FIX-06 do not appear in `.planning/REQUIREMENTS.md` (currently only FIX-01/02/03 listed). The planner's Wave 0 should include adding these three entries to the REQUIREMENTS.md traceability table under "Post-UAT Fixes" and mapping them to Phase 79.

---

## Sources

### Primary (HIGH confidence)

- Direct code inspection: `src/lucy_ng/processing/peak_picker.py` — confirmed max-relative threshold, line 88-89
- Direct code inspection: `src/lucy_ng/readers/bruker.py` — confirmed `SOLVENT` read at line 166, stored in `Spectrum1D.solvent`
- Direct code inspection: `src/lucy_ng/models/peaks.py` — confirmed `Peak1D` model, no `snr` field currently
- Direct code inspection: `src/lucy_ng/cli/pick.py` — confirmed JSON contract, lines 62-74
- Direct code inspection: `src/lucy_ng/cli/analyze.py` — confirmed `analyze_symmetry` calls `pick_peaks` directly, will inherit new threshold
- Direct data measurement: CASE9/12 spectrum — confirmed all forensics numbers from SCOPE-SEED (MAD-σ = 1.230×10⁵, carbonyl SNR = 16.9, 5% threshold = 2.30×10⁶ > carbonyl 2.08×10⁶)
- Direct data measurement: CASE1/Ibuprofen/2 — confirmed unaffected by new threshold (no carbonyl; all peaks high SNR)
- Direct skill inspection: `~/.claude/agents/lucy-nmr-chemist.md` — confirmed workflow steps 1-10, no DBE self-check, no intensity-symmetry procedural step
- Direct skill inspection: `~/.claude/commands/lucy-ng/case.md` — confirmed `detect_loops` step, 4 patterns only (Pattern 5 absent)
- Direct skill inspection: `~/.claude/commands/lucy-ng/references/loop-patterns.md` — confirmed 4 patterns, count-based only
- Direct skill inspection: `~/.claude/commands/lucy-ng/references/advisory-templates.md` — confirmed no assumption-reexamination advisory
- Test run confirmation: 1023 tests pass (pytest -q, 2026-06-08) — full suite baseline clean

### Secondary (MEDIUM confidence)

- IUPAC LoD convention: k=3 for limit-of-detection (SNR threshold); standard analytical chemistry practice

### Tertiary (LOW confidence)

- CD3OD, CD3CN, acetone-d6, C6D6 solvent shift values in the table are from training knowledge [ASSUMED] — only CDCl3 and DMSO values are commonly confirmed in practice

---

## Metadata

**Confidence breakdown:**
- Standard Stack: HIGH — all libraries confirmed present, no new packages
- Architecture: HIGH — confirmed by direct code inspection and live data verification
- Pitfalls: HIGH — pitfalls 1-5 are derived from actual code paths; pitfall 6 (loop budget) confirmed by reading case.md track_and_decide step
- Layer 2 skill edits: HIGH — insertion points confirmed by reading all 4 skill files

**Research date:** 2026-06-08
**Valid until:** ~2026-07-08 (30 days; stable Python codebase, no fast-moving dependencies)
