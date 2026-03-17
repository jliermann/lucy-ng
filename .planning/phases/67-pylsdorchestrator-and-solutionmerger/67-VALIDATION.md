---
phase: 67
slug: pylsdorchestrator-and-solutionmerger
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 67 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_lsd_orchestrator.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_lsd_orchestrator.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 67-01-01 | 01 | 1 | ORCH-01 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_generates_permutation_files" -x` | ❌ W0 | ⬜ pending |
| 67-01-02 | 01 | 1 | ORCH-01 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_permutation_content" -x` | ❌ W0 | ⬜ pending |
| 67-01-03 | 01 | 1 | ORCH-02 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_k_greater_than_3_raises" -x` | ❌ W0 | ⬜ pending |
| 67-01-04 | 01 | 1 | ORCH-02 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_k_boundary" -x` | ❌ W0 | ⬜ pending |
| 67-02-01 | 02 | 1 | ORCH-03 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_deduplication" -x` | ❌ W0 | ⬜ pending |
| 67-02-02 | 02 | 1 | ORCH-03 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_merged_smi_written" -x` | ❌ W0 | ⬜ pending |
| 67-02-03 | 02 | 1 | ORCH-04 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_run_report_provenance" -x` | ❌ W0 | ⬜ pending |
| 67-02-04 | 02 | 1 | ORCH-04 | unit | `pytest tests/test_lsd_orchestrator.py -k "test_multi_perm_provenance" -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_lsd_orchestrator.py` — stubs for ORCH-01 through ORCH-04 (8 test behaviors)
- [ ] No framework changes needed — uses existing pytest setup

*Testing strategy: Mock `LSDRunner.run_file()` and provide fixture SMILES files in `tmp_path`. No LSD binary required.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
