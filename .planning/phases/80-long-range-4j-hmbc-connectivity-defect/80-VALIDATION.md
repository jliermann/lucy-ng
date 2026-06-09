---
phase: 80
slug: long-range-4j-hmbc-connectivity-defect
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-09
---

# Phase 80 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` (project root) |
| **Quick run command** | `pytest tests/test_lsd_generator.py tests/test_ranking.py tests/test_inventory_schema.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~60 seconds (quick) / ~5 min (full) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_lsd_generator.py tests/test_ranking.py tests/test_inventory_schema.py -x`
- **After every plan wave:** Run `pytest` (full suite)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds (quick), 300 seconds (full)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| FIX-07-A | TBD | 1 | FIX-07 | — | N/A | unit | `pytest tests/test_lsd_generator.py::TestElimBudget -x` | ❌ W0 | ⬜ pending |
| FIX-07-B | TBD | 1 | FIX-07 | — | N/A | unit | `pytest tests/test_lsd_generator.py::TestElimBudget -x` | ❌ W0 | ⬜ pending |
| FIX-07-C | TBD | 1 | FIX-07 | — | N/A | unit | `pytest tests/test_ranking.py::TestPlausibilityFilter -x` | ❌ W0 | ⬜ pending |
| FIX-07-D | TBD | 1 | FIX-07 | — | N/A | unit | `pytest tests/test_ranking.py::TestPlausibilityFilterOrdering -x` | ❌ W0 | ⬜ pending |
| FIX-07-E | TBD | 1 | FIX-07 | — | N/A | unit | `pytest tests/test_inventory_schema.py::TestSchemaV2Phase80 -x` | ❌ W0 | ⬜ pending |
| FIX-07-F | TBD | 2 | FIX-07 | — | N/A | agent-experiment | `scripts/verify_case_solution.py solutions.smi C12H16O3` | ✅ | ⬜ pending |
| FIX-07-G | TBD | 2 | FIX-07 | — | N/A | agent-experiment | `scripts/verify_case_solution.py solutions.smi C13H18O2` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*Task IDs map to the FIX-07-{A..G} validation rows from 80-RESEARCH.md; plan IDs assigned at planning time.*

---

## Wave 0 Requirements

- [ ] `tests/test_lsd_generator.py::TestElimBudget` — new test class: `elim_budget` field emission (`ELIM 1 0` when budget=1; no ELIM line when budget=0)
- [ ] `tests/test_ranking.py::TestPlausibilityFilter` — new test class: `_is_chemically_plausible()` rejects non-aromatic solution when ≥4 shifts in 110–160 ppm
- [ ] `tests/test_ranking.py::TestPlausibilityFilterOrdering` — new test class: pre-filter preserves ranking order (matched_count desc, MAE asc) for survivors
- [ ] `tests/test_inventory_schema.py::TestSchemaV2Phase80` — new test: schema accepts inventory without `deferred_4j`/`pylsd_mode`/`elim_annotated`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CASE9 blind UAT reaches RDKit-verified C12H16O3 para-benzoate in top-3 via emergent path + ELIM escalation; Phase-78 AND-gate re-applied | FIX-07 (SC-4) | Full CASE run is agent-driven, not unit-testable; must be run by a FRESH BLIND instance per `feedback_blind_uat` | Spawn blind instance, run `/lucy-ng:case` on CASE9, verify `merged.smi`/`solutions.smi` via `scripts/verify_case_solution.py solutions.smi C12H16O3` independently in RDKit |
| CASE1 (ibuprofen) no regression: still found with `ELIM 0` first (no escalation needed) | FIX-07 (SC-3) | Same — agent-driven CASE run | Blind CASE1 run; verify ibuprofen via `scripts/verify_case_solution.py solutions.smi C13H18O2`; confirm ELIM did not escalate above 0 |

*The two agent-experiment rows (FIX-07-F/G) are the v9.0 milestone-ship gate and are intentionally manual/blind — never trust agent self-report.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (3 new test classes)
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s (quick suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
