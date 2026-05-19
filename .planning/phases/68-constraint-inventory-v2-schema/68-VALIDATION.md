---
phase: 68
slug: constraint-inventory-v2-schema
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-19
---

# Phase 68 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_lsd_inventory_schema.py tests/test_cli_validate_inventory.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD     | TBD  | TBD  | INPUT-05    | —          | JSON Schema validation rejects malformed inventories | unit | `pytest tests/test_lsd_inventory_schema.py` | ❌ W0 | ⬜ pending |
| TBD     | TBD  | TBD  | INPUT-05    | —          | CLI exits non-zero on invalid inventory | integration | `pytest tests/test_cli_validate_inventory.py` | ❌ W0 | ⬜ pending |
| TBD     | TBD  | TBD  | INPUT-05    | —          | G2 detects bare `ELIM N M` (not `; ELIM` annotation) | unit | `pytest tests/test_cli_validate_inventory.py -k elim_anchor` | ❌ W0 | ⬜ pending |

*Final task IDs filled in by planner. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_lsd_inventory_schema.py` — JSON Schema loading + validation cases for INPUT-05
- [ ] `tests/test_cli_validate_inventory.py` — `lucy lsd validate-inventory` exit codes + `--format json` output
- [ ] `schemas/constraint_inventory_v2.json` — JSON Schema Draft 2020-12 source of truth
- [ ] `pyproject.toml` — `jsonschema>=4.18.0` dependency declared

*If unchanged: rely on `tests/test_lsd_models.py` and `tests/test_lsd_generator.py` patterns.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Skill docs (`lucy-lsd-engineer.md` §5, `lucy-devils-advocate.md` §5) reflect v2 schema and CLI replacement | INPUT-05 | Markdown skill files for agents; no automated MD-content test exists | Diff-read both files; confirm v2 delimiter, `pylsd_mode`/`deferred_4j`/`elim_annotated` fields, and `lucy lsd validate-inventory --format json` invocation are documented |
| v7.0 post-mortem cited in G2 explanation | INPUT-05 | Pedagogical text; no schema test | Read `lucy-devils-advocate.md` §5B updated text; confirm reference to "Statistical 4J detection non-viable — 100% FP rate" appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
