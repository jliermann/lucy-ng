# Requirements: lucy-ng v5.0 Fragment Library

**Defined:** 2026-02-19
**Core Value:** AI agent autonomously determines compound structures from NMR, with a collaborative team architecture that self-corrects through peer review

## v5.0 Requirements

Requirements for fragment library milestone. Each maps to roadmap phases.

### Fragment Infrastructure

- [x] **FRAG-01**: Fragment database schema v7 with `ssc` and `ssc_bitset` tables in separate `lucy-ng-fragments.db`
- [x] **FRAG-02**: SSC extraction pipeline extracts substructure-subspectrum correlations from 928K compounds using BFS sphere fragmentation with bond-preservation rules
- [x] **FRAG-03**: Extraction pipeline supports checkpointing and resume for multi-hour runs
- [x] **FRAG-04**: Fingerprint bin size (2 ppm) validated on 1K compound sample before full extraction

### Fragment Search

- [x] **SRCH-01**: 256-bit fingerprint generated per SSC (2 ppm bins, 0-510 ppm range) with tolerance expansion
- [x] **SRCH-02**: Boolean AND pre-screening eliminates non-matching SSCs before fine matching
- [x] **SRCH-03**: Fine spectral matching filters by DEV (2 ppm), AVGDEV (1 ppm), multiplicity, and equivalence
- [x] **SRCH-04**: Fragment results ranked by heavy atom count (descending) then AVGDEV (ascending)
- [x] **SRCH-05**: CLI `lucy fragment search --shifts "..." --format json` returns ranked fragments with matched signals
- [x] **SRCH-06**: CLI `lucy fragment info` reports library statistics (SSC count, database size)

### LSD Integration

- [x] **LINT-01**: Fragment SMILES converted to LSD DEFF goodlist file format (validated against LSD manual)
- [x] **LINT-02**: CLI `lucy fragment to-lsd` generates fragment definition file from SMILES
- [x] **LINT-03**: DEFF/FEXP commands placed before MULT in LSD file (critical ordering)

### Agent Integration

- [ ] **AGNT-01**: lsd-engineer runs fragment search before each LSD iteration and applies best fragment as DEFF/FEXP
- [ ] **AGNT-02**: Sequential injection protocol: one fragment at a time, discard if zero solutions, log conflict and continue
- [ ] **AGNT-03**: Fragment constraints tracked in constraint inventory JSON (DEFF/FEXP section)
- [ ] **AGNT-04**: Devils-advocate verifies fragment file existence before LSD solver run

### Validation

- [ ] **VALD-01**: Multi-compound UAT on 5+ compounds from Sherlock test set with solution count before/after fragment injection
- [ ] **VALD-02**: Self-search validation: 100 compounds' own spectra must find their own SSCs (>99% recall)

## Future Requirements

Deferred to v5.x or later. Tracked but not in current roadmap.

### Fragment Enhancements

- **FRAG-05**: Multi-fragment sequential injection (inject second fragment if first yields >5 solutions)
- **FRAG-06**: Formula-aware pre-screening (filter SSCs by atom composition against query formula)
- **FRAG-07**: Fragment search statistics in CLI output (pre-screen count, fine match count)
- **FRAG-08**: Fragment display in CASE-PROGRESS.md for chemist review

### System Improvements

- **SYS-01**: Statistical 4J HMBC coupling detection (DB-based probability for atom-type pairs)
- **SYS-02**: COSY correlation integration in LSD constraints
- **SYS-03**: NP-likeness scoring for solution filtering
- **SYS-04**: Solvent-aware 13C prediction (per-solvent HOSE statistics)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Custom user-uploaded fragments | High complexity, low value — agent can write manual DEFF if needed |
| Real-time SSC extraction per CASE run | 24M fragments from 928K compounds takes hours; must be pre-built offline |
| Using HOSE codes instead of SSC fragmentation | Different purpose: HOSE = atom-level prediction, SSC = substructure-level matching |
| Simultaneous multi-fragment injection (3+ at once) | Over-constraining risk; sequential single-fragment with validation is safer |
| Fragment database regeneration automation | Only needed on rare compound DB updates; manual for now |
| GUI or web visualization of fragments | CLI-only architecture; not in scope |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FRAG-01 | Phase 49 | Complete |
| FRAG-02 | Phase 50 | Complete |
| FRAG-03 | Phase 50 | Complete |
| FRAG-04 | Phase 50 | Complete |
| SRCH-01 | Phase 51 | Complete |
| SRCH-02 | Phase 51 | Complete |
| SRCH-03 | Phase 51 | Complete |
| SRCH-04 | Phase 51 | Complete |
| SRCH-05 | Phase 51 | Complete |
| SRCH-06 | Phase 51 | Complete |
| LINT-01 | Phase 52 | Complete |
| LINT-02 | Phase 52 | Complete |
| LINT-03 | Phase 52 | Complete |
| AGNT-01 | Phase 53 | Pending |
| AGNT-02 | Phase 53 | Pending |
| AGNT-03 | Phase 53 | Pending |
| AGNT-04 | Phase 53 | Pending |
| VALD-01 | Phase 54 | Pending |
| VALD-02 | Phase 54 | Pending |

**Coverage:**
- v5.0 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-02-19*
*Last updated: 2026-02-19 after roadmap created — traceability complete*
