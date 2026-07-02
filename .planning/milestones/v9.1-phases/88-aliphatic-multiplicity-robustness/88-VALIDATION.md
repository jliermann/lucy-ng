---
phase: 88
slug: aliphatic-multiplicity-robustness
status: ready
nyquist_compliant: true
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
| **Quick run command** | `pytest tests/test_cli_pick.py -k multiplicity_edited -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | quick subset <30s; full suite per existing baseline |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_cli_pick.py -k multiplicity_edited -q` (Plan 01 only; skill-only commits run no new tests).
- **After every plan wave:** Run `pytest`.
- **Before `/gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 30 seconds (quick subset).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 88-01 T1 — `pick hsqc` multiplicity_edited + negative_crosspeak_count | 01 | 1 | MULT-04 | unit (CLI) | `pytest tests/test_cli_pick.py -k multiplicity_edited -q` | ❌ W0 | ⬜ pending |
| 88-01 T2 — true/false/zeros unit tests | 01 | 1 | MULT-04 | unit | `pytest tests/test_cli_pick.py -k multiplicity_edited -q` | ❌ W0 | ⬜ pending |
| 88-02 T1 — nmr-chemist [MULTIPLICITY-AMBIGUOUS] + viable families | 02 | 2 | MULT-04, MULT-01 | source-assertion (grep) + blind UAT | grep gate (see plan) + CASE4 blind re-run (UAT-01) | ✅ exists | ⬜ pending |
| 88-02 T2 — lsd-engineer per-family runs + deduped union | 02 | 2 | MULT-01 | source-assertion (grep) + blind UAT | grep gate (see plan) + CASE4 blind re-run (UAT-01) | ✅ exists | ⬜ pending |
| 88-03 T1 — DA binding [MULT-EVIDENCE-FOR] flag | 03 | 3 | MULT-03 | source-assertion (grep) + blind UAT | grep gate (see plan) + CASE4 blind re-run (UAT-01) | ✅ exists | ⬜ pending |
| 88-03 T2 — case.md pre-accept coverage gate + ledger | 03 | 3 | MULT-02 | source-assertion (grep) + blind UAT | grep gate (see plan) + CASE4 blind re-run (UAT-01) | ✅ exists | ⬜ pending |
| 88-03 T3 — coverage reopen pattern + advisory wording | 03 | 3 | MULT-02 | source-assertion (grep) | grep gate (see plan) | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Planner decision (Open Q2):** the optional `enumerate_aliphatic_families` Python helper was NOT added — family enumeration stays in the nmr-chemist prompt (RESEARCH A3 primary recommendation: cheaper, fewer moving parts). The only unit-testable Python seam is the `pick hsqc multiplicity_edited` flag (Plan 01).

**Note:** The CORE behavioral changes (per-family LSD runs, the pre-accept coverage gate, the binding DA multiplicity flag) live in CASE-agent markdown prompts — they are NOT unit-testable this session (fresh-session reload required). Their acceptance is the **blind CASE4 re-run = UAT-01 (Phase 89)**: chamazulene's di-methyl-ethyl constitution must appear in the searched solution set. The grep gates assert the prompt edits are present; the blind UAT validates behavior. Only the Plan-01 Python seam is unit-tested now.

---

## Wave 0 Requirements

- [ ] `tests/test_cli_pick.py` — add the `multiplicity_edited` true/false/zeros tests for `lucy pick hsqc` (negative-crosspeak detection ported from the `lucy pick 1d` `negative_detected` path); the False case uses the in-repo non-edited HSQC `data/Ibuprofen/6`; the True + zeros cases drive a tiny pure detector function (`_detect_multiplicity_edited`) with a synthesized negative-crosspeak ndarray and an all-zero ndarray.
- [ ] Existing pytest infrastructure (pyproject.toml) — no new framework install.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| lsd-engineer runs each viable family as a separate fully-constrained LSD run and ranks across the deduped union | MULT-01 | LLM-agent prompt behavior; fresh-session reload | Blind CASE4 re-run (UAT-01): confirm ≥2 multiplicity families searched + chamazulene di-methyl-ethyl constitution in the union |
| Pre-accept coverage gate reopens when a viable family was not searched (MAE-independent, counts SEARCHED not RANKED) | MULT-02 | Orchestrator prompt behavior; not unit-testable | Blind run with non-edited HSQC + iPr-vs-ethyl ambiguity: confirm the run does NOT accept until both families searched |
| DA "evidence FOR model X" flag forces model X into the search and cannot be narrated away | MULT-03 | LLM-agent prompt behavior | Blind CASE4: confirm the HMBC-11→13 "evidence for ethyl" flag forces the ethyl family into the search |
| nmr-chemist emits [MULTIPLICITY-AMBIGUOUS] on non-edited HSQC AND/OR phase-unreliable APT/DEPT | MULT-04 | Combines the unit-tested boolean with LLM reliability assessment | Plan-01 unit test pins the boolean; blind CASE4 confirms the combined signal fires |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (Python seam) OR a documented blind-UAT manual item (agent edits)
- [x] Sampling continuity: the Python seam is unit-tested; agent edits are grep-gated + blind-UAT-validated
- [x] Wave 0 covers the `pick hsqc` flag test
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready for execution
