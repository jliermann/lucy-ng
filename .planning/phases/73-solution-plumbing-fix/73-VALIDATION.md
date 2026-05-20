---
phase: 73
slug: solution-plumbing-fix
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-20
---

# Phase 73 — Validation Strategy

> Keystone tooling fix. Validation = LSD solutions flow end-to-end to SMILES, proven by a real LSD run (skipif-gated) + no regression.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_lsd_runner.py tests/test_lsd_regression.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30s (full suite); LSD-dependent tests skipped without binary |

---

## Sampling Rate

- **After every task commit:** quick run command
- **After all tasks:** full `pytest -q`
- **Before phase close:** full suite green; the new end-to-end test passes on this machine (LSD installed)
- **Max feedback latency:** 30s

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 1 | RELI-01 | `lucy lsd run <file.lsd>` runs LSD in file-argument mode → writes `.sol` to CWD (no stdin mode) | integration | `pytest tests/test_lsd_runner.py -k file_argument` (skipif LSD) | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | RELI-01 | `_run_outlsd` uses `outlsd 5` with `.sol` as stdin; N LSD solutions → N SMILES (not a 10-line header) | integration | `pytest tests/test_lsd_runner.py -k outlsd_smiles` (skipif LSD) | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | RELI-01 | `lucy lsd run` no longer reports success when 0 SMILES result (no silent false-positive); exit code reflects real outcome | unit/integration | `pytest tests/test_lsd_runner.py -k no_false_positive` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | RELI-01 | Phase 69 regression baseline still aligns (same ibuprofen InChI set via fixed path) | integration | `pytest tests/test_lsd_regression.py` (skipif LSD) | ✅ | ⬜ pending |

*Final task IDs filled by planner. Status: ⬜ pending · ✅ green · ❌ red.*

---

## Wave 0 Requirements

- [ ] `tests/test_lsd_runner.py` — end-to-end runner test (file-argument LSD run + outlsd → SMILES count) with `@skipif(shutil.which("LSD") is None)`
- [ ] Existing `tests/test_lsd_regression.py` (Phase 69) must still pass with the fixed runner path
- [ ] LSD + outlsd binaries at `/Users/steinbeck/Dropbox/develop/LSD/` (present on dev box)
- [ ] A small known LSD fixture with ≥1 solution (reuse Phase 69 `tests/fixtures/regression/ibuprofen_no_4j.lsd` or the Phase 72 experiment arm files)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `lucy lsd run` → `lucy lsd rank` chain works end-to-end on a real compound | RELI-01 | Full CLI chain on dev box with LSD | Run `lucy lsd run <fixture>` then `lucy lsd rank` on the output; confirm ranked SMILES appear (no "No SMILES found") |

---

## Validation Sign-Off

- [ ] File-argument LSD invocation verified (writes .sol); stdin mode removed
- [ ] outlsd uses `5` + .sol stdin; N solutions → N SMILES proven
- [ ] Silent false-positive eliminated (success requires real SMILES output)
- [ ] runner.py converged onto the orchestrator.py correct pattern (shared helper preferred)
- [ ] Phase 69 regression test still green
- [ ] LSD-dependent tests skipif-gated; full suite green
- [ ] `nyquist_compliant: true`

**Approval:** pending
