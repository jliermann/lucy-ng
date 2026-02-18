# Technology Stack: Multi-Agent CASE Coordination

**Project:** lucy-ng
**Milestone:** v4.0 Agent Teams for CASE
**Researched:** 2026-02-16
**Confidence:** HIGH

---

## Executive Summary

lucy-ng v3.0 uses single autonomous CASE agent with post-hoc orchestrator intervention. v4.0 replaces this with 5-agent collaborative team for real-time self-correction.

**Core finding:** Claude Code's agent teams feature (released Feb 5, 2026) provides all required coordination primitives. No new Python dependencies. Integration is orchestrator-level only—CLI tools and agent knowledge remain unchanged.

**Critical difference from v2.1 Task-based pattern:**
- v2.1: Task() spawns isolated subagents that report back to parent only
- v4.0: TeamCreate + Task(team_name) spawns teammates that message each other directly

---

## Core Agent Teams Stack

### Team Coordination APIs

| API | Purpose | lucy-ng v4.0 Usage |
|-----|---------|-------------------|
| **TeamCreate** | Initialize team infrastructure | Coordinator calls once at workflow start. Creates `~/.claude/teams/case-{compound}/config.json` and `~/.claude/tasks/case-{compound}/` task list. |
| **Task (with team_name)** | Spawn teammates | Coordinator spawns 4 specialists via `Task(team_name="case-{compound}", name="nmr-chemist", ...)`. Different from v3.0 isolated Task() calls. |
| **SendMessage** | Inter-agent messaging | All agents use for direct communication. nmr-chemist → lsd-engineer (peak assignments), solution-analyst ↔ devils-advocate (ranking debates), coordinator → all (broadcasts). |
| **TaskCreate** | Create shared work items | Coordinator populates task list with: peak-picking, statistical-detection, lsd-iteration-NN, ranking, final-analysis. |
| **TaskList** | Query task state | All agents query to discover available work and check completion. Used by specialists to claim next task when idle. |
| **TaskUpdate** | Modify task status/ownership | Specialists call when claiming (pending → in_progress), completing (in_progress → completed), or releasing blocked work. |

**Version:** Released Feb 5, 2026 alongside Claude Opus 4.6
**Feature flag:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (environment variable)
**Documentation:** https://code.claude.com/docs/en/agent-teams (official)

**Confidence:** HIGH (official docs, verified API parameters)

### Message Types

| Type | Purpose | lucy-ng Usage |
|------|---------|---------------|
| `"message"` | Direct 1-to-1 messaging | nmr-chemist sends peak assignments to lsd-engineer: `SendMessage(to="lsd-engineer", type="message", content="...")` |
| `"broadcast"` | Team-wide announcements | Coordinator announces milestones: `SendMessage(type="broadcast", content="Iteration 3 complete, 47 solutions")` |
| `"shutdown_request"` | Graceful termination | Coordinator sends when workflow complete or user stops. Teammates finalize work, save state, confirm ready. |
| `"shutdown_response"` | Confirm shutdown readiness | Teammates respond to shutdown_request with approval or rejection + reason. |
| `"plan_approval_request"` | Quality gate enforcement | NOT used in v4.0 MVP (no plan-before-implement workflow). Reserved for future if coordinator requires teammate approval before LSD changes. |
| `"plan_approval_response"` | Approve/reject plans | NOT used in v4.0 MVP. |

**Message delivery:** Automatic. SendMessage writes to `~/.claude/teams/{team}/inboxes/{agent}.json`. Recipient polls inbox on next turn.

**Confidence:** HIGH (official docs, verified message flow)

### Task Structure

| Field | Type | Purpose | Example Value |
|-------|------|---------|---------------|
| `subject` | string | Task name/ID | `"lsd-iteration-03"` |
| `description` | string | Task instructions | `"Run LSD iteration 3 with next HMBC batch (correlations 11-15)"` |
| `status` | enum | Current state | `"pending"` / `"in_progress"` / `"completed"` |
| `owner` | string | Assigned agent | `"lsd-engineer"` or `null` if unclaimed |
| `dependencies` | array | Prerequisite tasks | `["peak-picking", "statistical-detection"]` |

**Storage:** `~/.claude/tasks/{team-name}/{task-id}.json`
**Locking:** File-based locking prevents race conditions when multiple agents claim same task.

**Confidence:** HIGH (official docs, verified task schema)

### Team Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| `teammateMode` | `"auto"` (default) | Uses tmux split panes if available (visual monitoring of 5 agents), falls back to in-process if not. No forced tmux prevents setup friction. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `"1"` | Required environment variable to enable feature. Documented in case.md orchestrator setup. |
| Delegate mode | Enabled for coordinator | Restricts coordinator to coordination-only tools (TeamCreate, SendMessage, TaskCreate, TaskUpdate). Prevents coordinator from doing CASE work—only teammates execute. |
| Permission inheritance | From coordinator session | Teammates start with coordinator's permission mode. If coordinator runs `--dangerously-skip-permissions`, all teammates inherit. Can change per-teammate after spawn. |
| Model per agent | All opus (v4.0) | All agents need full reasoning for NMR/chemistry domain. No sonnet variants—CASE errors expensive (wasted LSD iterations). |

**Confidence:** HIGH (official docs, verified configuration options)

---

## Agent Definitions Required

### Coordinator (Team Lead)

**File:** `~/.claude/agents/lucy-case-coordinator.md`

**Role:** CASE workflow orchestration via team coordination, NOT execution

**Tools allowed:** TeamCreate, SendMessage, TaskCreate, TaskUpdate, TaskList, Read, Glob

**Tools forbidden:** Bash (no lucy CLI execution), Write (no LSD file writing)

**Why delegate mode:** Without it, coordinator implements tasks itself instead of delegating. Explicit tool restriction forces delegation-only workflow.

**Responsibilities:**
- Initialize team with TeamCreate(name="case-{compound}")
- Spawn 4 specialists via Task(team_name="case-{compound}", name="...", agent_type="...")
- Create task sequence: peak-picking → statistical-detection → lsd-iteration-01 → ... → ranking → final-analysis
- Broadcast iteration milestones: "Iteration N complete, X solutions, Y constraints added"
- Monitor task completion via TaskList, reassign if stuck
- Send shutdown_request when workflow complete or user stops
- Synthesize final results from solution-analyst + devils-advocate reports

**Key knowledge:** Workflow structure, task dependencies, milestone definitions. NO NMR domain knowledge (delegates all chemistry reasoning).

**Confidence:** HIGH (pattern adapted from GSD gsd-orchestrator, agent teams docs)

### NMR Chemist (Specialist)

**File:** `~/.claude/agents/lucy-nmr-chemist.md`

**Role:** Peak picking, quality assessment, multiplicity determination

**Tools:** Bash (lucy CLI), Read, Write, TaskList, SendMessage

**Knowledge source:** Sections 2-3 from current lucy-case-agent.md (NMR background, spectral quality, peak picking)

**Responsibilities:**
- Claim peak-picking task from shared list
- Run lucy pick 1d/hsqc/hmbc with quality-adjusted thresholds
- Detect DEPT-135 negative peaks (CH2), disambiguate CH vs CH3
- Assess spectral quality (SNR, digital resolution), adjust thresholds
- Run statistical detection (hybridisation, neighbours, hhb, grouping)
- Send findings to lsd-engineer via SendMessage(to="lsd-engineer", type="message", content="Peak assignments: ...")
- Flag ambiguities (overlapping signals, low SNR) to coordinator

**Output format:** Structured message with peak assignments + detection results + quality flags

**Confidence:** HIGH (knowledge extraction from validated lucy-case-agent.md)

### LSD Engineer (Specialist)

**File:** `~/.claude/agents/lucy-lsd-engineer.md`

**Role:** LSD file construction, constraint translation, iteration execution

**Tools:** Bash (lucy CLI, LSD), Read, Write, TaskList, SendMessage

**Knowledge source:** Sections 3-4 from current lucy-case-agent.md (LSD command reference, statistical detection protocol, incremental HMBC strategy)

**Responsibilities:**
- Claim lsd-iteration-NN tasks from shared list
- Receive peak assignments + statistical detection results from nmr-chemist (via inbox or shared file)
- Translate to LSD constraints: MULT, HSQC, HMBC, BOND, PROP
- Apply chemistry-first hierarchy when detection conflicts with NMR
- Write LSD file to analysis/iteration_NN/compound.lsd
- Run LSD from iteration directory, convert solutions with outlsd 5
- Send solution count + diagnostic summary to coordinator
- Respond to diagnostic queries from devils-advocate
- Update CASE-PROGRESS.md after EVERY iteration (append-only)

**Critical constraint:** Must preserve auxiliary constraints (badlist DEFF NOT, signal grouping, heteroatom PROP) across iterations. v3.0 UAT showed agent drops these when rebuilding LSD file—v4.0 devils-advocate monitors for this.

**Confidence:** HIGH (knowledge extraction from validated lucy-case-agent.md, UAT findings documented)

### Solution Analyst (Specialist)

**File:** `~/.claude/agents/lucy-solution-analyst.md`

**Role:** 13C prediction ranking, confidence scoring, final structure selection

**Tools:** Bash (lucy CLI), Read, Write, TaskList, SendMessage

**Knowledge source:** Sections 6-7 from current lucy-case-agent.md (Ranking algorithm, confidence scoring)

**Responsibilities:**
- Claim ranking task when solution count ≤ 10 (task dependency: lsd-iteration-NN complete + solution_count ≤ 10)
- Run lucy lsd rank solutions.smi --shifts "..."
- Analyze two-tier ranking: match count (descending) → MAE (ascending)
- Compute per-atom confidence: resolution + HOSE quality + correlations
- Derive overall structure confidence: HIGH/MEDIUM/LOW
- Send top candidates to devils-advocate for critique via SendMessage
- Write final recommendation to analysis/final_results.md

**Key insight:** Two-tier ranking means 13/13 matches with MAE 2.5 beats 11/13 matches with MAE 1.8. Completeness > precision. Devils-advocate validates this logic.

**Confidence:** HIGH (algorithm validated in v3.0 UAT, ranking logic proven)

### Devils Advocate (Specialist)

**File:** `~/.claude/agents/lucy-devils-advocate.md`

**Role:** Challenge assumptions, detect loops, prevent premature convergence

**Tools:** Read, TaskList, SendMessage (NO execution tools—advisory only)

**Knowledge source:** Loop detection patterns from current case.md orchestrator (detect_loops, diagnose steps), UAT learnings

**Responsibilities:**
- Monitor all task completions via TaskList
- Read CASE-PROGRESS.md after each lsd-iteration-NN task completes
- Detect loop patterns:
  - ELIM thrashing (ELIM added/removed repeatedly)
  - Zero-solution loop (3+ consecutive iterations with 0 solutions)
  - Solution explosion (3+ iterations with >100 solutions, <10% reduction each)
  - Constraint churning (high add/remove activity without convergence)
- Challenge solution-analyst rankings: "Why does rank #1 have lower match count than rank #2?"
- Question lsd-engineer constraint choices: "Why BOND for second oxygen instead of PROP? (Pitfall 6)"
- Check for dropped constraints: "Iteration 1 had 6 DEFF NOT patterns, iteration 2 has 0—why?"
- Send diagnostic advisories to coordinator via SendMessage when patterns detected
- Challenge coordinator decisions: "Are we rushing to ranking with 47 solutions? Standard is ≤10."

**Key knowledge:** Loop patterns, UAT failure modes (badlist dropped, grouped notation dropped, PROP not used), chemistry pitfalls (Pitfall 6: over-constraining heteroatoms, Pitfall 7: H budget diagnosis order)

**Confidence:** HIGH (pattern extraction from validated case.md orchestrator, UAT findings)

---

## Orchestrator Integration

### case.md Skill Changes (v3.0 → v4.0)

**File:** `~/.claude/commands/lucy-ng/case.md`

**v3.0 pattern (Task-based single agent):**
```python
Task(
  agent_type="lucy-case-agent",
  model="opus",
  instructions="Perform CASE for compound at {path} with formula {formula}. Write CASE-PROGRESS.md after EVERY iteration."
)
# Wait for agent return
# Read CASE-PROGRESS.md
# Detect loops post-hoc
# Re-spawn agent with advisory if loop detected
```

**v4.0 pattern (agent teams):**
```python
# Step 1: Initialize team
TeamCreate(
  name="case-{compound_name}",
  description="CASE workflow for {compound_name} ({formula})"
)

# Step 2: Spawn coordinator as team lead
Task(
  team_name="case-{compound_name}",
  name="coordinator",
  agent_type="lucy-case-coordinator",
  model="opus",
  instructions="Orchestrate CASE workflow. Spawn specialists: nmr-chemist, lsd-engineer, solution-analyst, devils-advocate. Create task sequence. Monitor progress. Synthesize results."
)

# Coordinator spawns specialists internally via Task(team_name, name)
# Coordinator manages task list via TaskCreate/TaskUpdate
# Specialists communicate via SendMessage
# Coordinator waits for all tasks complete before returning
```

**Key differences:**
- v3.0: Skill spawns agent directly → monitors externally → intervenes post-hoc
- v4.0: Skill spawns coordinator → coordinator spawns specialists → real-time self-correction via devils-advocate

**Why better:** Loop detection happens in real-time (devils-advocate monitors CASE-PROGRESS.md after each iteration), not after 3-5 wasted iterations.

**Confidence:** HIGH (pattern from official agent teams docs, adapted to CASE workflow)

### Task Dependency DAG

```
peak-picking (no deps)
  ↓
statistical-detection (depends: peak-picking)
  ↓
lsd-iteration-01 (depends: statistical-detection)
  ↓
lsd-iteration-02 (depends: lsd-iteration-01)
  ↓
lsd-iteration-03 (depends: lsd-iteration-02)
  ↓
... (conditional: while solution_count > 10 AND iterations < 10)
  ↓
ranking (depends: lsd-iteration-NN, condition: solution_count ≤ 10)
  ↓
final-analysis (depends: ranking)
```

**Coordinator responsibilities:**
- Create all tasks at start (or dynamically as iterations progress)
- Set dependencies correctly
- Monitor TaskList to detect stuck tasks
- Send broadcasts for milestone transitions

**Specialist responsibilities:**
- Query TaskList for available work (status=pending, deps satisfied, owner=null)
- Claim task via TaskUpdate(id, owner=self, status=in_progress)
- Execute work
- Report completion via TaskUpdate(id, status=completed) + SendMessage to relevant agents

**Confidence:** HIGH (task-based coordination pattern from official docs)

---

## Architecture Patterns

### Pattern 1: Task-Based Coordination (Recommended for v4.0)

**How it works:**
1. Coordinator creates tasks for each workflow stage
2. Specialists claim tasks from shared list when ready
3. Task dependencies prevent out-of-order execution
4. TaskList provides shared visibility of workflow state

**Example:**
```python
# Coordinator creates tasks
TaskCreate(subject="peak-picking", description="...", dependencies=[])
TaskCreate(subject="lsd-iteration-01", description="...", dependencies=["peak-picking", "statistical-detection"])
TaskCreate(subject="ranking", description="...", dependencies=["lsd-iteration-NN"], condition="solution_count <= 10")

# Specialists query and claim
tasks = TaskList()  # nmr-chemist queries
available = [t for t in tasks if t.status == "pending" and t.owner is None and deps_satisfied(t)]
claim = available[0]
TaskUpdate(claim.id, owner="nmr-chemist", status="in_progress")
# Execute work
TaskUpdate(claim.id, status="completed")
```

**Advantages:**
- Self-documenting workflow state (TaskList shows pending/complete)
- Automatic dependency resolution (blocked tasks unblock when deps complete)
- Graceful resumption (if coordinator crashes, task state persists in filesystem)
- Audit trail (task completion timestamps in JSON files)

**When to use:** Default pattern for CASE. Iterative workflows with clear stage dependencies.

**Confidence:** HIGH (official docs, verified task-based pattern)

### Pattern 2: Direct Messaging Coordination (Alternative)

**How it works:**
1. Coordinator spawns all teammates at start
2. Sends instructions via SendMessage one-by-one
3. Teammates report results via reply messages
4. No task list—coordinator tracks state internally

**Advantages:**
- Simpler for short workflows (3-4 steps)
- No task state management overhead
- More flexible for dynamic workflows (branching logic)

**Disadvantages:**
- No shared visibility (coordinator is bottleneck)
- No automatic dependency resolution
- Hard to resume if coordinator crashes (no persistent state)

**When to use:** Quick investigations (dereplication only, predict only). NOT recommended for full CASE (10+ iterations, complex state).

**Confidence:** MEDIUM (pattern mentioned in docs but not detailed)

### Pattern 3: Broadcast + Self-Coordination (Future)

**How it works:**
1. Coordinator broadcasts milestone announcements
2. Specialists monitor broadcasts, self-coordinate via direct SendMessage
3. No central task queue—specialists decide next work autonomously

**Advantages:**
- Maximum autonomy for specialists
- Scales to larger teams (no central bottleneck)
- Resilient to coordinator failure

**Disadvantages:**
- Complex coordination logic in each specialist
- Risk of duplicate work or missed work
- Hard to debug (no central state view)

**When to use:** NOT for v4.0 MVP. Reserved for future multi-compound parallel CASE where multiple coordinators run simultaneously.

**Confidence:** LOW (speculative pattern, not documented)

---

## What NOT to Use

### ❌ Nested Teams (Teammates Spawning Teammates)

**API limitation:** Only team lead can spawn teammates. Teammates cannot call TeamCreate or spawn sub-teammates.

**lucy-ng implication:** Coordinator must spawn all 4 specialists directly. lsd-engineer cannot spawn diagnostic sub-specialist.

**Workaround:** If diagnostic needed, lsd-engineer sends message to coordinator requesting diagnostic spawn. Coordinator spawns 5th teammate (lucy-diagnostic) and connects lsd-engineer ↔ lucy-diagnostic via messaging.

**Confidence:** HIGH (explicit limitation in official docs)

### ❌ Plan Approval Gates (v4.0)

**Feature:** SendMessage(type="plan_approval_request") + plan_approval_response

**Why not use:** CASE iterations are exploratory—require rapid cycle time. Plan approval adds round-trip delay (lsd-engineer plans → coordinator reviews → approve/reject → lsd-engineer implements). Net loss: slows iteration without clear benefit.

**Alternative:** Devils-advocate critiques post-facto. LSD iteration executes immediately, devils-advocate reviews CASE-PROGRESS.md and challenges decisions. If mistake detected, next iteration corrects.

**Confidence:** HIGH (design decision based on CASE workflow analysis)

### ❌ Broadcast for Routine Updates

**Token cost:** Broadcast scales with team size. 5 agents × broadcast = 5× message cost vs direct message.

**lucy-ng guideline:** Use SendMessage(to="specific-agent") for routine updates. Reserve broadcast ONLY for critical announcements:
- "Zero solutions detected, all agents pause for diagnosis"
- "User requested stop, begin shutdown sequence"
- "Iteration 5 complete, solution count now 12—prepare for ranking"

**Confidence:** HIGH (official docs warn about broadcast cost)

### ❌ In-Process Mode (Forced)

**Setting:** `teammateMode: "in-process"` forces all teammates into main terminal, no visual separation.

**Why not:** User cannot see specialist activity. Debugging difficult when loop occurs. No way to inspect individual agent state.

**Recommended:** `teammateMode: "auto"` (uses tmux if available, fallback in-process). User can Shift+Up/Down to switch between agents in-process mode, or see all agents in split panes with tmux.

**Confidence:** HIGH (official docs, usability analysis)

### ❌ Single Model Tier (All Sonnet)

**Cost consideration:** Sonnet cheaper than Opus. Why not use sonnet for simple tasks?

**CASE reality:** NMR/chemistry reasoning is complex. Errors = wasted LSD iterations (15-30 min per iteration × 3-5 wasted = 45-150 min). Sonnet error rate higher than opus for domain reasoning.

**Token cost vs time cost:** Extra opus cost (~$3-6 per run) < cost of rework (45-150 min × user hourly value).

**Decision:** All agents use opus. Token cost justified by avoiding iteration rework.

**Confidence:** HIGH (domain complexity analysis, UAT learnings)

---

## Team State Management

| State Location | What's Stored | Who Reads | Who Writes |
|----------------|---------------|-----------|------------|
| `~/.claude/teams/{team}/config.json` | Team member list (names, agent IDs, types) | All agents (discover teammates via Read) | TeamCreate (init), Task(team_name) (add member) |
| `~/.claude/tasks/{team}/` | Task definitions (subject, status, deps, owner) | All agents (via TaskList) | Coordinator (via TaskCreate), Specialists (via TaskUpdate) |
| `~/.claude/teams/{team}/inboxes/{agent}.json` | Pending messages for agent | Each agent (inbox polling on each turn) | SendMessage callers |
| `analysis/CASE-PROGRESS.md` | Iteration history, diagnostics | All agents (via Read) | lsd-engineer (append per iteration) |
| `analysis/iteration_NN/compound.lsd` | LSD constraint definitions | lsd-engineer (current), solution-analyst (review), devils-advocate (audit) | lsd-engineer (Write) |
| `analysis/final_results.md` | Top candidates, confidence, recommendation | Coordinator (synthesize), User (final output) | solution-analyst (Write) |

**Critical insight:** Agent teams use filesystem for state, not in-memory. Enables:
- Session resumption (coordinator crashes, re-spawn reads task state from disk)
- Parallel inspection (user can `cat ~/.claude/tasks/{team}/task-03.json` to debug)
- Audit trail (task completion timestamps in filesystem metadata)
- Human monitoring (`tail -f analysis/CASE-PROGRESS.md` works during team execution)

**Confidence:** HIGH (official docs, verified file locations)

---

## Token Cost Model

| Agent | Turns per Run | Avg Context per Turn | Total Tokens (Estimated) |
|-------|---------------|----------------------|--------------------------|
| Coordinator | 20-30 (task mgmt, broadcasts) | 5k (no NMR domain, coordination only) | 100-150k |
| NMR Chemist | 5-8 (peak picking, quality, detection) | 15k (spectra summaries + detection results) | 75-120k |
| LSD Engineer | 10-15 (iterations) | 20k (CASE-PROGRESS + LSD files + domain knowledge) | 200-300k |
| Solution Analyst | 2-3 (ranking, confidence) | 15k (ranking results + top candidates) | 30-45k |
| Devils Advocate | 10-20 (loop checks, challenges) | 8k (read-only, no execution, pattern matching) | 80-160k |
| **TOTAL** | | | **485-775k tokens/run** |

**Comparison to v3.0 single agent:**
- v3.0: ~300-400k tokens/run (single agent, 10 iterations, post-hoc supervisor interventions)
- v4.0: ~485-775k tokens/run (team, same 10 iterations, real-time self-correction)
- **Overhead:** 60-95% increase
- **Benefit:** Zero supervisor interventions (loop detection built-in), faster convergence (devils-advocate prevents thrashing), better quality (peer review at each step)

**Cost justification:** LSD iteration rework is expensive (15-30 min per iteration × 3-5 wasted iterations = 45-150 min). Agent team overhead (185-375k extra tokens = ~$3.70-7.50 at opus pricing $0.02/1k input) prevents 1-2 wasted iterations → net time savings of 30-60 min.

**Confidence:** MEDIUM (estimated based on v3.0 token usage extrapolated to 5 agents)

---

## Installation

```bash
# 1. Enable agent teams feature
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Or add to ~/.claude/settings.json:
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "auto"
}

# 2. Create agent definitions directory (if not exists)
mkdir -p ~/.claude/agents

# 3. Write 5 agent definition files:
# - lucy-case-coordinator.md (team lead, delegation-only)
# - lucy-nmr-chemist.md (peak picking, quality, detection)
# - lucy-lsd-engineer.md (LSD files, iterations, constraints)
# - lucy-solution-analyst.md (ranking, confidence, recommendations)
# - lucy-devils-advocate.md (loop detection, challenges, quality gates)

# 4. Update case.md orchestrator skill
# Change from Task(agent_type) to TeamCreate + Task(team_name, name)

# 5. Verify setup
claude --version  # Should be >= Feb 5 2026 release
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS  # Should print "1"

# No new Python packages needed—agent teams are built into Claude Code
```

**Confidence:** HIGH (setup steps from official docs)

---

## Version Compatibility

| Component | Version | Notes |
|-----------|---------|-------|
| Claude Code | ≥ Feb 5 2026 release | Agent teams released alongside Opus 4.6 |
| Claude model | claude-opus-4-6 | Agent teams require opus model tier |
| CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | `"1"` | Must be set in environment or settings.json |
| lucy-ng CLI | ≥ v3.0 | No CLI changes required—tools work identically in team context |
| Existing agent definitions | DEPRECATED | lucy-case-agent.md (666 lines) NOT used in v4.0—knowledge split across 5 specialists |
| Existing orchestrator | REPLACED | case.md orchestrator rewritten from Task() to TeamCreate + team-based Task() |

**Breaking change:** v3.0 → v4.0 requires:
1. Replace single lucy-case-agent.md with 5 specialist agents
2. Rewrite case.md orchestrator from Task(agent_type) to TeamCreate + Task(team_name)
3. Add devils-advocate loop detection (replaces post-hoc supervisor pattern)

**Migration effort:** High (complete orchestrator rewrite). No backward compatibility (Task vs TeamCreate are different spawn mechanisms).

**Confidence:** HIGH (API differences verified against official docs)

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Agent teams (5 specialists) | Task-based subagents (current v3.0) | Single-compound CASE where real-time self-correction not needed. Cheaper (40-60% lower token cost). |
| Task-based coordination (shared task list) | Direct messaging (SendMessage only) | Simple workflows with < 5 steps and no complex dependencies. |
| Delegate mode for coordinator | Coordinator with full tools | Rapid prototyping where coordinator may need to intervene directly. Risk: coordinator does work instead of delegating. |
| 5 specialized agents (nmr, lsd, analyst, advocate, coordinator) | 3 general agents (nmr, lsd, qa) | Smaller team reduces coordination overhead (40% fewer agents). Loses devils-advocate real-time loop detection. |
| All opus model tier | Mixed opus (coordinator) + sonnet (specialists) | If chemistry reasoning offloaded to specialist knowledge base. Risk: sonnet errors in NMR domain. |

**Confidence:** HIGH (alternatives analysis based on official docs + CASE requirements)

---

## Sources

### Official Documentation

**PRIMARY SOURCES (HIGH confidence):**
- [Orchestrate teams of Claude Code sessions - Claude Code Docs](https://code.claude.com/docs/en/agent-teams) — TeamCreate, SendMessage, Task API, team configuration, teammate spawning
- [TechCrunch: Anthropic releases Opus 4.6 with agent teams](https://techcrunch.com/2026/02/05/anthropic-releases-opus-4-6-with-new-agent-teams/) — Release date Feb 5 2026, official announcement

**SECONDARY SOURCES (MEDIUM confidence, verified against official docs):**
- [Claude Code Swarm Orchestration Gist](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea) — TeammateTool operations (13 operations: spawnTeam, write, broadcast, requestShutdown, etc.), message flow, spawn backends
- [From Tasks to Swarms: Agent Teams in Claude Code](https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/) — Task-based coordination patterns, practical examples
- [Enable Team Mode in Claude Code](https://scottspence.com/posts/enable-team-mode-in-claude-code/) — Setup instructions, settings.json configuration, environment variable

**TERTIARY SOURCES (LOW confidence, community discussions):**
- [GitHub Issue: Superpowers #429](https://github.com/obra/superpowers/issues/429) — TeammateTool, SendMessage, TaskList API discussion (feature request, not authoritative)
- [GitHub Issue: Superpowers #469](https://github.com/obra/superpowers/issues/469) — Parallel plan execution with agent teams (planning discussion, not implementation)

### Existing lucy-ng Implementation (for knowledge migration)

**AUTHORITATIVE SOURCES (HIGH confidence, validated via UAT):**
- `/Users/steinbeck/.claude/agents/lucy-case-agent.md` (666 lines) — NMR domain knowledge, CASE workflow, statistical detection, pitfalls
- `/Users/steinbeck/.claude/commands/lucy-ng/case.md` (672 lines) — Loop detection patterns, diagnostic decision trees, intervention logic
- `/Users/steinbeck/Dropbox/develop/lucy-ng/CLAUDE.md` — Lucy-ng CLI reference, tool syntax
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/STATE.md` — v3.0 UAT findings: badlist dropped, grouped notation dropped, PROP not used, H budget diagnosis order

**Knowledge distribution for v4.0:**
- lucy-case-agent.md Sections 1-3 → lucy-nmr-chemist.md (NMR background, quality, peak picking)
- lucy-case-agent.md Sections 3-4 → lucy-lsd-engineer.md (LSD syntax, constraints, incremental HMBC)
- lucy-case-agent.md Sections 6-7 → lucy-solution-analyst.md (ranking, confidence scoring)
- case.md detect_loops + diagnose → lucy-devils-advocate.md (loop patterns, challenges, diagnostics)
- case.md orchestrator → lucy-case-coordinator.md (workflow structure, task dependencies, synthesis)

**Confidence:** HIGH (direct knowledge extraction from validated implementations)

---

## Next Steps

**ARCHITECTURE.md:** Agent interaction patterns, message flow diagrams, task dependency DAG, error handling

**PITFALLS.md:** Team coordination failure modes, message delivery issues, task race conditions, coordinator bottleneck scenarios

**SUMMARY.md:** Roadmap implications for v4.0 milestone (phase structure, research flags, integration with existing v3.0 baseline)

---

*Stack research for: Multi-agent CASE workflow coordination with Claude Code agent teams*
*Researched: 2026-02-16*
*Confidence: HIGH (official docs + validated v3.0 baseline)*
