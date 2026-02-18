# lucy-ng Roadmap

## Milestones

- [v1.0 Core CASE Pipeline](milestones/v1.0-ROADMAP.md) - Phases 1-10 (shipped 2026-01-12)
- [v1.1 Database-Backed Dereplication](milestones/v1.1-ROADMAP.md) - Phases 11-15 (shipped 2026-01-15)
- [v1.2 HOSE Database Prediction](milestones/v1.2-ROADMAP.md) - Phases 16-19 (shipped 2026-01-18)
- **v2.0 Robust Multi-Agent CASE** - Phases 20-26 (shipped 2026-02-08)
- **v2.1 Working Multi-Agent CASE** - Phases 27-33 (shipped 2026-02-09)
- [v3.0 Statistical Detection](milestones/v3.0-ROADMAP.md) - Phases 34-40 (shipped 2026-02-16)
- **v4.0 Team-Based CASE** - Phases 41-47 (current)

---

## v4.0 Team-Based CASE (Phases 41-47)

**Milestone Goal:** Replace the single autonomous CASE agent with a 5-agent collaborative team that self-corrects through real-time peer review, fixing all v3.0 constraint-loss bugs.

**Motivation:** Live ibuprofen UAT (v3.0) revealed that the monolithic agent builds constraints correctly for iteration 1 but loses them when rewriting the LSD file for subsequent iterations. DEFF NOT patterns, SYME constraints, grouped notation, and statistical detection results all get dropped. A multi-agent team with explicit constraint tracking and pre-run validation prevents these losses.

**Team architecture:**
- **Coordinator** (team lead): Workflow orchestration, iteration management, result synthesis
- **NMR-Chemist**: Peak picking, multiplicity assignment, statistical detection, spectral quality
- **LSD-Engineer**: Constraint building, LSD file construction, inventory management
- **Solution-Analyst**: Ranking, chemical plausibility, quality assessment
- **Devils-Advocate**: Pre-run validation, constraint checking, diff analysis

**Phase overview:**

- [x] **Phase 41: Orchestrator Skill Modification** - Update case.md to spawn team via TeamCreate instead of single Task() (completed 2026-02-17)
- [x] **Phase 42: Agent Definitions** - Create 5 specialized agent files with distributed domain knowledge (completed 2026-02-17)
- [x] **Phase 43: Constraint Inventory System** - JSON-based constraint tracking in LSD file headers (completed 2026-02-17)
- [x] **Phase 44: CASE-PROGRESS.md Format** - Multi-agent journal with per-agent sections (completed 2026-02-17)
- [x] **Phase 45: Team Coordination Protocol** - Iteration loop, task assignment, stopping conditions (completed 2026-02-17)
- [x] **Phase 46: Diagnostic Integration** - Specialist integration with team context (completed 2026-02-17)
- [ ] **Phase 47: UAT with Live Compounds** - Validation against v3.0 baseline

---

### Phase 41: Orchestrator Skill Modification
**Goal**: case.md orchestrator spawns a 5-agent team via TeamCreate instead of a single autonomous agent via Task()
**Depends on**: v3.0 complete
**Requirements**: TEAM-01, TEAM-02
**Success Criteria** (what must be TRUE):
  1. case.md uses TeamCreate API to spawn 5-agent team (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate)
  2. Orchestrator monitors team progress via CASE-PROGRESS.md (same pattern as v3.0, multi-agent format)
  3. Orchestrator handles team lifecycle (spawn, monitor, terminate)
  4. Advisory interventions delivered to coordinator via SendMessage (not agent re-spawn)
  5. Loop detection and escalation logic preserved from v3.0 (4 patterns, per-pattern counters)
  6. Early TeamCreate API validation — confirm 5-agent team spawns and communicates successfully

**Research**: Complete (41-RESEARCH.md)
**Plans:** 3/3 plans complete

Plans:
- [ ] 41-01-PLAN.md — Create 4 stub agent definitions for early validation
- [ ] 41-02-PLAN.md — Rewrite case.md orchestrator for Agent Teams API
- [ ] 41-03-PLAN.md — Early validation of team spawning and communication

---

### Phase 42: Agent Definitions with Knowledge Distribution
**Goal**: 5 specialized agent definitions with distributed domain knowledge and clear inter-agent interfaces
**Depends on**: Phase 41 (orchestrator can spawn team)
**Requirements**: TEAM-03, TEAM-04, TEAM-05
**Success Criteria** (what must be TRUE):
  1. Agent definitions at ~/.claude/agents/lucy-{role}.md for all 5 roles (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate)
  2. Domain knowledge distributed by responsibility: NMR in nmr-chemist, LSD syntax in lsd-engineer, ranking in solution-analyst, validation in devils-advocate
  3. Each agent has clear interface definition (WHAT it posts to team, WHAT it reads from others)
  4. Shared knowledge policy defined (minimal duplication of core concepts, cross-references for details)
  5. No agent has knowledge gaps that would cause workflow failure (coverage validated)
  6. Old lucy-case-agent.md preserved as reference until v4.0 ships

**Research**: Complete (42-RESEARCH.md)
**Plans:** 5/5 plans complete

Plans:
- [ ] 42-01-PLAN.md -- NMR-Chemist full agent definition
- [ ] 42-02-PLAN.md -- LSD-Engineer full agent definition
- [ ] 42-03-PLAN.md -- Solution-Analyst full agent definition
- [ ] 42-04-PLAN.md -- Devils-Advocate full agent definition
- [ ] 42-05-PLAN.md -- Knowledge coverage validation

---

### Phase 43: Constraint Inventory System
**Goal**: Explicit JSON-based constraint tracking prevents loss of DEFF NOT, SYME, grouped notation, and detection results across iterations
**Depends on**: Phase 42 (lsd-engineer and devils-advocate agents defined)
**Requirements**: TEAM-06, TEAM-07, TEAM-08
**Success Criteria** (what must be TRUE):
  1. Constraint inventory stored as JSON comment block in LSD file header
  2. Inventory tracks all constraint types: MULT, HSQC, HMBC, DEFF NOT, SYME, BOND, LIST/PROP, ELIM
  3. LSD-Engineer reads previous LSD file (never reconstructs from memory) and updates inventory
  4. Devils-Advocate diffs iteration N vs N-1 and flags any constraint count decrease
  5. Grouped notation (HMBC (5 6) 10) preserved in inventory across iterations
  6. Detection results (hybridisation, neighbours, HHB, grouping) tracked in inventory with source annotation

**Research**: Complete (43-RESEARCH.md)
**Plans:** 2/2 plans complete

Plans:
- [ ] 43-01-PLAN.md -- LSD-Engineer inventory schema and procedures
- [ ] 43-02-PLAN.md -- Devils-Advocate inventory validation protocol

---

### Phase 44: CASE-PROGRESS.md Format
**Goal**: Multi-agent journal format with per-agent sections that orchestrator can reliably parse
**Depends on**: Phase 42 (agents defined, interfaces known)
**Requirements**: TEAM-09
**Success Criteria** (what must be TRUE):
  1. CASE-PROGRESS.md has per-iteration sections with per-agent contributions
  2. Coordinator is sole writer (agents post to team, coordinator writes to file) — prevents corruption
  3. Orchestrator can parse multi-agent format to extract solution count, constraints, issues
  4. Format is backward-compatible with v3.0 orchestrator parsing (solution count, iteration count)
  5. Each agent's contribution clearly attributed (who detected what, who validated what)

**Research**: Complete (44-RESEARCH.md)
**Plans:** 2/2 plans complete

Plans:
- [ ] 44-01-PLAN.md — Update 4 specialist agents with structured SendMessage templates (coordinator-as-sole-writer)
- [ ] 44-02-PLAN.md — Add write_progress step to orchestrator with full multi-agent format spec

---

### Phase 45: Team Coordination Protocol
**Goal**: Complete iteration workflow tested: NMR-Chemist detects, LSD-Engineer builds, Devils-Advocate validates, Coordinator runs LSD, Solution-Analyst reviews
**Depends on**: Phases 43, 44 (inventory and format ready)
**Requirements**: TEAM-10, TEAM-11, TEAM-12
**Success Criteria** (what must be TRUE):
  1. Single iteration workflow completes: detect → build → validate → solve → review
  2. Task assignment parallelizes where possible (NMR detection and solution review are independent)
  3. Devils-Advocate approval required before every LSD solver run (validation gate)
  4. Stopping conditions defined: convergence (solution count stable), max iterations (10), user escalation
  5. Coordinator synthesizes results from all agents into final report
  6. Time to solution measured and compared against v3.0 baseline (target: < 2x)

**Research**: Complete (45-RESEARCH.md)
**Plans:** 2/2 plans complete

Plans:
- [ ] 45-01-PLAN.md — Close 4 coordination gaps (iteration tasks, shift list, parallel tasks, time measurement)
- [ ] 45-02-PLAN.md — Dry-run coordination verification (trace full message flow, verify all 6 SCs)

---

### Phase 46: Diagnostic Integration
**Goal**: Diagnostic specialist works with team context for deep LSD failure analysis
**Depends on**: Phase 45 (team coordination working)
**Requirements**: TEAM-13
**Success Criteria** (what must be TRUE):
  1. Diagnostic specialist remains orchestrator-spawned (not a team member) for objectivity
  2. Specialist receives team context (CASE-PROGRESS.md, constraint inventory) for informed analysis
  3. Diagnostic report delivered to coordinator via orchestrator advisory
  4. Delegation trigger unchanged from v3.0 (2 failed basic interventions with same pattern)

**Research**: Complete (46-RESEARCH.md)
**Plans:** 1/1 plans complete

Plans:
- [ ] 46-01-PLAN.md — Update specialist instructions and knowledge for constraint inventory awareness and analysis/ path

---

### Phase 46.1: Agent Aromatic Ring Awareness (INSERTED)

**Goal:** Update CASE team agent instructions so they detect and act on aromatic ring mismatches between NMR evidence and LSD solutions
**Depends on:** Phase 46 + aromatic sanity check in ranking code (commit 2d4ce88)
**Motivation:** v4.0 UAT on ibuprofen: NMR-chemist correctly identified 5 sp2 carbons at 127-141 ppm (classic aromatic), but when all 7 solutions lacked aromatic rings, no agent flagged it. Solution-analyst hallucinated rank #1 as ibuprofen (actually a 7-membered ring). The ranking code now emits a `warnings` field with an aromatic mismatch message, but no agent reads or acts on it.

**Success Criteria** (what must be TRUE):
  1. solution-analyst checks `warnings` field from `lucy lsd rank --format json` output; if aromatic warning present, reports it as a critical finding to coordinator (not silently ignored)
  2. nmr-chemist explicitly flags "aromatic ring expected" in [SETUP-COMPLETE] message when it detects a cluster (>= 4) of sp2 carbons in 110-160 ppm region
  3. solution-analyst chemical plausibility assessment includes aromatic ring verification: if NMR-chemist flagged aromaticity expected, checks `has_aromatic_ring` field on top-ranked solutions
  4. When aromatic mismatch detected, solution-analyst recommends specific remediation (remove suspect HMBC correlations between aromatic positions and benzylic/alpha substituents)

**Agents to modify:**
- `~/.claude/agents/lucy-solution-analyst.md` — primary: read warnings, verify aromatic rings, report mismatch
- `~/.claude/agents/lucy-nmr-chemist.md` — flag aromatic expectation in setup message
- `~/.claude/agents/lucy-devils-advocate.md` — optional: post-ranking aromatic sanity check

**Plans:** 2 plans

Plans:
- [ ] 46.1-01-PLAN.md — Solution-analyst: Check 6 aromatic ring verification + [RANKING-COMPLETE] template + workflow --format json
- [ ] 46.1-02-PLAN.md — NMR-chemist: Aromatic expectation field + Devils-advocate: Aromatic Ring Expectation check

### Phase 47: UAT with Live Compounds
**Goal**: Team-based CASE validated against v3.0 baseline with diverse compounds
**Depends on**: Phase 46 (all components integrated)
**Requirements**: TEAM-14, TEAM-15
**Success Criteria** (what must be TRUE):
  1. Ibuprofen (C13H18O2): correct structure in top 3, all DEFF NOT patterns preserved across iterations
  2. All v3.0 constraint-loss bugs verified fixed: DEFF NOT persistence, SYME applied, grouped notation preserved, detection results translated to constraints
  3. Time to solution < 2x v3.0 baseline (coordination overhead acceptable)
  4. Additional test compounds (Pulegone, Virgiline) if time permits
  5. Performance comparison report: v3.0 monolithic vs v4.0 team (solution quality, constraint coverage, iteration count)

**Research**: Complete (47-RESEARCH.md)
**Plans:** 2 plans

Plans:
- [ ] 47-01-PLAN.md -- Live UAT run on Ibuprofen with v3.0 bug evaluation
- [ ] 47-02-PLAN.md -- Performance comparison report (v3.0 vs v4.0)

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 41. Orchestrator Skill Modification | v4.0 | Complete    | 2026-02-17 | -- |
| 42. Agent Definitions | v4.0 | Complete    | 2026-02-17 | -- |
| 43. Constraint Inventory System | v4.0 | Complete    | 2026-02-17 | -- |
| 44. CASE-PROGRESS.md Format | v4.0 | Complete    | 2026-02-17 | -- |
| 45. Team Coordination Protocol | v4.0 | Complete    | 2026-02-17 | -- |
| 46. Diagnostic Integration | v4.0 | Complete    | 2026-02-17 | -- |
| 47. UAT with Live Compounds | v4.0 | -- | Planned | -- |

---
*Last updated: 2026-02-17 after v4.0 milestone creation*
