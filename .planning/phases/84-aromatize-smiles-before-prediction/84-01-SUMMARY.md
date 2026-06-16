---
phase: 84-aromatize-smiles-before-prediction
plan: 01
subsystem: prediction
tags: [prediction, hose, aromaticity, rdkit, skill-hygiene, FIX-11]
requires:
  - "HOSECodeGenerator.prepare_mol (prediction choke point)"
  - "predict_from_smiles routing (predictor.py:86, ranker.py:137)"
provides:
  - "Hardened prepare_mol: explicit Chem.SetAromaticity, no-explicit-H preserved"
  - "Guard + pin tests for Kekulé aromatization"
  - "Compound-agnostic solution-analyst canonicalize-before-predict note"
affects:
  - "lucy predict c13 and lucy lsd rank (both route through prepare_mol)"
tech-stack:
  added: []
  patterns:
    - "Explicit aromaticity perception at the prediction choke point instead of relying on implicit RDKit default sanitization"
key-files:
  created: []
  modified:
    - "src/lucy_ng/prediction/hose.py (prepare_mol hardened)"
    - "src/lucy_ng/ranking/ranker.py (FIX-11 scope comments at :66 and :157 region)"
    - "tests/test_prediction.py (guard + pin tests)"
    - ".claude/agents/lucy-solution-analyst.md (skill note; symlink target of ~/.claude/agents/lucy-solution-analyst.md)"
decisions:
  - "prepare_mol enforces Chem.SetAromaticity explicitly (hardening + pin), not a behavioral bug fix — the RDKit default already aromatizes the real Kekulé form"
  - "No MolToSmiles round-trip in production prepare_mol (avoids extra parse)"
  - "ranker.py:66/157 left as default-sanitize MolFromSmiles, documented as outside FIX-11 scope"
  - "No AddHs — no-explicit-H HOSE invariant preserved (CLAUDE.md)"
metrics:
  duration: ~10m
  completed: 2026-06-16
  tasks: 3
  files: 4
---

# Phase 84 Plan 01: Aromatize SMILES Before Prediction Summary

Hardened the 13C-prediction choke point (`HOSECodeGenerator.prepare_mol`) to explicitly enforce aromaticity perception via `Chem.SetAromaticity`, pinning the guarantee that Kekulé-form solver SMILES are aromatized before HOSE generation, and added the compound-agnostic solution-analyst skill note that is the actual fix for the FIX-11 agent-side false-escalation incident.

## What Was Built

- **`prepare_mol` hardening (Task 2):** After `Chem.MolFromSmiles(smiles)` (implicit H, no `AddHs`), guard the `None` case, then call `Chem.SetAromaticity(mol)` before returning. Kekulé rings (e.g. `outlsd` output `CC(O)C(=C1)C=CC(=C1)C(=O)OC(C)C`) are now explicitly aromatized regardless of parser-default drift. Signature/return type unchanged; no-explicit-H invariant preserved (downstream `Chem.RemoveHs` at predictor.py:116 still enforces it).
- **Ranker scope notes (Task 2):** `ranker.py` `MolFromSmiles` calls in the DBE check (`is_plausible`) and the `has_aromatic` check carry one-line comments stating they rely on RDKit default sanitization and are intentionally outside FIX-11 scope (`grep -c FIX-11 ranker.py` == 2). No behavioral change.
- **Guard + pin tests (Task 3):**
  - `test_prepare_mol_restores_aromaticity_on_unaromatized_input` — proves an un-aromatized state is reachable (`MolFromSmiles(..., sanitize=False)` + `SanitizeMol(SANITIZE_ALL ^ SANITIZE_SETAROMATICITY)` → 0 aromatic atoms), then asserts `prepare_mol` restores 6 aromatic ring atoms with an aromatic-carbon HOSE `*C` marker and no explicit H. This is the test that actually exercises `SetAromaticity` and would fail if it were removed under a parser-default drift.
  - `test_kekule_predicts_like_canonical_aromatic` — pin test: Kekulé and canonical forms canonicalize identically, both aromatic, identical ring-carbon HOSE multiset, no explicit H. Inline comment documents it passes with or without the fix (existing library guarantee, honest framing).
- **Solution-analyst skill note (Task 3):** A compound-agnostic paragraph in Section 3 of `.claude/agents/lucy-solution-analyst.md` instructing canonicalize/aromatize-before-predict (un-aromatized ring → non-aromatic diene → wrong shifts → false implausibility verdict). No compound names, ppm values, CASE/phase/FIX IDs, or answer-key SMILES.

## Verification Results

- **Task 1 (investigation):** confirmed `MolFromSmiles(kekulé)` → 6 aromatic atoms (default sanitize), `sanitize=False` → 0; `prepare_mol` is the choke point; `RemoveHs` enforces no-explicit-H downstream; ranker.py:66/157 are direct `MolFromSmiles` outside scope.
- **Task 2:** inline assert OK (6 aromatic, no H, None on invalid); `grep -c FIX-11 ranker.py` == 2; `SetAromaticity` present in hose.py.
- **Task 3:** `pytest tests/test_prediction.py` → 48 passed; FIX-09 grep gate on skill file → N=0 (clean).
- **Full suite:** `pytest -q` → 1074 passed, 14 skipped, 1 xfailed, 0 failures.
- **Ruff (touched files vs baseline):** hose.py 0→0, ranker.py 0→0, test_prediction.py 4→3 (no NEW errors; count decreased). No new ruff errors.
- **Mypy:** no new errors. `ranker.py:165` `GetAtoms()` finding is pre-existing (the `has_aromatic` line, shifted down 3 lines by the comment insertion); `orchestrator.py` findings are untouched/pre-existing.

## Deviations from Plan

None — plan executed exactly as written.

## Authentication Gates

None.

## Self-Check: PASSED

- src/lucy_ng/prediction/hose.py — FOUND (contains SetAromaticity)
- src/lucy_ng/ranking/ranker.py — FOUND (2× FIX-11)
- tests/test_prediction.py — FOUND (guard + pin tests, sanitize=False)
- .claude/agents/lucy-solution-analyst.md — FOUND (canonicalize note, grep gate N=0)
- Commit 0a9e3fe — present (fix: prepare_mol hardening + ranker notes)
- Commit 8571bb4 — present (test: guard/pin + skill note)
