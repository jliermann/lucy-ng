# Requirements: v8.0 pyLSD Integration

**Defined:** 2026-03-13
**Core Value:** AI agent autonomously determines compound structures from NMR, with systematic 4J HMBC exploration via multi-run solver orchestration

## v1 Requirements

Requirements for v8.0 release. Each maps to roadmap phases.

### Validation Gate

- [x] **GATE-01**: Manual hypothesis test — run ibuprofen LSD with 3 known 4J HMBC correlations removed, confirm solutions with aromatic rings appear (30-minute test, gates entire roadmap)

### LSD Input Generation

- [x] **INPUT-01**: LSDInputGenerator supports FORM command for molecular formula declaration in pyLSD-format files
- [x] **INPUT-02**: LSDInputGenerator supports ELIM header command (`ELIM N M` for correlation elimination)
- [x] **INPUT-03**: LSDInputGenerator supports SHIX/SHIH commands for chemical shift assignment to atoms
- [x] **INPUT-04**: LSDInputGenerator supports extended HMBC bond range syntax (`HMBC X Y 2 4` for 2-4 bond correlations)
- [ ] **INPUT-05**: Constraint inventory schema v2 tracks 4J suspect correlations with `pylsd_mode`, `deferred_4j` metadata

### Multi-Run Orchestration

- [ ] **ORCH-01**: PyLSDOrchestrator generates permutations of LSD input files with different 4J correlation configurations (include/exclude suspect HMBCs)
- [ ] **ORCH-02**: PyLSDOrchestrator caps permutation count (K≤3 excluded correlations) to prevent combinatorial explosion
- [ ] **ORCH-03**: SolutionMerger deduplicates solutions from multiple LSD runs using InChI canonicalization
- [ ] **ORCH-04**: SolutionMerger preserves provenance (which correlation configuration produced each solution)

### CLI

- [ ] **CLI-01**: `lucy pylsd run <file>` command executes multi-run orchestration and returns merged solutions
- [ ] **CLI-02**: `lucy pylsd run` reuses existing `lucy lsd rank` for two-tier ranking (match count primary, MAE secondary)
- [ ] **CLI-03**: Regression: all existing `lucy lsd run` commands work unchanged (coexist, not replace)

### Agent Integration

- [ ] **AGT-01**: lsd-engineer writes extended HMBC bond range (`HMBC X Y 2 4`) for suspect 4J correlations identified by nmr-chemist
- [ ] **AGT-02**: lsd-engineer uses `lucy pylsd run` when constraint inventory has `pylsd_mode: true` (4J suspects present)
- [ ] **AGT-03**: case.md orchestrator routes to multi-run path when nmr-chemist flags aromatic 4J risk
- [ ] **AGT-04**: devils-advocate validates 4J deferral decisions (checks which correlations deferred, permutation count reasonable)

### UAT

- [ ] **UAT-01**: Ibuprofen CASE run using pyLSD multi-run orchestration finds correct structure with aromatic ring in top-ranked solutions
- [ ] **UAT-02**: Ibuprofen 3 known 4J correlations (ArCH 129.38↔CH2 45.03, ArCH 127.26↔CH 44.90) correctly handled via extended bond range or exclusion permutations

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Heteroatom Ambiguity

- **HETERO-01**: Multi-state MULT for ambiguous heteroatoms (e.g., `MULT 14 O (2 3) (0 1)`) with combinatorial LSD runs
- **HETERO-02**: Automatic default state insertion for undefined heteroatom hybridisation/multiplicity

### Multi-Compound UAT

- **MUAT-01**: Multi-compound CASE comparison UAT with non-aromatic test compounds
- **MUAT-02**: COSY correlation integration in LSD constraints

## Out of Scope

| Feature | Reason |
|---------|--------|
| Statistical 4J detection | v7.0 proved non-viable (100% false positive rate) |
| pyLSD as external dependency | Implement orchestration directly in Python — pyLSD is just an LSD driver |
| Multi-state MULT for heteroatoms | Deferred to v9.0 — focus v8.0 purely on 4J |
| pyLSD's built-in nmrshiftdb ranking | Bypass — use existing two-tier HOSE ranking |
| Parallel LSD binary execution | Nice-to-have but sequential runs are sufficient for ≤8 permutations |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GATE-01 | Phase 65 | Complete |
| INPUT-01 | Phase 66 | Complete |
| INPUT-02 | Phase 66 | Complete |
| INPUT-03 | Phase 66 | Complete |
| INPUT-04 | Phase 66 | Complete |
| INPUT-05 | Phase 68 | Pending |
| ORCH-01 | Phase 67 | Pending |
| ORCH-02 | Phase 67 | Pending |
| ORCH-03 | Phase 67 | Pending |
| ORCH-04 | Phase 67 | Pending |
| CLI-01 | Phase 69 | Pending |
| CLI-02 | Phase 69 | Pending |
| CLI-03 | Phase 69 | Pending |
| AGT-01 | Phase 70 | Pending |
| AGT-02 | Phase 70 | Pending |
| AGT-03 | Phase 70 | Pending |
| AGT-04 | Phase 70 | Pending |
| UAT-01 | Phase 71 | Pending |
| UAT-02 | Phase 71 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 — traceability complete after roadmap creation*
