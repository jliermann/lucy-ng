# lucy-ng Roadmap

## Milestones

- ✅ [v1.0 Core CASE Pipeline](milestones/v1.0-ROADMAP.md) - Phases 1-10 (shipped 2026-01-12)
- ✅ [v1.1 Database-Backed Dereplication](milestones/v1.1-ROADMAP.md) - Phases 11-15 (shipped 2026-01-15)
- ✅ [v1.2 HOSE Database Prediction](milestones/v1.2-ROADMAP.md) - Phases 16-19 (shipped 2026-01-18)
- ✅ **v2.0 Robust Multi-Agent CASE** - Phases 20-26 (completed 2026-02-08)
- ✅ **v2.1 Working Multi-Agent CASE** - Phases 27-33 (completed 2026-02-09)
- 🚧 **v3.0 Statistical Detection** - Phases 34-40 (in progress)

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

<details>
<summary>v2.0 Robust Multi-Agent CASE (Phases 20-26) -- SHIPPED 2026-02-08</summary>

**Milestone Goal:** Transform lucy-ng from a tool-heavy system into an AI-first skill with thin tool wrappers and a multi-agent architecture that prevents unproductive loops during structure elucidation.

**Three pillars:**
1. Audit and Simplify -- examine every component, classify intelligence for migration
2. Skill Rewrite -- incremental HMBC strategy, error tolerance as AI knowledge, spectral quality assessment
3. Multi-Agent Architecture -- supervisor + CASE agent + diagnostic specialist; supervisor detects loops and redirects

**Phase overview:**

- [x] **Phase 20: System Audit** -- COMPLETE 2026-02-06. 15 MCP tools, 9 CLI groups, 1,080-line CLAUDE.md classified
- [x] **Phase 21: Skill Restructure** -- COMPLETE 2026-02-06. CLAUDE.md 305 lines, SKILL.md 418 lines, SUPERVISOR.md 78 lines, zero duplication
- [x] **Phase 22: HMBC Strategy and Spectral Quality** -- COMPLETE 2026-02-06. SKILL.md 610 lines (+192), spectral quality + incremental HMBC strategy
- [x] **Phase 23: Error Tolerance and Confidence** -- COMPLETE 2026-02-07. SKILL.md 1,079 lines (+469), error tolerance + ambiguity detection + confidence scoring
- [x] **Phase 24: Supervisor Agent** -- COMPLETE 2026-02-07. Supervisor agent at .claude/agents/supervisor.md (383 lines), skill/supervisor/SKILL.md (678 lines), CASE-PROGRESS.md checkpoint writing
- [x] **Phase 25: Diagnostic Specialist** -- COMPLETE 2026-02-07. skill/diagnostic/SKILL.md (1,874 lines), .claude/agents/diagnostic-specialist.md (455 lines), supervisor integration
- [x] **Phase 26: Thin Tools** -- COMPLETE 2026-02-08. MCP removed, CLI thinned, intelligence in skills, Ibuprofen CASE validated

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
**Plans**: 3 plans
Plans:
- [x] 20-01-PLAN.md -- Audit MCP tools and CLI commands (tier classification)
- [x] 20-02-PLAN.md -- Audit CLAUDE.md (duplication and misplacement analysis)
- [x] 20-03-PLAN.md -- Compile final audit report with migration roadmap

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
**Plans**: 3 plans
Plans:
- [x] 21-01-PLAN.md -- Write canonical skill/SKILL.md with deduplicated CASE domain knowledge (~500 lines)
- [x] 21-02-PLAN.md -- Trim CLAUDE.md to project-level content (~298 lines) and create supervisor skill
- [x] 21-03-PLAN.md -- Update subskills to remove duplication and verify zero cross-document duplication

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
**Plans**: 1 plan
Plans:
- [x] 22-01-PLAN.md -- Add Spectral Quality Assessment + Incremental HMBC Strategy to SKILL.md, update CASE Workflow and Quick Reference

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
**Plans**: 2 plans
Plans:
- [x] 23-01-PLAN.md -- Add Error Tolerance and Ambiguity Detection section to SKILL.md (close carbons, DEPT/HSQC conflicts, quaternary HMBC sparsity)
- [x] 23-02-PLAN.md -- Add Confidence Scoring section and integrate into CASE Workflow and Quick Reference

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
**Plans**: 2 plans
Plans:
- [x] 24-01-PLAN.md -- Expand supervisor SKILL.md with loop detection, diagnostics, convergence, CASE-PROGRESS.md format + update CASE subskill with checkpoint writing
- [x] 24-02-PLAN.md -- Create .claude/agents/supervisor.md agent definition with routing, supervision, and intervention logic

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
**Plans**: 2 plans
Plans:
- [x] 25-01-PLAN.md -- Create diagnostic specialist skill (skill/diagnostic/SKILL.md) and agent definition (.claude/agents/diagnostic-specialist.md)
- [x] 25-02-PLAN.md -- Update supervisor agent and skill to integrate diagnostic specialist delegation

---

### Phase 26: Thin Tools
**Goal**: MCP removed entirely, CLI commands are thin data-access wrappers, AI agent is sole intelligence layer using skill documents for all reasoning
**Depends on**: Phases 22, 23, 24 (skill content must encode the intelligence being removed from tools; multi-agent validated)
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04
**Success Criteria** (what must be TRUE):
  1. MCP server removed entirely -- no src/lucy_ng/mcp/, no lucy-mcp entry point
  2. CLI commands are thin data-access wrappers -- pick hsqc/hmbc return raw peaks, analyze symmetry returns raw counts, lsd generate removed
  3. Intelligence previously in Python documented in SKILL.md as AI-executable strategy
  4. AI agent using thin CLI + SKILL.md solves Ibuprofen de novo CASE with correct structure in top 3
**Plans**: 5 plans
Plans:
- [x] 26-01-PLAN.md -- Remove MCP server entirely and clean up pyproject.toml
- [x] 26-02-PLAN.md -- Thin Tier 3 CLI commands (pick hsqc/hmbc raw, remove lsd generate, thin analyze symmetry)
- [x] 26-03-PLAN.md -- Consolidate duplicated code (database finder, LSD parser)
- [x] 26-04-PLAN.md -- Update CLAUDE.md, skill files, and agent definitions for CLI-only architecture
- [x] 26-05-PLAN.md -- Validate Ibuprofen de novo CASE with thin CLI + skill knowledge

</details>

---

<details>
<summary>v2.1 Working Multi-Agent CASE (Phases 27-33) -- SHIPPED 2026-02-09</summary>

**Milestone Goal:** Make multi-agent CASE orchestration actually work by implementing Claude Code's native orchestration primitives correctly, replacing v2.0's paper-only architecture with working sub-command skills that spawn agents, monitor progress, detect loops, and intervene autonomously.

**Core shift:** Supervisor logic dissolves from separate agent (supervisor.md) into orchestrator sub-command skill (case.md). Skills become entry points that spawn worker agents with inlined domain knowledge. Validation-first development prevents repeating v2.0's paper architecture mistake.

**Phase overview:**

- [x] **Phase 27: Sub-Command Skills Foundation** -- COMPLETE 2026-02-08. ~/.claude/commands/lucy-ng/ with 4 files (status, dereplicate, predict, routing page)
- [x] **Phase 28: CASE Agent Definition** -- COMPLETE 2026-02-08. ~/.claude/agents/lucy-case-agent.md (613 lines, 528 inlined knowledge, all 5 CASE reqs validated)
- [x] **Phase 29: CASE Orchestrator Skill** -- COMPLETE 2026-02-08. ~/.claude/commands/lucy-ng/case.md (622 lines, 9 requirements, 12-step orchestration)
- [x] **Phase 30: Diagnostic Specialist Integration** -- COMPLETE 2026-02-08. ~/.claude/agents/lucy-diagnostic.md + delegation wired into case.md (3 requirements, 7/7 must-haves)
- [x] **Phase 31: Sanitization Skill** -- COMPLETE 2026-02-08. ~/.claude/commands/lucy-ng/sanitise.md (422 lines, pure AI workflow, 5 requirements, 7/7 must-haves)
- [x] **Phase 32: End-to-End Validation** -- COMPLETE 2026-02-08. 31/31 pre-flight checks passed, 530-line validation guide created, all VALD requirements documented
- [x] **Phase 33: Documentation and Cleanup** -- COMPLETE 2026-02-09. CLAUDE.md updated with sub-command reference, PROJECT.md refreshed, diagnostic agent hybrid inlined (1,145 lines), v2.1 release notes written

---

### Phase 27: Sub-Command Skills Foundation
**Goal**: Simple sub-command skills work and validate the GSD pattern before complex orchestration
**Depends on**: Phase 26 (thin CLI validated)
**Requirements**: SCMD-01, SCMD-04, SCMD-05, SCMD-06, SCMD-07
**Success Criteria** (what must be TRUE):
  1. Directory ~/.claude/commands/lucy-ng/ exists with proper permissions
  2. /lucy-ng:status runs and reports lucy-ng version, LSD availability, database presence
  3. /lucy-ng:dereplicate wraps `lucy dereplicate c13` and returns top matches with scores
  4. /lucy-ng:predict wraps `lucy predict c13` and returns shift predictions with confidence
  5. Old monolithic /lucy-ng skill replaced with routing page listing all sub-commands

**Plans**: 2 plans

Plans:
- [x] 27-01-PLAN.md -- Create directory, status.md, and dereplicate.md skills
- [x] 27-02-PLAN.md -- Create predict.md skill and routing page

---

### Phase 28: CASE Agent Definition
**Goal**: Autonomous CASE agent spawns successfully and writes structured progress before orchestrator depends on it
**Depends on**: Phase 27 (foundation validated)
**Requirements**: CASE-01, CASE-02, CASE-03, CASE-04, CASE-05
**Success Criteria** (what must be TRUE):
  1. Agent definition at ~/.claude/agents/lucy-case-agent.md with valid YAML frontmatter (name, description, tools: Read + Write + Bash + Glob + Grep)
  2. Agent receives inlined skill content (NMR background, CASE workflow, LSD basics) approximately 500-700 lines plus file path references for detailed knowledge
  3. Agent executes CASE workflow and writes CASE-PROGRESS.md after every LSD iteration with required fields (solution count, constraints added/removed, reasoning, confidence, sp2/H checks)
  4. Agent never attempts dereplication (absolute workflow separation validated)
  5. Integration test passes: spawn agent with minimal task, verify CASE-PROGRESS.md created with expected structure

**Plans**: 1 plan

Plans:
- [x] 28-01-PLAN.md -- Create lucy-case-agent.md with YAML frontmatter, inlined skill knowledge, workflow, and progress format; validate against all 5 CASE requirements

---

### Phase 29: CASE Orchestrator Skill
**Goal**: Core orchestration working -- spawn agent with context, monitor progress, detect 4 loop patterns, diagnose, intervene, escalate
**Depends on**: Phase 28 (agent proven spawn-able)
**Requirements**: SCMD-02, ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05, ORCH-06, ORCH-07, ORCH-08
**Success Criteria** (what must be TRUE):
  1. Skill file at ~/.claude/commands/lucy-ng/case.md spawns lucy-case-agent via Task() with hybrid context inlining (critical workflow inlined, detailed references via file paths)
  2. Orchestrator reads CASE-PROGRESS.md after agent completes and successfully parses solution count, constraints, reasoning
  3. Orchestrator detects ELIM thrashing (ELIM added 2+ times), zero-solution loop (3+ iterations with 0 solutions), solution explosion (3+ iterations >100 solutions <10% reduction), constraint churning (5+ iterations high add/remove activity)
  4. Orchestrator performs basic diagnosis (sp2 count even, H budget matches formula, 1J artifacts within tolerance) before intervention
  5. Orchestrator generates advisory interventions (WHAT to fix, not HOW) -- never prescribes specific LSD file edits
  6. Orchestrator tracks intervention counts separately per pattern (not global counter)
  7. Orchestrator escalates to user after 10 failed intervention cycles per pattern
  8. Orchestrator re-spawns agent with advisory constraints and skip-completed-work instructions in handoff

**Plans**: 1 plan

Plans:
- [x] 29-01-PLAN.md -- Create case.md orchestrator skill with spawning, monitoring, loop detection, diagnosis, advisory, escalation, re-spawning; update routing page

---

### Phase 30: Diagnostic Specialist Integration
**Goal**: Deep LSD failure analysis delegated to specialist after basic interventions fail
**Depends on**: Phase 29 (orchestrator working)
**Requirements**: DIAG-06, DIAG-07, DIAG-08
**Success Criteria** (what must be TRUE):
  1. Agent definition renamed from ~/.claude/agents/diagnostic-specialist.md to ~/.claude/agents/lucy-diagnostic.md with updated frontmatter (agent name matches new file)
  2. Orchestrator delegates to diagnostic specialist after 2 failed interventions with same loop pattern
  3. Orchestrator reads DIAGNOSTIC-REPORT.md, extracts root cause and primary fix, and includes in CASE agent advisory on next spawn
  4. Integration test passes: force repeated zero-solution failure, verify specialist spawned after 2 basic intervention failures, DIAGNOSTIC-REPORT.md created with systematic check results

**Plans**: 1 plan

Plans:
- [x] 30-01-PLAN.md -- Rename diagnostic agent to lucy-diagnostic.md, wire delegation trigger + specialist spawning + report parsing into case.md orchestrator

---

### Phase 31: Sanitization Skill
**Goal**: AI-driven compound identifier removal for blind dataset evaluation
**Depends on**: Phase 27 (independent from orchestration)
**Requirements**: SCMD-03, SANT-01, SANT-02, SANT-03, SANT-04
**Success Criteria** (what must be TRUE):
  1. Skill file at ~/.claude/commands/lucy-ng/sanitise.md with explicit statement: "There is NO CLI command for sanitization -- this requires AI semantic reasoning"
  2. AI detects compound identifiers: chemical names (IUPAC, common), SMILES strings, InChI/InChIKey, CAS numbers, MOL file structures, dataset naming patterns (e.g., "Ibuprofen_HSQC")
  3. AI generates redaction manifest and applies bulk sanitization using existing helper scripts (lucy_text_extractor.py, lucy_bulk_sanitize.py)
  4. Skill verifies completeness by re-extracting text and confirming no identifiers remain

NOTE: Success criterion #3 mentions helper scripts but CONTEXT.md OVERRIDES this -- pure AI approach, no scripts.

**Plans**: 1 plan

Plans:
- [x] 31-01-PLAN.md -- Create sanitise.md skill, delete old skill/sanitize/ directory, update routing page

---

### Phase 32: End-to-End Validation
**Goal**: All orchestration components validated through comprehensive integration tests before milestone ships
**Depends on**: Phases 29, 30, 31 (all features complete)
**Requirements**: VALD-01, VALD-02, VALD-03, VALD-04, VALD-05
**Success Criteria** (what must be TRUE):
  1. Integration test passes: orchestrator spawns CASE agent, agent writes CASE-PROGRESS.md, orchestrator reads and parses progress
  2. Loop detection test passes: construct known failure patterns (force ELIM thrashing, force zero solutions, force explosion), verify orchestrator detects and intervenes
  3. Diagnostic delegation test passes: repeated failures with same pattern trigger specialist spawn, DIAGNOSTIC-REPORT.md generated and consumed by orchestrator
  4. Ibuprofen CASE passes via /lucy-ng:case -- reproduces Phase 26-05 success through full orchestration (spawn → monitor → detect → intervene if needed → converge to correct structure in top 3)
  5. All simple sub-commands work: /lucy-ng:dereplicate returns matches, /lucy-ng:predict returns shifts, /lucy-ng:status reports system readiness

**Plans**: 1 plan

Plans:
- [x] 32-01-PLAN.md -- Run pre-flight checks, create validation guide with test instructions and expected outcomes

---

### Phase 33: Documentation and Cleanup
**Goal**: Remove deprecated components and update documentation for v2.1 architecture
**Depends on**: Phase 32 (validation passed)
**Requirements**: CLNP-01, CLNP-02, CLNP-03
**Success Criteria** (what must be TRUE):
  1. File ~/.claude/agents/supervisor.md deleted (logic now in case.md orchestrator)
  2. CLAUDE.md updated with sub-command reference section listing all /lucy-ng:* commands with one-line descriptions
  3. PROJECT.md decisions table updated with v2.1 architecture choices (orchestration via Task(), hybrid context inlining, per-pattern intervention counters, diagnostic delegation threshold)
  4. v2.1 release notes written summarizing working multi-agent orchestration vs v2.0 paper architecture

**Plans**: 2 plans

Plans:
- [x] 33-01-PLAN.md -- Update CLAUDE.md with sub-command reference and corrected architecture; write v2.1 release notes
- [x] 33-02-PLAN.md -- Refresh PROJECT.md to v2.1 reality; inline LSD knowledge into diagnostic agent; confirm supervisor.md deletion

</details>

---

## v3.0 Statistical Detection (Phases 34-40)

**Milestone Goal:** Add data-driven statistical detection to replace agent guesswork in structure elucidation. Agent autonomously uses HOSE database statistics to constrain LSD input files with hybridisation, neighbourhood, and hetero-hetero bond detection. Two-tier ranking and badlist filters prevent MAE hallucinations. Inspired by Sherlock CASE system (Wenk PhD thesis) which achieved 5 orders of magnitude search space reduction.

**Motivation:** Live ibuprofen CASE testing revealed that v2.1 produces wrong cyclohexadiene solutions because agent lacks statistical constraints. Sherlock solves the same case trivially because hybridisation + neighbourhood constraints reduce search space dramatically (Caripyrin: 8.5M → 30 structures). Without data-driven constraints, the AI agent is guessing.

**Phase overview:**

- [x] **Phase 34: Hybridisation Detection** - Database schema extension, statistics generation, CLI command for sp1/sp2/sp3 detection from shift queries
- [x] **Phase 35: Neighbourhood Detection** - Bond partner statistics, CLI commands for forbidden/mandatory neighbour detection from HOSE sphere 1
- [x] **Phase 36: HHB and Ring Detection** - Hetero-hetero bond statistics, ring statistics for badlist foundation
- [x] **Phase 37: Signal Grouping** - Multiplicity-aware close shift detection, LSD parenthesized atom list generation
- [x] **Phase 38: Two-Tier Ranking and Badlist** - Match-count-first ranking, hardcoded 3/4-membered ring filters in agent
- [ ] **Phase 39: Agent Integration** - CASE agent learns statistical detection protocol, chemistry-first hierarchy, threshold overrides
- [ ] **Phase 40: Validation** - Test suite with Sherlock's 45 cases, metrics (accuracy, search space reduction, rank improvement)

---

### Phase 34: Hybridisation Detection
**Goal**: Agent can query database for hybridisation state distribution of any 13C shift
**Depends on**: Phase 33 (v2.1 complete)
**Requirements**: DETECT-01, DETECT-06, DETECT-07
**Success Criteria** (what must be TRUE):
  1. Database schema extended with hybridization column in hose_stats table (TEXT storing sp3/sp2/sp1)
  2. Statistics generator computes sp2/sp3/sp1 fractions during HOSE processing and stores in database
  3. CLI command `lucy detect hybridisation <db> <shift>` returns JSON with sp2/sp3/sp1 fractions and confidence
  4. Detection queries shift +/- 2 ppm window and returns distributions excluding states <1% frequency
  5. Command works on existing lucy-ng-derep.db after schema migration or fresh generation
**Plans**: 3 plans

Plans:
- [x] 34-01-PLAN.md -- Extend database schema (v3->v4), migration script, shift-window query method
- [x] 34-02-PLAN.md -- Update stats_generator.py to extract and store hybridisation during HOSE processing
- [x] 34-03-PLAN.md -- Create detection module and `lucy detect hybridisation` CLI command

---

### Phase 35: Neighbourhood Detection
**Goal**: Agent can query database for forbidden and mandatory bond partners for any 13C shift
**Depends on**: Phase 34 (schema and stats pipeline established)
**Requirements**: DETECT-02, DETECT-03, DETECT-06, DETECT-07
**Success Criteria** (what must be TRUE):
  1. Database schema extended with bond partner columns (has_carbon_neighbor, has_oxygen_neighbor, has_nitrogen_neighbor, has_sulfur_neighbor, has_halogen_neighbor integer counts)
  2. Statistics generator extracts sphere 1 neighbours from HOSE codes and computes element frequencies
  3. CLI command `lucy detect neighbours <shift>` returns forbidden elements (<1% frequency) and mandatory elements (>95% frequency)
  4. Detection supports override flags (--min-frequency, --max-frequency, --mode relaxed for rare cases)
  5. Command correctly identifies forbidden O-O bonds in non-peroxides and mandatory C=O bonds in carbonyl regions
**Plans**: 4 plans

Plans:
- [x] 35-01-PLAN.md -- Extend schema (v4->v5) with 5 neighbour columns, create HOSE sphere 1 parser, update DatabaseManager
- [x] 35-02-PLAN.md -- Update stats_generator.py WelfordAccumulator and generators to extract and track neighbours
- [x] 35-03-PLAN.md -- Extend StatisticalDetector with detect_neighbours() and add Pydantic result models
- [x] 35-04-PLAN.md -- Add `lucy detect neighbours` CLI subcommand with threshold override flags

---

### Phase 36: HHB and Ring Detection ✅ (2026-02-11)
**Goal**: Agent can query hetero-hetero bond allowance and access ring statistics for badlist filtering
**Depends on**: Phase 34 (schema established)
**Requirements**: DETECT-04, DETECT-06, DETECT-07
**Success Criteria** (what must be TRUE):
  1. Database schema extended with ring columns (in_3ring, in_4ring, in_aromatic counts)
  2. Statistics generator uses RDKit GetRingInfo() to compute ring membership during HOSE processing
  3. CLI command `lucy detect hhb <db> <formula>` returns hetero-hetero bond frequency (percentage of compounds with element pair)
  4. Detection uses 1% threshold for HHB allowance (returns "allowed" if >1% of compounds with formula contain bond pair)
  5. Ring statistics accessible for Phase 38 badlist implementation (no dedicated CLI, queried internally)
**Plans**: 3 plans
**Verified**: 18/18 must-haves passed

Plans:
- [x] 36-01-PLAN.md — Extend schema to v6 with bond_pair_stats table and ring columns
- [x] 36-02-PLAN.md — Update stats generators with ring tracking and create BondPairStatsGenerator
- [x] 36-03-PLAN.md — Add HHB detection module and `lucy detect hhb` CLI subcommand

---

### Phase 37: Signal Grouping ✅ (2026-02-11)
**Goal**: Agent can identify close carbon shifts for combinatorial LSD atom exchange
**Depends on**: Phase 34 (independent of database, but follows detection pattern)
**Requirements**: DETECT-05
**Success Criteria** (what must be TRUE):
  1. CLI command `lucy analyze grouping <shifts>` identifies clusters within 0.25 ppm tolerance
  2. Grouping is multiplicity-aware (only groups CH/CH3 together if both ambiguous, never groups CH2 with CH)
  3. Command returns LSD-compatible output format (parenthesized atom lists for HMBC constraints)
  4. Agent can use grouped output to write LSD HMBC commands like `HMBC (2 3) 8` for combinatorial exploration
  5. Documentation warns about false positive risk (close shifts that are truly different carbons)
**Plans**: 3 plans

**Verified**: 5/5 must-haves passed

Plans:
- [x] 37-01-PLAN.md — Signal grouping algorithm with Pydantic models and TDD tests
- [x] 37-02-PLAN.md — Validate LSD parenthesized syntax with actual solver runs
- [x] 37-03-PLAN.md — Add `lucy analyze grouping` CLI subcommand

---

### Phase 38: Two-Tier Ranking and Badlist ✅ (2026-02-11)
**Goal**: Solution ranking prevents MAE hallucinations and badlist excludes strained rings
**Depends on**: Phase 36 (ring statistics available)
**Requirements**: RANK-01, RANK-02, RANK-03, RANK-04
**Success Criteria** (what must be TRUE):
  1. Modified `lucy lsd rank` command ranks by signal match count first (within 10 ppm tolerance), then MAE among matched signals
  2. Solutions with fewer matched signals rank lower regardless of MAE (prevents ibuprofen cyclohexadiene hallucination)
  3. Badlist patterns for 3/4-membered rings documented in CASE agent knowledge (DEFF/FEXP NOT commands)
  4. Agent can optionally exclude strained rings by adding badlist filters to LSD input
  5. Ranking reports HOSE prediction radius used per carbon (transparency for low-confidence predictions)
**Plans**: 2 plans
**Verified**: 11/11 must-haves passed

Plans:
- [x] 38-01-PLAN.md — Two-tier ranking sort order + tests + CLI output (TDD)
- [x] 38-02-PLAN.md — Badlist patterns in CASE agent knowledge + CLAUDE.md docs

---

### Phase 39: Agent Integration
**Goal**: CASE agent autonomously uses statistical detection to write better-constrained LSD files
**Depends on**: Phases 34, 35, 36, 37, 38 (all CLI commands stable)
**Requirements**: AGENT-01, AGENT-02, AGENT-03, AGENT-04, AGENT-05, AGENT-06
**Success Criteria** (what must be TRUE):
  1. CASE agent definition (lucy-case-agent.md) teaches statistical detection protocol (call detect commands before writing LSD)
  2. Agent uses hybridisation detection to set MULT hybridisation values in LSD (sp2 carbons get hybridisation hints)
  3. Agent uses neighbourhood detection to add ELIM forbidden or LIST mandatory constraints
  4. Agent uses HHB detection to decide whether to add hetero-hetero BOND constraints
  5. Agent applies chemistry-first hierarchy (NMR knowledge trumps statistics, stats augment but don't override)
  6. Agent uses signal grouping detection to identify ambiguous assignments and document in CASE-PROGRESS.md
**Plans**: TBD

Plans:
- [ ] 39-01-PLAN.md: Update lucy-case-agent.md with statistical detection workflow section
- [ ] 39-02-PLAN.md: Add chemistry-first hierarchy rules and threshold override examples
- [ ] 39-03-PLAN.md: Create integration test with ibuprofen (verify correct aromatic structure found)

---

### Phase 40: Validation
**Goal**: Statistical detection improvements measured against test cases before shipping
**Depends on**: Phase 39 (agent integration complete)
**Requirements**: None (validation phase, ensures quality)
**Success Criteria** (what must be TRUE):
  1. Validation test suite created with Sherlock's 45 test cases (downloaded from nmrXiv, sanitized)
  2. Metrics computed for constraint accuracy (do detected constraints match known structures?)
  3. Search space reduction measured (solution count with vs without statistical constraints)
  4. Rank improvement measured (does correct structure rank higher with constraints?)
  5. Ibuprofen CASE produces correct isobutylphenylpropanoic acid structure in top 3 (fixes v2.1 cyclohexadiene failure)
**Plans**: TBD

Plans:
- [ ] 40-01-PLAN.md: Download and sanitize Sherlock's 45 test cases from nmrXiv
- [ ] 40-02-PLAN.md: Create validation script to run CASE with/without statistical constraints
- [ ] 40-03-PLAN.md: Compute metrics and write validation report

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
| 20. System Audit | v2.0 | 3/3 | Complete | 2026-02-06 |
| 21. Skill Restructure | v2.0 | 3/3 | Complete | 2026-02-06 |
| 22. HMBC Strategy + Quality | v2.0 | 1/1 | Complete | 2026-02-06 |
| 23. Error Tolerance + Confidence | v2.0 | 2/2 | Complete | 2026-02-07 |
| 24. Supervisor Agent | v2.0 | 2/2 | Complete | 2026-02-07 |
| 25. Diagnostic Specialist | v2.0 | 2/2 | Complete | 2026-02-07 |
| 26. Thin Tools | v2.0 | 5/5 | Complete | 2026-02-08 |
| 27. Sub-Command Skills Foundation | v2.1 | 2/2 | Complete | 2026-02-08 |
| 28. CASE Agent Definition | v2.1 | 1/1 | Complete | 2026-02-08 |
| 29. CASE Orchestrator Skill | v2.1 | 1/1 | Complete | 2026-02-08 |
| 30. Diagnostic Specialist Integration | v2.1 | 1/1 | Complete | 2026-02-08 |
| 31. Sanitization Skill | v2.1 | 1/1 | Complete | 2026-02-08 |
| 32. End-to-End Validation | v2.1 | 1/1 | Complete | 2026-02-08 |
| 33. Documentation and Cleanup | v2.1 | 2/2 | Complete | 2026-02-09 |
| 34. Hybridisation Detection | v3.0 | 3/3 | Complete | 2026-02-10 |
| 35. Neighbourhood Detection | v3.0 | 4/4 | Complete | 2026-02-11 |
| 36. HHB and Ring Detection | v3.0 | 3/3 | Complete | 2026-02-11 |
| 37. Signal Grouping | v3.0 | 3/3 | Complete | 2026-02-11 |
| 38. Two-Tier Ranking and Badlist | v3.0 | 2/2 | Complete | 2026-02-11 |
| 39. Agent Integration | v3.0 | 0/3 | Not started | - |
| 40. Validation | v3.0 | 0/3 | Not started | - |

---
*Last updated: 2026-02-11 after Phase 38 execution*
