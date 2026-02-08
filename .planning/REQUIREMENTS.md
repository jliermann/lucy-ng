# Requirements: lucy-ng v2.1

**Defined:** 2026-02-08
**Core Value:** An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with working multi-agent orchestration that prevents unproductive loops via sub-command skills following the GSD pattern.

## v2.0 Requirements (Complete)

Requirements for v2.0 Robust Multi-Agent CASE. Each maps to roadmap phases.

### Audit

- [x] **AUDT-01**: Audit all 16 MCP tools -- classify each as Tier 1 (pure data access, keep), Tier 2 (moderate intelligence, migrate to skill), or Tier 3 (complex logic, refactor to thin wrapper)
- [x] **AUDT-02**: Audit all 7 CLI command groups -- identify which intelligence should move to skill vs stay in code
- [x] **AUDT-03**: Audit CLAUDE.md (1080 lines) -- identify duplication, misplaced intelligence, sections that should move to separate skill documents
- [x] **AUDT-04**: Produce audit report with specific recommendations for each component

### Skill Architecture

- [x] **SKIL-01**: Split CLAUDE.md into project-level document (setup, database, references, developer info) and CASE workflow document (SKILL.md)
- [x] **SKIL-02**: Create SUPERVISOR.md with loop detection patterns, intervention strategies, and escalation criteria
- [x] **SKIL-03**: Remove duplication between CLAUDE.md and skill documents
- [x] **SKIL-04**: Skill documents sized appropriately -- CLAUDE.md <800 lines, SKILL.md <1500 lines, SUPERVISOR.md <500 lines

### Incremental HMBC Strategy

- [x] **HMBC-01**: Skill encodes adaptive incremental constraint strategy: start with high-confidence correlations, add 3-5 per iteration, observe solution count change (replaces fixed 3-phase recipe per CONTEXT.md decision)
- [x] **HMBC-02**: Skill explicitly teaches "start with 5-10 high-confidence HMBC correlations, not all"
- [x] **HMBC-03**: Skill includes decision tree for when to add more correlations vs when to investigate failures
- [x] **HMBC-04**: Skill explicitly prohibits "throw everything in" approach -- no guidance saying "use all correlations from peak picking"

### Error Tolerance

- [x] **ETOL-01**: Skill teaches resolution-based close carbon detection -- AI identifies unresolvable carbons using digital resolution (pts/ppm) and documents ambiguity with LIST/PROP encoding
- [x] **ETOL-02**: Skill teaches context-dependent DEPT/HSQC conflict resolution -- priority tree (DEPT-90 > S/N > shift > consistency) with documented reasoning
- [x] **ETOL-03**: Skill teaches ambiguous HMBC assignment -- AI uses LSD LIST/PROP mechanism in single file (NOT separate variant files) for close carbon positions
- [x] **ETOL-04**: Skill teaches quaternary carbon HMBC sparsity -- shift-based constraints + incremental 20% threshold reduction for targeted correlation search

### Supervisor Agent

- [x] **SUPV-01**: Supervisor agent defined as Claude Code subagent at .claude/agents/supervisor.md (383 lines) with YAML frontmatter (name, tools, model) and complete system prompt
- [x] **SUPV-02**: Supervisor detects ELIM thrashing -- CASE-PROGRESS.md shows ELIM added 2+ times; diagnostic checks sp2 count, H budget, 1J artifacts
- [x] **SUPV-03**: Supervisor detects zero-solution loops -- 3+ iterations with 0 solutions; diagnostic removes last batch, tests individual correlations
- [x] **SUPV-04**: Supervisor detects solution explosion -- 3+ iterations >100 solutions with <10% reduction; checks ELIM, heteroatom constraints, quaternary carbons
- [x] **SUPV-05**: Supervisor detects constraint churning -- 5+ iterations with high add/remove activity; resets to last good state, follows incremental HMBC strategy
- [x] **SUPV-06**: Supervisor interventions are advisory -- tells CASE agent WHAT to fix (specific diagnosis) not HOW; four advisory message templates with per-pattern diagnostic procedures
- [x] **SUPV-07**: Supervisor escalates to user after 10 failed intervention cycles per pattern (per CONTEXT.md decision, overrides original 3-attempt spec)

### Diagnostic & LSD Expert Specialist

- [x] **DIAG-01**: Diagnostic specialist agent at .claude/agents/diagnostic-specialist.md (455 lines) with YAML frontmatter, 5-step workflow, tools: Read + Bash, model: sonnet
- [x] **DIAG-02**: For 0 solutions: 5-check procedure (sp2 count even, H budget, 1J artifacts ±1.5/±0.3 ppm, correlation order, close carbons) in skill/diagnostic/SKILL.md Section 2.1
- [x] **DIAG-03**: For 1000+ solutions: 5-check procedure (ELIM presence, constraint/atom ratio 0.5, quaternary connectivity, heteroatom constraints, symmetry encoding) in Section 2.2
- [x] **DIAG-04**: Structured DIAGNOSTIC-REPORT.md template (8 sections: Summary, Findings, Root Cause, Recommended Fixes with LSD commands, Supporting Data, Next Steps, Methodology, Metadata)
- [x] **DIAG-05**: Full LSD manual in skill/diagnostic/SKILL.md Section 1 (1,874 lines total): MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM with edge cases and error patterns

### Thin Tools

- [x] **TOOL-01**: MCP tools reduced to thin data access wrappers -- no embedded domain logic
- [x] **TOOL-02**: Peak picking tools return raw peaks above threshold without DEPT-guided filtering or HMBC validation
- [x] **TOOL-03**: Intelligence previously in Python (adaptive thresholding, conflict resolution, auto-constraint generation) migrated to skill
- [x] **TOOL-04**: CLI retains smart behavior for backward compatibility (dual mode: smart CLI, thin MCP)

### Spectral Quality Assessment

- [x] **QUAL-01**: Skill teaches S/N assessment -- AI evaluates signal-to-noise and adjusts expectations
- [x] **QUAL-02**: Skill teaches digital resolution impact -- AI documents when close carbons may alias
- [x] **QUAL-03**: Skill teaches artifact recognition -- AI identifies 1J correlations, t1 noise, baseline roll

### Confidence-Annotated Output

- [x] **CONF-01**: CASE workflow produces assignments with qualitative confidence levels (High/Medium/Low based on 3-factor judgment: resolution, HOSE MAE, correlations) -- NOT computed percentages
- [x] **CONF-02**: Ambiguous assignments explicitly documented with reasoning in mandatory Ambiguities Detected table (Carbon/Issue, Type, Resolution Detail, Impact on Constraints)
- [x] **CONF-03**: Analysis output suggests specific additional NMR experiments (WHAT experiment, WHY it helps, WHICH atom/issue it resolves) for Medium/Low confidence atoms

## v2.1 Requirements

Requirements for v2.1 Working Multi-Agent CASE. Sub-command skills, real agent orchestration, working AI-driven sanitisation.

### Sub-Command Skills

- [ ] **SCMD-01**: Create `~/.claude/commands/lucy-ng/` directory with sub-command skills following GSD pattern (YAML frontmatter + markdown body)
- [ ] **SCMD-02**: `/lucy-ng:case` orchestrator skill that spawns autonomous CASE agent via Task(), monitors progress, detects loops, intervenes with advisory, delegates to diagnostic specialist
- [ ] **SCMD-03**: `/lucy-ng:sanitise` AI-driven skill for compound identifier removal (no CLI — requires AI reasoning)
- [ ] **SCMD-04**: `/lucy-ng:dereplicate` thin wrapper skill around `lucy dereplicate c13` CLI
- [ ] **SCMD-05**: `/lucy-ng:predict` thin wrapper skill around `lucy predict c13` CLI
- [ ] **SCMD-06**: `/lucy-ng:status` environment readiness check skill (lucy-ng, LSD, database)
- [ ] **SCMD-07**: Old monolithic `/lucy-ng` skill replaced by sub-command routing page

### Autonomous CASE Agent

- [ ] **CASE-01**: CASE agent definition at `~/.claude/agents/lucy-case-agent.md` with YAML frontmatter (name, description, tools: Read + Write + Bash + Glob + Grep)
- [ ] **CASE-02**: CASE agent receives inlined skill content (NMR background, CASE workflow, LSD basics, CASE-PROGRESS.md format) plus file path references for detailed domain knowledge
- [ ] **CASE-03**: CASE agent writes CASE-PROGRESS.md after EVERY LSD iteration with required fields (solution count, constraints added/removed, reasoning, confidence, sp2/H checks)
- [ ] **CASE-04**: CASE agent follows skill/CASE/SKILL.md workflow — NEVER attempts dereplication (absolute separation)
- [ ] **CASE-05**: CASE agent implements advisory constraints from supervisor (understands WHAT to fix, decides HOW autonomously)

### CASE Orchestration

- [ ] **ORCH-01**: Orchestrator spawns CASE agent with hybrid context inlining (~500-700 lines critical content inlined, detailed references via file paths)
- [ ] **ORCH-02**: Orchestrator reads CASE-PROGRESS.md after agent returns to monitor progress
- [ ] **ORCH-03**: Orchestrator detects 4 loop patterns: ELIM thrashing, zero-solution loop, solution explosion, constraint churning
- [ ] **ORCH-04**: Orchestrator performs basic diagnosis before intervention (sp2 count, H budget, 1J artifacts)
- [ ] **ORCH-05**: Orchestrator generates advisory interventions (WHAT not HOW) — never prescribes specific LSD file edits
- [ ] **ORCH-06**: Orchestrator tracks intervention counts per pattern (not global counter)
- [ ] **ORCH-07**: Orchestrator escalates to user after 10 failed intervention cycles per pattern
- [ ] **ORCH-08**: Orchestrator re-spawns CASE agent with advisory constraints and skip-completed-work instructions

### Diagnostic Specialist Integration

- [ ] **DIAG-06**: Diagnostic specialist agent renamed to `~/.claude/agents/lucy-diagnostic.md` with updated frontmatter
- [ ] **DIAG-07**: Orchestrator delegates to diagnostic specialist after 2 failed interventions with same loop pattern
- [ ] **DIAG-08**: Orchestrator reads DIAGNOSTIC-REPORT.md and extracts root cause + primary fix for CASE agent advisory

### AI-Driven Sanitisation

- [ ] **SANT-01**: Sanitise skill explicitly states there is NO CLI command for sanitisation — it requires AI reasoning
- [ ] **SANT-02**: AI detects compound identifiers: chemical names, SMILES, InChI, InChIKey, CAS numbers, MOL file structures, dataset naming patterns
- [ ] **SANT-03**: AI generates redaction manifest and applies bulk sanitisation using existing helper scripts (lucy_text_extractor.py, lucy_bulk_sanitize.py)
- [ ] **SANT-04**: Sanitise skill verifies completeness by re-extracting text and confirming no identifiers remain

### Validation Gate

- [ ] **VALD-01**: End-to-end integration test: orchestrator spawns CASE agent, agent writes progress, orchestrator reads and monitors
- [ ] **VALD-02**: Loop detection test: force known failure patterns, verify detection and intervention
- [ ] **VALD-03**: Diagnostic delegation test: repeated failures trigger specialist, report generated
- [ ] **VALD-04**: Ibuprofen CASE passes via `/lucy-ng:case` (reproduces Phase 26-05 success through orchestration)
- [ ] **VALD-05**: All simple sub-commands work (`/lucy-ng:dereplicate`, `/lucy-ng:predict`, `/lucy-ng:status`)

### Cleanup

- [ ] **CLNP-01**: Delete `.claude/agents/supervisor.md` (logic dissolved into case.md orchestrator)
- [ ] **CLNP-02**: Update CLAUDE.md with sub-command reference section
- [ ] **CLNP-03**: Update PROJECT.md decisions table with v2.1 architecture choices

## Deferred Requirements

Tracked but not in v2.1 scope.

### Constraint Explorer Specialist

- **CEXP-01**: Specialist agent generates multiple LSD input variants for ambiguous cases
- **CEXP-02**: Runs LSD on all variants in parallel and reports which succeeded
- **CEXP-03**: Supports close carbon assignment (try both) and heteroatom placement variants

### Solution Explainer Specialist

- **SEXP-01**: Specialist explains WHY a solution ranks #1 vs alternatives
- **SEXP-02**: Generates comparative report showing constraint satisfaction and shift prediction quality per solution

### Advanced Multi-Agent

- **AMAG-01**: Agent Teams integration (experimental Claude Code feature)
- **AMAG-02**: Parallel hypothesis exploration via background subagents

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| COSY correlation support | Notoriously difficult to analyze, deferred indefinitely |
| Stereochemistry handling (E/Z, R/S) | Requires different NMR experiments, out of scope |
| Interactive CASE with user feedback loop | v2.1 focuses on unattended elucidation |
| Automatic HMBC conflict resolution (Python) | Anti-feature: AI should reason about conflicts, not code |
| Automatic symmetry constraint generation | Anti-feature: AI reasons better from raw intensity data |
| Automatic threshold tuning | Anti-feature: hides decisions from AI, context-dependent |
| One-shot LSD generation with all correlations | Anti-feature: incremental strategy is more robust |
| New Python dependencies for orchestration | Claude Code Task tool provides all primitives natively |
| GUI or web visualization | Purely programmatic interface |
| Non-Bruker vendor formats | Bruker only |
| CLI command for sanitisation | Anti-feature: requires AI reasoning, CLI gives false security |
| Dereplication in CASE orchestrator | Anti-feature: absolute separation, user invokes separately |
| Directive supervision (HOW not WHAT) | Anti-feature: removes agent autonomy |
| Global intervention counter | Anti-feature: different patterns need different tracking |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

### v2.0 (Complete)

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDT-01..04 | Phase 20 | Complete |
| SKIL-01..04 | Phase 21 | Complete |
| HMBC-01..04 | Phase 22 | Complete |
| QUAL-01..03 | Phase 22 | Complete |
| ETOL-01..04 | Phase 23 | Complete |
| CONF-01..03 | Phase 23 | Complete |
| SUPV-01..07 | Phase 24 | Complete |
| DIAG-01..05 | Phase 25 | Complete |
| TOOL-01..04 | Phase 26 | Complete |

### v2.1 (Active)

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCMD-01 | Phase 27 | Pending |
| SCMD-04 | Phase 27 | Pending |
| SCMD-05 | Phase 27 | Pending |
| SCMD-06 | Phase 27 | Pending |
| SCMD-07 | Phase 27 | Pending |
| CASE-01 | Phase 28 | Pending |
| CASE-02 | Phase 28 | Pending |
| CASE-03 | Phase 28 | Pending |
| CASE-04 | Phase 28 | Pending |
| CASE-05 | Phase 28 | Pending |
| SCMD-02 | Phase 29 | Pending |
| ORCH-01 | Phase 29 | Pending |
| ORCH-02 | Phase 29 | Pending |
| ORCH-03 | Phase 29 | Pending |
| ORCH-04 | Phase 29 | Pending |
| ORCH-05 | Phase 29 | Pending |
| ORCH-06 | Phase 29 | Pending |
| ORCH-07 | Phase 29 | Pending |
| ORCH-08 | Phase 29 | Pending |
| DIAG-06 | Phase 30 | Pending |
| DIAG-07 | Phase 30 | Pending |
| DIAG-08 | Phase 30 | Pending |
| SCMD-03 | Phase 31 | Pending |
| SANT-01 | Phase 31 | Pending |
| SANT-02 | Phase 31 | Pending |
| SANT-03 | Phase 31 | Pending |
| SANT-04 | Phase 31 | Pending |
| VALD-01 | Phase 32 | Pending |
| VALD-02 | Phase 32 | Pending |
| VALD-03 | Phase 32 | Pending |
| VALD-04 | Phase 32 | Pending |
| VALD-05 | Phase 32 | Pending |
| CLNP-01 | Phase 33 | Pending |
| CLNP-02 | Phase 33 | Pending |
| CLNP-03 | Phase 33 | Pending |

**Coverage:**
- v2.0 requirements: 38 total (all complete)
- v2.1 requirements: 30 total
- Mapped to phases: 30/30 (100% coverage)
- Unmapped: 0

---
*Requirements defined: 2026-02-06 (v2.0), 2026-02-08 (v2.1)*
*Last updated: 2026-02-08 after v2.1 roadmap creation*
