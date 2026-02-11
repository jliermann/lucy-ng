# Requirements: lucy-ng v3.0 Statistical Detection

**Defined:** 2026-02-10
**Core Value:** AI agent autonomously determines compound structures from NMR, with data-driven statistical constraints replacing guesswork

## v3.0 Requirements

Requirements for v3.0 milestone. Each maps to roadmap phases.

### Statistical Detection

- [x] **DETECT-01**: CLI command detects hybridisation (sp1/sp2/sp3) for a given 13C shift from HOSE database frequency distributions
- [x] **DETECT-02**: CLI command detects forbidden neighbour atoms (<1% frequency) for a given 13C shift and multiplicity
- [x] **DETECT-03**: CLI command detects mandatory neighbour atoms (>95% frequency) for a given 13C shift and multiplicity
- [x] **DETECT-04**: CLI command detects hetero-hetero bond allowance from bond pair statistics (1% threshold)
- [x] **DETECT-05**: CLI command detects signal grouping (shifts within 0.25 ppm tolerance with matching multiplicities)
- [x] **DETECT-06**: Database schema extended with hybridisation and neighbour statistics in hose_stats table
- [x] **DETECT-07**: Statistics generator computes detection statistics during HOSE stats generation

### Ranking & Filtering

- [ ] **RANK-01**: Two-tier ranking scores solutions by signal match count first, then average deviation
- [ ] **RANK-02**: Solutions with fewer matched signals rank lower regardless of MAE
- [ ] **RANK-03**: Badlist filter excludes solutions containing 3-membered rings
- [ ] **RANK-04**: Badlist filter excludes solutions containing 4-membered rings

### Agent Integration

- [ ] **AGENT-01**: CASE agent calls lucy detect CLI commands to generate statistical constraints before writing LSD files
- [ ] **AGENT-02**: CASE agent uses hybridisation detection to set MULT hybridisation values in LSD
- [ ] **AGENT-03**: CASE agent uses neighbourhood detection to add ELIM/LIST constraints in LSD
- [ ] **AGENT-04**: CASE agent uses HHB detection to add or omit hetero-hetero BOND constraints in LSD
- [ ] **AGENT-05**: CASE agent applies chemistry-first hierarchy — NMR knowledge takes priority, statistics augment but don't override
- [ ] **AGENT-06**: CASE agent uses signal grouping detection to identify ambiguous carbon assignments

## Previous Milestones (Complete)

### v2.0 Requirements (38 total — all complete)

Audit (AUDT-01..04), Skill Architecture (SKIL-01..04), Incremental HMBC (HMBC-01..04), Error Tolerance (ETOL-01..04), Supervisor Agent (SUPV-01..07), Diagnostic Specialist (DIAG-01..05), Thin Tools (TOOL-01..04), Spectral Quality (QUAL-01..03), Confidence Output (CONF-01..03).

### v2.1 Requirements (30 total — all complete)

Sub-Command Skills (SCMD-01..07), Autonomous CASE Agent (CASE-01..05), CASE Orchestration (ORCH-01..08), Diagnostic Integration (DIAG-06..08), AI-Driven Sanitisation (SANT-01..04), Validation Gate (VALD-01..05), Cleanup (CLNP-01..03).

## Future Requirements

Deferred to later milestones. Tracked but not in current roadmap.

### Signal Grouping Combinatorial Exchange (v3.1)

- **GROUP-01**: Combinatorial atom exchange for grouped signals (try all permutations)
- **GROUP-02**: Automatic retry with swapped assignments when first attempt yields 0 solutions

### Fragment Library (v3.2)

- **FRAG-01**: Fragment library built from 24.5M substructure-subspectrum correlations (SSCs)
- **FRAG-02**: Fragment search by shift pattern to suggest substructures
- **FRAG-03**: Fragment constraints integrated into LSD input generation

### Constraint Explorer Specialist (future)

- **CEXP-01**: Specialist agent generates multiple LSD input variants for ambiguous cases
- **CEXP-02**: Runs LSD on all variants in parallel and reports which succeeded

### Solution Explainer Specialist (future)

- **SEXP-01**: Specialist explains WHY a solution ranks #1 vs alternatives
- **SEXP-02**: Comparative report showing constraint satisfaction and shift prediction quality

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic threshold tuning | Sherlock's fixed thresholds work for 82% of cases; override flags sufficient |
| COSY correlation support | Notoriously difficult to analyze, deferred indefinitely |
| Real-time statistics computation | Pre-computed during DB build; no runtime queries against raw HOSE data |
| GUI for detection results | CLI-only architecture; AI agent consumes JSON output |
| Custom HOSE radius for detection | Default radius sufficient; configurable radius adds complexity without clear benefit |
| Stereochemistry handling (E/Z, R/S) | Requires different NMR experiments, out of scope |
| CLI command for sanitisation | Anti-feature: requires AI reasoning |
| Dereplication in CASE orchestrator | Anti-feature: absolute separation |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

### v3.0 (Active)

| Requirement | Phase | Status |
|-------------|-------|--------|
| DETECT-01 | Phase 34 | Complete |
| DETECT-06 | Phase 34 | Complete |
| DETECT-07 | Phase 34 | Complete |
| DETECT-02 | Phase 35 | Complete |
| DETECT-03 | Phase 35 | Complete |
| DETECT-04 | Phase 36 | Complete |
| DETECT-05 | Phase 37 | Complete |
| RANK-01 | Phase 38 | Pending |
| RANK-02 | Phase 38 | Pending |
| RANK-03 | Phase 38 | Pending |
| RANK-04 | Phase 38 | Pending |
| AGENT-01 | Phase 39 | Pending |
| AGENT-02 | Phase 39 | Pending |
| AGENT-03 | Phase 39 | Pending |
| AGENT-04 | Phase 39 | Pending |
| AGENT-05 | Phase 39 | Pending |
| AGENT-06 | Phase 39 | Pending |

**Coverage:**
- v3.0 requirements: 17 total
- Mapped to phases: 17 (100% coverage)
- Phase 34: 3 requirements (DETECT-01, DETECT-06, DETECT-07)
- Phase 35: 4 requirements (DETECT-02, DETECT-03, DETECT-06, DETECT-07)
- Phase 36: 3 requirements (DETECT-04, DETECT-06, DETECT-07)
- Phase 37: 1 requirement (DETECT-05)
- Phase 38: 4 requirements (RANK-01, RANK-02, RANK-03, RANK-04)
- Phase 39: 6 requirements (AGENT-01 through AGENT-06)
- Phase 40: 0 requirements (validation phase)

**Note:** DETECT-06 and DETECT-07 are foundational requirements that span Phases 34-36 since all detection features require schema extension and statistics generation.

### v2.0/v2.1 (Complete)

All 68 requirements (38 v2.0 + 30 v2.1) mapped and complete. See git history for full traceability tables.

---
*Requirements defined: 2026-02-10*
*Last updated: 2026-02-11 after Phase 37 execution*
