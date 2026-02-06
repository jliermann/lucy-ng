# lucy-ng Roadmap

## Milestones

- ✅ [v1.0 Core CASE Pipeline](milestones/v1.0-ROADMAP.md) - Phases 1-10 (shipped 2026-01-12)
- ✅ [v1.1 Database-Backed Dereplication](milestones/v1.1-ROADMAP.md) - Phases 11-15 (shipped 2026-01-15)
- ✅ [v1.2 HOSE Database Prediction](milestones/v1.2-ROADMAP.md) - Phases 16-19 (shipped 2026-01-18)
- **v2.0 Robust Multi-Agent CASE** - Phases 20-26 (in progress)

---

<details>
<summary>v1.0 Core CASE Pipeline (Phases 1-10) - COMPLETE 2026-01-12</summary>

### Phase 1: Foundation
**Goal**: Project structure, dependencies, and NMR library evaluation

- Set up Python package structure with modern tooling (pyproject.toml)
- Research and evaluate NMR parsing libraries (nmrglue, bruker-reader, etc.)
- Establish core data models for spectra and peaks
- Basic test infrastructure

**Research**: NMR parsing library selection

---

### Phase 2: 1D NMR Reading
**Goal**: Read Bruker 1D spectra (1H, 13C) reliably

- Implement Bruker 1D file reader (fid, acqus, procs)
- Parse acquisition and processing parameters
- Handle spectrum data (real/imaginary, processed)
- Data structures for 1D spectra with metadata

---

### Phase 2.1: 1D Carbon Dereplication (INSERTED)
**Goal**: Validate pipeline with 1D dereplication against nmrshiftdb

- Peak picking from 1D 13C spectrum
- Download/query reference data from nmrshiftdb by molecular formula
- Match observed peaks against reference spectra
- Score and rank candidate structures
- Return dereplication results (match/no match/candidates)

**Depends on:** Phase 2
**Research**: nmrshiftdb API/data format, matching algorithms

---

### Phase 3: 2D NMR Reading
**Goal**: Read Bruker 2D spectra (HSQC, HMBC)

- Implement Bruker 2D file reader (ser, acqu2s)
- Parse 2D acquisition parameters (F1/F2 dimensions)
- Handle 2D data matrices
- Data structures for 2D spectra with correlation information

---

### Phase 4: Peak Picking
**Goal**: Automated peak detection for 1D and 2D spectra

- 1D peak picking algorithm (threshold, noise estimation)
- 2D peak picking (local maxima, cross-peak detection)
- Peak list data structures
- Peak filtering and validation

**Research**: Peak picking algorithms and thresholds

---

### Phase 4.1: 2D Peak Picking Validation (INSERTED)
**Goal**: Validate that 2D peak picking produces scientifically reasonable results

- Cross-validate HSQC peaks against 1D 13C peaks
- Every HSQC F1 position should correspond to a 1D 13C peak
- Develop validation utility for peak list quality assurance
- Tolerance-based matching between 2D F1 and 1D peak positions

**Depends on:** Phase 4
**Rationale**: Ensure 2D peak picking is physically plausible before using peaks for structure elucidation

---

### Phase 4.2: DEPT-Guided Adaptive HSQC Peak Picking (INSERTED)
**Goal**: Use DEPT data as ground truth to adaptively tune HSQC peak picking

- Read DEPT-135 spectrum to identify all protonated carbons
- Use DEPT peaks as validation targets for HSQC
- Adaptively lower HSQC threshold until all DEPT carbons are matched
- Filter HSQC peaks to only those corresponding to real carbons
- Return validated, noise-free HSQC peak list

**Depends on:** Phase 4.1
**Rationale**: DEPT provides definitive ground truth for which carbons carry hydrogens; HSQC must find all of them

---

### Phase 5: LSD Integration
**Goal**: Generate input files and execute LSD/pyLSD solvers

- Research LSD/pyLSD input file format
- Generate constraint files from peak data
- Execute LSD/pyLSD as subprocess
- Parse and structure solution output

**Research**: LSD/pyLSD file formats and CLI interface

---

### Phase 5.1: HMBC-Guided Peak Picking (INSERTED)
**Goal**: Filter HMBC peaks using validated carbon and proton positions

- Use 13C/DEPT peaks as valid carbon positions
- Use HSQC proton positions as valid proton positions
- Filter HMBC to only peaks matching both constraints
- Reduce noise and improve LSD constraint quality

**Depends on:** Phase 5
**Rationale**: HMBC noise produces spurious correlations; filtering by known positions improves LSD results

---

### Phase 5.2: Symmetry Detection from Spectroscopic Data (INSERTED)
**Goal**: Detect molecular symmetry to properly handle equivalent atoms in LSD input

- Hydrogen counting: Compare MF hydrogen count with carbon-assigned H sum
- Detect "missing" hydrogens indicating equivalent carbons
- Intensity analysis: Identify doubled signals from relative peak intensities
- Pattern recognition: Recognize symmetric motifs (para-substituted benzene, isopropyl, etc.)
- Generate proper atom definitions for equivalent positions
- Support LSD SYME commands for equivalent atom constraints

**Depends on:** Phase 5.1
**Rationale**: Molecular symmetry causes fewer NMR signals than atoms; without handling this, LSD fails with valence errors

---

### Phase 6: CLI Interface
**Goal**: Command-line interface for all operations

- CLI framework setup (click or typer)
- Commands for reading spectra
- Commands for peak picking
- Commands for LSD execution
- Workflow commands (full pipeline)

---

### Phase 7: MCP Server
**Goal**: Model Context Protocol tools for Claude agent integration

- MCP server setup
- Tool definitions for all operations
- Structured input/output schemas
- Agent-friendly error handling and feedback

---

### Phase 8: HOSE-Based 13C Spectrum Predictor
**Goal**: Build pure Python 13C NMR predictor using HOSE codes and COCONUT database

- HOSE code generation wrapper using hosegen library
- Build lookup table from COCONUT SD file (~895K molecules)
- Predictor class with fallback to shorter HOSE radii
- Confidence scoring based on match count and variance
- CLI command for shift prediction
- MCP tool for agent integration

**Research**: Completed - evaluated nmrgnn, CASCADE, nmr_mpnn (all had dependency issues); HOSE codes selected

---

### Phase 9: LSD Solution Ranking
**Goal**: Rank LSD solutions by similarity between experimental 13C spectrum and predicted spectrum

- Use Phase 8 predictor for candidate structure shifts
- Compare predicted shifts with experimental 13C peaks
- Score solutions by spectrum similarity (e.g., MAE, RMSE, or cosine similarity)
- Rank and filter solutions by prediction quality
- Return ranked solution list with confidence scores

**Depends on:** Phase 8 (HOSE Predictor)

---

### Phase 10: NMRXiv Dataset Fetching
**Goal**: Fetch spectroscopic datasets from nmrxiv.org for structure elucidation

- Research NMRXiv API and data access methods
- Implement dataset fetching by identifier or search criteria
- Parse and convert NMRXiv data to lucy-ng formats
- CLI command for dataset retrieval
- MCP tool for agent integration

**Depends on:** Phase 6 (CLI Interface)

</details>

---

<details>
<summary>v1.1 Database-Backed Dereplication (Phases 11-15) -- SHIPPED 2026-01-15</summary>

### Phase 11: Database Schema
**Goal**: Design and implement SQLite schema for compounds and 13C shifts, indexed by molecular formula
**Plans**: 1/1 complete
**Completed**: 2026-01-13

---

### Phase 12: Database Import
**Goal**: Build import scripts for NMRShiftDB and COCONUT SDF files
**Plans**: 1/1 complete
**Completed**: 2026-01-13

---

### Phase 13: Database Query API
**Goal**: Implement query interface for formula-based compound lookup
**Plans**: 1/1 complete
**Completed**: 2026-01-13

---

### Phase 14: CLI Integration
**Goal**: Update `lucy dereplicate c13` to use database backend
**Plans**: 1/1 complete
**Completed**: 2026-01-15

---

### Phase 15: MCP Integration
**Goal**: Update MCP tool for database-backed dereplication
**Plans**: 1/1 complete
**Completed**: 2026-01-15

</details>

---

<details>
<summary>v1.2 HOSE Database Prediction (Phases 16-19) -- SHIPPED 2026-01-18</summary>

### Phase 16: Database Schema
**Goal**: Add hose_stats table to compounds.db for HOSE-based shift prediction
**Depends on**: Milestone v1.1 complete
**Completed**: 2026-01-15
**Plans**: 1/1 complete

---

### Phase 17: HOSE Generation
**Goal**: Batch generate HOSE codes (radii 1-6) for all 895K COCONUT compounds
**Depends on**: Phase 16
**Completed**: 2026-01-16
**Plans**: 1/1 complete

---

### Phase 18: Prediction API
**Goal**: Update HOSEPredictor to query database with radius fallback
**Depends on**: Phase 17
**Completed**: 2026-01-18
**Plans**: 1/1 complete

---

### Phase 19: CLI/MCP Integration
**Goal**: Update `lucy predict c13` CLI and MCP tools for database-backed prediction
**Depends on**: Phase 18
**Completed**: 2026-01-18
**Plans**: 1/1 complete

</details>

---

### v2.0 Robust Multi-Agent CASE (Phases 20-26)

**Milestone Goal:** Transform lucy-ng from a tool-heavy system into an AI-first skill with thin tool wrappers and a multi-agent architecture that prevents unproductive loops during structure elucidation.

**Three pillars:**
1. Audit and Simplify -- examine every component, classify intelligence for migration
2. Skill Rewrite -- incremental HMBC strategy, error tolerance as AI knowledge, spectral quality assessment
3. Multi-Agent Architecture -- supervisor + CASE agent + diagnostic specialist; supervisor detects loops and redirects

**Phase overview:**

- [ ] **Phase 20: System Audit** -- Classify all components by intelligence level; produce actionable migration plan
- [ ] **Phase 21: Skill Restructure** -- Split CLAUDE.md into project-level and CASE workflow documents
- [ ] **Phase 22: HMBC Strategy and Spectral Quality** -- Encode incremental constraint strategy and quality assessment in skill
- [ ] **Phase 23: Error Tolerance and Confidence** -- Encode error handling patterns and confidence-annotated output in skill
- [ ] **Phase 24: Supervisor Agent** -- Create supervisor with loop detection, intervention strategies, and escalation
- [ ] **Phase 25: Diagnostic Specialist** -- Create LSD expert agent for systematic failure diagnosis
- [ ] **Phase 26: Thin Tools** -- Migrate embedded intelligence from MCP tools to skill; tools become data access wrappers

---

### Phase 20: System Audit
**Goal**: Every CLI command, MCP tool, and skill section classified by intelligence level with a concrete migration recommendation
**Depends on**: Nothing (first phase of v2.0)
**Requirements**: AUDT-01, AUDT-02, AUDT-03, AUDT-04
**Success Criteria** (what must be TRUE):
  1. All 16 MCP tools classified as Tier 1 (keep), Tier 2 (migrate strategy to skill), or Tier 3 (refactor to thin wrapper)
  2. All 7 CLI command groups classified with recommendation for what intelligence stays vs moves to skill
  3. CLAUDE.md sections catalogued with duplication and misplacement identified
  4. Audit report exists with specific, actionable recommendation per component (not generic "simplify later")
**Plans**: TBD

---

### Phase 21: Skill Restructure
**Goal**: CASE workflow knowledge lives in a dedicated skill document separate from project-level instructions, with no duplication between documents
**Depends on**: Phase 20 (audit identifies what goes where)
**Requirements**: SKIL-01, SKIL-02, SKIL-03, SKIL-04
**Success Criteria** (what must be TRUE):
  1. CLAUDE.md contains only project-level content (setup, database, developer reference, quick reference) and is under 800 lines
  2. SKILL.md contains the full CASE workflow (dereplication through ranking) with checkpoint markers for supervisor monitoring
  3. SUPERVISOR.md exists with loop detection patterns, intervention strategies, and escalation criteria
  4. No paragraph of domain knowledge appears in more than one document
**Plans**: TBD

---

### Phase 22: HMBC Strategy and Spectral Quality
**Goal**: The CASE skill teaches an incremental constraint strategy and spectral quality awareness so the AI agent builds LSD files in phases rather than dumping all correlations at once
**Depends on**: Phase 21 (needs SKILL.md to add content to)
**Requirements**: HMBC-01, HMBC-02, HMBC-03, HMBC-04, QUAL-01, QUAL-02, QUAL-03
**Success Criteria** (what must be TRUE):
  1. SKILL.md contains a 3-phase HMBC constraint addition strategy (core structure from high-confidence signals, resolve ambiguity with diagnostic correlations, refine with full constraint set)
  2. SKILL.md explicitly states "start with 5-10 high-confidence HMBC correlations" and the decision tree for when to add more vs investigate failures
  3. SKILL.md explicitly prohibits the "use all correlations from peak picking" approach
  4. SKILL.md contains spectral quality assessment section covering S/N evaluation, digital resolution impact on close carbons, and artifact recognition (1J correlations, t1 noise, baseline roll)
  5. An AI agent reading SKILL.md would know to assess spectrum quality BEFORE picking peaks and to adjust expectations based on quality findings
**Plans**: TBD

---

### Phase 23: Error Tolerance and Confidence
**Goal**: The CASE skill teaches proactive error detection and requires confidence-annotated output so the AI agent documents ambiguity instead of guessing
**Depends on**: Phase 21 (needs SKILL.md to add content to)
**Requirements**: ETOL-01, ETOL-02, ETOL-03, ETOL-04, CONF-01, CONF-02, CONF-03
**Success Criteria** (what must be TRUE):
  1. SKILL.md teaches close carbon shift detection -- AI identifies carbons within 0.3-0.5 ppm and documents the ambiguity before building LSD constraints
  2. SKILL.md teaches DEPT phase conflict handling -- AI compares HSQC vs DEPT multiplicities and chooses ground truth with documented reasoning
  3. SKILL.md teaches ambiguous HMBC assignment -- AI generates LSD variants when carbon positions are close (<1 ppm) rather than picking one arbitrarily
  4. SKILL.md teaches quaternary carbon HMBC sparsity -- AI uses chemical shift to constrain heteroatom attachment when few HMBC correlations are visible
  5. CASE workflow produces assignments with confidence levels (High >90%, Medium 60-90%, Low <60%) and explicitly flags where additional NMR experiments might help
**Plans**: TBD

---

### Phase 24: Supervisor Agent
**Goal**: A supervisor agent can detect when the CASE agent is stuck in an unproductive loop and intervene with a specific diagnosis-first redirect
**Depends on**: Phase 21 (needs SUPERVISOR.md as knowledge source)
**Requirements**: SUPV-01, SUPV-02, SUPV-03, SUPV-04, SUPV-05, SUPV-06, SUPV-07
**Success Criteria** (what must be TRUE):
  1. Supervisor agent is defined as a Claude Code subagent (markdown file with YAML frontmatter in `.claude/agents/`)
  2. Supervisor detects ELIM thrashing -- adding ELIM repeatedly without diagnosing root cause triggers intervention
  3. Supervisor detects zero-solution loops -- 3+ attempts with 0 solutions and same approach triggers redirect
  4. Supervisor detects solution explosion -- 1000+ solutions with minor tweaks not reducing count triggers redirect
  5. Every supervisor intervention requires diagnosis before allowing retry (not generic "try again" -- specific like "validate sp2 count before trying ELIM")
  6. Supervisor escalates to user after 3 failed attempts with the same detected pattern
**Plans**: TBD

---

### Phase 25: Diagnostic Specialist
**Goal**: A diagnostic specialist agent can systematically determine WHY LSD failed and produce a structured report with root cause and recommended fixes
**Depends on**: Phase 24 (needs supervisor pattern validated; specialist uses same subagent mechanism)
**Requirements**: DIAG-01, DIAG-02, DIAG-03, DIAG-04, DIAG-05
**Success Criteria** (what must be TRUE):
  1. Diagnostic specialist is defined as a Claude Code subagent with deep LSD manual knowledge (MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM)
  2. For 0-solution failures: specialist systematically checks sp2 count (even?), hydrogen budget (matches formula?), HMBC conflicts, and correlation order -- and reports which check failed
  3. For 1000+ solution failures: specialist checks constraint count, quaternary carbon connectivity, heteroatom constraints, and symmetry encoding -- and reports which is insufficient
  4. Specialist produces a structured diagnostic report (markdown) with findings, root cause, and recommended fixes that the CASE agent can act on
**Plans**: TBD

---

### Phase 26: Thin Tools
**Goal**: MCP tools are data access wrappers with no embedded domain logic; intelligence previously in Python has been migrated to the skill where the AI can reason about it
**Depends on**: Phases 22, 23, 24 (skill content must encode the intelligence being removed from tools; multi-agent validated)
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04
**Success Criteria** (what must be TRUE):
  1. MCP tools contain no embedded domain logic -- peak picking tools return raw peaks above threshold without DEPT-guided filtering or HMBC validation
  2. Intelligence previously in Python (adaptive thresholding, conflict resolution, auto-constraint generation) is documented in SKILL.md as AI-executable strategy
  3. CLI retains smart behavior for backward compatibility (dual mode: `lucy pick hsqc` still uses DEPT-guided algorithm; MCP tool returns raw peaks)
  4. An AI agent using the thin MCP tools plus SKILL.md can reproduce the same analysis quality as the current smart tools -- validated on at least one test compound
**Plans**: TBD

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Foundation | v1.0 | 1/1 | Complete | 2026-01-08 |
| 2. 1D NMR Reading | v1.0 | 1/1 | Complete | 2026-01-08 |
| 2.1 1D Carbon Dereplication | v1.0 | 1/1 | Complete | 2026-01-09 |
| 3. 2D NMR Reading | v1.0 | 1/1 | Complete | 2026-01-09 |
| 4. Peak Picking | v1.0 | 1/1 | Complete | 2026-01-09 |
| 4.1 2D Peak Validation | v1.0 | 1/1 | Complete | 2026-01-10 |
| 4.2 DEPT-Guided HSQC | v1.0 | 1/1 | Complete | 2026-01-10 |
| 5. LSD Integration | v1.0 | 1/1 | Complete | 2026-01-10 |
| 5.1 HMBC-Guided Picking | v1.0 | -- | Complete | 2026-01-10 |
| 5.2 Symmetry Detection | v1.0 | -- | Complete | 2026-01-10 |
| 6. CLI Interface | v1.0 | 1/1 | Complete | 2026-01-11 |
| 7. MCP Server | v1.0 | 1/1 | Complete | 2026-01-11 |
| 8. HOSE Predictor | v1.0 | 1/1 | Complete | 2026-01-11 |
| 9. LSD Solution Ranking | v1.0 | 1/1 | Complete | 2026-01-12 |
| 10. NMRXiv Fetching | v1.0 | 1/1 | Complete | 2026-01-12 |
| 11. Database Schema | v1.1 | 1/1 | Complete | 2026-01-13 |
| 12. Database Import | v1.1 | 1/1 | Complete | 2026-01-13 |
| 13. Database Query API | v1.1 | 1/1 | Complete | 2026-01-13 |
| 14. CLI Integration | v1.1 | 1/1 | Complete | 2026-01-15 |
| 15. MCP Integration | v1.1 | 1/1 | Complete | 2026-01-15 |
| 16. Database Schema | v1.2 | 1/1 | Complete | 2026-01-15 |
| 17. HOSE Generation | v1.2 | 1/1 | Complete | 2026-01-16 |
| 18. Prediction API | v1.2 | 1/1 | Complete | 2026-01-18 |
| 19. CLI/MCP Integration | v1.2 | 1/1 | Complete | 2026-01-18 |
| 20. System Audit | v2.0 | TBD | Not started | - |
| 21. Skill Restructure | v2.0 | TBD | Not started | - |
| 22. HMBC Strategy + Quality | v2.0 | TBD | Not started | - |
| 23. Error Tolerance + Confidence | v2.0 | TBD | Not started | - |
| 24. Supervisor Agent | v2.0 | TBD | Not started | - |
| 25. Diagnostic Specialist | v2.0 | TBD | Not started | - |
| 26. Thin Tools | v2.0 | TBD | Not started | - |

---
*Last updated: 2026-02-06*
