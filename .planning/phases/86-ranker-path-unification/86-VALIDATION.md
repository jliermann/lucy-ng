---
phase: 86
slug: ranker-path-unification
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-23
---

# Phase 86 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/ -k "rank or predict" -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~quick: a few seconds (deterministic temp_db); full: minutes |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -k "rank or predict" -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds for the targeted ranker/predict subset

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 86-01-01 | 01 | 1 | RANK-01 | — | N/A (offline dev tooling) | unit | `pytest tests/test_ranking.py -k from_database -x` | ❌ W0 | ⬜ pending |
| 86-01-02 | 01 | 1 | RANK-01 | — | N/A | unit | `pytest tests/test_ranking.py -k "resolver or resolve" -x` | ❌ W0 | ⬜ pending |
| 86-02-01 | 02 | 2 | RANK-01 | — | N/A | unit | `pytest tests/test_ranking.py -k "cli" -x && pytest tests/test_prediction.py -k "predict_c13 or from_database" -x` | ❌ W0 | ⬜ pending |
| 86-02-02 | 02 | 2 | RANK-01, RANK-02, RANK-03 | — | N/A | unit + skipif real-DB | `pytest tests/test_ranking.py -k "regression or rank01 or rank02 or rank03 or parity or agreement" -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Note: deterministic temp_db tests pin RANK-01/02 path-parity in CI; the wrong-isomer ordering fix (success criteria 2 & 3 / RANK-03 intent) is carried by the `skipif(find_hose_database() is None)` real-DB test — the executor's environment MUST have the real HOSE DB so that test runs (not silently skips) before the phase is marked complete.*

---

## Wave 0 Requirements

- [ ] Regression test pinning ranker↔predict agreement on CASE1 (ibuprofen) and CASE3 (pulegone) molecules — deterministic `temp_db` fixture (mirror existing prediction test fixtures)
- [ ] Reuse existing pytest infrastructure (already present)

*Existing infrastructure covers framework needs; only new tests are added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full 3.97 GB DB-backed ranker agreement | RANK-02 | Real DB is ~830 MB download / not in CI | Run `lucy lsd rank` and `lucy predict c13` on the same molecule with the real DB; diff predicted shifts |

*Deterministic agreement is automated via temp_db; real-DB parity is the manual cross-check.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
