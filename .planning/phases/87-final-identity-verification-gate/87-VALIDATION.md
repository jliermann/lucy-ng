---
phase: 87
slug: final-identity-verification-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-23
---

# Phase 87 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/ -k identity -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~quick subset <30s; full suite per existing baseline |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -k identity -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds (quick subset)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD by planner | — | — | IDENT-01/02/03 | — | N/A | unit | `pytest tests/ -k identity` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note: gate-effectiveness on CASE4 (chamazulene) / CASE5 (indigo↔isoindigo, indirubin) is the Success-Criterion-4 regression fixture — pin those structures as test cases.*

---

## Wave 0 Requirements

- [ ] `tests/test_verify_case_identity.py` — stubs for IDENT-01/02/03 + CASE4/CASE5 fixtures
- [ ] Existing pytest infrastructure (pyproject.toml) covers framework — no new install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Devils-advocate advisory name↔structure gate fires in a CASE run | IDENT-02 | LLM-agent prompt behavior; not unit-testable | Re-run a CASE on CASE4/CASE5 structures in a fresh session; confirm DA flags the mismatch |
| Analyst renders tentative-name qualifier in `CASE Results` report | IDENT-03 | Agent prompt-output formatting | Inspect a CASE run report for the "(tentative, unverified)" rendering on a no-DB-hit structure |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
