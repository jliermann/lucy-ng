---
phase: 88
slug: aliphatic-multiplicity-robustness
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-25
---

# Phase 88 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/ -k multiplicity -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | quick subset <30s; full suite per existing baseline |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -k multiplicity -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds (quick subset)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD by planner — `pick hsqc` multiplicity_edited flag | — | 1 | MULT-04 | unit | `pytest tests/ -k "hsqc and multiplicity"` | ❌ W0 | ⬜ pending |
| TBD by planner — (optional) enumerate_aliphatic_families helper | — | 1 | MULT-01 | unit | `pytest tests/ -k "enumerate and famil"` | ❌ W0 | ⬜ pending |
| TBD by planner — agent/orchestrator edits (per-family, coverage gate, DA flag) | — | 2 | MULT-01/02/03 | source-assertion (grep) + blind UAT | `grep` checks + CASE4 blind re-run (UAT-01) | ✅ files exist | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Note:** The CORE behavioral changes (per-family LSD runs, the pre-accept coverage gate, the binding DA multiplicity flag) live in CASE-agent markdown prompts — they are NOT unit-testable this session (fresh-session reload required). Their acceptance is the **blind CASE4 re-run = UAT-01 (Phase 89)**: chamazulene's di-methyl-ethyl constitution must appear in the searched solution set. Only the two Python seams below are unit-testable now.

---

## Wave 0 Requirements

- [ ] `tests/test_pick_hsqc_multiplicity.py` — the `multiplicity_edited` boolean on `lucy pick hsqc` (negative-crosspeak detection ported from the `lucy pick 1d` `negative_detected` path); fixtures for an edited (CH₂ negative) vs non-edited HSQC.
- [ ] (optional, if planner adds the helper) `tests/test_enumerate_aliphatic_families.py` — valid CH₃/CH₂/CH whole-molecule partitions consistent with formula/H-count/DBE; iPr-vs-ethyl fixture yields BOTH families; cap enforced.
- [ ] Existing pytest infrastructure (pyproject.toml) — no new framework install.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| lsd-engineer runs each viable family as a separate fully-constrained LSD run and ranks across the union | MULT-01 | LLM-agent prompt behavior; fresh-session reload | Blind CASE4 re-run (UAT-01): confirm ≥2 multiplicity families searched + chamazulene di-methyl-ethyl constitution in the union |
| Pre-accept coverage gate reopens when a viable family was not searched | MULT-02 | Orchestrator prompt behavior; not unit-testable | Blind run with non-edited HSQC + iPr-vs-ethyl ambiguity: confirm the run does NOT accept until both families searched |
| DA "evidence FOR model X" flag forces model X into the search and cannot be narrated away | MULT-03 | LLM-agent prompt behavior | Blind CASE4: confirm the HMBC-11→13 "evidence for ethyl" flag forces the ethyl family into the search |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies (Python seams) OR a documented blind-UAT manual item (agent edits)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (where automatable)
- [ ] Wave 0 covers the `pick hsqc` flag test
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
