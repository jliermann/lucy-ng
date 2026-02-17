# Phase 41: Orchestrator Skill Modification - Research

**Researched:** 2026-02-17
**Domain:** Claude Code Agent Teams API — TeamCreate, Task(team_name), SendMessage, TaskCreate/TaskList/TaskUpdate
**Confidence:** HIGH

---

## Summary

Phase 41 modifies the `/lucy-ng:case` orchestrator skill (`~/.claude/commands/lucy-ng/case.md`) to spawn a 5-agent team via the Claude Code Agent Teams API instead of spawning a single `lucy-case-agent` via `Task()`. This phase is primarily an API integration task: replacing one spawn pattern with another, then adapting the monitoring, intervention, and lifecycle management logic to work with the team.

**Critical finding: the orchestrator skill IS the team lead.** The main Claude Code session running the skill calls `TeamCreate`, spawns 4 specialist teammates via `Task(team_name=...)`, and manages the team directly. There is no separate "coordinator" agent — the skill itself performs that role. This is constrained by the official API: teammates cannot spawn their own teams or teammates. Only the lead (the session that called TeamCreate) can manage the team.

The prior research documents (STACK.md, ARCHITECTURE.md) describe a "coordinator" teammate who spawns the other specialists. This pattern is INVALID per the official API. The correct architecture has the orchestrator skill acting as coordinator, spawning all 4 specialists directly.

**Primary recommendation:** Rewrite the `spawn_case_agent` and `respawn` steps in case.md to use TeamCreate + Task(team_name). Replace the re-spawn intervention pattern with SendMessage advisory delivery to the surviving team. Adapt loop detection to parse multi-agent CASE-PROGRESS.md format.

---

## Standard Stack

### Core — Agent Teams API (Claude Code built-in)

| Tool | Purpose | How Used in Phase 41 |
|------|---------|---------------------|
| `TeamCreate` | Initialize team namespace on disk | Call once in spawn step: `TeamCreate(team_name="case-{compound}", description="CASE workflow for {formula}")` |
| `Task(team_name, name)` | Spawn a teammate into the team | Spawn 4 specialists: `Task(name="nmr-chemist", team_name="case-{compound}", subagent_type="...", ...)` |
| `TaskCreate` | Define work items on shared task list | Create iteration tasks: peak-picking, lsd-iteration-NN, ranking, final-analysis |
| `TaskList` | Query shared task state | Monitor progress: check which tasks are in_progress/completed |
| `TaskUpdate` | Modify task status/ownership | Teammates use to claim and complete tasks; lead uses to reassign stuck work |
| `SendMessage` | Inter-agent messaging | Deliver advisory constraints to running team; shut down team at end |
| `TeamDelete` | Clean up team resources | Called after team completes work and all teammates shut down |

**Enabling:** Agent teams are disabled by default. Requires:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```
Or `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in shell environment.

**Source:** Official Claude Code docs at https://code.claude.com/docs/en/agent-teams (HIGH confidence, verified 2026-02-17)

### Supporting — Existing case.md Logic (Preserved)

| Component | Current Location | Changes in Phase 41 |
|-----------|-----------------|---------------------|
| Argument parsing | `parse_arguments` step | No change |
| Prerequisite validation | `validate_prerequisites` step | Add: check `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set |
| Loop detection (4 patterns) | `detect_loops` step | Adapt to parse multi-agent CASE-PROGRESS.md format |
| Diagnosis logic | `diagnose` step | No change (reads LSD files, not agent-specific) |
| Intervention templates | `intervene` step | No change (advisory text content unchanged) |
| Intervention delivery | `respawn` step | REPLACE: re-spawn → SendMessage to surviving team |
| Per-pattern counters | `track_and_decide` step | No change in logic; delivery mechanism changes |
| Diagnostic specialist delegation | `delegate_specialist` step | No change (spawns Task outside team, unchanged) |
| Results presentation | `present_results` step | No change (reads files, agent-agnostic) |
| Escalation report | `escalate` step | No change |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TeamCreate + 4 specialized teammates | Enhanced monolithic agent (v3.5) | Monolithic = less overhead but same v3.0 constraint-loss bugs persist |
| Orchestrator-as-lead (skill manages team) | Spawning a coordinator teammate who manages others | INVALID per API: teammates cannot spawn teammates. Only session-that-called-TeamCreate can manage team. |
| Task(team_name) for all 4 specialists | Some specialists as regular Task() subagents | All 4 must be team members to use shared TaskList and SendMessage to each other |

---

## Architecture Patterns

### The Correct Architecture: Orchestrator Skill as Team Lead

The orchestrator skill runs in the user's main Claude Code session. When it calls `TeamCreate`, THAT session becomes the team lead for the lifetime of the team. The skill can then call `Task(team_name=...)` to spawn teammates.

```
User session (runs case.md skill)
    │
    ├─ TeamCreate("case-ibuprofen")          ← skill becomes team lead
    ├─ TaskCreate("peak-picking")
    ├─ TaskCreate("lsd-iteration-01")
    ├─ TaskCreate("ranking")
    │
    ├─ Task(name="nmr-chemist", team_name="case-ibuprofen")   ← spawned teammate
    ├─ Task(name="lsd-engineer", team_name="case-ibuprofen")  ← spawned teammate
    ├─ Task(name="solution-analyst", team_name="case-ibuprofen") ← spawned teammate
    └─ Task(name="devils-advocate", team_name="case-ibuprofen")  ← spawned teammate
```

**The "coordinator" role is played by the orchestrator skill itself, not a spawned agent.**

This means the v4.0 architecture has 4 spawned specialist teammates (not 5). The 5th "role" (coordinator) is the orchestrator skill.

### Spawn Sequence (Replaces current spawn_case_agent step)

```markdown
<step name="spawn_case_team">

# Step 1: Initialize team namespace
TeamCreate(
  team_name="case-{compound_name}",
  description="CASE workflow for {compound_path} — formula {formula}"
)

# Step 2: Create initial task list (iteration tasks added dynamically by lsd-engineer)
TaskCreate(
  subject="peak-picking",
  description="Pick 13C, HSQC, HMBC peaks for {compound_path} with formula {formula}.
               Run statistical detection (hybridisation, neighbours, hhb, grouping).
               Send structured peak assignments to lsd-engineer via SendMessage.",
  activeForm="Picking peaks"
)

TaskCreate(
  subject="lsd-iteration-01",
  description="Build initial LSD file from peak assignments. Use HSQC for MULT, add
               first HMBC batch (3-5 high-confidence correlations). Run LSD. Log to
               analysis/CASE-PROGRESS.md. Create lsd-iteration-02 task when done.",
  activeForm="Running LSD iteration 1"
)

# Step 3: Spawn 4 specialist teammates
Task(
  name="nmr-chemist",
  team_name="case-{compound_name}",
  subagent_type="lucy-nmr-chemist",
  model="opus",
  prompt="You are the NMR chemist for CASE of {formula} at {compound_path}.
          Claim the peak-picking task from TaskList. Execute peak picking and
          statistical detection. Send results to lsd-engineer via SendMessage."
)

Task(
  name="lsd-engineer",
  team_name="case-{compound_name}",
  subagent_type="lucy-lsd-engineer",
  model="opus",
  prompt="You are the LSD engineer for CASE of {formula} at {compound_path}.
          Wait for nmr-chemist peak assignments. Claim iteration tasks. Build
          LSD files, run LSD, log CASE-PROGRESS.md after EVERY iteration."
)

Task(
  name="solution-analyst",
  team_name="case-{compound_name}",
  subagent_type="lucy-solution-analyst",
  model="opus",
  prompt="You are the solution analyst for CASE of {formula} at {compound_path}.
          Claim ranking task when solution_count <= 10. Run lucy lsd rank.
          Write final_results.md."
)

Task(
  name="devils-advocate",
  team_name="case-{compound_name}",
  subagent_type="lucy-devils-advocate",
  model="opus",
  prompt="You are the devils advocate for CASE of {formula} at {compound_path}.
          Monitor CASE-PROGRESS.md after each iteration. Check for dropped
          constraints (DEFF NOT, SYME, grouped notation). Detect loop patterns.
          Send advisories to team lead via SendMessage when issues found."
)

# Orchestrator waits for messages from team (progress, loop flags, completion)
</step>
```

### Advisory Delivery (Replaces current respawn step)

Instead of re-spawning the agent with advisory text in the spawn prompt, the orchestrator sends a message to the surviving team:

```markdown
<step name="deliver_advisory">
# v3.0 pattern: Kill agent, re-spawn with advisory in instructions
# v4.0 pattern: Send advisory to running team via SendMessage

SendMessage(
  type="message",
  recipient="lsd-engineer",
  content="[SUPERVISOR ADVISORY] {advisory_text_from_intervene_step}",
  summary="Supervisor advisory: {pattern_name} detected"
)

# Also notify devils-advocate so it monitors the fix
SendMessage(
  type="message",
  recipient="devils-advocate",
  content="[SUPERVISOR] {pattern_name} detected. Advisory sent to lsd-engineer.
           Monitor next iteration for resolution. Verify fix applied correctly.",
  summary="Loop pattern flagged, monitor fix"
)
</step>
```

### Team Lifecycle Management (New step)

```markdown
<step name="terminate_team">
# Send shutdown requests to all teammates
SendMessage(type="shutdown_request", recipient="nmr-chemist",
            content="CASE workflow complete. Shut down.")
SendMessage(type="shutdown_request", recipient="lsd-engineer",
            content="CASE workflow complete. Shut down.")
SendMessage(type="shutdown_request", recipient="solution-analyst",
            content="CASE workflow complete. Shut down.")
SendMessage(type="shutdown_request", recipient="devils-advocate",
            content="CASE workflow complete. Shut down.")

# Wait for shutdown confirmations
# Then clean up team resources
TeamDelete()
</step>
```

### Recommended Project Structure (New agent files for Phase 42)

Phase 41 only modifies case.md. Agent definitions are Phase 42. But Phase 41 must reference agent types that Phase 42 will create:

```
~/.claude/agents/
├── lucy-diagnostic.md          (unchanged from v3.0)
├── lucy-nmr-chemist.md         (Phase 42 creates)
├── lucy-lsd-engineer.md        (Phase 42 creates)
├── lucy-solution-analyst.md    (Phase 42 creates)
└── lucy-devils-advocate.md     (Phase 42 creates)
```

Note: Prior research (ARCHITECTURE.md) proposed `~/.claude/agents/lucy-ng/case-team/` subdirectory. This needs validation — Claude Code may not discover agents in subdirectories. Phase 41 research notes this as an open question (see Open Questions section).

### Anti-Patterns to Avoid

- **Spawning a coordinator agent to manage others:** INVALID. Only the session that called TeamCreate can spawn teammates or call TeamDelete. A "coordinator" agent has no special team management powers.
- **Using broadcast for routine updates:** Expensive — costs scale with team size. Use direct `SendMessage` to specific recipient.
- **Calling TeamDelete before all teammates shut down:** TeamDelete fails if teammates still active. Always send shutdown_request first, wait for confirmations.
- **Using plan_approval_request gates in CASE iterations:** Adds round-trip delay. CASE iterations are exploratory — rapid cycle time matters. Devils-advocate reviews post-facto instead.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Task claiming race conditions | Custom file locking | TeamCreate task system | Built-in file locking prevents two agents claiming same task |
| Agent discovery | Hardcoded agent IDs | Read `~/.claude/teams/{team}/config.json` | Team config contains all members with their names |
| Message delivery | Custom inbox polling | SendMessage | Automatic delivery — recipients don't poll |
| Dependency resolution | Custom dependency checker | TaskCreate with addBlockedBy | System automatically unblocks dependent tasks when deps complete |

**Key insight:** All state is on disk. `~/.claude/teams/{team}/config.json` has member list. `~/.claude/tasks/{team}/` has task state. No in-memory coordination required.

---

## Common Pitfalls

### Pitfall 1: Spawning a Coordinator Teammate (API Misunderstanding)

**What goes wrong:** Prior research STACK.md/ARCHITECTURE.md describes spawning a "coordinator" agent as team lead. Developer implements this, coordinator then tries to spawn specialists — fails silently.

**Why it happens:** Prior research was written before official API clarification. The docs say "teammates cannot spawn their own teams or teammates. Only the lead can manage the team."

**How to avoid:** The orchestrator SKILL is the team lead. Skill calls TeamCreate, skill spawns all 4 specialists via Task(team_name=...), skill manages task list.

**Warning signs:** If you see a "coordinator" teammate in the Task spawn sequence, something is wrong. The 4 specialists are: nmr-chemist, lsd-engineer, solution-analyst, devils-advocate.

**Confidence:** HIGH (verified against official docs: "No nested teams: teammates cannot spawn their own teams or teammates")

---

### Pitfall 2: Advisory Delivery to Non-Existent Re-Spawned Agent

**What goes wrong:** v3.0 orchestrator delivers advisory by re-spawning agent with advisory text in instructions. In v4.0, the team is still running. Re-spawning creates a 5th agent outside the team that has no access to team state.

**Why it happens:** v3.0 muscle memory. The `respawn` step literally says "Re-spawn the CASE agent with advisory constraints." That pattern is invalid with a running team.

**How to avoid:** Replace the `respawn` step entirely. Use SendMessage to deliver advisory to the running lsd-engineer and devils-advocate. Team continues from current state without restart.

**Warning signs:** `Task()` call without `team_name` inside the advisory delivery step — that spawns an isolated subagent, not a team advisory.

**Confidence:** HIGH (architectural consequence of team lifecycle)

---

### Pitfall 3: TeamDelete Before Teammates Shut Down

**What goes wrong:** Orchestrator calls TeamDelete while teammates still running. TeamDelete fails, leaving orphaned team resources.

**Why it happens:** Official docs warn: "Clean up the team — it checks for active teammates and fails if any are still running."

**How to avoid:** Always send shutdown_request to all teammates first. Wait for shutdown_response confirmations (or timeout). Then call TeamDelete.

**Warning signs:** TeamDelete returns error. Check `~/.claude/teams/{team}/config.json` for still-active members.

**Confidence:** HIGH (explicit warning in official docs)

---

### Pitfall 4: Agent Teams Feature Not Enabled

**What goes wrong:** TeamCreate tool not available because `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is not set. Orchestrator skill fails at first TeamCreate call.

**Why it happens:** Feature is experimental and disabled by default. Orchestrator must check environment before attempting to spawn team.

**How to avoid:** Add environment check to validate_prerequisites step. If env var not set, provide setup instructions and stop.

**Warning signs:** TeamCreate tool not in tool list, or error at TeamCreate call saying feature not enabled.

**Check to add:**
```bash
# In validate_prerequisites step
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
# If not "1": "Run: export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
```

**Confidence:** HIGH (documented in official Claude Code docs)

---

### Pitfall 5: Loop Detection Parsing Fails with Multi-Agent CASE-PROGRESS.md

**What goes wrong:** Loop detection step parses single-agent CASE-PROGRESS.md format (each entry = one agent's narrative). With multi-agent team, each iteration has multiple agent contributions in different sections. Parser fails to extract solution counts or constraint lists.

**Why it happens:** CASE-PROGRESS.md format changes in v4.0 (Phase 44 defines the new format). Phase 41 orchestrator must handle the new format.

**How to avoid:** Phase 41 loop detection parser must be designed for multi-agent format, OR Phase 41 assumes legacy format and Phase 44 updates both CASE-PROGRESS.md format AND the parser. Dependency chain: define format (44) → update parser (44 or 41). Plan accordingly.

**Warning signs:** Loop detection reports "no iterations found" or incorrect solution counts despite agent running.

**Confidence:** HIGH (dependency between Phase 41 and Phase 44 is real)

---

### Pitfall 6: Agent Definitions Don't Exist When Team Spawned

**What goes wrong:** Phase 41 modifies case.md to spawn `lucy-nmr-chemist`, `lucy-lsd-engineer`, etc. But those agent definition files don't exist until Phase 42. Team spawn fails for all 4 specialists.

**Why it happens:** Phase 41 (orchestrator) and Phase 42 (agent definitions) are separate phases in dependency order: orchestrator first, then agents.

**How to avoid:** Phase 41 must include early validation that uses TEMPORARY or STUB agent definitions, not the final Phase 42 agents. Success criterion 6 says "Early TeamCreate API validation" — this means Phase 41 tests with stub agents. Final integration happens after Phase 42.

**Warning signs:** Task() calls with `subagent_type` referencing non-existent agent definitions fail silently or use generic agent.

**Confidence:** HIGH (explicit in phase description: "Early TeamCreate API validation — confirm 5-agent team spawns and communicates successfully")

---

## Code Examples

Verified patterns from official sources:

### TeamCreate (Team Initialization)
```
# Source: code.claude.com/docs/en/agent-teams (official)
TeamCreate({
  team_name: "case-ibuprofen",
  description: "CASE workflow for data/Ibuprofen — formula C13H18O2"
})
# Creates: ~/.claude/teams/case-ibuprofen/config.json
#          ~/.claude/tasks/case-ibuprofen/
```

### Task with team_name (Spawn Teammate)
```
# Source: alexop.dev (verified against official docs pattern)
Task({
  description: "NMR peak picking for CASE workflow",
  subagent_type: "lucy-nmr-chemist",
  name: "nmr-chemist",
  team_name: "case-ibuprofen",
  model: "opus",
  prompt: "You are the NMR chemist. Claim peak-picking task from TaskList..."
})
```

### TaskCreate (Create Shared Work Item)
```
# Source: alexop.dev (verified against official docs pattern)
TaskCreate({
  subject: "lsd-iteration-02",
  description: "Run LSD iteration 2. Read iteration 1 LSD file. Add next HMBC batch (correlations 6-10). Write to analysis/iteration_02/compound.lsd. Log to CASE-PROGRESS.md.",
  activeForm: "Running LSD iteration 2"
})
```

### SendMessage (Direct Advisory Delivery)
```
# Source: alexop.dev (verified against official docs SendMessage spec)
SendMessage({
  type: "message",
  recipient: "lsd-engineer",
  content: "[SUPERVISOR ADVISORY] ELIM thrashing detected. Before retrying: verify sp2 count is even (current: N). Verify hydrogen budget matches formula...",
  summary: "ELIM thrashing advisory"
})
```

### TaskList (Monitor Progress)
```
# Source: official docs (task list state)
TaskList()
# Returns: [{id: "1", subject: "peak-picking", status: "completed", owner: "nmr-chemist"},
#            {id: "2", subject: "lsd-iteration-01", status: "in_progress", owner: "lsd-engineer"},
#            {id: "3", subject: "lsd-iteration-02", status: "pending", owner: ""}]
```

### TeamDelete (Cleanup)
```
# Source: official docs
# MUST call SendMessage(shutdown_request) to all teammates first
# Then:
TeamDelete()
# Removes: ~/.claude/teams/case-ibuprofen/
#           ~/.claude/tasks/case-ibuprofen/
```

---

## State of the Art

| Old Approach (v3.0) | New Approach (v4.0) | When Changed | Impact |
|---------------------|---------------------|--------------|--------|
| `Task(agent_type="lucy-case-agent")` | `TeamCreate() + Task(team_name="case-X", name="specialist")` × 4 | Feb 5, 2026 (Opus 4.6) | Enables inter-agent peer review, real-time loop detection |
| Re-spawn agent with advisory | `SendMessage(advisory)` to running team | Phase 41 | No restart overhead; team retains context and state |
| Orchestrator loops after Task returns | Orchestrator monitors TaskList + receives messages | Phase 41 | Continuous monitoring, not batch wait-and-check |
| Loop detection after 3-5 wasted iterations | Devils-advocate detects in real-time per iteration | Phase 41+42 | Earlier intervention, fewer wasted LSD runs |

**Deprecated/outdated:**
- `Task(agent_type="lucy-case-agent")` alone (without team_name): works but spawns isolated subagent, no team coordination
- Re-spawn pattern in `respawn` step: replaced by SendMessage to running team

---

## Open Questions

1. **Do agent definitions in subdirectories work?**
   - What we know: Prior research (ARCHITECTURE.md) proposes `~/.claude/agents/lucy-ng/case-team/` subdirectory for team agents
   - What's unclear: Whether Claude Code discovers agent definitions in subdirectories, or only flat `~/.claude/agents/`
   - Recommendation: Phase 41 stub validation should test both flat names (`lucy-nmr-chemist`) and subdirectory names (`lucy-ng/case-team/nmr-chemist`) to confirm. If subdirectories don't work, use flat names with `lucy-` prefix.
   - Confidence: LOW — not explicitly documented in official docs

2. **How does orchestrator receive messages from team while managing other steps?**
   - What we know: "Messages from teammates are automatically delivered to you" (official docs) — delivered as new conversation turns
   - What's unclear: In a skill context, how does the orchestrator handle interleaved team messages while also performing loop detection and monitoring? Does the skill pause and wait for team messages, or does it actively poll TaskList?
   - Recommendation: Design orchestrator to poll TaskList for task completion (active monitoring) rather than waiting for messages (passive). Messages from devils-advocate arrive asynchronously and trigger intervention flow when received.
   - Confidence: MEDIUM — message delivery mechanics documented, skill integration not explicitly covered

3. **Can the orchestrator use TeamCreate/SendMessage/TeamDelete in a skill context?**
   - What we know: These tools are available to the current session (they are listed in available tools). The skill runs in the main session.
   - What's unclear: Are there any restrictions on using Agent Teams tools from within a slash command skill vs. from interactive use?
   - Recommendation: Phase 41 early validation should test a minimal TeamCreate + Task(team_name) + TeamDelete in skill context before full implementation.
   - Confidence: MEDIUM — no documented restrictions, but skill context not explicitly tested

4. **Does the `respawn` step structure need to be preserved or can it be fully replaced?**
   - What we know: v3.0 `respawn` step re-spawns the agent with advisory text. v4.0 replaces re-spawn with SendMessage.
   - What's unclear: Should the step be renamed `deliver_advisory` or kept as `respawn` with different content? What happens to per-pattern counter logic in `track_and_decide`?
   - Recommendation: Rename step to `deliver_advisory` for clarity. Per-pattern counter logic unchanged — counter still increments per delivery, escalate logic unchanged. Only the delivery mechanism changes.
   - Confidence: HIGH — architectural consequence is clear, naming is convention choice

---

## Sources

### Primary (HIGH confidence)
- Official Claude Code Agent Teams docs: https://code.claude.com/docs/en/agent-teams — TeamCreate, Task(team_name), SendMessage, TaskCreate/TaskList/TaskUpdate, TeamDelete, team lifecycle, limitations (no nested teams, no session resumption, one team per session)
- alexop.dev tutorial (verified against official docs): https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/ — TeamCreate parameters, Task with team_name/name, complete spawn sequence example
- Existing case.md at `~/.claude/commands/lucy-ng/case.md` — v3.0 orchestrator structure, steps to preserve, steps to replace
- Prior research STACK.md at `.planning/research/STACK.md` — API parameters, message types, task schema, configuration options (HIGH confidence sections verified against official docs)
- Prior research ARCHITECTURE.md at `.planning/research/ARCHITECTURE.md` — agent interaction patterns, knowledge distribution, integration points

### Secondary (MEDIUM confidence)
- Prior research SUMMARY-v4.0.md at `.planning/research/SUMMARY-v4.0.md` — phase ordering rationale, pitfall analysis

### Tertiary (LOW confidence)
- GitHub gist (kieranklaassen): https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea — alternative API description using "Teammate" tool operation pattern; may be outdated or community-specific variation

---

## Metadata

**Confidence breakdown:**
- Agent Teams API (TeamCreate, Task(team_name), SendMessage, TeamDelete): HIGH — verified against official docs 2026-02-17
- Who is the team lead (skill vs coordinator agent): HIGH — official docs explicit: "teammates cannot spawn teammates, only lead can manage team"
- Spawn sequence and step replacement: HIGH — direct architectural consequence of API constraints
- Advisory delivery via SendMessage: HIGH — direct consequence of team lifecycle (don't re-spawn)
- Agent definition subdirectory support: LOW — not documented, needs empirical validation in Phase 41
- Skill context compatibility with Agent Teams tools: MEDIUM — not explicitly documented, needs early validation test

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable API, but experimental feature — check for updates)

---

## Phase 41 Implementation Scope Summary

**What Phase 41 DOES modify in case.md:**

| Step | v3.0 | v4.0 | Change Type |
|------|------|------|-------------|
| `validate_prerequisites` | Check lucy, LSD, database, directory | + Check CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 | Addition |
| `spawn_case_agent` | Task(lucy-case-agent) | TeamCreate + TaskCreate(tasks) + Task(team_name) × 4 | Full rewrite |
| `monitor_progress` | Read CASE-PROGRESS.md after Task returns | Poll TaskList + read CASE-PROGRESS.md continuously | Rewrite |
| `respawn` → `deliver_advisory` | Task(lucy-case-agent with advisory) | SendMessage(advisory) to lsd-engineer + devils-advocate | Full rewrite |
| New: `terminate_team` | (didn't exist) | SendMessage(shutdown_request) × 4 + TeamDelete() | New step |

**What Phase 41 does NOT change:**
- `parse_arguments` step — unchanged
- `detect_loops` step — unchanged logic; format adaptation deferred to Phase 44
- `diagnose` step — unchanged (reads files, agent-agnostic)
- `intervene` step — unchanged (advisory text content preserved)
- `track_and_decide` step — unchanged (per-pattern counters preserved)
- `escalate` step — unchanged
- `delegate_specialist` step — unchanged (diagnostic specialist spawned outside team)
- `extract_diagnostic_findings` step — unchanged
- `present_results` step — unchanged (reads files, agent-agnostic)

**Phase 41 stub agent requirement:**

Success criterion 6 requires early validation before Phase 42 agent definitions exist. Phase 41 must include TEMPORARY stub agent definitions for `lucy-nmr-chemist`, `lucy-lsd-engineer`, `lucy-solution-analyst`, `lucy-devils-advocate` that are minimal (just enough to confirm team spawning and messaging works). These stubs are replaced by full definitions in Phase 42.
