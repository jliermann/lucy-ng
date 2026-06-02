# 78 — Pre-Run Sanitisation / Blindness Check

**Performed:** 2026-06-02 12:22 UTC
**By:** Tainted bookkeeper (orchestrating session)
**Purpose (D-78-02):** Confirm both datasets are free of compound-identity leakage and the
verification harness is operational *before* any blind run begins. The blind runs (Plan 02 /
Plan 03) MUST NOT proceed unless the Overall gate below reads **READY**.

---

## CASE1 — sanitised ibuprofen (C13H18O2)

**Formula file:** `molecular-formula.txt` → `C13H18O2` (formula is provided to the agent; acceptable).

**Title file checks** (`find CASE1 -name title`):

| Experiment | title content | name leak? |
|-----------|---------------|------------|
| 2/pdata/1 | `125.7 MHz 13C NMR Bruker AVANCE 500 (DRX)` | no |
| 3/pdata/1 | `125.7MHz 13C DEPT-135 Bruker AVANCE 500 (DRX)` | no |
| 4/pdata/1 | `125.7MHz 13C DEPT-90 Bruker AVANCE 500 (DRX)` | no |
| 5/pdata/1 | `gs-COSY90` | no |
| 6/pdata/1 | `gs-HMQC` | no |
| 7/pdata/1 | `gs-HMBC` | no |

**Whole-tree name grep:** `grep -ril "ibuprofen" CASE1/` → **0 matches**.

**Stray state:** `CASE1/.claude/` is empty; no prior `analysis/` directory present (fresh).

**Verdict: PASS** — already sanitised, no compound-name or structure leakage. Only the
molecular formula (intentionally provided) is present.

---

## CASE9 — C12H16O3 (para-aromatic, same 4J failure mode; identity bookkeeper-only)

**Formula file:** `molecular-formula.txt` → `C12H16O3` (provided to the agent; acceptable).

**Title file checks** (`find CASE9 -name title`):

| Experiment | title content | name leak? |
|-----------|---------------|------------|
| 1/pdata/1  | `1H - 400 MHz - CDCl3 - C12H16O3` | formula only — OK |
| 4/pdata/1  | `HC_HMBC_long CDCl3 {D:\Topspin} las 42` | no (operator code `las`) |
| 5/pdata/1  | `HC_HSQC` | no |
| 8/pdata/1  | `H,H-COSY` | no |
| 12/pdata/1 | `13C{1H} - 100 MHz - CDCl3 - C12H16O3` | formula only — OK |
| 13/pdata/1 | `13C_DEPT CDCl3 {D:\Topspin} las 55 …` | no (operator code `las`) |

**Name-fragment grep:** `grep -ril "isopropyl\|benzoic\|hydroxyethyl\|hydroxy.*benzo\|benzo.*ester\|propan-2-yl" CASE9/` → **0 matches**.

**Metadata audit (acqus / audita.txt):**
- `##$USERA1..5` fields: empty or literal `user` — no name.
- `##ORIGIN= Bruker BioSpin GmbH`, `##OWNER= nmr` — standard vendor fields.
- `##$EXP=` fields: experiment types only (`1H_zg30`, `13C_CPD_long`, `13C_DEPT`).
- acqus path tokens: `D:\Topspin/data/las/nmr/las_S013(_II)` — sample/dataset code, not a compound name.
- audita.txt `user comment:` blocks contain only `ICON-NMR User ID: las` (operator initials).

**Verdict: PASS** — no compound-name or structure leakage. Formula (`C12H16O3`, provided) is
the only chemical identifier present. No sanitisation remediation required.

---

## verify_case_solution.py — independent verification harness

- File exists at `scripts/verify_case_solution.py`: **yes**
- `python scripts/verify_case_solution.py --help` exit code: **0**
- CLI contract confirmed — positional args: `merged_smi`, `formula`
  (e.g. `python scripts/verify_case_solution.py <path>/solutions.smi C13H18O2`)
- Phase 78 must NOT modify this script (T-78-04) — read-only confirmation only. **PASS**

---

## Overall gate: **READY**

| Item | Verdict |
|------|---------|
| CASE1 identity audit | PASS |
| CASE9 identity audit | PASS |
| verify_case_solution.py | PASS |

All three checks pass. Both datasets are confirmed identity-clean (formula-only). The
independent verification harness is operational. **Blind runs (Plan 02 CASE1, Plan 03 CASE9)
may proceed.**

No leakage was found in either dataset, so no `/lucy-ng:sanitise` remediation was needed.
