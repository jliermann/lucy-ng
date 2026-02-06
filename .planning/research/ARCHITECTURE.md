# Architecture Patterns: Multi-Agent CASE Integration

**Domain:** Computer-Assisted Structure Elucidation (CASE)
**Researched:** 2026-02-06
**Focus:** Multi-agent + skill-first architecture for robust CASE

## Executive Summary

The v2.0 multi-agent architecture represents a paradigm shift from tool-heavy to skill-first design. The current system (v1.2) has 16 MCP tools with embedded intelligence (DEPT-guided picking, HMBC filtering, LSD generation). The new architecture pushes domain knowledge into skill instructions while simplifying tools to thin data access wrappers, with a supervisor agent preventing unproductive loops during structure elucidation.

**Key finding:** Research shows hybrid architectures with hierarchical skill routing and supervisor patterns dominate enterprise AI in 2026. Tool-heavy systems degrade beyond 50-100 tools, while skill-first approaches with dynamic capability loading maintain performance.

**Integration strategy:** Incremental refactoring, not rewrite. Keep working tools, layer in multi-agent orchestration, migrate intelligence from Python to skill over time.

## Recommended Architecture

### Three-Layer Model

```
┌─────────────────────────────────────────────────────┐
│              SKILL LAYER (Intelligence)              │
│  - CLAUDE.md (project-level instructions)           │
│  - skill/SKILL.md (workflow strategy)               │
│  - Supervisor rules (loop detection, redirection)   │
│  - Domain knowledge (tolerances, error handling)    │
└─────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────┐
│         MULTI-AGENT LAYER (Orchestration)           │
│  - Supervisor Agent (watches progress)              │
│  - CASE Agent (drives elucidation)                  │
│  - Specialist Agents (optional: peak picking, etc.) │
└─────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────┐
│            TOOL LAYER (Data Access)                  │
│  - 16 MCP tools (thin wrappers)                     │
│  - Python libraries (nmrglue, RDKit, LSD)           │
│  - SQLite database (928K compounds, 7.9M HOSE)      │
└─────────────────────────────────────────────────────┘
```

### Agent Roles

| Agent | Responsibility | Knowledge Source |
|-------|---------------|------------------|
| **Supervisor** | Monitor CASE progress, detect loops, redirect strategy | Supervisor rules in skill |
| **CASE Agent** | Execute structure elucidation workflow | SKILL.md workflow |
| **Peak Picker** (optional) | Specialist for spectral analysis | Peak picking section of skill |
| **LSD Specialist** (optional) | Constraint debugging, LSD file tuning | LSD troubleshooting section |

## Component Analysis: Current vs Target

### 1. SKILL ARCHITECTURE

**Current State (v1.2):**
- Single monolithic CLAUDE.md (1080 lines)
- Single SKILL.md (descriptive front matter + duplicate of CLAUDE.md)
- All knowledge in one document
- No separation of concerns

**Target State (v2.0):**

**Option A: Single Skill with Role Sections** (RECOMMENDED)
```
CLAUDE.md (project-level, applies to ALL agents)
  - Setup instructions
  - Database information
  - Common reference data
  - Quick reference card

skill/SKILL.md (CASE workflow, primary agent)
  - Full CASE workflow (dereplication → peak picking → LSD → ranking)
  - Domain knowledge (tolerances, shift regions, symmetry)
  - Supervisor rules (embedded in workflow checkpoints)

skill/SUPERVISOR.md (supervisor-specific rules)
  - Loop detection patterns
  - Redirection strategies
  - Progress checkpoints
  - Escalation criteria
```

**Option B: Modular Skills per Agent** (Alternative)
```
CLAUDE.md (project-level)
  - As above

skill/CASE.md (main CASE agent)
  - Workflow steps
  - Integration with specialists

skill/SUPERVISOR.md (supervisor agent)
  - Loop detection
  - Progress monitoring

skill/PEAK_PICKING.md (optional specialist)
  - DEPT-guided strategy
  - HMBC filtering knowledge

skill/LSD_DEBUG.md (optional specialist)
  - Constraint troubleshooting
  - sp2 counting rules
```

**Recommendation:** Start with Option A (single skill + supervisor rules). Only split to Option B if the main skill grows unwieldy (>2000 lines) or specialists are actively used.

**Rationale:**
- Simpler to maintain
- Less duplication
- Clearer for AI to understand role
- Easier to ensure consistency

### 2. TOOL LAYER ANALYSIS

Current tools categorized by intelligence level:

#### Tier 1: Pure Data Access (KEEP AS-IS)
These are thin wrappers, no intelligence to extract.

| Tool | Function | Intelligence Level |
|------|----------|-------------------|
| `read_spectrum_1d` | Read Bruker 1D file | **None** - pure data access |
| `read_spectrum_2d` | Read Bruker 2D file | **None** - pure data access |
| `check_lsd_availability` | Check if LSD installed | **None** - environment check |
| `run_lsd` | Execute LSD solver | **None** - subprocess wrapper |
| `fetch_nmrxiv_dataset` | Download from NMRXiv | **None** - API wrapper |
| `dereplicate_c13` | Database lookup | **None** - SQL query wrapper |
| `predict_c13_shifts` | HOSE-based prediction | **None** - database lookup |
| `get_hose_stats_info` | Database statistics | **None** - metadata query |

**Verdict:** 8/16 tools are already thin. No changes needed.

#### Tier 2: Moderate Intelligence (MIGRATE TO SKILL)
These encode strategy or filtering logic.

| Tool | Intelligence to Extract | Target Location |
|------|------------------------|-----------------|
| `pick_peaks_1d` | Threshold selection (default 0.05) | SKILL: "use threshold 0.05 for 1D, adjust if needed" |
| `pick_hsqc_peaks` | DEPT-guided adaptive algorithm | SKILL: "DEPT-guided picking ensures all carbons found" |
| `pick_hmbc_peaks` | Reference-based filtering (±1.5 ppm C, ±0.1 ppm H) | SKILL: "guided HMBC requires C match and H match" |
| `analyze_symmetry` | Interpretation hints in output | SKILL: "symmetry analysis checks observed vs expected" |
| `rank_lsd_solutions` | Tolerance (default 3.0 ppm), top_n selection | SKILL: "ranking uses 3 ppm tolerance for MAE" |

**Verdict:** Tools stay, but skill should explain WHEN and HOW to use them. The intelligence is the strategy (adaptive thresholding concept), not the parameter values.

**Action:**
1. Document the picking strategies in SKILL.md
2. Explain tolerance values and when to adjust
3. Tools remain as-is (backwards compatible)

#### Tier 3: Complex Intelligence (REFACTOR LATER)
These generate complex structures from NMR data.

| Tool | Intelligence | Refactoring Strategy |
|------|-------------|---------------------|
| `generate_lsd_input` | - Auto-detect experiments<br>- Map spectra to LSD atoms<br>- Generate MULT/HSQC/HMBC commands<br>- Heteroatom constraint logic | **Phase 2 refactor:**<br>- Move heteroatom logic to skill<br>- Simplify to data mapper<br>- AI constructs LSD file guided by skill |
| `generate_correlation_diagram` | - Parse LSD files<br>- Route arrows<br>- Layout optimization | **Keep as-is** (visualization, not CASE-critical) |

**Verdict:** `generate_lsd_input` is the most complex tool. Defer refactoring until supervisor architecture is validated. The AI can already bypass it by constructing LSD files directly (as seen in Virgiline case).

### 3. MULTI-AGENT FLOW

**Data flow between agents:**

```
User Request
    ↓
┌──────────────────────────────────────────────┐
│ Supervisor Agent                              │
│ - Spawns CASE agent with full context        │
│ - Monitors progress via checkpoints           │
│ - Receives status reports from CASE          │
└──────────────────────────────────────────────┘
    ↓ (spawn)
┌──────────────────────────────────────────────┐
│ CASE Agent                                    │
│ - Reads SKILL.md for workflow                │
│ - Executes: dereplication → symmetry → ...   │
│ - Reports to supervisor at checkpoints       │
│ - May spawn specialists for subtasks         │
└──────────────────────────────────────────────┘
    ↓ (optional spawn)
┌──────────────────────────────────────────────┐
│ Specialist Agents (if needed)                │
│ - Peak Picker: troubleshoot noisy HMBC       │
│ - LSD Debug: diagnose 0 solutions            │
│ - Return findings to CASE agent              │
└──────────────────────────────────────────────┘
```

**Communication protocol:**

Based on Claude Code's TeammateTool pattern (2026):

1. **Task List:** Shared markdown file `analysis/TASKS.md`
   - Supervisor writes high-level goal
   - CASE agent claims task
   - Checkpoints documented as completed tasks

2. **Messaging:** Inbox files in `analysis/messages/`
   - CASE → Supervisor: `progress_report_N.md`
   - Supervisor → CASE: `redirect_strategy.md`

3. **State Tracking:** `analysis/STATE.md`
   - Current workflow step
   - LSD solution count
   - Iterations attempted
   - Issues encountered

**Checkpoints (Supervisor monitors):**

| Checkpoint | Normal Progress | Warning Signs | Supervisor Action |
|------------|----------------|---------------|-------------------|
| After dereplication | Match found OR no match | N/A | None (continue) |
| After symmetry | Discrepancy explained | Unexplained missing carbons | Ask CASE to investigate |
| After LSD run 1 | 1-10 solutions | 0 or >100 solutions | Normal (CASE iterates per skill) |
| After LSD run 2 | 1-10 solutions | Still 0 or >100 | Review constraints with CASE |
| After LSD run 3+ | 1-10 solutions | **Same error repeated** | **INTERVENTION:** Redirect |

**Loop Detection Pattern:**

```python
# Pseudocode for supervisor
loop_detected = (
    (last_3_actions == ["modify HMBC", "run LSD", "0 solutions"]) or
    (iterations > 5 and solution_count_unchanged)
)

if loop_detected:
    # Supervisor intervenes
    send_message("redirect_strategy.md", content="""
    You've tried adjusting HMBC 3 times with 0 solutions each time.

    Alternative strategies:
    1. Check sp2 count (must be EVEN)
    2. Verify hydrogen count matches formula
    3. Try ELIM 1 0 (last resort)
    4. Question: Is the molecular formula correct?

    Choose one approach and document why.
    """)
```

### 4. STATE MANAGEMENT

**What supervisor tracks:**

```yaml
# analysis/STATE.md (structured markdown)
workflow_stage: "lsd_solving"
iteration: 3
solution_count: 0
last_action: "Added ELIM 1 0"
issues:
  - sp2_count_verified: true
  - hydrogen_count_verified: true
  - formula_questioned: false
flags:
  loop_detected: true
  intervention_count: 1
```

**State transitions:**

```
INIT → DEREPLICATION → SYMMETRY → PEAK_PICKING → LSD_GENERATION
  → LSD_SOLVING → [iteration loop] → RANKING → COMPLETE
```

**Loop back conditions:**
- LSD returns 0 solutions → iterate (up to N times)
- LSD returns >10 solutions → add constraints, iterate
- After N iterations with no progress → supervisor intervenes

## Integration Points with Existing System

### Integration Point 1: MCP Tools
**Current:** 16 tools directly callable
**New:** Same tools, but CASE agent calls them (not user directly)
**Change:** None to tools themselves, usage context changes

### Integration Point 2: Database
**Current:** SQLite with 928K compounds, 7.9M HOSE stats
**New:** Shared resource, all agents access same database
**Change:** None

### Integration Point 3: LSD Solver
**Current:** External binary, Python wrapper (`run_lsd`)
**New:** CASE agent orchestrates LSD runs with iterative refinement
**Change:** More sophisticated retry logic in SKILL, not code

### Integration Point 4: Skill Files
**Current:** CLAUDE.md + SKILL.md (duplicative)
**New:** CLAUDE.md (project-level) + SKILL.md (workflow) + SUPERVISOR.md (rules)
**Change:** Reorganize content, no new concepts needed

## New Components Needed

### Component 1: Supervisor Skill Document

**File:** `skill/SUPERVISOR.md`

**Contents:**
- Loop detection patterns
- Checkpoint monitoring rules
- Intervention strategies
- Escalation criteria

**Integration:** Supervisor agent reads this instead of main SKILL.md

### Component 2: State Tracking Templates

**File:** `analysis/STATE.md` (template)

**Contents:**
- Current stage
- Iteration count
- Issues encountered
- Flags for supervisor

**Integration:** CASE agent updates, supervisor reads

### Component 3: Task List

**File:** `analysis/TASKS.md`

**Contents:**
- High-level goal from user
- Subtasks (checkpoints)
- Completion status

**Integration:** Both agents read/write

### Component 4: Message Inbox

**Directory:** `analysis/messages/`

**Contents:**
- `progress_report_N.md` (CASE → Supervisor)
- `redirect_strategy.md` (Supervisor → CASE)

**Integration:** Asynchronous communication between agents

## Build Order (Considering Dependencies)

### Phase 1: Foundation (Can Start Immediately)
**Goal:** Set up multi-agent infrastructure without changing tools

**Tasks:**
1. Create `skill/SUPERVISOR.md` with loop detection rules
2. Create state tracking templates (`analysis/STATE.md`, `TASKS.md`)
3. Document supervisor intervention patterns
4. Write test scenarios (simple cases)

**Dependencies:** None
**Risk:** Low (additive, doesn't break anything)

### Phase 2: Skill Restructure (Parallel with Phase 1)
**Goal:** Reorganize skill content without changing behavior

**Tasks:**
1. Audit CLAUDE.md: separate project-level from workflow
2. Extract workflow to SKILL.md
3. Remove duplication
4. Add checkpoint markers in workflow
5. Document tool usage strategy (not code changes)

**Dependencies:** None (content reorganization)
**Risk:** Low (documentation change)

### Phase 3: Supervisor Integration (Depends on Phase 1)
**Goal:** Implement supervisor agent watching CASE agent

**Tasks:**
1. Create supervisor spawn pattern (based on TeammateTool)
2. Implement checkpoint monitoring
3. Test loop detection on known failure cases (Virgiline)
4. Validate intervention strategies

**Dependencies:** Phase 1 complete
**Risk:** Medium (new agent interaction pattern)

### Phase 4: Tool Simplification (Depends on Phase 2, 3 validated)
**Goal:** Migrate intelligence from tools to skill

**Tasks:**
1. Document picking strategies in SKILL.md
2. Document tolerance values and adjustment criteria
3. (Optional) Simplify `generate_lsd_input` if supervisor approach works
4. Add error tolerance knowledge to skill

**Dependencies:** Phases 2 and 3 complete, multi-agent validated
**Risk:** Medium (behavior changes, needs testing)

### Phase 5: Specialist Agents (Optional, Depends on Phase 3)
**Goal:** Add specialist agents for complex subtasks

**Tasks:**
1. Create Peak Picker specialist skill
2. Create LSD Debug specialist skill
3. Implement spawn/return pattern
4. Test on difficult cases

**Dependencies:** Phase 3 validated
**Risk:** High (complex, may not be needed if supervisor works well)

**Recommendation:** Skip Phase 5 initially. Supervisor + CASE agent may be sufficient.

## Suggested Build Order Summary

```
IMMEDIATE:
├─ Phase 1: Supervisor infrastructure (templates, rules)
└─ Phase 2: Skill restructure (parallel)

AFTER VALIDATION:
├─ Phase 3: Supervisor integration (depends on 1)
└─ Phase 4: Tool simplification (depends on 2, 3 working)

OPTIONAL (DEFER):
└─ Phase 5: Specialist agents (only if needed)
```

**Critical path:** Phase 1 → Phase 3 (supervisor working)
**Parallel work:** Phase 2 can happen anytime
**Deferred:** Phase 5 (specialists) until supervisor pattern validated

## Architecture Patterns from Research

### Supervisor Pattern (Databricks, Microsoft Azure, 2026)

**Key principle:** Exactly ONE agent designated as orchestrator to prevent coordination conflicts.

**Implementation:**
- Central coordinator receives request
- Decomposes into subtasks
- Delegates to specialists
- Monitors progress
- Validates outputs
- Synthesizes final response

**Lucy-ng application:**
- Supervisor = orchestrator
- CASE agent = primary specialist
- Optional specialists for peak picking, LSD debug

### Skill-First vs Tool-Heavy (HyperAI, 2026)

**Research finding:** Tool-heavy systems degrade beyond 50-100 tools due to semantic confusion and cognitive overload.

**Solution:** Skill-first with hierarchical routing:
- Core LLM dynamically loads reusable capabilities
- Skills organized into categories (math, retrieval, coding)
- Restores accuracy by up to 40% in large skill libraries

**Lucy-ng application:**
- Current: 16 tools (below degradation threshold, but growing)
- Target: Thin tools + skill-based strategy routing
- Prevents future scalability issues

### TeammateTool Pattern (Claude Code 2.1, 2026)

**Architecture:**
- Team lead spawns teammates (independent context windows)
- Shared task list with dependency tracking
- Inbox-based messaging for communication
- Teammates self-claim work as they finish

**Lucy-ng application:**
- Supervisor = team lead
- CASE agent = primary teammate
- Shared analysis/ directory for tasks and state
- Messaging via markdown files

## References and Sources

**Multi-Agent Orchestration:**
- [Multi-Agent Supervisor Architecture: Orchestrating Enterprise AI at Scale | Databricks](https://www.databricks.com/blog/multi-agent-supervisor-architecture-orchestrating-enterprise-ai-scale)
- [AI Agent Orchestration Patterns - Azure Architecture Center | Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Choosing the right orchestration pattern for multi agent systems | Kore.ai](https://www.kore.ai/blog/choosing-the-right-orchestration-pattern-for-multi-agent-systems)

**Claude Code Agent Teams:**
- [Claude Code's Hidden Multi-Agent System | Paddo.dev](https://paddo.dev/blog/claude-code-hidden-swarm/)
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Build Agent Skills Faster with Claude Code 2.1 Release | Medium](https://medium.com/@richardhightower/build-agent-skills-faster-with-claude-code-2-1-release-6d821d5b8179)

**Skill-First Architecture:**
- [AI Agent Architectures: Efficiency vs. Scaling Limits in 2026 | HyperAI](https://beta.hyper.ai/en/stories/53d4fafdd3b77c15bc7008b4122bc84c)
- [Multi-Agent AI Systems: The Complete Enterprise Guide for 2026 | Neomanex](https://neomanex.com/posts/multi-agent-ai-systems-orchestration)

## Critical Decisions

| Decision | Rationale |
|----------|-----------|
| **Single supervisor + CASE agent (not swarm)** | CASE is sequential workflow, not parallel tasks; supervisor prevents loops |
| **State tracking via markdown files** | Follows TeammateTool pattern; readable by AI and humans; no complex infrastructure |
| **Skill restructure before tool changes** | Safer; content changes don't break code; validates approach before refactoring |
| **Defer specialist agents** | Complexity not justified until supervisor pattern validated; may not be needed |
| **Keep 16 MCP tools as-is initially** | Backwards compatible; working system; migrate intelligence incrementally |
| **Extract heteroatom logic last** | Most complex tool intelligence; defer until supervisor proves value |

## Risks and Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Supervisor adds latency | Low | Checkpoints only, not continuous monitoring |
| State tracking fragile | Medium | Use structured markdown with validation |
| Skills diverge/duplicate | Medium | Regular audits, clear ownership (project vs workflow) |
| Specialist agents underutilized | Low | Don't build until proven needed (Phase 5 optional) |
| Tool simplification breaks backward compat | High | Keep dual mode (intelligent tools + skill guidance) during transition |

## Success Criteria

**Supervisor agent working:**
- [ ] Detects loop: same error 3x in a row
- [ ] Intervenes: sends redirect message to CASE agent
- [ ] CASE agent changes strategy based on supervisor input

**Skill-first validated:**
- [ ] CASE agent constructs LSD file without `generate_lsd_input` (using skill knowledge)
- [ ] Error tolerance handled by AI reasoning, not Python code
- [ ] Picking strategy decisions documented in analysis/, not hard-coded

**Integration complete:**
- [ ] Backward compatible: existing CLI usage still works
- [ ] Multi-agent mode: supervisor + CASE agent successfully solve difficult case (Virgiline)
- [ ] State tracking: clear audit trail in analysis/ directory

## Open Questions for Roadmap Phase Structure

**1. Should audit happen before or after supervisor prototype?**
- **Before:** Understand full codebase before adding complexity
- **After:** Validate supervisor approach first, audit informed by what worked

**Recommendation:** Parallel. Quick audit (categorize tools) informs Phase 1. Deep audit in Phase 4.

**2. How minimal should the first supervisor be?**
- **Minimal:** Just loop detection + redirect message
- **Full:** Complete checkpoint monitoring, state tracking, all intervention strategies

**Recommendation:** Start minimal. Add monitoring incrementally as patterns emerge.

**3. Should specialist agents be in scope for v2.0?**
- **Yes:** Complete multi-agent architecture
- **No:** Supervisor + CASE is sufficient, defer to v2.1

**Recommendation:** No. Supervisor alone addresses the Virgiline loop problem. Specialists are premature optimization.

**4. What's the migration path for existing users?**
- **Breaking:** New skill structure, must update
- **Compatible:** Dual mode (tools work standalone, multi-agent optional)

**Recommendation:** Compatible. CLI tools work standalone (existing behavior). Multi-agent is additive feature.

## Implications for Roadmap

**Suggested phase structure based on build order:**

1. **Phase: Supervisor Infrastructure** (Foundation)
   - Create supervisor skill document
   - Design state tracking templates
   - Document loop detection rules
   - Can start immediately, low risk

2. **Phase: Skill Restructure** (Parallel with #1)
   - Audit CLAUDE.md vs SKILL.md
   - Extract project-level vs workflow
   - Remove duplication
   - Add checkpoint markers
   - Low risk, content changes only

3. **Phase: Supervisor Integration** (Depends on #1)
   - Implement supervisor spawn pattern
   - Add checkpoint monitoring
   - Test on known failure cases
   - Validate intervention strategies
   - Medium risk, new agent interaction

4. **Phase: Tool Intelligence Migration** (Depends on #2, #3 validated)
   - Document strategies in skill
   - Add error tolerance knowledge
   - Simplify tools incrementally
   - Test backward compatibility
   - Medium risk, behavior changes

**Phase ordering rationale:**
- Phases 1 and 2 can run in parallel (independent)
- Phase 3 depends on 1 (needs supervisor templates)
- Phase 4 depends on 2 (skill must exist) and 3 (multi-agent validated before changing tools)

**Research flags for phases:**
- **Phase 1:** Low risk, standard pattern from literature
- **Phase 2:** Low risk, documentation restructure
- **Phase 3:** May need iteration on loop detection logic (test with real cases)
- **Phase 4:** Tool changes need careful validation (regression testing)

**Specialist agents (Phase 5) recommended for v2.1, not v2.0.**
