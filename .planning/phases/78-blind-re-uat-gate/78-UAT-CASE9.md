---
phase: 78-blind-re-uat-gate
requirement: UAT-04
compound: CASE9
formula: C12H16O3
verdict: FAIL
run_date: 2026-06-03
bookkeeper_forensics_date: 2026-06-08
---

# 78 — CASE9 Blind UAT Evidence Record (UAT-04)

**Run date:** 2026-06-03 (CASE Team v4.0, blind session via `/lucy-ng:case`)
**Compound:** CASE9 — C12H16O3 (true structure bookkeeper-only: 4-(1-hydroxyethyl)benzoic
acid isopropyl ester, para-disubstituted benzene with an ester carbonyl)
**Blind handoff:** `/lucy-ng:case …/CASE9 C12H16O3`
**Bookkeeper:** tainted orchestrating session — all criteria measured from on-disk artifacts
(`…/CASE9/analysis/`), never from agent self-report (D-78-03). Forensic root-cause added
2026-06-08.

---

## Verdict: **UAT-04 = FAIL**

The blind run did **not** reach the correct structure. It terminated after 5 iterations with an
explicit "Offene Frage / Grund des Stopps" (open question / reason for stopping) in
`CASE-PROGRESS.md`, having mis-interpreted the spectra. The benzene ring appeared only via a
**forced 6-fold ring-BOND escalation** (D-04), not emergently. The failure traces to an
**upstream peak-picking / symmetry-detection defect**, not to the Phase-77 LSD mechanism.

---

## Run narrative (from on-disk artifacts)

Five iterations, non-monotone: **211 → 4 → 18 → 12 → (iter 5 incomplete)**.

| Iter | Key constraints | Solutions | Aromatic | Assessment |
|------|-----------------|-----------|----------|------------|
| 1 | HMBC×5, BOND 1-13 (aryl-O), ring-excl | 211 | none ranked | baseline, non-aromatic |
| 2 | + COSY 9-10 | 4 | none ranked | 98% reduction, still wrong |
| 3 | + aromatic COSY, separate O-BONDs | 18 | none ranked | clean Option A/C; counter 3/3 |
| 4 | **+ 6 ring-BONDs (D-04 escalation)** | 12 | **12/12** | ring forced; best MAE 4.86 ppm |
| 5 | BOND 1-13→1-7 (alkylbenzene), no COSY 9-10 | 15 (5 clean) | yes | clean solutions are acetals (disproven); **no solutions.smi written** |

iteration_05 contains only `compound.lsd` — no `.sol`/`.smi`. The last evaluated iteration is 04.

---

## Criterion 1 — Solve correctness: **FAIL (correct structure never reached)**

**Final evaluated solutions:** `…/CASE9/analysis/iteration_04/solutions.smi` (12 solutions).

```
python scripts/verify_case_solution.py …/CASE9/analysis/iteration_04/solutions.smi C12H16O3
```
**Exit code:** 0 — `"pass": true`. **But the harness only checks formula + presence of an
aromatic ring, not structural correctness.** All 12 solutions are monosubstituted
phenyl-ether / acetal scaffolds, e.g. `C1=CC=C(C=C1)OC(C)C(C)(O2)CCO2`. **None contains an
ester group; none is para-disubstituted.** The true structure
(`CC(O)c1ccc(C(=O)OC(C)C)cc1`) is **absent from every iteration**, not merely outside the top-3.

→ Letter of D-76-06 ("some aromatic C12H16O3 isomer in top-3") is met; **spirit fails** — same
distinction that failed CASE1 in Phase 76.

---

## Criterion 2 — Native-only emission / mechanism: **CONDITIONAL → counts as FAIL in context**

Final emitted LSD (iter 5): `SYME=0`, `DEFF NOT=0`, `SKEL=0` ✓ (native-only). **But:** the
benzene ring is established by **6 explicit ring-BONDs** (`BOND 1 2 / 1 3 / 2 4 / 3 5 / 4 6 /
5 6`), documented in `CASE-PROGRESS.md` as a D-04 escalation after 3 ranked non-aromatic
iterations. Per D-77-06 this is the **CONDITIONAL PASS (documented escalation)** tier — *not*
the clean EMERGENT pass that CASE1 achieved.

**Why the canonical emergent mechanism never fired:** `lucy detect aromatic-cosy` returned **no
equivalence pairs** for CASE9. The nmr-chemist read the ring as **monosubstituted** (5 CH + 1
Cq) → no symmetric C-pairs → no cross-ring COSY input → emergent ring impossible → forced BONDs.

---

## Criterion 3 — No path-changing intervention: **FAIL**

`CASE-PROGRESS.md` records a **"Governance-Deadlock"** in iteration 3, escalated to the user, who
imposed a "STRIKTE POLICY-EINHALTUNG" decision that re-routed the run strategy
(D-04 rollback, restore Option A/C). Additionally an **outlsd `#`-comment parse bug** struck
iteration 1 (solver produced 211 solutions per `solncounter` but outlsd rejected the `.sol`
until comments were stripped) — the same class of plumbing fragility Phase 77 targeted.

---

## Criterion 4 — AND-gate contribution: **FAIL**

CASE9 fails C1 (correct structure never reached), C2 is only conditional, and C3 fails. UAT-04 =
**FAIL**.

---

## Root-cause forensics (bookkeeper, 2026-06-08)

Both failure questions resolve to a **single upstream defect**, proven from the raw 13C
spectrum (`…/CASE9/12`):

### Finding 1 — the ester carbonyl is in the spectrum but the peak-picker dropped it
- Real signal at **166.08 ppm, SNR ≈ 17** (intensity 2.08e6; MAD-noise 1.23e5).
- `lucy pick 1d` (default) does **not** list it. The effective threshold sits between 2.08e6
  and 2.72e6 because the **CDCl₃ triplet at 77 ppm (4.6e7)** dominates the scale and the
  max-relative threshold drops the weak quaternary carbonyl. (130.16 @ 2.86e6 is picked;
  166.08 @ 2.08e6 is not.)
- Consequence: DBE = 5 is computed **without** the carbonyl → benzene (4) + a forced extra
  ring → the entire "aliphatic O-ring / acetal" mis-hypothesis.

### Finding 2 — the para-symmetry is encoded in peak intensities but was ignored
| 13C peak | intensity | truth | nmr-chemist read |
|----------|-----------|-------|------------------|
| 129.94 | **1.81e7 (~2×)** | CH pair (2C) — equivalence pair | "meta-CH ×2" (coincidentally 2C) |
| 125.31 | **1.72e7 (~2×)** | CH pair (2C) — equivalence pair | "para-CH 1C" ✗ |
| 22.10 | **1.70e7 (~2×)** | isopropyl (CH₃)₂ — 2C | — |
| 150.80 | 3.3e6 (1×) | Cq (ipso-alkyl) | Cq ipso ✓ |
| 130.16 | 2.9e6 (1×) | **Cq (ipso-COO)** | "ortho-CH ×2" ✗ |

The 13C intensity doubling (2C signals) was not used as a symmetry indicator. The ring was
read as monosubstituted instead of para-disubstituted.

### Causal chain
```
carbonyl masked (CDCl3-relative threshold)  ─┐
                                              ├─→ monosubst. instead of para-disubst.
intensity-symmetry not used  ────────────────┘
   → no equivalent C-pairs
   → `lucy detect aromatic-cosy` returns nothing
   → emergent-ring mechanism has no input
   → ring-BOND escalation (D-04)
   → structure space shifted to phenyl-ether/acetal → correct structure unreachable
```

**Key point:** the Phase-77 emergent-COSY mechanism is **not refuted** — given correct
para-symmetry input (pairs 129.94≡, 125.31≡) it would have fired exactly as it did for CASE1.
CASE1 did not hit this defect because it has no weak quaternary carbonyl hidden in the CDCl₃
shadow.

### Two concrete, fixable tooling defects (→ Phase 79)
1. **Peak-picker:** use an SNR-based (not max-relative) threshold, or exclude the CDCl₃
   solvent multiplet before computing the threshold → weak quaternary carbonyls no longer
   masked.
2. **Symmetry detection:** use 13C peak intensity as an equivalence indicator (detect 2C
   signals) → feeds `lucy detect aromatic-cosy` so para-symmetry yields cross-ring COSY pairs.

---

## Evidence index (all on-disk)
- `…/CASE9/analysis/CASE-PROGRESS.md` — run log, governance-deadlock, D-04 escalation, self-rated CONDITIONAL PASS
- `…/CASE9/analysis/final_results.md` — iteration ranking table, all-acetal outcome
- `…/CASE9/analysis/iteration_04/solutions.smi` — 12 finals (verify_case_solution.py exit 0, formula+aromatic only)
- `…/CASE9/analysis/iteration_05/compound.lsd` — 6 forced ring-BONDs (D-04), SYME/DEFF NOT/SKEL=0
- `…/CASE9/12` (raw 13C) — carbonyl 166.08 ppm SNR≈17 (picker miss); intensity-symmetry of 129.94/125.31/22.10
