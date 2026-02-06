# Requirements: lucy-ng v2.0

**Defined:** 2026-02-06
**Core Value:** An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## v2.0 Requirements

Requirements for v2.0 Robust Multi-Agent CASE. Each maps to roadmap phases.

### Audit

- [ ] **AUDT-01**: Audit all 16 MCP tools -- classify each as Tier 1 (pure data access, keep), Tier 2 (moderate intelligence, migrate to skill), or Tier 3 (complex logic, refactor to thin wrapper)
- [ ] **AUDT-02**: Audit all 7 CLI command groups -- identify which intelligence should move to skill vs stay in code
- [ ] **AUDT-03**: Audit CLAUDE.md (1080 lines) -- identify duplication, misplaced intelligence, sections that should move to separate skill documents
- [ ] **AUDT-04**: Produce audit report with specific recommendations for each component

### Skill Architecture

- [ ] **SKIL-01**: Split CLAUDE.md into project-level document (setup, database, references, developer info) and CASE workflow document (SKILL.md)
- [ ] **SKIL-02**: Create SUPERVISOR.md with loop detection patterns, intervention strategies, and escalation criteria
- [ ] **SKIL-03**: Remove duplication between CLAUDE.md and skill documents
- [ ] **SKIL-04**: Skill documents sized appropriately -- CLAUDE.md <800 lines, SKILL.md <1500 lines, SUPERVISOR.md <500 lines

### Incremental HMBC Strategy

- [ ] **HMBC-01**: Skill encodes 3-phase constraint addition strategy: Phase 1 (core structure from high-confidence signals), Phase 2 (resolve ambiguity with diagnostic correlations), Phase 3 (refine with full constraint set)
- [ ] **HMBC-02**: Skill explicitly teaches "start with 5-10 high-confidence HMBC correlations, not all"
- [ ] **HMBC-03**: Skill includes decision tree for when to add more correlations vs when to investigate failures
- [ ] **HMBC-04**: Skill explicitly prohibits "throw everything in" approach -- no guidance saying "use all correlations from peak picking"

### Error Tolerance

- [ ] **ETOL-01**: Skill teaches close carbon shift detection -- AI identifies carbons within 0.3-0.5 ppm proactively and documents ambiguity
- [ ] **ETOL-02**: Skill teaches DEPT phase conflict handling -- AI compares HSQC vs DEPT and chooses ground truth
- [ ] **ETOL-03**: Skill teaches ambiguous HMBC assignment -- AI generates LSD variants when carbon positions are close (<1 ppm)
- [ ] **ETOL-04**: Skill teaches quaternary carbon HMBC sparsity -- AI uses chemical shift to constrain when few HMBC visible

### Supervisor Agent

- [ ] **SUPV-01**: Supervisor agent defined as Claude Code subagent (markdown file with YAML frontmatter)
- [ ] **SUPV-02**: Supervisor detects ELIM thrashing -- adding ELIM repeatedly without diagnosing root cause
- [ ] **SUPV-03**: Supervisor detects zero-solution loops -- repeated 0-solution attempts without changing approach
- [ ] **SUPV-04**: Supervisor detects solution explosion -- 1000+ solutions with minor tweaks not reducing count
- [ ] **SUPV-05**: Supervisor detects constraint churning -- adding/removing constraints randomly without progress
- [ ] **SUPV-06**: Supervisor interventions are specific -- require diagnosis before allowing retry (e.g., "validate sp2 count before trying ELIM")
- [ ] **SUPV-07**: Supervisor escalates to user after 3 failed attempts with same pattern

### Diagnostic & LSD Expert Specialist

- [ ] **DIAG-01**: Diagnostic specialist agent defined as Claude Code subagent with deep LSD manual knowledge
- [ ] **DIAG-02**: For 0 solutions: systematically checks sp2 count (even?), hydrogen budget (matches formula?), HMBC conflicts, correlation order
- [ ] **DIAG-03**: For 1000+ solutions: checks constraint count, quaternary carbon connectivity, heteroatom constraints, symmetry encoding
- [ ] **DIAG-04**: Produces structured diagnostic report with root cause and recommended fixes
- [ ] **DIAG-05**: Agent has internalized full LSD manual (MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM, etc.) and can advise on advanced constraint strategies

### Thin Tools

- [ ] **TOOL-01**: MCP tools reduced to thin data access wrappers -- no embedded domain logic
- [ ] **TOOL-02**: Peak picking tools return raw peaks above threshold without DEPT-guided filtering or HMBC validation
- [ ] **TOOL-03**: Intelligence previously in Python (adaptive thresholding, conflict resolution, auto-constraint generation) migrated to skill
- [ ] **TOOL-04**: CLI retains smart behavior for backward compatibility (dual mode: smart CLI, thin MCP)

### Spectral Quality Assessment

- [ ] **QUAL-01**: Skill teaches S/N assessment -- AI evaluates signal-to-noise and adjusts expectations
- [ ] **QUAL-02**: Skill teaches digital resolution impact -- AI documents when close carbons may alias
- [ ] **QUAL-03**: Skill teaches artifact recognition -- AI identifies 1J correlations, t1 noise, baseline roll

### Confidence-Annotated Output

- [ ] **CONF-01**: CASE workflow produces assignments with confidence levels (High >90%, Medium 60-90%, Low <60%)
- [ ] **CONF-02**: Ambiguous assignments explicitly documented with reasoning
- [ ] **CONF-03**: Analysis output flags areas where additional NMR experiments might help

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
| AUDT-01 | Phase 20 | Pending |
| AUDT-02 | Phase 20 | Pending |
| AUDT-03 | Phase 20 | Pending |
| AUDT-04 | Phase 20 | Pending |
| SKIL-01 | Phase 21 | Pending |
| SKIL-02 | Phase 21 | Pending |
| SKIL-03 | Phase 21 | Pending |
| SKIL-04 | Phase 21 | Pending |
| HMBC-01 | Phase 22 | Pending |
| HMBC-02 | Phase 22 | Pending |
| HMBC-03 | Phase 22 | Pending |
| HMBC-04 | Phase 22 | Pending |
| QUAL-01 | Phase 22 | Pending |
| QUAL-02 | Phase 22 | Pending |
| QUAL-03 | Phase 22 | Pending |
| ETOL-01 | Phase 23 | Pending |
| ETOL-02 | Phase 23 | Pending |
| ETOL-03 | Phase 23 | Pending |
| ETOL-04 | Phase 23 | Pending |
| CONF-01 | Phase 23 | Pending |
| CONF-02 | Phase 23 | Pending |
| CONF-03 | Phase 23 | Pending |
| SUPV-01 | Phase 24 | Pending |
| SUPV-02 | Phase 24 | Pending |
| SUPV-03 | Phase 24 | Pending |
| SUPV-04 | Phase 24 | Pending |
| SUPV-05 | Phase 24 | Pending |
| SUPV-06 | Phase 24 | Pending |
| SUPV-07 | Phase 24 | Pending |
| DIAG-01 | Phase 25 | Pending |
| DIAG-02 | Phase 25 | Pending |
| DIAG-03 | Phase 25 | Pending |
| DIAG-04 | Phase 25 | Pending |
| DIAG-05 | Phase 25 | Pending |
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
*Last updated: 2026-02-06 after roadmap creation*
