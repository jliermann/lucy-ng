# Research Summary: v4.0 Team-Based CASE Architecture

**Domain:** Multi-agent CASE workflow for NMR structure elucidation
**Researched:** 2026-02-16
**Overall confidence:** HIGH

## Executive Summary

The v4.0 milestone transitions from a single autonomous CASE agent to a 5-agent collaborative team using Claude Opus 4.6's TeamCreate API. This architectural shift addresses all v3.0 constraint-loss bugs by distributing responsibilities across specialized agents with real-time peer review.

**Core changes:**
1. **Orchestrator skill** replaces `Task(lucy-case-agent)` with `TeamCreate(team_definition)`
2. **5 specialized agents** replace monolithic lucy-case-agent.md: coordinator (team lead), nmr-chemist, lsd-engineer, solution-analyst, devils-advocate
3. **Constraint inventory system** tracks all constraints across iterations, preventing loss
4. **Pre-run validation** catches dropped constraints (DEFF NOT, SYME, grouped notation) before LSD runs
5. **Multi-agent journal** (CASE-PROGRESS.md) with per-agent sections replaces single-agent narrative

The architecture builds on proven multi-agent patterns (hierarchical coordinator, specialized teammates) and leverages Claude Opus 4.6's native team collaboration features (shared task list, direct messaging, parallel execution).

## Key Findings

### Stack: Claude Opus 4.6 Team Architecture

**Recommendation:** Use TeamCreate API with hierarchical pattern (1 lead + 4 teammates)

**Why:**
- Native support for team coordination (released Feb 5, 2026 with Opus 4.6)
- Shared task list enables async collaboration
- Direct messaging between teammates (no bottleneck through orchestrator)
- Proven at scale (Anthropic built C compiler with 16 agents, 100K lines of code)

**Integration:** Orchestrator skill (`~/.claude/commands/lucy-ng/case.md`) spawns team via TeamCreate, monitors progress, handles escalations

### Architecture: Specialized Agent Team with Constraint Inventory

**Recommendation:** 5-agent team with distributed domain knowledge and explicit constraint tracking

**Team structure:**
- **Coordinator** (team lead): Workflow orchestration, iteration management, result synthesis
- **NMR-Chemist:** Peak picking, multiplicity assignment, statistical detection, spectral quality
- **LSD-Engineer:** Constraint building, LSD file construction, inventory management (reads previous file, never reconstructs from memory)
- **Solution-Analyst:** Ranking, chemical plausibility, quality assessment
- **Devils-Advocate:** Pre-run validation, constraint checking, diff analysis (catches dropped constraints before LSD runs)

**Critical architecture component:** Constraint inventory in LSD file header comment (JSON format) tracks all constraints (MULT, HSQC, HMBC, DEFF NOT, SYME, BOND, LIST/PROP, ELIM) across iterations. LSD-Engineer reads previous file, Devils-Advocate diffs and validates.

**Confidence:** HIGH — Pattern is well-established (hierarchical/supervisor pattern), TeamCreate API is documented, constraint inventory is implementable

### Features: Fixes for v3.0 Constraint-Loss Bugs

**v3.0 bugs identified from UAT:**
1. DEFF NOT dropped after iteration 1 (6 patterns → 0 patterns)
2. SYME constraints never applied despite signal grouping detection
3. Grouped notation lost after iteration 1 (HMBC (6 7) → HMBC 6)
4. Detection results documented but not translated to constraints

**v4.0 fixes:**
1. **Constraint inventory:** LSD-Engineer maintains count, Devils-Advocate validates before every run → DEFF NOT persistence enforced
2. **Pre-run validation:** Devils-Advocate diffs iteration N vs N-1, flags missing SYME → forces application
3. **Constraint diff:** Devils-Advocate checks grouped notation preserved → prevents regression
4. **Multi-agent workflow:** NMR-Chemist detects grouping → posts to team → LSD-Engineer translates → Devils-Advocate validates → no silent dropping

**Table stakes features:**
- Team lifecycle management (spawn, coordinate, terminate)
- Multi-agent CASE-PROGRESS.md format (per-agent sections)
- Knowledge distribution across agents (NMR knowledge in nmr-chemist, LSD syntax in lsd-engineer)
- Real-time peer feedback (any agent can flag issues in others' work)

**Differentiators:**
- Constraint inventory system (explicit tracking, not implicit memory)
- Pre-run validation gate (devils-advocate approval required before LSD runs)
- Post-run quality review (solution-analyst checks chemical plausibility, not just solution count)
- Self-correcting loop (dropped constraints caught and fixed within same iteration)

### Pitfalls: Team Coordination Overhead and Knowledge Gaps

**Critical Pitfall 1: Team Coordination Overhead**
- **What goes wrong:** 5 agents coordinating may be 5x slower than 1 monolithic agent
- **Why it happens:** Task assignment, result synthesis, message passing all take time
- **Consequences:** User frustration, workflow timeouts
- **Prevention:** Benchmark v3.0 vs v4.0 on same compounds, optimize task assignment (parallelize where possible)
- **Detection:** Time to solution > 2x v3.0 baseline
- **Mitigation:** If overhead excessive, reduce team size (3 agents: coordinator, scientist, validator) or revert to enhanced monolithic agent with constraint inventory

**Critical Pitfall 2: Knowledge Distribution Gaps**
- **What goes wrong:** Splitting knowledge across 5 agents creates gaps where no agent knows full context
- **Why it happens:** Overly aggressive specialization, unclear interface boundaries
- **Consequences:** Workflow failures (agent doesn't know how to do assigned task), incorrect chemistry (agent makes decision without full context)
- **Prevention:** Define clear interfaces (WHAT each agent posts to team), validate coverage during Phase 2, include cross-references in agent definitions
- **Detection:** Agent posts "I don't know how to X" or makes chemically implausible decision
- **Mitigation:** Re-inline shared knowledge (duplicated across agents), provide lookup references to other agents

**Moderate Pitfall 3: CASE-PROGRESS.md Corruption**
- **What goes wrong:** Multiple agents appending concurrently corrupt file (interleaved writes, truncated sections)
- **Why it happens:** No file locking, append-only protocol not enforced
- **Prevention:** Use structured sections (agent name headers) for safe parsing, test concurrent writes during Phase 4
- **Detection:** Orchestrator fails to parse CASE-PROGRESS.md, missing sections
- **Mitigation:** Coordinator as sole writer (agents post to team, coordinator writes to file), or implement file locking

**Moderate Pitfall 4: Constraint Inventory Maintenance Burden**
- **What goes wrong:** LSD-Engineer maintains inaccurate inventory (count mismatch, missing constraints)
- **Why it happens:** Manual inventory updates error-prone, complex constraint types (LIST/PROP)
- **Prevention:** Structured inventory format (JSON), devils-advocate validates on every run, automated diff checking
- **Detection:** Devils-Advocate flags inventory mismatch (comment says 6 DEFF NOT, file has 4)
- **Mitigation:** Fail-safe rebuild from full LSD file parse if inventory corrupt, simplified inventory (count-only)

**Minor Pitfall 5: TeamCreate API Limitations**
- **What goes wrong:** Claude SDK TeamCreate has undocumented limitations (max team size, message latency, API bugs)
- **Why it happens:** New feature (Feb 2026), edge cases not fully documented
- **Prevention:** Early prototype during Phase 1, test team size limits (5 agents may be near max), engage Anthropic support
- **Detection:** TeamCreate fails to spawn, messages not delivered, team hangs
- **Mitigation:** Revert to Task-based architecture with enhanced monolithic agent (v3.5 instead of v4.0)

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Orchestrator Skill Modification (Week 1)
**Addresses:** Team spawning, progress monitoring, advisory delivery
**Avoids:** Pitfall 5 (TeamCreate limitations) by early validation

**Rationale:** Orchestrator is foundation — team cannot spawn without it. Early testing exposes TeamCreate API limitations before committing to full build.

**Research flags:** None — TeamCreate API is documented, mapping from Task to TeamCreate is straightforward

### Phase 2: Agent Definitions with Knowledge Distribution (Weeks 1-2)
**Addresses:** Specialized agents, domain knowledge splitting, inter-agent interfaces
**Avoids:** Pitfall 2 (knowledge gaps) by explicit interface definition and coverage validation

**Rationale:** Agents must exist before coordination can be tested. Knowledge distribution is critical — gaps here cause failures later.

**Research flags:** Likely needs deeper research on inter-agent interfaces (WHAT each agent posts to team). Current research defines structure but not detailed message schemas.

### Phase 3: Constraint Inventory System (Week 2)
**Addresses:** DEFF NOT persistence, SYME tracking, grouped notation preservation (fixes v3.0 bugs)
**Avoids:** Pitfall 4 (inventory maintenance) by structured format and validation

**Rationale:** This is THE critical success factor. Without reliable constraint tracking, v4.0 has same bugs as v3.0.

**Research flags:** Inventory format needs detailed design (JSON schema, diff protocol). Current research provides concept but not implementation details.

### Phase 4: CASE-PROGRESS.md Format (Week 2)
**Addresses:** Multi-agent journal, per-agent sections, orchestrator parsing
**Avoids:** Pitfall 3 (file corruption) by append-only protocol and structured sections

**Rationale:** Communication protocol must be stable before coordination workflow depends on it.

**Research flags:** None — format is well-defined, standard patterns apply

### Phase 5: Team Coordination Protocol (Week 3)
**Addresses:** Iteration loop, task assignment, result synthesis, stopping conditions
**Avoids:** Pitfall 1 (coordination overhead) by parallelization where possible

**Rationale:** All pieces assembled, now integrate workflow. This is where team dynamics are validated.

**Research flags:** Likely needs iterative tuning based on UAT. Coordination efficiency unknown until tested with real compounds.

### Phase 6: Diagnostic Integration (Week 3)
**Addresses:** Specialist integration with team context, advisory delivery via TeamMessage
**Avoids:** Edge case failures by keeping diagnostic specialist as orchestrator-spawned (not team member)

**Rationale:** Edge case handling after core workflow works. Diagnostic specialist remains independent for objective analysis.

**Research flags:** None — pattern is unchanged from v3.0, just TeamMessage instead of Task re-spawn

### Phase 7: UAT with Live Compounds (Week 4)
**Addresses:** Validation against v3.0 baseline, bug verification, performance measurement
**Avoids:** All pitfalls by empirical testing with diverse compounds

**Rationale:** Full system validation with real data. Success criteria: all v3.0 bugs fixed, time to solution < 2x v3.0, correct structure in top 3.

**Research flags:** None — standard UAT pattern, test cases defined (Ibuprofen, Pulegone, Virgiline)

**Phase ordering rationale:**
- Orchestrator → Agents → Inventory → Format → Coordination → Diagnostic → UAT
- Each phase builds on previous (dependency chain)
- Critical path: Orchestrator → Agents → Inventory → Coordination → UAT
- Inventory is THE gate (Phase 3) — without it, workflow proceeds but v3.0 bugs remain

**Research flags for phases:**
- Phase 2: Likely needs deeper research on inter-agent message schemas
- Phase 3: Likely needs deeper research on constraint inventory JSON schema and diff protocol
- Phase 5: Likely needs iterative tuning based on UAT (coordination efficiency unknown)

**Phases unlikely to need research:**
- Phase 1: Standard patterns, well-documented API
- Phase 4: Standard append-only file protocol
- Phase 6: Unchanged pattern from v3.0
- Phase 7: Standard UAT, test cases defined

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | TeamCreate API documented, native team collaboration features proven |
| Features | HIGH | v3.0 bugs well-understood, fixes are architectural (constraint inventory, pre-run validation) |
| Architecture | HIGH | Hierarchical/supervisor pattern is standard, knowledge distribution is logical |
| Pitfalls | MEDIUM | Coordination overhead unknown until UAT, knowledge gaps mitigable but require validation |

**Overall confidence: HIGH** — Architecture is sound, integration points are clear, build order is logical. Main uncertainty is team dynamics (coordination efficiency, knowledge distribution effectiveness) which requires empirical validation through UAT.

## Gaps to Address

### Areas where research was inconclusive:

**1. Inter-agent message schemas (Phase 2)**
- Current research defines WHAT agents communicate (assignments, results, validations)
- Missing: Detailed message schemas (JSON structure, required fields, optional fields)
- Example gap: NMR-Chemist posts "sp2=0.92" to team — is this free text or structured JSON?
- Impact: Message parsing failures if schema not standardized
- Resolution: Define schemas during Phase 2 implementation

**2. Constraint inventory JSON schema (Phase 3)**
- Current research defines inventory concept (track all constraints in LSD comment)
- Missing: Exact JSON schema (nested structure, array vs object for HMBC batches, versioning)
- Example gap: How to represent grouped notation (HMBC (5 6) 10) in JSON?
- Impact: Inventory parsing failures, diff protocol complexity
- Resolution: Design schema during Phase 3 implementation, validate with diff examples

**3. Team coordination efficiency (Phase 5)**
- Current research assumes < 2x overhead is acceptable
- Missing: Empirical data on task assignment latency, message passing speed, parallel execution effectiveness
- Example gap: Does coordinator assign tasks sequentially (slow) or broadcast to team (fast)?
- Impact: User-visible slowness if coordination bottlenecks workflow
- Resolution: Benchmark during Phase 5, optimize if needed, fallback to reduced team size

**4. Knowledge distribution edge cases (Phase 2)**
- Current research distributes by responsibility (NMR in nmr-chemist, LSD in lsd-engineer)
- Missing: Handling of shared concepts (chemical shift regions known by both nmr-chemist and lsd-engineer)
- Example gap: Who knows that 180 ppm = likely carbonyl? NMR-Chemist (shift interpretation) or LSD-Engineer (constraint context)?
- Impact: Redundant knowledge (bloat) or gaps (failures)
- Resolution: Define shared knowledge policy during Phase 2 (duplicate minimal core, cross-reference for details)

### Topics needing phase-specific research later:

**Phase 2 (Agent Definitions):**
- Detailed inter-agent message schemas
- Shared knowledge duplication vs cross-referencing policy
- Agent definition size limits (how much knowledge per agent before bloat)

**Phase 3 (Constraint Inventory):**
- JSON schema design and versioning
- Diff protocol algorithm (line-by-line vs semantic diff)
- Inventory rebuild fail-safe (when to rebuild from full parse)

**Phase 5 (Team Coordination):**
- Task assignment optimization (sequential vs parallel, broadcast vs direct)
- Coordination overhead benchmarking (v3.0 vs v4.0 time to solution)
- Team size tuning (5 agents vs 3 agents vs enhanced monolithic)

**Phase 7 (UAT):**
- Additional test compounds if Ibuprofen/Pulegone/Virgiline insufficient
- Failure mode analysis (what breaks team workflow that didn't break monolithic?)
- User feedback on CASE-PROGRESS.md readability (too verbose? missing context?)

## Sources

Research based on:

**Claude Agent Teams:**
- [Orchestrate teams of Claude Code sessions - Claude Code Docs](https://code.claude.com/docs/en/agent-teams)
- [Agent Teams with Claude Code and Claude Agent SDK | Medium](https://kargarisaac.medium.com/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e)
- [Claude Code Agent Teams: Multi-Session Orchestration](https://claudefa.st/blog/guide/agents/agent-teams)
- [Anthropic releases Opus 4.6 with new 'agent teams' | TechCrunch](https://techcrunch.com/2026/02/05/anthropic-releases-opus-4-6-with-new-agent-teams/)
- [Introducing Claude Opus 4.6 | Anthropic](https://www.anthropic.com/news/claude-opus-4-6)

**Multi-Agent Architecture Patterns:**
- [AI Agent Orchestration Patterns - Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Four Design Patterns for Event-Driven, Multi-Agent Systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/)
- [Choose a design pattern for your agentic AI system | Google Cloud](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)
- [Choosing the Right Multi-Agent Architecture | LangChain](https://blog.langchain.com/choosing-the-right-multi-agent-architecture/)

**Project Context:**
- lucy-ng CLAUDE.md, PROJECT.md, STATE.md (local project files)
- Existing ARCHITECTURE.md (statistical detection features, v3.0)
- lucy-case-agent.md (666 lines, monolithic autonomous agent)
- lucy-diagnostic.md (diagnostic specialist, orchestrator-spawned)
- case.md (672 lines, v3.0 orchestrator with Task-based spawning)

---
*Research summary for: lucy-ng v4.0 Team-Based CASE Architecture*
*Researched: 2026-02-16*
