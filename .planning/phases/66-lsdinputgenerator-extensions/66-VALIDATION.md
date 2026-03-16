---
phase: 66
slug: lsdinputgenerator-extensions
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 66 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_lsd_generator.py tests/test_lsd_models.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_lsd_generator.py tests/test_lsd_models.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 66-01-01 | 01 | 1 | INPUT-04 | unit | `pytest tests/test_lsd_models.py -k "hmbc_extended" -x` | W0 | pending |
| 66-01-02 | 01 | 1 | INPUT-04 | regression | `pytest tests/test_lsd_models.py::TestLSDCorrelation::test_to_lsd_line_hmbc -x` | yes | pending |
| 66-02-01 | 02 | 2 | INPUT-01 | unit | `pytest tests/test_lsd_generator.py -k "form" -x` | W0 | pending |
| 66-02-02 | 02 | 2 | INPUT-02 | unit | `pytest tests/test_lsd_generator.py -k "elim" -x` | W0 | pending |
| 66-02-03 | 02 | 2 | INPUT-03 | unit | `pytest tests/test_lsd_generator.py -k "shih" -x` | W0 | pending |
| 66-02-04 | 02 | 2 | INPUT-03 | regression | `pytest tests/test_lsd_generator.py::TestLSDInputGeneratorBasic::test_generate_with_chemical_shifts -x` | yes | pending |
| 66-02-05 | 02 | 2 | INPUT-01 | unit | `pytest tests/test_lsd_generator.py -k "pylsd_form" -x` | W0 | pending |
| 66-02-06 | 02 | 2 | INPUT-02 | unit | `pytest tests/test_lsd_generator.py -k "elim_commands" -x` | W0 | pending |
| 66-02-07 | 02 | 2 | INPUT-03 | unit | `pytest tests/test_lsd_generator.py -k "proton_shift" -x` | W0 | pending |
| 66-02-08 | 02 | 2 | INPUT-04 | unit | `pytest tests/test_lsd_generator.py -k "hmbc_bond_range" -x` | W0 | pending |
| 66-02-09 | 02 | 2 | INPUT-01 | unit | `pytest tests/test_lsd_generator.py -k "validate_pylsd" -x` | W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] New test method `TestLSDCorrelation::test_to_lsd_line_hmbc_extended` in `tests/test_lsd_models.py` -- covers INPUT-04 `to_lsd_line()` change
- [ ] New test class `TestPyLSDExtensions` in `tests/test_lsd_generator.py` -- covers INPUT-01, INPUT-02, INPUT-03, INPUT-04 emitter methods
- [ ] New test class `TestPyLSDValidator` in `tests/test_lsd_generator.py` -- covers `validate_pylsd_input()` error and pass cases

*No new test files needed -- extend existing files.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
