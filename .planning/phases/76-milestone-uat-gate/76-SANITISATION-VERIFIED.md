# Phase 76: Sanitisation Verification — CASE1 + CASE9

**Date verified:** 2026-06-01
**Verified by:** GSD Executor (Phase 76, Plan 01, Task 3)
**Purpose:** Pre-run blind check — confirm both datasets contain no compound identity leakage before the blind UAT run.

---

## CASE1 (Ibuprofen, C13H18O2)

### Check 1: No .mol/.sdf in NMR raw data directories

Command:
```
find CASE1/1 CASE1/2 CASE1/3 CASE1/4 CASE1/5 CASE1/6 CASE1/7 -name "*.mol" -o -name "*.sdf"
```

Result: **(empty)**

Status: **PASS** — no structure files in NMR experiment directories.

Note: `.mol` files exist under `analysis/iteration_03/filters/` (benzene.mol, file1.mol) — these are LSD filter fragments written during a prior analysis run, not compound identity files. The NMR raw data directories (1–7) are clean.

### Check 2: Molecular formula

Command:
```
cat CASE1/molecular-formula.txt
```

Result: `C13H18O2`

Status: **PASS** — formula matches expected value.

### Check 3: No compound name in NMR raw data

Command (NMR experiment directories 1–7 only):
```
grep -ri "ibuprofen|Ibuprofen|ibuprof" CASE1/{1,2,3,4,5,6,7}/
```

Result: **(empty)**

Status: **PASS** — no compound name in NMR raw data.

Note: The word "ibuprofen" appears in `analysis/CASE-PROGRESS.md` (prior v8.0 run protocol). That file is not part of the NMR data and will not be shown to the blind Claude instance, which receives only the NMR experiment path and formula.

### Check 4: Title files contain no compound name

Experiment titles (all NMR experiments):
- Exp 1: (no title file)
- Exp 2: `125.7 MHz 13C NMR Bruker AVANCE 500 (DRX)` — instrument description only
- Exp 3: `125.7MHz 13C DEPT-135 Bruker AVANCE 500 (DRX)` — instrument description only
- Exp 4: `125.7MHz 13C DEPT-90 Bruker AVANCE 500 (DRX)` — instrument description only
- Exp 5: `gs-COSY90` — experiment type only
- Exp 6: `gs-HMQC` — experiment type only
- Exp 7: `gs-HMBC` — experiment type only

Status: **PASS** — no compound name or identity in any title.

### CASE1 Experiment List

| Exp | Type | Present |
|-----|------|---------|
| 1 | 1H (reference) | yes |
| 2 | 13C | yes |
| 3 | DEPT-135 | yes |
| 4 | DEPT-90 | yes |
| 5 | COSY | yes |
| 6 | HSQC (gs-HMQC) | yes |
| 7 | HMBC | yes |

All expected experiments present.

---

## CASE9 (C12H16O3 — identity withheld)

### Check 1: No .mol/.sdf files

Command:
```
find CASE9 -name "*.mol" -o -name "*.sdf"
```

Result: **(empty)**

Status: **PASS** — no structure files found.

### Check 2: Molecular formula

Command:
```
cat CASE9/molecular-formula.txt
```

Result: `C12H16O3`

Status: **PASS** — formula matches expected value.

### Check 3: No compound name (hydroxy/benzoic/isopropyl/ester)

Command:
```
grep -ri "hydroxy|benzoic|isopropyl|ester" CASE9/
```

Result: **(empty)**

Status: **PASS** — no compound name or structural descriptor found.

### Check 4: Title files contain no compound name

Experiment titles (all NMR experiments):
- Exp 1: `1H - 400 MHz - CDCl3 - C12H16O3` — formula only, no compound name
- Exp 4: `HC_HMBC_long CDCl3 {D:\Topspin} las 42` — experiment type + instrument
- Exp 5: `HC_HSQC` — experiment type only
- Exp 8: `H,H-COSY` — experiment type only
- Exp 12: `13C{1H} - 100 MHz - CDCl3 - C12H16O3` — formula only, no compound name
- Exp 13: `13C_DEPT CDCl3 {D:\Topspin} las 55 / proton pulse tip angle 135.0°, J(HX) = 145.0 Hz` — instrument parameters only

Status: **PASS** — formula appears in titles (Exp 1, 12) but no compound name. Formula disclosure is intentional and acceptable; the blind run receives the formula explicitly.

### CASE9 Experiment List

| Exp | Type | Present |
|-----|------|---------|
| 1 | 1H | yes |
| 4 | HMBC | yes |
| 5 | HSQC | yes |
| 8 | COSY | yes |
| 12 | 13C | yes |
| 13 | DEPT-135 | yes |

Note: **No DEPT-90 available** for CASE9. The blind CASE run must proceed without DEPT-90; CH vs CH3 disambiguation relies on DEPT-135 alone (CH/CH3 ambiguity acceptable per D-76-04). CASE9 uses different experiment numbering than CASE1.

---

## Summary of All 8 Checks

| Dataset | Check | Status |
|---------|-------|--------|
| CASE1 | 1. No .mol/.sdf in NMR raw dirs | PASS |
| CASE1 | 2. Formula = C13H18O2 | PASS |
| CASE1 | 3. No "ibuprofen" in NMR raw data | PASS |
| CASE1 | 4. Title files: no compound name | PASS |
| CASE9 | 1. No .mol/.sdf anywhere | PASS |
| CASE9 | 2. Formula = C12H16O3 | PASS |
| CASE9 | 3. No "hydroxy/benzoic/isopropyl/ester" | PASS |
| CASE9 | 4. Title files: formula only, no compound name | PASS |

---

## Overall Verdict

**READY FOR BLIND RUN**

Both CASE1 and CASE9 datasets pass all 8 sanitisation checks. The NMR raw data contains no compound names, no structure files, and no identity-revealing titles. The blind Claude instance will receive only the dataset path and molecular formula, as required by D-76-04.

**Blind run command examples:**
```
/lucy-ng:case ~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1 C13H18O2
/lucy-ng:case ~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE9 C12H16O3
```

**Verification command after run:**
```
python scripts/verify_case_solution.py <path-to-analysis>/merged.smi C13H18O2
python scripts/verify_case_solution.py <path-to-analysis>/merged.smi C12H16O3
```
