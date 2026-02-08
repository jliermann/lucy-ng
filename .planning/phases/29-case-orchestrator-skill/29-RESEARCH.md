# Phase 29: CASE Orchestrator Skill - Research

**Researched:** 2026-02-08
**Domain:** Multi-agent orchestration via Claude Code sub-commands
**Confidence:** HIGH

## Summary

Phase 29 implements the CASE orchestrator skill as a sub-command at `~/.claude/commands/lucy-ng/case.md`. This orchestrator spawns the autonomous CASE agent (from Phase 28) via the Task tool, monitors progress through CASE-PROGRESS.md, detects 4 unproductive loop patterns, diagnoses root causes, and intervenes with advisory constraints. The orchestrator tracks intervention failures per pattern and escalates to the user after 10 cycles per pattern.

The architecture follows Claude Code's sub-command skill pattern with Task tool spawning for agent orchestration. The orchestrator never performs CASE work itself—it delegates to the autonomous agent and handles supervision.

**Primary recommendation:** Follow the GSD sub-command skill pattern (status.md, dereplicate.md) with Task tool spawning documented in the Phase 28 agent definition. Use CASE-PROGRESS.md as the monitoring interface. Implement loop detection as pattern-matching on iteration history. Keep intervention logic advisory (WHAT not HOW). Phase 32 validates the spawning mechanism works.

## Standard Stack

The established tools for this domain:

### Core
| Tool/Pattern | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Task tool | Claude Code 2.1+ | Spawn subagents with custom context | Official Claude Code agent orchestration mechanism |
| Sub-command skills | ~/.claude/commands pattern | Define slash commands that spawn agents | GSD-validated pattern for lucy-ng v2.1 |
| CASE-PROGRESS.md | append-only markdown | Communication interface between agent and orchestrator | Defined in Phase 28, enables supervisor monitoring |
| skill/supervisor/SKILL.md | existing file | Loop detection patterns and diagnostic procedures | Existing v2.0 supervisor logic being dissolved into orchestrator |

### Supporting
| Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Bash | system | Run lucy CLI commands for initial checks | Prerequisite validation before spawning agent |
| Read | built-in | Parse CASE-PROGRESS.md for loop detection | After each agent iteration batch |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Task tool | Agent teams | Task tool is correct for this use case—single orchestrator spawning one agent iteratively; teams are for parallel workers |
| Advisory intervention | Directive commands | Advisory preserves agent autonomy (WHAT not HOW), directive violates Phase 28 design |
| Per-pattern counters | Global counter | Per-pattern tracking identifies which specific failure mode is recurring; global counter masks root causes |

**Installation:**
No external dependencies. Uses Claude Code built-in Task tool and file-based agent definitions from Phase 28.

## Architecture Patterns

### Recommended Orchestrator Structure

The case.md skill follows this structure (based on existing sub-command skills + Task spawning pattern):

```
~/.claude/commands/lucy-ng/case.md
├── YAML frontmatter (name, description, allowed-tools)
├── <objective> - What the orchestrator does
├── <process>
│   ├── <step name="parse_arguments"> - Extract compound path, formula
│   ├── <step name="spawn_case_agent"> - Invoke Task tool with agent context
│   ├── <step name="monitor_progress"> - Read CASE-PROGRESS.md
│   ├── <step name="detect_loops"> - Pattern matching on iteration history
│   ├── <step name="diagnose"> - Basic checks (sp2, H budget, 1J artifacts)
│   ├── <step name="intervene"> - Generate advisory constraints
│   ├── <step name="escalate"> - After 10 cycles per pattern
│   └── <step name="present_results"> - Show final structures and confidence
└── Supporting sections (loop patterns, diagnostic procedures)
```

### Pattern 1: Task Tool Spawning with Hybrid Context Inlining

**What:** Spawn CASE agent via Task tool with critical content inlined in instructions, detailed references via file paths.

**When to use:** When orchestrator needs to delegate multi-iteration autonomous work to a spawned agent.

**Example from Phase 28 agent definition:**
```markdown
Task(
  agent_type="lucy-case-agent",
  instructions="Perform CASE workflow for compound at <path> with formula <formula>.

  Write CASE-PROGRESS.md after EVERY LSD iteration with all required fields.

  Follow incremental HMBC strategy: add 3-5 high-confidence correlations per iteration.

  Stop when solution count ≤ 10 or after ~10 iterations.

  For full domain knowledge, see:
  - /Users/steinbeck/Dropbox/develop/lucy-ng/skill/SKILL.md
  - /Users/steinbeck/Dropbox/develop/lucy-ng/skill/CASE/SKILL.md

  [Inline critical workflow content: ~500-700 lines from agent definition]
  "
)
```

**Key points:**
- Agent has 500-700 lines of inlined critical knowledge (from Phase 28)
- Orchestrator adds task-specific instructions (compound path, formula)
- File path references point to comprehensive skill files for deeper detail
- Agent runs autonomously, writes CASE-PROGRESS.md, returns when complete or stuck

**Source:** Phase 28 agent definition at ~/.claude/agents/lucy-case-agent.md (created in 28-01-PLAN.md)

### Pattern 2: Append-Only Progress Monitoring

**What:** Agent writes CASE-PROGRESS.md after every LSD iteration; orchestrator reads it to detect loops.

**When to use:** When autonomous agent performs multi-iteration work and supervisor needs to detect unproductive patterns.

**Example CASE-PROGRESS.md structure (from Phase 28):**
```markdown
# CASE Progress Log

**Compound:** data/compound/virgiline
**Formula:** C16H21NO2
**Started:** 2026-02-07 14:32:15
**CASE Agent:** general-purpose

---

## Iteration 1: Baseline (MULT + HSQC only)

**Time:** 14:32:45
**LSD file:** virgiline-01.lsd
**Solution count:** 1,234

**Constraints added:** None (baseline run)
**Constraints removed:** None

**Why:** Establish unconstrained baseline before adding HMBC correlations.

**Constraint effectiveness:** N/A (baseline)
**Confidence:** Too many solutions (under-constrained)
**HMBC correlations used:** 0/43

**Notes:**
- sp2 atom count: 8 (even) ✓
- Hydrogen budget: 21 H (matches formula) ✓
- All protonated carbons have HSQC ✓

---

## Iteration 2: Add high-confidence HMBC batch 1
[...continues with same structure...]
```

**Orchestrator reads this to:**
- Extract solution count trends
- Detect loop patterns (Section 4 of skill/supervisor/SKILL.md)
- Check diagnostic fields (sp2 count, H budget)
- Generate intervention advisories

**Source:** skill/supervisor/SKILL.md Section 8 (CASE-PROGRESS.md Format Specification)

### Pattern 3: Loop Detection via Pattern Matching

**What:** Read recent iterations from CASE-PROGRESS.md and match against 4 loop patterns.

**When to use:** After each agent batch completes, before re-spawning.

**4 Loop Patterns (from skill/supervisor/SKILL.md Section 4):**

**ELIM Thrashing:**
- Detection: "ELIM" appears in constraints added 2+ times across iterations
- Diagnosis: Check sp2 count even, H budget matches, 1J artifacts
- Advisory: "Do NOT add ELIM again until all checks pass"

**Zero-Solution Loop:**
- Detection: 3+ consecutive iterations with solution_count = 0
- Diagnosis: Remove last batch, test correlations individually, check for conflicts
- Advisory: "Only re-add correlations after resolving the conflict"

**Solution Explosion:**
- Detection: 3+ iterations with solution_count > 100 and < 10% reduction each
- Diagnosis: Check if ELIM present, verify correlations connect new fragments, check heteroatom constraints
- Advisory: "Focus on high-leverage constraints that separate structural classes"

**Constraint Churning:**
- Detection: 5+ recent iterations, >10 constraints added AND >5 removed, solution_count still > 50
- Diagnosis: Check if systematic strategy followed, verify correlations selected by criteria not randomly
- Advisory: "Reset to last known-good state, follow incremental HMBC strategy"

**Implementation:**
```python
# Pseudocode for loop detection
def detect_loops(iterations):
    recent = iterations[-5:]  # Last 5 iterations

    # ELIM thrashing
    elim_count = sum(1 for it in iterations if "ELIM" in it.constraints_added)
    if elim_count >= 2:
        return "ELIM_THRASHING"

    # Zero-solution loop
    if all(it.solution_count == 0 for it in recent[-3:]):
        return "ZERO_SOLUTION_LOOP"

    # Solution explosion
    if all(it.solution_count > 100 for it in recent[-3:]):
        reductions = [(recent[i-1].solution_count - recent[i].solution_count) / recent[i-1].solution_count
                      for i in range(1, len(recent[-3:]))]
        if all(r < 0.10 for r in reductions):
            return "SOLUTION_EXPLOSION"

    # Constraint churning
    if len(recent) >= 5:
        adds = sum(len(it.constraints_added) for it in recent)
        removes = sum(len(it.constraints_removed) for it in recent)
        if adds > 10 and removes > 5 and recent[-1].solution_count > 50:
            return "CONSTRAINT_CHURNING"

    return None
```

**Source:** skill/supervisor/SKILL.md Section 4 (Loop Detection Patterns)

### Pattern 4: Advisory Intervention (WHAT not HOW)

**What:** When loop detected, tell agent WHAT to fix, not HOW to fix it.

**When to use:** After diagnosis identifies root cause.

**Advisory examples (from skill/supervisor/SKILL.md):**

**For ELIM thrashing:**
```
ELIM thrashing detected. Before retrying:
1. Verify sp2 count is even (see skill/SKILL.md Section 5.3)
2. Verify hydrogen budget matches formula
3. Check last batch of HMBC correlations for 1J artifacts
   (compare against HSQC positions)

Do NOT add ELIM again until all three checks pass.
```

**Contrast with DIRECTIVE (incorrect):**
```
Change line 15 of compound.lsd from `MULT 5 C 2 1` to `MULT 5 C 3 1`
```

**Why advisory is correct:**
- Agent from Phase 28 retains autonomy to decide HOW to implement the fix
- Agent has full domain knowledge (inlined + file references) to make correct decisions
- Directive intervention makes orchestrator brittle (assumes specific file structure)

**Source:** skill/supervisor/SKILL.md Section 3 (Advisory Intervention Model)

### Pattern 5: Per-Pattern Intervention Tracking

**What:** Track intervention count separately for each of the 4 loop patterns.

**When to use:** Always when tracking intervention failures.

**Why per-pattern not global:**
- Different patterns have different root causes
- Global counter masks which specific failure mode is recurring
- Escalation after 10 cycles means "this pattern failed 10 times" not "10 generic failures"

**Implementation:**
```python
intervention_counts = {
    "ELIM_THRASHING": 0,
    "ZERO_SOLUTION_LOOP": 0,
    "SOLUTION_EXPLOSION": 0,
    "CONSTRAINT_CHURNING": 0
}

def handle_loop(pattern):
    intervention_counts[pattern] += 1

    if intervention_counts[pattern] >= 10:
        escalate_to_user(pattern, intervention_counts[pattern])
    else:
        advise_and_respawn(pattern)
```

**Source:** skill/supervisor/SKILL.md Section 7 (Intervention Tracking and Escalation)

### Pattern 6: Diagnostic Specialist Delegation (Future)

**What:** After 2 failed basic interventions with SAME pattern, delegate to diagnostic specialist for deep analysis.

**When to use:** When basic supervisor diagnosis (sp2 check, H budget, 1J artifacts) does not resolve the issue.

**Note:** Phase 29 implements basic diagnosis only. Phase 30 implements diagnostic specialist agent. Phase 29 should prepare for delegation but not implement it.

**Interface (for Phase 30):**
```markdown
Task(
  agent_type="diagnostic-specialist",
  instructions="Analyze LSD failure for compound at <compound_path>.

  Read:
  - <compound_path>/CASE-PROGRESS.md (iteration history)
  - <compound_path>/<filename>.lsd (latest LSD file)

  Failure type: <0 solutions | 1000+ solutions>

  Run systematic diagnostic checks per skill/diagnostic/SKILL.md.
  Document ALL checks (PASS and FAIL).
  Identify root cause with evidence.

  Write structured report to <compound_path>/DIAGNOSTIC-REPORT.md.
  Include: findings, root cause, recommended fixes with LSD command examples.
  Rate all findings and recommendations as HIGH/MEDIUM/LOW confidence.
  "
)
```

**Source:** skill/supervisor/SKILL.md Section 5 (Diagnostic Specialist Delegation)

### Anti-Patterns to Avoid

- **Dereplication in orchestrator:** CASE-only skill, never attempts dereplication (absolute separation from Phase 27)
- **Directive intervention:** Prescribing specific LSD file edits (violates Phase 28 agent autonomy)
- **Global intervention counter:** Masks which specific pattern is recurring
- **Over-inlining in Task instructions:** Agent already has 500-700 lines inlined, orchestrator should NOT duplicate that content
- **Synchronous iteration monitoring:** Spawning agent for every single iteration is inefficient; spawn for batch, read progress after batch completes

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent spawning | Custom subprocess/API calls | Task tool | Task tool handles context forking, model inheritance, tool access, permissions automatically |
| Progress monitoring format | JSON or custom binary | Markdown with structured sections | Human-readable for user debugging, AI-parseable, append-only simplifies implementation |
| Loop detection | Statistical anomaly detection | Pattern matching on known failure modes | 4 patterns are well-understood from v2.0 supervisor, ML overkill |
| Intervention counters | Session-persistent database | In-memory dictionary reset per session | CASE sessions are single-run (not multi-session), persistence adds complexity |

**Key insight:** Claude Code's Task tool was designed for exactly this use case (hierarchical supervisor spawning autonomous agent). Using custom spawning mechanisms loses Claude Code's context management, tool access control, and permission delegation. The built-in tools are production-ready.

## Common Pitfalls

### Pitfall 1: Over-Inlining Context in Task Instructions

**What goes wrong:** Orchestrator duplicates all 500-700 lines of agent's inlined content in Task instructions, causing context bloat.

**Why it happens:** Misunderstanding of Phase 28 hybrid context inlining—agent ALREADY has the content, orchestrator should NOT repeat it.

**How to avoid:**
- Agent definition (Phase 28) has inlined content
- Task instructions should add ONLY task-specific details (compound path, formula, advisory constraints)
- File path references are sufficient for deeper detail

**Warning signs:** Task instructions exceed 200 lines, or include tables/examples that are already in agent definition.

### Pitfall 2: Directive Intervention (Not Advisory)

**What goes wrong:** Orchestrator prescribes exact LSD file edits: "Change line 15 from X to Y"

**Why it happens:** Natural for humans to give specific instructions, but violates Phase 28 agent autonomy design.

**How to avoid:**
- Tell agent WHAT to fix (e.g., "sp2 count is odd")
- Let agent decide HOW to fix it (re-examine DEPT, adjust MULT definitions)
- Agent has full domain knowledge to make correct decisions

**Warning signs:** Advisory contains LSD commands, line numbers, or specific file edits.

### Pitfall 3: Synchronous Per-Iteration Spawning

**What goes wrong:** Orchestrator spawns agent for EVERY single LSD iteration, causing excessive Task calls.

**Why it happens:** Misunderstanding of agent autonomy—agent runs MULTIPLE iterations autonomously before returning.

**How to avoid:**
- Spawn agent ONCE with instructions to iterate until convergence or ~10 iterations
- Agent writes CASE-PROGRESS.md after each iteration (within its own execution)
- Orchestrator reads progress AFTER agent returns (batch monitoring, not synchronous)
- Re-spawn ONLY if loop detected and intervention needed

**Warning signs:** More than 3 Task calls per CASE session, or Task call inside iteration loop.

### Pitfall 4: Global Intervention Counter

**What goes wrong:** Single counter tracks all intervention failures, masking which specific pattern is recurring.

**Why it happens:** Simpler to implement one counter than four.

**How to avoid:**
- Track counts per pattern: `{ELIM_THRASHING: 2, ZERO_SOLUTION_LOOP: 0, ...}`
- Escalate when SPECIFIC pattern hits 10 cycles
- Different patterns have different root causes, global counter loses diagnostic value

**Warning signs:** Escalation message does not identify which pattern failed, or says "10 interventions" without specifying pattern.

## Code Examples

Verified patterns from official sources and Phase 28:

### Task Tool Spawning (from Phase 28 and Claude Code docs)

```markdown
<step name="spawn_case_agent">
Use the Task tool to spawn the lucy-case-agent:

Task(
  agent_type="lucy-case-agent",
  instructions="Perform CASE workflow for compound at <compound_path> with formula <formula>.

  [Task-specific instructions only—agent has inlined knowledge]

  Write CASE-PROGRESS.md after EVERY LSD iteration.
  Follow incremental HMBC strategy.
  Stop when solution_count ≤ 10 or after ~10 iterations.
  "
)

Wait for agent to complete or return for intervention.
</step>
```

**Source:** Phase 28 agent definition + Claude Code sub-agents documentation

### Reading CASE-PROGRESS.md for Loop Detection

```markdown
<step name="monitor_progress">
After agent completes, read CASE-PROGRESS.md:

```bash
cat <compound_path>/CASE-PROGRESS.md
```

Parse iteration history:
- Extract solution counts for each iteration
- Extract constraints added/removed
- Extract sp2 checks and H budget from Notes
- Count HMBC correlations used

Check for 4 loop patterns (Section 4).
</step>
```

**Source:** skill/supervisor/SKILL.md Section 3

### Basic Diagnosis (from skill/supervisor/SKILL.md)

```markdown
<step name="diagnose">
For detected loop pattern, perform basic diagnosis:

**For ELIM thrashing:**
1. Parse all MULT commands from latest LSD file
2. Count atoms with hybridization = 2 (sp2)
3. If count is odd → root cause found
4. Sum all H-counts from MULT commands
5. Compare to molecular formula
6. If mismatch → root cause found

**For zero-solution loop:**
1. Read last 2 iterations from CASE-PROGRESS.md
2. Identify which constraints were added when solutions went to 0
3. Check if any HMBC correlations match HSQC positions (1J artifacts)
4. Check if carbons in that batch are within 3 ppm (ambiguous)

**For solution explosion:**
1. Check if ELIM command is present in LSD file
2. If yes → advisory: remove ELIM
3. Check if heteroatom constraints (BOND, LIST, PROP) are present
4. If no → advisory: add heteroatom constraints

**For constraint churning:**
1. Review last 5 iterations
2. Check if correlations selected by criteria (isolated carbons, unique protons)
3. If random → advisory: reset to known-good state, follow systematic strategy
</step>
```

**Source:** skill/supervisor/SKILL.md Section 4 (Loop Detection Patterns)

### Advisory Generation

```markdown
<step name="intervene">
Based on diagnosis, generate advisory constraint for agent.

Format: WHAT to fix (not HOW).

Example for ELIM thrashing with odd sp2 count:

"ELIM thrashing detected. Root cause: sp2 atom count is 9 (odd).

Before retrying:
1. Re-examine DEPT-135 spectrum to verify sp2 assignments
2. Check if carbonyl oxygen is sp2 (should be) or sp3 (incorrect)
3. Adjust one MULT definition to make total sp2 count even

Reference: skill/SKILL.md Section 5.3 (Hybridization Rules)

Do NOT add ELIM again until sp2 count is even."

Re-spawn agent with this advisory in Task instructions.
</step>
```

**Source:** skill/supervisor/SKILL.md Section 4.1 (ELIM Thrashing advisory template)

### Escalation After 10 Cycles

```markdown
<step name="escalate">
If intervention count for THIS PATTERN reaches 10:

Present escalation report to user:

```markdown
## CASE Escalation Required

**Compound:** <compound_path>
**Formula:** <formula>
**Pattern:** <pattern_name>
**Intervention attempts:** 10

### What Was Detected

<Description of the loop pattern>

### Diagnostics Attempted

1. <First diagnostic approach>
2. <Second diagnostic approach>
...

### Current State

- Solution count: <count>
- HMBC correlations used: X/Y
- Iterations completed: N

### Supervisor Recommendation

<What the supervisor recommends the user investigate>

Examples:
- "Molecular formula may be incorrect—verify HRMS data"
- "HMBC spectrum quality is insufficient for automated elucidation—consider re-acquisition"
- "Structure may have unusual features (e.g., long-range ⁴J correlations) not handled by standard strategy"
```

Do NOT continue automated intervention—user must investigate.
</step>
```

**Source:** skill/supervisor/SKILL.md Section 7 (Escalation After 10 Cycles)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic /lucy-ng skill | Sub-command skills at ~/.claude/commands/lucy-ng/*.md | Phase 27 (v2.1) | Clean separation of concerns, routing page pattern |
| v2.0 supervisor.md agent (project-level) | Supervisor logic dissolved into case.md orchestrator skill | Phase 29 (v2.1) | No separate supervisor agent, orchestrator is a skill that spawns CASE agent |
| Global intervention counter | Per-pattern intervention counters | Phase 29 (v2.1) | Identifies which specific failure mode is recurring |
| Directive intervention | Advisory intervention (WHAT not HOW) | Phase 28-29 (v2.1) | Preserves agent autonomy, follows Option A supervision model |
| Paper-only agents (v2.0) | Validation-first development with Task tool | Phase 28-32 (v2.1) | Proves agents actually work, not just defined |

**Deprecated/outdated:**
- `.claude/agents/supervisor.md` (v2.0 project-level supervisor) — being dissolved into case.md orchestrator skill in Phase 29
- Synchronous iteration monitoring — Phase 29 uses batch monitoring (spawn once, iterate autonomously, read progress after batch)
- MCP server architecture (Phase 26 removed) — CLI-only architecture with thin Bash commands

## Open Questions

Things that couldn't be fully resolved:

1. **Task tool model parameter bug (#18873)**
   - What we know: Task tool has a bug where model parameter is not respected; workaround is `model: inherit` in agent frontmatter
   - What's unclear: When/if this bug will be fixed, whether workaround will remain valid
   - Recommendation: Use `model: inherit` in lucy-case-agent.md (already done in Phase 28), document the workaround, monitor Claude Code release notes for fix

2. **Optimal batch size for autonomous iteration**
   - What we know: Agent should iterate autonomously for multiple LSD runs before returning (~10 iterations per skill/SKILL.md Section 7)
   - What's unclear: Whether 10 is optimal, or if fewer iterations per batch with more frequent monitoring is better
   - Recommendation: Start with ~10 iterations per batch (as specified in Phase 28 agent), adjust based on Phase 32 validation results

3. **Diagnostic specialist delegation trigger threshold**
   - What we know: Delegate after 2 failed basic interventions with SAME pattern (per skill/supervisor/SKILL.md Section 5)
   - What's unclear: Whether 2 is optimal or if 3-5 would reduce false delegations
   - Recommendation: Implement 2-failure threshold as specified, monitor in Phase 30 (diagnostic specialist implementation) for adjustment

4. **Intervention counter persistence across sessions**
   - What we know: CASE sessions are single-run (not multi-session), counters can be in-memory
   - What's unclear: Whether users might want to resume failed CASE sessions and preserve intervention history
   - Recommendation: In-memory counters for Phase 29, consider persistence in future if user feedback indicates need

## Sources

### Primary (HIGH confidence)
- Phase 28 agent definition: `~/.claude/agents/lucy-case-agent.md` (created in 28-01-PLAN.md)
- skill/supervisor/SKILL.md: Sections 1-8 (supervisor logic being dissolved into orchestrator)
- skill/SKILL.md: Sections 1, 6, 7, 9 (domain knowledge referenced by agent)
- skill/diagnostic/SKILL.md: Section 1 (LSD command reference for basic diagnosis)
- Claude Code sub-agents documentation: https://code.claude.com/docs/en/sub-agents (Task tool spawning patterns)
- Existing sub-command skills: ~/.claude/commands/lucy-ng/status.md, dereplicate.md, predict.md (pattern examples)

### Secondary (MEDIUM confidence)
- .planning/REQUIREMENTS.md: Requirements SCMD-02, ORCH-01 through ORCH-08
- .planning/STATE.md: v2.1 key decisions (GSD sub-commands, Option A supervision, per-pattern counters)
- .planning/ROADMAP.md: Phase 29 success criteria and dependencies

### Tertiary (LOW confidence)
- Web search results for "Claude Code 2.1 Task tool 2026" — verified Task tool spawning patterns exist and are standard
- DEV Community article on Task tool — confirms orchestration system exists, not authoritative for implementation details

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Task tool, sub-command skills, CASE-PROGRESS.md are all validated in previous phases
- Architecture: HIGH — Patterns extracted from Phase 28 agent definition, skill/supervisor/SKILL.md, and existing sub-command skills
- Pitfalls: HIGH — Based on Phase 28 design decisions (advisory not directive, batch not synchronous monitoring) and GSD best practices

**Research date:** 2026-02-08
**Valid until:** 90 days (stable patterns, v2.1 architecture is final for this milestone)

## Sources

- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [The Task Tool: Claude Code's Agent Orchestration System - DEV Community](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2)
- [Claude Code's 'Tasks' update lets agents work longer and coordinate across sessions | VentureBeat](https://venturebeat.com/orchestration/claude-codes-tasks-update-lets-agents-work-longer-and-coordinate-across)
- [Claude Code Swarm Orchestration Skill - Complete guide to multi-agent coordination](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea)
- [Claude Code Tasks: Complete Guide to AI Agent Workflow | dplooy](https://www.dplooy.com/blog/claude-code-tasks-complete-guide-to-ai-agent-workflow)
- [Build Agent Skills Faster with Claude Code 2.1 Release | Medium](https://medium.com/@richardhightower/build-agent-skills-faster-with-claude-code-2-1-release-6d821d5b8179)
