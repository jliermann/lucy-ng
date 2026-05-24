# Requirements: v9.0 CASE Reliability & Skill Consolidation

**Defined:** 2026-05-20
**Core Value:** AI agent autonomously determines compound structures from NMR — and the pipeline that produces the answer is reliable and uses the intended mechanism, not a manual bypass.
**Driver:** `.planning/v8.0-UAT-POSTMORTEM.md` (v8.0 found ibuprofen but bypassed its own pyLSD system).

## v1 Requirements

Requirements for v9.0 release. Outcome-level where possible so they survive the Phase-1 design decisions. Each maps to roadmap phases.

### Design Re-Validation (FIRST — gates all fixes)

- [ ] **DESIGN-01**: 4J-handling and aromatic-ring approach is decided and documented, with the Phase-65 hypothesis ("removing 4J HMBC makes the aromatic ring appear") re-evaluated against actual CASE evidence (ring had to be force-fragmented in the v8.0 UAT)
- [ ] **DESIGN-02**: Solver-path architecture is decided (single path vs normal-LSD + pyLSD dual path) together with a skill-documentation strategy that prevents the agent reverting to the better-documented path

### Reliability (design-agnostic, outcome-level)

- [ ] **RELI-01**: LSD solutions reliably convert to ranked SMILES with no silent solution loss — when the solver finds N solutions, the pipeline ranks them (covers the outlsd conversion / `lucy lsd run` exit-255 / empty-merge failures)
- [x] **RELI-02**: Every solver invocation runs with the COMPLETE validated constraint set — no silent constraint loss on any solver path (covers permutation-file constraint drop and the non-native-translation gap)
- [x] **RELI-03**: Aromatic compounds reliably yield aromatic-ring solutions in the ranked output (per the DESIGN-01 decision)

### Skill Consolidation

- [x] **SKILL-01**: All agent skills are correct against actual LSD-3.4.9 behavior — no commands taught that the binary rejects (e.g., SYME / DEFF NOT are non-native); native equivalents documented
- [x] **SKILL-02**: Skills give unambiguous single-solver-path guidance per DESIGN-02 (resolve the normal-LSD-vs-pyLSD documentation imbalance)
- [x] **SKILL-03**: devils-advocate gates detect the v8.0 failure modes — silent constraint loss, empty/zero merge despite per-run solutions, and post-validation file edits

### UAT (milestone gate)

- [ ] **UAT-03**: CASE1 blind re-run solves ibuprofen via the intended mechanism (not a manual bypass); all four Phase-71 success criteria pass against on-disk artifacts (independent RDKit verification)
- [ ] **UAT-04**: CASE9 blind run (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3 — different molecule, same para-aromatic 4J failure mode) solves correctly via the intended mechanism

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Performance

- **PERF-01**: Parallel LSD binary execution across permutations (sequential is acceptable for ≤8 permutations; revisit only if UAT shows it is too slow)

### Heteroatom Ambiguity (carried from v8.0 deferral)

- **HETERO-01**: Multi-state MULT for ambiguous heteroatoms with combinatorial LSD runs
- **HETERO-02**: Automatic default state insertion for undefined heteroatom hybridisation/multiplicity

## Out of Scope

| Feature | Reason |
|---------|--------|
| Statistical 4J detection | v7.0 proved non-viable (100% false positive rate) |
| pyLSD as external dependency | Orchestration is implemented directly in Python |
| New domain features | v9.0 is reliability + consolidation of existing capabilities, not new functionality |
| Re-deriving v8.0 infrastructure from scratch | Repair/consolidate the shipped v8.0 code, do not rewrite wholesale |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DESIGN-01 | Phase 72 | Pending |
| DESIGN-02 | Phase 72 | Pending |
| RELI-01 | Phase 73 | Pending |
| RELI-02 | Phase 74 | Complete |
| RELI-03 | Phase 74 | Complete |
| SKILL-01 | Phase 75 | Complete |
| SKILL-02 | Phase 75 | Complete |
| SKILL-03 | Phase 75 | Complete |
| UAT-03 | Phase 76 | Pending |
| UAT-04 | Phase 76 | Pending |

**Coverage:**
- v1 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

---
*Requirements defined: 2026-05-20*
*Traceability filled: 2026-05-20 — roadmapper assigned all 10 requirements to phases 72-76*
*v8.0 requirements (GATE/INPUT/ORCH/CLI/AGT/UAT-01/02) preserved in git history + ROADMAP.md phase sections + v8.0-UAT-POSTMORTEM.md*
