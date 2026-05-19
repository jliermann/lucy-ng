---
phase: 69
slug: cli-command-and-regression-suite
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-19
---

# Phase 69 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_pylsd_cli.py tests/test_lsd_form_tolerance.py tests/test_lsd_regression.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30 seconds (full suite); LSD-dependent tests skipped without binary |

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
| TBD | TBD | TBD | CLI-01 | — | `lucy pylsd run` orchestrates and emits ranked solutions to stdout | integration | `pytest tests/test_pylsd_cli.py -k orchestration` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CLI-01 | — | `--no-rank` writes merged.smi + run_report.json without ranking | integration | `pytest tests/test_pylsd_cli.py -k no_rank` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CLI-01 | — | Suspect-source resolution: inventory primary, annotation sanity, grep fallback | unit + integration | `pytest tests/test_pylsd_cli.py -k suspect_source` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CLI-02 | — | Integrated rank uses extracted helper from `lucy lsd rank` (no subprocess) | unit | `pytest tests/test_pylsd_cli.py -k rank_helper` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | CLI-03 | — | `lucy lsd run` ibuprofen_no_4j produces baseline InChI set | integration | `pytest tests/test_lsd_regression.py` (skipif LSD missing) | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | — (D-15) | — | LSD binary ignores `FORM` line (same solutions w/ and w/o FORM) | integration | `pytest tests/test_lsd_form_tolerance.py` (skipif LSD missing) | ❌ W0 | ⬜ pending |

*Final task IDs filled in by planner. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pylsd_cli.py` — `lucy pylsd run` CLI integration tests (orchestration, --no-rank, --format json, suspect resolution, rank-helper-reuse)
- [ ] `tests/test_lsd_form_tolerance.py` — FORM-line tolerance test with `@skipif(shutil.which('LSD') is None)`
- [ ] `tests/test_lsd_regression.py` — Set-equal InChI regression test with `@skipif`
- [ ] `tests/fixtures/regression/ibuprofen_no_4j.lsd` — input fixture (derive from Phase 65 sol/smi shortcut where possible)
- [ ] `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` — versioned baseline (sorted InChIs, manually verified at first generation per D-16a)
- [ ] `tests/fixtures/form_tolerance/minimal.lsd` and `minimal_with_form.lsd` — paired fixtures for FORM test
- [ ] `src/lucy_ng/cli/pylsd.py` — new CLI module
- [ ] `.planning/findings/form-tolerance.md` — audit-trail document
- [ ] `lsd_rank` helper extraction in `src/lucy_ng/cli/lsd.py` — refactor inlined logic into a callable helper (e.g., `_rank_smiles_file()`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Regression baseline chemical plausibility (D-16a) | CLI-03 | Requires human chemical-intuition judgment about solution candidates | Run `lucy lsd run tests/fixtures/regression/ibuprofen_no_4j.lsd`, inspect resulting InChIs, confirm they correspond to chemically reasonable C13H18O2 isomers, commit baseline file |
| `form-tolerance.md` LSD-version capture | — (D-15a) | One-time audit-trail document, version-specific attribution | Run `LSD 2>&1 \| head -1`, paste version into Findings doc Setup section |
| pylsd run end-to-end smoke (LSD-installed dev box) | CLI-01 | Real LSD-binary integration check beyond test isolation | Manual run on ibuprofen with v2 inventory; confirm ranked output appears on stdout in same format as `lucy lsd rank` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (test files + fixtures)
- [ ] LSD-dependent tests use `@pytest.mark.skipif(shutil.which('LSD') is None)` — green path on CI even without LSD, real coverage on dev box
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
