---
phase: 79
slug: peak-picking-symmetry-fix
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-08
---

# Phase 79 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (`[tool.pytest]`) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest --cov=lucy_ng` |
| **Estimated runtime** | ~60 seconds |

**Note:** CASE NMR test data lives OUTSIDE the repo at
`~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/` (CASE9/12 = 13C carbonyl-masking
fixture; CASE1 = ibuprofen unchanged-regression fixture). Regression tests must reference these
paths via a fixture/skip-if-absent guard so CI without the data still runs.

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest --cov=lucy_ng`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 79-XX-XX | TBD | TBD | FIX-04 | — | N/A | unit | `pytest tests/test_peak_picker_snr.py -q` | ❌ W0 | ⬜ pending |
| 79-XX-XX | TBD | TBD | FIX-04 | — | N/A | regression | `pytest tests/test_peak_picker_case_regression.py -q` | ❌ W0 | ⬜ pending |
| 79-XX-XX | TBD | TBD | FIX-05 | — | N/A | unit | `pytest tests/test_intensity_symmetry.py -q` | ❌ W0 | ⬜ pending |
| 79-XX-XX | TBD | TBD | FIX-06 | — | N/A | manual | skill-prompt review (see Manual-Only) | n/a | ⬜ pending |

*Planner refines this map (concrete plan/wave/task IDs) during Step 8. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_peak_picker_snr.py` — SNR/MAD threshold unit tests (FIX-04): MAD-σ estimate, SNR≥3 floor, per-peak SNR annotation
- [ ] `tests/test_peak_picker_case_regression.py` — CASE9 carbonyl @166 ppm IS picked AND CASE1 ibuprofen picking unchanged (FIX-04, the load-bearing regression)
- [ ] `tests/test_intensity_symmetry.py` — 13C intensity class-normalized 2C-equivalence on CASE9 aromatics (FIX-05): 129.94≡, 125.31≡ emitted; aromatic noise floor does NOT produce false 2C candidates
- [ ] `tests/conftest.py` — fixtures for CASE9/CASE1 Bruker paths with skip-if-absent guard

*pytest framework already present — no install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| DBE self-check procedural in nmr-chemist (DBE deficit + empty 160–220 → re-pick before SETUP-COMPLETE) | FIX-06 | Skill is a markdown agent prompt, not executable code | Read ~/.claude/agents/lucy-nmr-chemist.md; confirm a mandatory DBE self-check step exists post-picking with formula-driven region hints |
| 5th quality loop-pattern wired into case.md/loop-patterns.md/advisory-templates.md (trigger=all top-K IMPLAUSIBLE; budget=1 cycle) | FIX-06 | Skill/command markdown, not executable code | Grep the three files for the new pattern; confirm trigger, 1-cycle budget, assumption-reexamination action |
| Blind CASE9 re-run reaches para-disubstituted ester via emergent path | SC-5 | Requires fresh blind Claude instance + RDKit verification (per feedback_blind_uat) | Out-of-band UAT in fresh instance; this (bookkeeper) instance only records the AND-gate verdict |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
