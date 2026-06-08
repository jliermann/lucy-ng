# Phase 79: Peak-Picking & Symmetry Detection Fix - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Eliminate the CASE9 failure mode at **two layers**:

- **Layer 1 (Tooling):** the peak-picker no longer masks weak quaternary carbonyls under a
  solvent-dominated threshold, and 13C intensity-symmetry is used to detect equivalent aromatic
  carbons that feed the (untouched) emergent-COSY mechanism.
- **Layer 2 (Skill feedback loop):** the CASE skill gains a sensor for a *clean-but-wrong*
  convergence so it returns to its assumptions instead of silently terminating.

**Out of scope (do NOT touch):** the Phase-77 emergent-COSY mechanism
(`detect_aromatic_cosy_pairs`) is NOT refuted — it never got correct input. This phase only feeds
it correctly. No LSD-mechanism changes, no ring-BOND/SKEL forcing as a primary path.

Verified by a blind CASE9 re-run reaching a para-disubstituted aromatic-ester C12H16O3 solution via
the emergent path, then re-applying the Phase-78 AND-gate.
</domain>

<decisions>
## Implementation Decisions

### Layer 1 — Peak-picker threshold & solvent masking (FIX-04)
- **D-01:** Replace the max-relative threshold (`abs_threshold = threshold * np.max(np.abs(data))`
  in `peak_picker.py`) with an **SNR/MAD-absolute** threshold (noise = 1.4826·MAD; emit peaks
  above `k·noise`). Solvent-agnostic and leaves CASE1 picking unchanged.
- **D-02:** Additionally **exclude the solvent multiplet** (CDCl₃ ~77 ppm) *before* computing any
  threshold/scale (belt-and-suspenders; collapses the inflated `max`).
- **D-03:** **Solvent detection** = read `SOLVENT` from Bruker `acqus` → known solvent-shift table
  (CDCl₃ 77.16 t, DMSO 39.5 sep, MeOD, D₂O, …). ppm-heuristic (~77 ppm) only as fallback when the
  param is absent.
- **D-04 (KEY — Steinbeck refinement):** **No hard-wired chemical threshold.** The picker answers
  only the *statistical* question "is this distinguishable from noise?" → emits **all peaks at
  SNR ≥ 3** (IUPAC limit-of-detection convention, not a tuned magic number) and **annotates every
  peak with its SNR**. The carbonyl at SNR ≈ 17 is then trivially included (5–6× margin). The
  *chemical* judgment about borderline/weak signals is **agentic** (nmr-chemist), not in the tool.
  Rationale: "no chemist would miss a peak sitting that cleanly above noise" — the fragility was
  never in the SNR cutoff, it was in benchmarking against `max` instead of noise.

### Layer 1 — Intensity-symmetry detection (FIX-05)
- **D-05:** Use **13C peak intensity normalized within multiplicity class** (compare arom-CH vs
  arom-CH): a signal at ~2× the median 1C intensity of its class = a **2C-equivalence candidate**.
  Class-binding sidesteps the quaternary T1/NOE unreliability.
- **D-06:** **Scope = protonated aromatic CH only** (where 13C intensity is reliable and exactly
  what the emergent-COSY mechanism needs). Symmetric Cq pairs are NOT treated as reliable
  equivalence. Output feeds `lucy analyze symmetry` / `lucy detect aromatic-cosy`.
- **D-07:** Detection must be **formula-aware in interpretation** (do we expect notoriously weak
  C=O/amide from the formula?) — but per D-11 this plausibility reasoning is the *agent's*, fed by
  a deterministic tool signal.

### Layer 2 — DBE self-check (FIX-06, part 1)
- **D-08:** **General DBE balance**, not carbonyl-only. Check: "is the DBE fully accounted for by
  what was found (rings + C=C + C=O + C=N + aromatics)?" On a deficit, derive **from the molecular
  formula where the missing unsaturation should appear** — O → carbonyl 160–220 ppm; N →
  amide/nitrile/imine regions — and report whether that region is suspiciously empty. Covers CASE9
  (O) and future N-containing cases (SCOPE-SEED Q4 = yes, cover N).
- **D-09:** The DBE self-check is **procedural/mandatory** in the nmr-chemist workflow after
  picking, before `[SETUP-COMPLETE]` (per Success Criterion 3) — not an optional note.

### Layer 2 — Quality loop-pattern (FIX-06, part 2)
- **D-10:** New **5th loop-pattern**. **Trigger = all top-K solutions IMPLAUSIBLE/QUESTIONABLE**
  (solution-analyst verdict, the most reliable signal) as primary; **best-MAE > tier threshold**
  as an additional OR-trigger. Do NOT wait N iterations — the clean-but-bad convergence *is* the
  signal (MAE alone is too noisy: a coincidentally low MAE on a wrong structure is the CASE9 trap).
- **D-11:** **Action = assumption re-examination** (reactivate nmr-chemist to re-check the
  *interpretation*: para-symmetry reading correct? multiplicities right? DBE fully explained?).
  A renewed low-threshold re-pick only **if a concrete suspicion exists** (empty region despite DBE
  deficit) — a blind re-pick is pointless since the floor is already at SNR ≥ 3.
- **D-12:** **Budget = exactly 1 re-look cycle**, then honest termination ("assumptions checked,
  still no plausible solution — additional experiments may be needed"). Prevents infinite re-pick.

### Tooling vs skill boundary (SCOPE-SEED Q2)
- **D-13:** **(B)+(A) split.** Tooling emits **deterministic sensor signals** (per-peak SNR;
  DBE-deficit + empty expected-region flag). The **decision** (re-pick? trust the symmetry?
  terminate?) stays **agentic** in the nmr-chemist skill. The agent is never blind, but the NMR
  judgment is not hard-coded.

### Claude's Discretion
- Exact `k` for the SNR floor is fixed at the IUPAC LoD convention (k = 3); the picker stays
  generous and reports SNR — planner/executor may choose the MAD implementation details.
- Solvent-shift table breadth (which solvents beyond CDCl₃/DMSO/MeOD/D₂O) — planner's call,
  driven by what the test/regression set needs.
- How the per-peak SNR annotation surfaces through the `lucy pick 1d` CLI/JSON contract.
- Regression-test construction (assert CASE9 carbonyl picked AND CASE1 picking unchanged).
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & forensics
- `.planning/phases/79-peak-picking-symmetry-fix/79-SCOPE-SEED.md` — two-layer scope, candidate
  fixes, the 4 open questions (all now answered in this CONTEXT.md)
- `.planning/phases/78-blind-re-uat-gate/78-UAT-CASE9.md` — CASE9 failure forensics
- `.planning/phases/78-blind-re-uat-gate/78-UAT-VERDICT.md` — AND-gate verdict, why v9.0 did not ship
- `.planning/ROADMAP.md` §"Phase 79" (lines 398–429) — Goal, FIX-04/05/06, 5 Success Criteria

### Layer 1 — tooling code to change
- `src/lucy_ng/processing/peak_picker.py` — current max-relative threshold
  (`np.max(np.abs(data))`); target of the SNR/MAD + solvent-exclusion rework
- `src/lucy_ng/cli/analyze.py` (`analyze_symmetry`, line ~35) — symmetry CLI surface
- `src/lucy_ng/cli/detect.py` (`aromatic-cosy`, lines ~200–245) — consumes grouping/symmetry
- `src/lucy_ng/lsd/generator.py` (`detect_aromatic_cosy_pairs`, line ~605) — **DO NOT MODIFY**;
  emergent mechanism, only feed correctly

### Layer 2 — skill files to extend (feedback loop)
- `~/.claude/agents/lucy-nmr-chemist.md` — add procedural DBE self-check + mandatory
  intensity-symmetry check after picking
- `~/.claude/commands/lucy-ng/case.md` (`detect_loops`) — wire the 5th loop-pattern
- `~/.claude/commands/lucy-ng/references/loop-patterns.md` — define the quality loop-pattern
- `~/.claude/commands/lucy-ng/references/advisory-templates.md` — advisory that reactivates nmr-chemist
- `~/.claude/agents/lucy-solution-analyst.md` — supplies the IMPLAUSIBLE/QUESTIONABLE verdict trigger

### Blind re-UAT
- `feedback_blind_uat` memory — CASE9 re-run MUST be a fresh blind instance; merged.smi verified
  independently via RDKit; this (bookkeeper) instance is tainted and acts only as bookkeeper
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `peak_picker.py` already computes a MAD-like structure and FWHM; the SNR/MAD noise estimate
  (1.4826·MAD) can replace `np.max(np.abs(data))` with minimal surface change.
- `detect_aromatic_cosy_pairs(groups)` (generator.py:605) already does cross-ring pairing
  (`zip(sorted(A), reversed(sorted(B)))`) — it just needs correct equivalence groups as input.
- `lucy detect aromatic-cosy` CLI is the authoritative cross-ring-pair source (Phase 77-02).

### Established Patterns
- Detection is currently "ONCE per compound, before first LSD iteration" (nmr-chemist Section 5) —
  fire-and-forget; Layer 2 deliberately adds a bounded return path.
- The 4 existing loop-patterns key on `solution_count`; the new pattern keys on **solution
  quality** (analyst verdict) — a new dimension, additive.

### Integration Points
- `lucy pick 1d` JSON contract gains per-peak SNR annotation (D-04).
- Bruker `acqus` SOLVENT parsing — confirm the reader exposes it; add if missing.

### Forensics anchors (CASE9 13C, dataset `.../CASE9/12`)
- 32768 pts; MAD-noise = 1.230e5; max = 4.591e7 (CDCl₃ triplet @77 ppm).
- Ester C=O 166.08 ppm, int 2.08e6 → SNR ≈ 17; default `5%·max` = 2.30e6 → masks it.
- 2C aromatics: 129.94 (1.81e7) ≡, 125.31 (1.72e7) ≡; isopropyl (CH₃)₂ 22.10 (1.70e7);
  two Cq 150.80/130.16 (~3e6).
</code_context>

<specifics>
## Specific Ideas

- **CASE9 provenance (for the record):** CASE9 = **4-(1-Hydroxyethyl)benzoic acid isopropylester**
  (C12H16O3). Source = the **teaching-datasets-1-university-of-duisburg-essen** collection, nmrXiv
  project UUID `b6c3016d-fc0c-4559-bbab-df8f56b834e4`. NOT discoverable via the public nmrXiv
  search/list API (likely unpublished) — no public P-identifier/DOI available; only the internal
  UUID. Operator tags `las 42` / `las 55`.
- Steinbeck's framing for D-04: a chemist reads SNR against *local noise*, never against the
  largest peak in the spectrum. Keep the tool statistical, keep chemistry agentic.
</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (The picker philosophy, symmetry source, loop bounds,
and DBE scope all clarify HOW to implement the already-scoped two-layer fix.)
</deferred>

---

*Phase: 79-peak-picking-symmetry-fix*
*Context gathered: 2026-06-08*
