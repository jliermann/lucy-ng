---
phase: 77
slug: fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-01
---

# Phase 77 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/lsd/ -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/lsd/ -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 77-01-xx | 01 | 1 | FIX-01 | — | runner exits non-zero + no false success on bad outlsd output | unit | `pytest tests/lsd/test_runner_*.py -q` | ❌ W0 | ⬜ pending |
| 77-02-xx | 02 | 1 | FIX-02 | — | deterministic cross-ring COSY pairs (4≡7,5≡6) emitted; no within-group pairs | unit | `pytest tests/lsd/test_*cosy*.py -q` | ❌ W0 | ⬜ pending |
| 77-03-xx | 03 | 1 | FIX-03 | — | N/A (skill/agent file hygiene — manual audit) | manual | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/lsd/test_runner_outlsd.py` — stubs for FIX-01 (happy path + error path)
- [ ] `tests/lsd/test_aromatic_cosy_pairs.py` — stubs for FIX-02 (cross-ring pairing)
- [ ] `tests/fixtures/regression/arm_a_ring_excl.lsd` — regression fixture (ring-exclusion .lsd that triggers the original bug)
- [ ] pytest already installed — no framework install needed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Deprecated `lucy-case-agent.md` retired; v9.0 single-path/emergent guidance prominent | FIX-03 | Skill/agent markdown files under `~/.claude/agents/` are not exercised by pytest | Grep deprecated file frontmatter `name:` neutralized; grep lucy-lsd-engineer.md lines 124-130 corrected; confirm COSY-helper reference present |
| D-76 mechanistic UAT criterion rewritten for Phase 78 | D-77-06 | Documentation artifact for downstream phase | Confirm Phase 78 CONTEXT/criteria carry emergent=pass / documented-BOND=conditional / silent-BOND or SKEL=fail |

*Most code behaviors (FIX-01, FIX-02) have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
