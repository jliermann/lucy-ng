# Requirements: lucy-ng

**Defined:** 2026-03-10
**Core Value:** AI agent autonomously determines compound structures from NMR, with a collaborative team architecture that self-corrects through peer review

## v6.0 Requirements

Requirements for Skill Quality Overhaul milestone. Each maps to roadmap phases.

### Skill Architecture

- [x] **ARCH-01**: case.md orchestrator skill is factored into core flow (<500 lines) plus bundled reference files for progress format, loop patterns, and advisory templates
- [x] **ARCH-02**: Legacy monolithic lucy-case-agent.md is archived with deprecation header and removed from active agent registry
- [x] **ARCH-03**: Shared NMR reference tables (experiment types, chemical shift regions) are extracted into a reference file that agents can read, reducing per-agent duplication by 30-50 lines each

### Agent Intelligence

- [x] **INTL-01**: nmr-chemist flags potential 4J HMBC couplings for aromatic systems (4+ carbons in 110-160 ppm) as separate category in [SETUP-COMPLETE] message
- [x] **INTL-02**: lsd-engineer defers correlations flagged as potential 4J to later HMBC batches, skipping them entirely if solutions already exist
- [x] **INTL-03**: solution-analyst uses lucy predict c13 to structurally verify aromatic ring presence in top candidates, not just the warnings array
- [x] **INTL-04**: Orchestrator validates incoming structured messages ([SETUP-COMPLETE], [ITERATION-COMPLETE], [RANKING-COMPLETE]) for required fields and requests resend if malformed

### Skill UX

- [ ] **SKUX-01**: All 5 skill descriptions are optimized for natural language triggering (NMR, structure determination, unknown compound, blind testing, etc.)
- [ ] **SKUX-02**: Routing page (lucy-ng.md) includes a decision tree guiding users to the correct sub-command
- [ ] **SKUX-03**: sanitise.md includes a dry-run mode that scans and reports findings without modifying files, requiring user confirmation before proceeding
- [ ] **SKUX-04**: predict.md handles HOSE code miss gracefully with suggestions (alternative SMILES, database coverage note)
- [ ] **SKUX-05**: dereplicate.md handles 0-match results with actionable guidance (check formula, try related formulas, compound may not be in database)

### Operations

- [ ] **OPER-01**: status.md checks lucy-ng CLI version against minimum required version and reports incompatibility clearly
- [ ] **OPER-02**: A lightweight smoke test mode exists for /lucy-ng:case that runs 1 iteration to verify the full pipeline (team spawn, peak picking, LSD file build, DA validation) without running to convergence

## Future Requirements

Deferred to future releases.

- **4J-01**: Statistical 4J HMBC coupling detection from database (DB-based probability for atom-type pairs)
- **UAT-01**: Multi-compound CASE comparison UAT with non-aromatic test compounds
- **COSY-01**: COSY correlation integration in LSD constraints
- **NPLIKE-01**: NP-likeness scoring for solution filtering
- **FRAG-05**: Multi-fragment sequential injection

## Out of Scope

| Feature | Reason |
|---------|--------|
| Python code refactoring | v6.0 is skill/agent quality, not Python infrastructure |
| New CLI commands | No new Python tools needed for skill improvements |
| Database schema changes | No data model changes in this milestone |
| Full CASE UAT on compounds | Blocked by 4J detection; smoke test sufficient for v6.0 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 55 | Complete |
| ARCH-02 | Phase 55 | Complete |
| ARCH-03 | Phase 55 | Complete |
| INTL-01 | Phase 56 | Complete |
| INTL-02 | Phase 56 | Complete |
| INTL-03 | Phase 56 | Complete |
| INTL-04 | Phase 56 | Complete |
| SKUX-01 | Phase 57 | Pending |
| SKUX-02 | Phase 57 | Pending |
| SKUX-03 | Phase 57 | Pending |
| SKUX-04 | Phase 57 | Pending |
| SKUX-05 | Phase 57 | Pending |
| OPER-01 | Phase 58 | Pending |
| OPER-02 | Phase 58 | Pending |

**Coverage:**
- v6.0 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 after roadmap created — all 14 requirements mapped*
