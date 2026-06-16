---
phase: 84-aromatize-smiles-before-prediction
verified: 2026-06-16T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
---

# Phase 84: Aromatize SMILES Before 13C Prediction (FIX-11) Verification Report

**Phase Goal:** Kekulé SMILES (as emitted by `outlsd`) must be RDKit-perceived as aromatic before HOSE generation, so a Kekulé benzene predicts identically to its canonical aromatic form. Code change is hardening (explicit, tested `SetAromaticity`) + a pin test; the actual recurrence fix is the compound-agnostic solution-analyst skill note. Must preserve "HOSE = no explicit H" (no AddHs).
**Verified:** 2026-06-16
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `prepare_mol` explicitly enforces aromaticity before HOSE; no AddHs (RemoveHs preserved downstream) | ✓ VERIFIED | hose.py:116-122 `Chem.MolFromSmiles` → None-guard → `Chem.SetAromaticity(mol)`. No AddHs anywhere (only docstring/comment stating "no AddHs"). predictor.py:116 `Chem.RemoveHs(mol)` preserves no-explicit-H downstream. |
| 2 | Guard test genuinely exercises the fix; pin test honestly framed | ✓ VERIFIED | test_prediction.py:35-74 builds un-aromatized mol (`MolFromSmiles(sanitize=False)` + `SanitizeMol(SANITIZE_ALL ^ SANITIZE_SETAROMATICITY)`), asserts 0 aromatic, then `prepare_mol` → 6 aromatic + `*C` + no H. Pin test :76-113 documents "passes WITH OR WITHOUT the SetAromaticity change… NOT a pre-fix failure." |
| 3 | ranker.py:66/157 carry FIX-11 out-of-scope comments, no behavior change | ✓ VERIFIED | ranker.py:66-69 (DBE check) and :160-162 (has_aromatic check) both carry FIX-11 scope comments; `grep -c FIX-11` = 2; underlying `Chem.MolFromSmiles` calls unchanged. |
| 4 | solution-analyst skill note added, compound-agnostic (FIX-09 grep gate = 0) | ✓ VERIFIED | lucy-solution-analyst.md:91 "Canonicalize before predicting" paragraph. FIX-09 grep gate N=0 (GREP-GATE-CLEAN); no compound names / ppm / CASE / FIX-IDs / answer SMILES. |
| 5 | No regression: no-explicit-H intact; no new ruff/mypy in touched files; full suite green | ✓ VERIFIED | Full suite 1081 passed, 7 skipped, 1 xfailed, 0 failures (exit 0). ruff: hose.py 0, ranker.py 0, test_prediction.py 3 (all pre-existing at lines 3/147/712, none in guard/pin tests; SUMMARY baseline 4→3). mypy: hose.py/ranker.py findings all pre-existing GetAtoms/import-stub patterns outside prepare_mol; ranker.py:165 is the unchanged has_aromatic line shifted +3 by the comment. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/prediction/hose.py` | prepare_mol with explicit SetAromaticity, no AddHs | ✓ VERIFIED | SetAromaticity at :121; choke point used by predictor.py:86 |
| `tests/test_prediction.py` | guard (sanitize=False restoration) + pin tests | ✓ VERIFIED | both present (:35, :76); `sanitize=False` + `SANITIZE_SETAROMATICITY` present; 48 passed in file |
| `.claude/agents/lucy-solution-analyst.md` | compound-agnostic canonicalize-before-predict note | ✓ VERIFIED | :91; symlinked from ~/.claude/agents; FIX-09 N=0 |
| `src/lucy_ng/ranking/ranker.py` | two FIX-11 scope comments | ✓ VERIFIED | :66-69 and :160-162; grep -c FIX-11 = 2 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| predictor.predict_from_smiles | hose.prepare_mol | `HOSECodeGenerator.prepare_mol(smiles)` | ✓ WIRED | predictor.py:86 |
| ranker.rank | predict_from_smiles | `self.predictor.predict_from_smiles(solution.smiles)` | ✓ WIRED | ranker.py:140 |
| predict_from_mol | no-explicit-H invariant | `Chem.RemoveHs(mol)` | ✓ WIRED | predictor.py:116 |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Independent guard reproduction | build un-aromatized mol → prepare_mol | un-arom=0, prepare_mol=6 aromatic, 0 explicit H, ring HOSE `C-3;*C*CC(*C,*C,CO//)` (contains `*C`), prepare_mol(invalid)=None | ✓ PASS |
| Prediction test file | `pytest tests/test_prediction.py -q` | 48 passed | ✓ PASS |
| Full suite | `pytest -q` | 1081 passed, 7 skipped, 1 xfailed, 0 failures | ✓ PASS |
| FIX-09 grep gate | plan Task 3 grep on skill file | N=0 (GREP-GATE-CLEAN) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| FIX-11 | 84-01 | Aromatize Kekulé SMILES before 13C prediction (hardening + pin + skill note) | ✓ SATISFIED | SetAromaticity in prepare_mol; guard+pin tests; skill note; ranker scope comments |

### Anti-Patterns Found

None. No TBD/FIXME/XXX in touched files. The "AddHs" occurrences in hose.py are negative references (docstring + comment stating the invariant). The guard/pin tests are substantive (independently reproduced).

### Human Verification Required

None. All criteria verified programmatically: code-level (SetAromaticity, no AddHs, RemoveHs, FIX-11 comments), live test execution (full suite + independent guard reproduction), and the FIX-09 grep gate. The skill note is a documentation change verified by content + grep gate; no runtime behavior to UAT in this phase.

### Gaps Summary

No gaps. The phase delivers exactly its honest scope:
- Hardening: `prepare_mol` now calls `Chem.SetAromaticity` explicitly (pins aromatization against RDKit default drift / future sanitize=False refactor), with the no-explicit-H invariant preserved.
- Pin: the guard test genuinely reaches an un-aromatized state and proves restoration (independently reproduced: 0 → 6 aromatic, `*C` marker); the pin test is honestly framed as documenting the pre-existing guarantee, not claiming a pre-fix failure.
- Real fix: the compound-agnostic solution-analyst note (canonicalize/aromatize before predicting), FIX-09 grep gate clean.
- No regression: full suite 1081 passed; no new ruff/mypy errors in touched files.

---

_Verified: 2026-06-16_
_Verifier: Claude (gsd-verifier)_
