---
phase: 74
slug: constraint-preservation-and-merge
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-22
---

# Phase 74 — Validation Strategy

> Native-only generation + constraint preservation across all Python solver paths. Scope = Python API (generator/model/orchestrator/merger). The agent's hand-written LSD path is Phase 75; full RELI-02/03 proof is the Phase 76 UAT.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_lsd_generator.py tests/test_lsd_orchestrator.py` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30s (full); LSD-dependent end-to-end tests skipif-gated |

---

## Sampling Rate

- **After every task commit:** quick run command
- **After all tasks:** full `pytest -q`
- **Before phase close:** full suite green; the end-to-end generator→LSD→aromatic test passes on dev box (LSD installed)
- **Max feedback latency:** 30s

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 1 | RELI-02 | LSDProblem carries equivalence + ring-exclusion fields; generator emits native BOND/COSY + DEFF F/FEXP for them | unit | `pytest tests/test_lsd_generator.py -k native_equivalence` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | RELI-02 | A generated LSD file contains NO `SYME` and NO `DEFF NOT <smarts>` (native-only) | unit | `pytest tests/test_lsd_generator.py -k native_only` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | RELI-02 | Filter files (ring3/ring4) bundled + written to output_dir; DEFF F references resolve | unit | `pytest tests/test_lsd_generator.py -k filter_files` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | RELI-02 | Permutation files carry the FULL constraint set (deepcopy) — not HMBC-only | unit | `pytest tests/test_lsd_orchestrator.py -k perm_constraints` | ✅ (deepcopy already) | ⬜ pending |
| TBD | TBD | 1 | RELI-03 | End-to-end: generator-built ibuprofen LSD → run → aromatic ring + ibuprofen emerges WITHOUT forced SKEL | integration | `pytest tests/test_lsd_generator.py -k aromatic_emergent` (skipif LSD) | ❌ W0 | ⬜ pending |

*Final task IDs filled by planner. Status: ⬜ pending · ✅ green · ❌ red.*

---

## Wave 0 Requirements

- [ ] `tests/test_lsd_generator.py` — native-equivalence + native-only + filter-file + emergent-aromatic tests (extend existing)
- [ ] `tests/test_lsd_orchestrator.py` — permutation-preservation test (full constraint set per perm)
- [ ] Bundled filter files under `src/lucy_ng/lsd/filters/` (ring3, ring4) — package resources copied to output_dir at write time
- [ ] LSD + outlsd on dev box for the emergent-aromatic integration test
- [ ] Phase 73 plumbing (fixed runner) present — the end-to-end test depends on it

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Homotopic CH2 equivalence translation | RELI-02 | Research flagged LOW confidence — whether SYME is ever used for same-carbon proton pairs and the correct native treatment | Inspect any SYME use site that maps to one carbon's two protons; confirm same-MULT-atom handling is correct or document the native form |

---

## Scope Boundary (explicit)

- **IN:** Python `generator.py` + `models.py` native-equivalence emission, filter-file bundling, permutation constraint preservation (verify deepcopy), SolutionMerger correctness confirmation, generator tests, ONE end-to-end emergent-aromatic test.
- **OUT (Phase 75):** the CASE agent writes LSD files by hand with `SYME`/`DEFF NOT` — changing the agent skills to write native commands is Phase 75. Phase 74 does NOT modify agent skill files.
- **OUT (Phase 76):** the full RELI-02/03 proof via blind CASE UAT.
- **OUT (D-04):** SKEL benzene forcing for the normal case (aromatic is emergent).

---

## Validation Sign-Off

- [ ] LSDProblem carries equivalence + ring-exclusion representation; generator emits native BOND/COSY + DEFF F/FEXP
- [ ] No generated file contains SYME or DEFF NOT
- [ ] Filter files bundled + resolve
- [ ] Permutation path preserves full constraint set
- [ ] End-to-end: generator → ibuprofen → aromatic ring emergent (no SKEL)
- [ ] Existing generator tests updated for native output; full suite green
- [ ] Scope boundary respected (no agent-skill changes — that is Phase 75)
- [ ] `nyquist_compliant: true`

**Approval:** pending
