# Requirements: lucy-ng v2.0

**Defined:** 2026-02-06
**Core Value:** An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## v2.0 Requirements

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

- [ ] **TOOL-01**: MCP tools reduced to thin data access wrappers -- no embedded domain logic
- [ ] **TOOL-02**: Peak picking tools return raw peaks above threshold without DEPT-guided filtering or HMBC validation
- [ ] **TOOL-03**: Intelligence previously in Python (adaptive thresholding, conflict resolution, auto-constraint generation) migrated to skill
- [ ] **TOOL-04**: CLI retains smart behavior for backward compatibility (dual mode: smart CLI, thin MCP)

### Spectral Quality Assessment

- [x] **QUAL-01**: Skill teaches S/N assessment -- AI evaluates signal-to-noise and adjusts expectations
- [x] **QUAL-02**: Skill teaches digital resolution impact -- AI documents when close carbons may alias
- [x] **QUAL-03**: Skill teaches artifact recognition -- AI identifies 1J correlations, t1 noise, baseline roll

### Confidence-Annotated Output

- [x] **CONF-01**: CASE workflow produces assignments with qualitative confidence levels (High/Medium/Low based on 3-factor judgment: resolution, HOSE MAE, correlations) -- NOT computed percentages
- [x] **CONF-02**: Ambiguous assignments explicitly documented with reasoning in mandatory Ambiguities Detected table (Carbon/Issue, Type, Resolution Detail, Impact on Constraints)
- [x] **CONF-03**: Analysis output suggests specific additional NMR experiments (WHAT experiment, WHY it helps, WHICH atom/issue it resolves) for Medium/Low confidence atoms

## v2.1 Requirements

Deferred to future release. Tracked but not in current roadmap.

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
| Interactive CASE with user feedback loop | v2.0 focuses on unattended elucidation |
| Automatic HMBC conflict resolution (Python) | Anti-feature: AI should reason about conflicts, not code |
| Automatic symmetry constraint generation | Anti-feature: AI reasons better from raw intensity data |
| Automatic threshold tuning | Anti-feature: hides decisions from AI, context-dependent |
| One-shot LSD generation with all correlations | Anti-feature: incremental strategy is more robust |
| New Python dependencies for orchestration | Claude Code Task tool provides all primitives natively |
| GUI or web visualization | Purely programmatic interface |
| Non-Bruker vendor formats | Bruker only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDT-01 | Phase 20 | Complete |
| AUDT-02 | Phase 20 | Complete |
| AUDT-03 | Phase 20 | Complete |
| AUDT-04 | Phase 20 | Complete |
| SKIL-01 | Phase 21 | Complete |
| SKIL-02 | Phase 21 | Complete |
| SKIL-03 | Phase 21 | Complete |
| SKIL-04 | Phase 21 | Complete |
| HMBC-01 | Phase 22 | Complete |
| HMBC-02 | Phase 22 | Complete |
| HMBC-03 | Phase 22 | Complete |
| HMBC-04 | Phase 22 | Complete |
| QUAL-01 | Phase 22 | Complete |
| QUAL-02 | Phase 22 | Complete |
| QUAL-03 | Phase 22 | Complete |
| ETOL-01 | Phase 23 | Complete |
| ETOL-02 | Phase 23 | Complete |
| ETOL-03 | Phase 23 | Complete |
| ETOL-04 | Phase 23 | Complete |
| CONF-01 | Phase 23 | Complete |
| CONF-02 | Phase 23 | Complete |
| CONF-03 | Phase 23 | Complete |
| SUPV-01 | Phase 24 | Complete |
| SUPV-02 | Phase 24 | Complete |
| SUPV-03 | Phase 24 | Complete |
| SUPV-04 | Phase 24 | Complete |
| SUPV-05 | Phase 24 | Complete |
| SUPV-06 | Phase 24 | Complete |
| SUPV-07 | Phase 24 | Complete |
| DIAG-01 | Phase 25 | Complete |
| DIAG-02 | Phase 25 | Complete |
| DIAG-03 | Phase 25 | Complete |
| DIAG-04 | Phase 25 | Complete |
| DIAG-05 | Phase 25 | Complete |
| TOOL-01 | Phase 26 | Pending |
| TOOL-02 | Phase 26 | Pending |
| TOOL-03 | Phase 26 | Pending |
| TOOL-04 | Phase 26 | Pending |

**Coverage:**
- v2.0 requirements: 38 total
- Mapped to phases: 38
- Unmapped: 0

---
*Requirements defined: 2026-02-06*
*Last updated: 2026-02-07 after Phase 25 completion*
