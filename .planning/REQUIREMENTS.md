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

### Post-UAT Fixes (Phase 77 — from 76-VERIFICATION.md forensics)

- [x] **FIX-01**: `lucy lsd run` produces real SMILES in solutions.smi and fails loud (non-zero exit, no false "success") when outlsd output is the error string / empty / non-SMILES; regression test covers happy + error paths
- [x] **FIX-02**: Cross-ring aromatic COSY equivalence pairs are emitted deterministically by tooling (from detected symmetry/grouping), so the aromatic ring emerges without manual atom-index reasoning or forced ring-BONDs; ring-BOND forcing demoted to documented escalation
- [x] **FIX-03**: Skill hygiene — deprecated lucy-case-agent.md retired; targeted skill-creator audit confirms v9.0 single-path + emergent/COSY guidance is prominent and flags dead/contradictory content
- [x] **FIX-04**: Peak-picker threshold replaced with SNR/MAD-absolute (noise = 1.4826·MAD, floor k=3 IUPAC LoD); solvent multiplet (CDCl₃ etc.) excluded before threshold/scale computation; per-peak SNR annotation added to Peak1D and JSON output; backwards-compatible (threshold param kept; use_snr=True is new default)
- [x] **FIX-05**: 13C intensity class-normalized 2C-equivalence detection for protonated aromatic CH (HSQC-confirmed, 100–165 ppm scope); output feeds `lucy analyze symmetry` / `lucy detect aromatic-cosy`; DO NOT modify detect_aromatic_cosy_pairs
- [x] **FIX-06**: Skill feedback loop — (a) DBE self-check procedural/mandatory in nmr-chemist after picking (O→carbonyl 160–220; N→amide/nitrile); (b) 5th quality loop-pattern QUALITY_CONVERGENCE_FAILURE in case.md detect_loops + loop-patterns.md + advisory-templates.md; budget = 1 re-look cycle; does NOT escalate to diagnostic specialist
- [ ] **FIX-07**: Long-range / 4J HMBC connectivity handling — false-positive long-range (4J) HMBC correlations must no longer be enforced as 2-3J bonds that exclude the correct structure. Exposed by the Phase-79 blind CASE9 UAT: `HMBC 1 8` (166.1↔70.2) + set 2 3 / 2 9 / 3 8 forced an impossible carbonyl→para-benzylic bond, excluding the true para-benzoate (`CC(C)OC(=O)c1ccc(C(C)O)cc1`). Must not reintroduce the v7.0 100%-FP statistical failure; must not regress the v4.0 ibuprofen 4J win. Approach (extended HMBC range / repaired pyLSD multi-run / narrow heuristic flag) to be chosen in discuss/research.

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
| FIX-01 | Phase 77 | Complete |
| FIX-02 | Phase 77 | Complete |
| FIX-03 | Phase 77 | Complete |
| FIX-04 | Phase 79 | Complete |
| FIX-05 | Phase 79 | Complete |
| FIX-06 | Phase 79 | Complete |
| FIX-07 | Phase 80 | Pending |
| UAT-03 | Phase 76 (failed) → Phase 78 | Pending |
| UAT-04 | Phase 76 (deferred) → Phase 78 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-05-20*
*Traceability filled: 2026-05-20 — roadmapper assigned all 10 requirements to phases 72-76*
*v8.0 requirements (GATE/INPUT/ORCH/CLI/AGT/UAT-01/02) preserved in git history + ROADMAP.md phase sections + v8.0-UAT-POSTMORTEM.md*
