# Phase 24: Supervisor Agent - Research

**Researched:** 2026-02-07
**Domain:** Multi-agent orchestration with Claude Code subagents
**Confidence:** HIGH

## Summary

The supervisor agent for lucy-ng will be a Claude Code subagent defined via markdown with YAML frontmatter in `.claude/agents/`. The supervisor wraps the CASE workflow, spawning the CASE agent as a subagent via the Task tool, monitoring progress through markdown checkpoint files, detecting unproductive loops, and intervening with diagnosis-first redirects.

Claude Code's 2026 subagent architecture provides native support for this pattern: subagents run in separate contexts with custom system prompts, tool access control, and independent permissions. The supervisor reads CASE-PROGRESS.md (accumulated markdown log written by CASE agent) to track solution counts, constraints added/removed, and iteration history. When loop patterns are detected (ELIM thrashing, zero-solution loops, solution explosion, constraint churning), the supervisor diagnoses the issue from the progress log and advises the CASE agent with specific constraints (e.g., "sp2 count issue detected, fix before retrying").

**Primary recommendation:** Use markdown for both agent definition (YAML frontmatter + system prompt) and state tracking (human-readable CASE-PROGRESS.md), leveraging Claude Code's native subagent system rather than building custom orchestration.

## Standard Stack

The established architecture for supervisor agents in Claude Code 2026:

### Core

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Claude Code subagents | Native | Multi-agent orchestration | Official Claude Code feature; markdown + YAML frontmatter; Task tool for spawning |
| Markdown + YAML | Standard | Agent definition format | Claude Code native format; YAML frontmatter for config, markdown for system prompt |
| Task tool | Native | Spawn and manage subagents | Claude Code built-in; runs up to 7 parallel subagents; returns structured results |
| Markdown checkpoints | Standard | State tracking between agents | Human-readable, AI-parseable, persistent across iterations |

### Supporting

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| Hooks (PreToolUse) | Native | Conditional tool validation | When restricting specific operations (e.g., read-only SQL) |
| Permission modes | Native | Control subagent capabilities | `delegate` for coordinators, `dontAsk` for autonomous agents |
| Persistent memory | Native | Cross-session learning | When supervisor should remember patterns (not needed for Phase 24) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Claude Code subagents | LangGraph supervisor | More control but custom infrastructure; Claude Code is native, simpler |
| Markdown state | JSON checkpoint files | More structured but less readable; AI agents parse natural language better |
| Task tool | Custom agent spawning | Full control but reinvents Claude Code machinery; Task tool is tested/stable |

**Installation:**

No installation required — Claude Code subagents are built-in. Agent definition files go in `.claude/agents/` (project-level) or `~/.claude/agents/` (user-level).

## Architecture Patterns

### Recommended Project Structure

```
.claude/
├── agents/
│   ├── supervisor.md          # Supervisor agent definition (YAML + system prompt)
│   └── case-agent.md          # CASE agent definition (optional - can be invoked generically)
skill/
├── supervisor/
│   └── SKILL.md               # Supervisor domain knowledge (loop patterns, diagnostics)
└── SKILL.md                   # CASE domain knowledge (consumed by CASE agent)
data/compound/
└── <compound-name>/
    ├── CASE-PROGRESS.md       # Accumulated iteration log (written by CASE agent)
    ├── *.lsd                  # LSD input files
    └── *.sol                  # LSD solution files
```

### Pattern 1: Supervisor Wrapping CASE Agent

**What:** Supervisor is the single entry point; spawns CASE agent via Task tool; reads progress checkpoints; intervenes when loops detected.

**When to use:** When you need to prevent runaway iterations and provide diagnostic feedback.

**Example:**

```yaml
---
name: lucy-supervisor
description: Orchestrates CASE workflow, routes to dereplication/CASE/sanitize, detects unproductive loops and intervenes
tools: Task(case-agent), Read, Bash
model: sonnet
permissionMode: default
---

You are the lucy-ng supervisor agent. You coordinate all structure elucidation tasks.

## Routing Logic

1. **Sanitize request?** → Use bash to call `lucy sanitize` CLI
2. **Dereplication only?** → Use bash to call `lucy dereplicate c13` CLI
3. **Full CASE?** → Spawn CASE agent via Task tool

## CASE Workflow Supervision

When running CASE:

1. Spawn CASE agent via Task tool with compound path and formula
2. CASE agent writes CASE-PROGRESS.md after each iteration
3. Read CASE-PROGRESS.md to check for loop patterns
4. If loop detected:
   - Diagnose from progress log (sp2 count, H budget, correlation conflicts)
   - Advise CASE agent with specific constraints (NOT generic "try again")
   - Track intervention count per pattern
   - Escalate to user after 10 failed interventions with same pattern

## Loop Detection Patterns

- **ELIM thrashing:** ELIM added/removed 2+ times without sp2/H diagnosis
- **Zero-solution loop:** 3+ iterations with 0 solutions, same approach
- **Solution explosion:** 3+ iterations with >100 solutions, <10% reduction each
- **Constraint churning:** Adding/removing constraints randomly without progress

See skill/supervisor/SKILL.md for detailed diagnostic procedures.
```

### Pattern 2: Checkpoint-Based State Tracking

**What:** CASE agent writes accumulating markdown log; supervisor reads to detect patterns.

**When to use:** When agents need shared state without tight coupling.

**Example:**

```markdown
# CASE Progress Log

**Compound:** data/compound/virgiline
**Formula:** C16H21NO2
**Started:** 2026-02-07 14:32:15

## Iteration 1: Initial LSD run (MULT + HSQC only)
- **Time:** 14:32:45
- **Solution count:** 1,234
- **Constraints added:** None (baseline)
- **Why:** Establish unconstrained baseline before adding HMBC
- **Confidence:** N/A (too many solutions)

## Iteration 2: Add high-confidence HMBC batch (5 correlations)
- **Time:** 14:35:12
- **Solution count:** 187
- **Constraints added:** HMBC C155.2-H7.8, C138.5-H3.2, C127.3-H7.8, C129.8-H3.2, C172.4-H7.8
- **Why:** Selected isolated carbons with unique proton assignments
- **Constraint effectiveness:** 85% reduction (1234 → 187), highly effective
- **Confidence:** Medium (need more constraints)
- **HMBC correlations used:** 5/43

## Iteration 3: Add quaternary carbon HMBC (3 correlations)
- **Time:** 14:38:05
- **Solution count:** 0
- **Constraints added:** HMBC C155.2-H2.1, C155.2-H4.3, C172.4-H2.1
- **Why:** Connect quaternary carbons to structure
- **Constraint effectiveness:** Over-constrained (187 → 0)
- **Problem detected:** Likely 1J artifact or ambiguous carbon assignment
- **Action:** Remove last batch, investigate conflicting correlations
```

**Supervisor reads this and detects:** Zero-solution result after iteration 3; diagnoses that batch of quaternary correlations caused conflict; advises CASE agent to check for 1J artifacts or close carbon shifts.

### Pattern 3: Advisory Intervention (Not Directive)

**What:** Supervisor tells CASE agent WHAT the problem is and WHAT to fix, but NOT exactly HOW to fix it.

**When to use:** When you want CASE agent to retain autonomy while getting diagnostic guidance.

**Example:**

```
SUPERVISOR → CASE AGENT:

Iteration 3 failed with 0 solutions after adding quaternary carbon HMBC correlations.

**Diagnosis:** Correlation at C155.2-H2.1 conflicts with existing constraints.

**Advisory:** Before retrying:
1. Check if C155.2 and nearby carbons (±3 ppm) are resolvable in HMBC F1 dimension
2. If close carbons exist, use LIST/PROP to encode ambiguity instead of picking one
3. Verify H2.1 position is correct (check for 1J artifact by comparing HMBC to HSQC)
4. Only re-add correlations after resolving ambiguity

Do NOT add ELIM. Fix the root cause first.

Retry when ready.
```

**NOT this (too directive):**

```
Change line 15 of compound.lsd from "HMBC 5 12" to "LIST L1 5 6" and add "PROP L1 1 LIST_H12".
```

### Anti-Patterns to Avoid

- **Micro-managing CASE agent:** Supervisor should NOT dictate exact LSD file edits; CASE agent figures out implementation
- **Generic retries:** "Try again" without diagnosis wastes iterations; always diagnose first
- **Ignoring intervention count:** Escalate after 10 failed interventions with same pattern (prevents infinite supervisor loops)
- **Spawning diagnostic specialist in Phase 24:** Phase 24 supervisor does basic diagnosis; Phase 25 adds delegation to specialist

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent definition format | Custom JSON config + Python orchestrator | Claude Code markdown + YAML subagents | Native support; loads at session start; works with Task tool |
| State tracking between agents | Shared Python objects or database | Markdown checkpoint files | AI agents parse natural language; human-readable; persistent |
| Subagent spawning | Custom subprocess management | Task tool | Handles parallelism (7 max), context isolation, result aggregation |
| Loop detection logic | Hard-coded Python rules | Supervisor skill document (markdown) | AI reasons about patterns; extensible without code changes |
| Progress logging | JSON or structured logs | Accumulated markdown with sections | AI-readable; includes reasoning ("WHY changes were made") |

**Key insight:** Claude Code subagents are designed for AI-to-AI orchestration. Use markdown for both definition and communication rather than building Python machinery.

## Common Pitfalls

### Pitfall 1: Subagents Cannot Spawn Subagents

**What goes wrong:** Trying to make CASE agent spawn a diagnostic specialist fails.

**Why it happens:** Claude Code explicitly prevents subagent nesting to avoid infinite recursion.

**How to avoid:** In Phase 24, supervisor handles its own basic diagnosis. Phase 25 adds diagnostic specialist that supervisor delegates to (not CASE agent).

**Warning signs:** Task tool fails when invoked from within a subagent; error message about nesting not allowed.

### Pitfall 2: JSON State Is Less Effective Than Markdown

**What goes wrong:** Using JSON for CASE-PROGRESS.md makes supervisor struggle to parse iteration history.

**Why it happens:** AI agents are language models trained on natural language, not JSON parsers.

**How to avoid:** Use markdown with clear section headers, bullet points, and natural language descriptions. Include "Why" for each decision.

**Warning signs:** Supervisor asks clarifying questions about JSON fields; misinterprets structured data.

### Pitfall 3: Forgetting Intervention Cap

**What goes wrong:** Supervisor loops indefinitely trying to fix same issue.

**Why it happens:** No counter tracking how many times same pattern has failed.

**How to avoid:** Supervisor tracks intervention count per pattern (ELIM thrashing, zero-solution, explosion). Escalate after 10 attempts.

**Warning signs:** User sees 20+ iterations with same error message; supervisor never escalates.

### Pitfall 4: Using Permission Mode Incorrectly

**What goes wrong:** Supervisor runs in `dontAsk` mode and cannot get user approval for destructive operations.

**Why it happens:** Misunderstanding permission modes; copying from wrong example.

**How to avoid:** Supervisor uses `default` or `delegate` mode. Only use `dontAsk` for fully autonomous background agents.

**Warning signs:** Supervisor blocks on operations requiring approval; user never sees prompts.

### Pitfall 5: Overwriting Progress Log Instead of Appending

**What goes wrong:** Each CASE iteration overwrites CASE-PROGRESS.md, losing history.

**Why it happens:** Using Write instead of append-style editing.

**How to avoid:** CASE agent appends new iteration section to end of file; never overwrites.

**Warning signs:** Progress log only shows latest iteration; supervisor cannot detect patterns across iterations.

## Code Examples

Verified patterns from official sources:

### Minimal Supervisor Agent Definition

```yaml
# Source: https://code.claude.com/docs/en/sub-agents (official Claude Code docs)
---
name: lucy-supervisor
description: Orchestrates lucy-ng workflows, routes to dereplication/CASE/sanitize, detects loops and intervenes
tools: Task, Read, Bash, Glob, Grep
model: sonnet
permissionMode: default
---

You are the lucy-ng supervisor agent. You are the single entry point for all lucy-ng operations.

## Your Responsibilities

1. **Route tasks:**
   - Sanitize → bash `lucy sanitize`
   - Dereplication → bash `lucy dereplicate c13`
   - Full CASE → spawn CASE agent via Task tool

2. **Monitor CASE progress:**
   - Read CASE-PROGRESS.md after each iteration
   - Detect loop patterns (ELIM thrashing, zero-solution, explosion)
   - Diagnose root cause from progress log

3. **Intervene when stuck:**
   - Advise CASE agent with specific diagnosis and constraints
   - Track intervention count per pattern
   - Escalate to user after 10 failed interventions

4. **Report results:**
   - Summarize final structure(s) with confidence
   - Document ambiguities and uncertainties
   - Suggest additional experiments if needed

See skill/supervisor/SKILL.md for detailed loop detection patterns and diagnostic procedures.
```

### Spawning CASE Agent via Task Tool

```markdown
# Source: https://code.claude.com/docs/en/sub-agents (Task tool usage)

Supervisor invokes CASE agent:

SUPERVISOR: I'll spawn a CASE agent to perform structure elucidation for this compound.

[Uses Task tool]
Task(agent_type="general-purpose", instructions="
  Perform CASE workflow for compound at data/compound/virgiline with formula C16H21NO2.

  Write CASE-PROGRESS.md in the compound directory after each LSD iteration.

  Include in each iteration entry:
  - Solution count
  - Constraints added/removed
  - WHY changes were made
  - Constraint effectiveness (% reduction or over-constrained)
  - Confidence assessment
  - HMBC correlations used count

  Follow incremental HMBC strategy from skill/SKILL.md Section 7.

  Stop when solution count ≤ 10 or after 10 iterations max.
")

[CASE agent runs, writes progress log, returns result]

SUPERVISOR: [Reads CASE-PROGRESS.md to check for loop patterns]
```

### Accumulating Progress Log Format

```markdown
# Source: Multi-agent progress tracking research (markdown format best practice)

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

**Why:** Establish unconstrained baseline before adding HMBC correlations. Verify atom definitions and HSQC correlations are correct.

**Constraint effectiveness:** N/A (baseline)
**Confidence:** Too many solutions (under-constrained)
**HMBC correlations used:** 0/43

**Notes:**
- sp2 atom count: 8 (even) ✓
- Hydrogen budget: 21 H (matches formula) ✓
- All protonated carbons have HSQC ✓

---

## Iteration 2: Add high-confidence HMBC batch 1

**Time:** 14:35:12
**LSD file:** virgiline-02.lsd
**Solution count:** 187

**Constraints added:**
- HMBC C155.2-H7.8 (isolated carbon, unique proton)
- HMBC C138.5-H3.2 (isolated carbon)
- HMBC C127.3-H7.8 (aromatic CH)
- HMBC C129.8-H3.2 (aromatic CH)
- HMBC C172.4-H7.8 (quaternary C=O)

**Constraints removed:** None

**Why:** Selected 5 correlations with isolated carbon shifts (>3 ppm from nearest neighbor) and unique proton assignments. Quaternary C172.4 is especially valuable for structure connectivity.

**Constraint effectiveness:** 85% reduction (1234 → 187), highly effective
**Confidence:** Medium (still need more constraints to narrow to <10 solutions)
**HMBC correlations used:** 5/43

**Notes:**
- All 5 correlations from top quartile of peak intensities
- No overlapping carbon or proton assignments
- Solution count decreased significantly → batch is productive

---

[Subsequent iterations continue in same format]
```

### Loop Detection from Progress Log

```python
# Source: Convergence detection patterns research (2026 multi-agent patterns)
# Pseudocode for supervisor logic (actual implementation is in supervisor's system prompt as natural language)

def detect_loops(progress_log_content):
    """
    Supervisor parses CASE-PROGRESS.md and detects loop patterns.
    This is conceptual — actual supervisor uses natural language reasoning.
    """
    iterations = parse_iterations(progress_log_content)

    # Pattern 1: ELIM thrashing
    elim_added_count = count_iterations_with("ELIM added", iterations)
    elim_removed_count = count_iterations_with("ELIM removed", iterations)
    if elim_added_count >= 2 or elim_removed_count >= 2:
        return "ELIM_THRASHING"

    # Pattern 2: Zero-solution loop
    zero_solution_runs = [i for i in iterations if i.solution_count == 0]
    if len(zero_solution_runs) >= 3:
        approaches = [i.constraints_added for i in zero_solution_runs]
        if all_same_approach(approaches):
            return "ZERO_SOLUTION_LOOP"

    # Pattern 3: Solution explosion (stalled at high count)
    high_count_runs = [i for i in iterations[-3:] if i.solution_count > 100]
    if len(high_count_runs) == 3:
        reductions = [calc_reduction(high_count_runs[i], high_count_runs[i+1])
                      for i in range(2)]
        if all(r < 0.10 for r in reductions):  # <10% reduction each
            return "SOLUTION_EXPLOSION"

    # Pattern 4: Constraint churning
    if len(iterations) >= 5:
        recent = iterations[-5:]
        added = sum(len(i.constraints_added) for i in recent)
        removed = sum(len(i.constraints_removed) for i in recent)
        if added > 10 and removed > 5:
            # High add/remove activity without convergence
            if recent[-1].solution_count > 50:
                return "CONSTRAINT_CHURNING"

    return None
```

## State of the Art

| Old Approach | Current Approach (2026) | When Changed | Impact |
|--------------|------------------------|--------------|--------|
| LangGraph supervisor with Python orchestration | Claude Code native subagents (markdown + YAML) | 2025-2026 | Simpler; no custom infrastructure; native Task tool |
| JSON for agent state | Markdown checkpoints | 2026 | AI-readable; human-inspectable; includes reasoning |
| Hard-coded loop detection in Python | Loop patterns in supervisor skill (natural language) | 2026 | AI reasons about patterns; extensible via skill updates |
| Directive interventions ("change line 15") | Advisory interventions (diagnose + constrain, not dictate) | 2026 | CASE agent retains autonomy; learns from constraints |
| Subagent spawns diagnostic specialist | Supervisor spawns diagnostic specialist (Phase 25) | 2026 | Avoids nesting limitation; supervisor coordinates both |

**Deprecated/outdated:**
- Custom Python orchestration (replaced by Claude Code Task tool)
- Tight coupling between supervisor and worker (replaced by checkpoint-based communication)
- Generic retry logic without diagnosis (replaced by diagnosis-first interventions)

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal intervention cap**
   - What we know: User specified 10 failed intervention cycles (not 3)
   - What's unclear: Is 10 too high for some patterns, too low for others? Should cap vary by pattern type?
   - Recommendation: Start with 10 for all patterns; adjust based on real usage. Track metrics to refine.

2. **Convergence criteria flexibility**
   - What we know: Ideal 1-5 solutions, acceptable <10, flexible if ranking differentiates
   - What's unclear: Exactly when to declare convergence at 11-20 solutions if ranking is strong
   - Recommendation: Supervisor judgment call based on ranking MAE spread; document reasoning in progress log

3. **CASE agent invocation method**
   - What we know: Task tool can spawn subagents; can pass instructions
   - What's unclear: Should CASE agent be a named subagent in `.claude/agents/case-agent.md` or invoked generically via general-purpose?
   - Recommendation: Start with general-purpose invocation (simpler); create named case-agent.md in Phase 26 if tool restrictions needed

4. **Progress log size management**
   - What we know: Accumulated log grows with each iteration; 20 iterations = potentially large file
   - What's unclear: At what size does reading progress log consume too much supervisor context?
   - Recommendation: Keep iteration entries concise (5-10 lines each); 20 iterations = ~200 lines, manageable. If becomes issue, compress old iterations.

## Sources

### Primary (HIGH confidence)

- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents) - Official documentation on subagent architecture, YAML frontmatter, Task tool usage
- [ClaudeLog - Task Tool Documentation](https://claudelog.com/mechanics/task-agent-tools/) - Task tool patterns, result integration, 7-parallel maximum
- skill/supervisor/SKILL.md (78 lines, local file) - Existing supervisor skill foundation with loop detection patterns
- skill/SKILL.md (1,079 lines, local file) - CASE domain knowledge including incremental HMBC strategy (Section 7) and convergence detection (Section 11)

### Secondary (MEDIUM confidence)

- [Claude Code multiple agent systems: Complete 2026 guide](https://www.eesel.ai/blog/claude-code-multiple-agent-systems-complete-2026-guide) - Multi-agent patterns, subagent vs team comparison
- [The Task Tool: Claude Code's Agent Orchestration System](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2) - Task tool mechanics verified with official docs
- [How to Build Multi-Agent Systems: Complete 2026 Guide](https://dev.to/eira-wexford/how-to-build-multi-agent-systems-complete-2026-guide-1io6) - Iteration caps, convergence detection, safety patterns
- [Google's Eight Essential Multi-Agent Design Patterns](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/) - Generator-critic pattern, human-in-the-loop, exit mechanisms
- [AI agent markdown progress report format structured logging 2026](https://www.ibm.com/think/tutorials/multi-agent-prd-ai-automation-metagpt-ollama-deepseek) - Markdown output for AI agents, structured logging
- [AGENTS.md: A Machine-Readable Alternative to README](https://research.aimultiple.com/agents-md/) - Markdown as standard format for AI agent communication

### Tertiary (LOW confidence - informational only)

- [Agentic Amnesia: The State Management Crisis](https://dev.to/prodevel/agentic-amnesia-the-state-management-crisis-6am) - State management challenges, checkpoint patterns
- [AI escalation management: turn misfires into trust-building](https://www.partnerhero.com/blog/ai-escalation-management) - Escalation patterns, intervention strategies
- [Root Cause Report Generator Agent - XMPRO](https://xmpro.com/solutions-library/ai-agent-library,content-agents/root-cause-report-generator-agent/) - Diagnostic report structures with confidence indicators

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Claude Code subagents are official, documented, production-ready
- Architecture: HIGH - Patterns verified in official docs; existing supervisor skill provides foundation
- Pitfalls: MEDIUM - Derived from general multi-agent patterns; some lucy-ng-specific issues discovered through context analysis

**Research date:** 2026-02-07
**Valid until:** 30 days (stable technology, but multi-agent patterns evolving rapidly in 2026)
