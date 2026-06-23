---
phase: 86
slug: ranker-path-unification
status: draft
nyquist_compliant: false
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
| TBD | TBD | TBD | RANK-01/02/03 | — | N/A (offline dev tooling) | unit | `pytest -k "rank or predict"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky — planner fills exact task IDs.*

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
