# Phase 28: CASE Agent Definition - Research

**Researched:** 2026-02-08
**Domain:** Claude Code subagent architecture, YAML frontmatter, skill content inlining
**Confidence:** HIGH

## Summary

Researched how to implement Phase 28 (CASE Agent Definition) by examining existing agent patterns, Claude Code subagent documentation, skill structures, and the GSD executor pattern. The goal is to create an autonomous CASE agent that spawns successfully, writes structured progress logs, and executes the full CASE workflow without attempting dereplication.

**Key findings:**

1. **Agent definition pattern established** - Existing GSD agents (gsd-executor, gsd-planner) provide proven YAML frontmatter + markdown template with clear sections (<role>, <execution_flow>, etc.)
2. **Skill content structure identified** - skill/SKILL.md (1,098 lines) has well-defined sections for inlining; CASE-PROGRESS.md format is defined in skill/supervisor/SKILL.md
3. **Spawning mechanism verified** - Task() tool references agent files in ~/.claude/agents/ by name; agent_type parameter matches the YAML `name` field
4. **Critical skill content mapped** - ~500-700 lines should be inlined (NMR background, CASE workflow, LSD basics, CASE-PROGRESS.md format); detailed references via file paths

**Primary recommendation:** Follow the gsd-executor.md pattern with YAML frontmatter (name, description, tools, color) + structured markdown body containing inlined critical knowledge from skill/SKILL.md Sections 1-2, 6-7, and skill/supervisor/SKILL.md Section 8.

## Standard Stack

The established libraries/tools for subagent definition in Claude Code:

### Core Components

| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| YAML frontmatter | Standard markdown YAML | Agent metadata and configuration | Official Claude Code subagent format |
| Markdown body | Standard markdown | System prompt and workflow instructions | Subagent receives this as system prompt |
| Task() tool | Built-in | Spawn subagents by name | Native Claude Code parallel processing |
| agent_type parameter | String matching `name` field | Target specific agent definitions | Maps to filename without .md extension |

### Supporting Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| Read, Write, Bash, Glob, Grep | File operations and execution | Standard CASE workflow tools |
| ~/.claude/agents/*.md | Agent definition storage | User-level agents available in all projects |
| .planning/config.json | Planning docs commit config | Controls whether planning artifacts are committed |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| YAML frontmatter | JSON via --agents CLI flag | JSON is session-only, not persistent; markdown files are version-controllable |
| Task() tool | Agent Teams | Teams are for sustained parallelism; subagents are simpler for orchestrator pattern |
| Full skill inlining | File path references only | Full inlining loses context; hybrid approach (500-700 lines inlined + references) is optimal |

**Installation:**

No installation required - uses built-in Claude Code subagent system and standard markdown files.

## Architecture Patterns

### Recommended Agent Structure

```
~/.claude/agents/lucy-case-agent.md
├── YAML frontmatter (lines 1-6)
│   ├── name: lucy-case-agent
│   ├── description: (when to use this agent)
│   ├── tools: Read, Write, Bash, Glob, Grep
│   ├── model: inherit
│   └── color: (visual identifier)
└── Markdown body
    ├── <role> - Agent identity and purpose
    ├── <inlined_critical_knowledge> - 500-700 lines
    │   ├── NMR background (skill/SKILL.md Section 1 excerpt)
    │   ├── CASE workflow overview (Section 9 excerpt)
    │   ├── LSD basics (Section 6 excerpt)
    │   ├── Incremental HMBC strategy (Section 7)
    │   └── CASE-PROGRESS.md format (skill/supervisor/SKILL.md Section 8)
    ├── <detailed_references> - File path pointers
    │   ├── Full NMR domain knowledge: skill/SKILL.md
    │   ├── LSD diagnostics: skill/diagnostic/SKILL.md
    │   └── CASE subskill: skill/CASE/SKILL.md
    ├── <workflow> - Step-by-step execution
    └── <output_format> - CASE-PROGRESS.md structure
```

### Pattern 1: GSD Executor Pattern (Proven Template)

**What:** Structured markdown with role definition, execution flow, and protocols
**When to use:** For agents that execute complex workflows with multiple steps
**Example:**

```markdown
---
name: lucy-case-agent
description: Autonomous CASE agent for NMR structure elucidation
tools: Read, Write, Bash, Glob, Grep
model: inherit
color: blue
---

<role>
You are an autonomous CASE (Computer-Assisted Structure Elucidation) agent.
Your job: Determine molecular structure from NMR spectra without attempting dereplication.
</role>

<execution_flow>
[Step-by-step workflow with clear checkpoints]
</execution_flow>

[Additional protocol sections]
```

**Source:** /Users/steinbeck/.claude/agents/gsd-executor.md (lines 1-785)

### Pattern 2: Hybrid Context Inlining

**What:** Inline ~500-700 lines of critical knowledge, reference detailed documentation via file paths
**When to use:** When agent needs immediate access to core concepts but detailed knowledge is too large
**Example:**

```markdown
<inlined_critical_knowledge>
## NMR Background (Essential Concepts)

[500-700 lines covering:]
- Experiment types and information (Section 1 excerpt)
- CASE workflow steps (Section 9 excerpt)
- LSD command basics (Section 6 excerpt)
- Incremental HMBC strategy (Section 7)
- CASE-PROGRESS.md format (supervisor Section 8)

</inlined_critical_knowledge>

<detailed_references>
For comprehensive domain knowledge:
- NMR spectroscopy, peak picking, symmetry, dereplication: skill/SKILL.md
- LSD diagnostics and manual: skill/diagnostic/SKILL.md
- CASE-specific workflow details: skill/CASE/SKILL.md
</detailed_references>
```

**Rationale:** Agent can start immediately with critical knowledge without reading files, but has references when it needs deeper detail.

### Pattern 3: CASE-PROGRESS.md Writing Protocol

**What:** Mandatory progress logging after every LSD iteration for supervisor monitoring
**When to use:** Any iterative agent workflow that requires loop detection
**Example:**

```markdown
<progress_logging>
After EVERY LSD iteration, append to CASE-PROGRESS.md:

## Iteration N: [brief description]

**Time:** [timestamp]
**LSD file:** [filename].lsd
**Solution count:** [count]

**Constraints added:**
- [constraint with reasoning]

**Constraints removed:**
- [constraint with reasoning]

**Why:** [natural language explanation of strategy]

**Constraint effectiveness:** [% reduction | "baseline" | "over-constrained"]
**Confidence:** [qualitative assessment]
**HMBC correlations used:** X/Y

**Notes:**
- sp2 count: [N] ([even/odd]) [✓ check / ⚠ warning]
- H budget: [matches / mismatch]
</progress_logging>
```

**Source:** skill/supervisor/SKILL.md Section 8 (lines 632-828)

### Anti-Patterns to Avoid

- **Including Task() in tools** - Subagents cannot spawn other subagents; this would fail
- **Directive system prompts** - Agent should understand WHAT to accomplish, not be given step-by-step HOW instructions
- **Attempting dereplication** - CASE agent has absolute separation from dereplication workflow (CASE-04 requirement)
- **Omitting CASE-PROGRESS.md** - Progress logging is mandatory for supervisor monitoring and loop detection
- **Full skill content inlining** - 1,098 lines of skill/SKILL.md would exceed reasonable system prompt length

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent definition format | Custom JSON or config format | YAML frontmatter + markdown body | Official Claude Code subagent format with proven ecosystem support |
| Subagent spawning | Custom process management | Task(agent_type="name") tool | Built-in Claude Code parallel processing with context isolation |
| Progress logging format | Ad-hoc text files | CASE-PROGRESS.md structured format from skill/supervisor/SKILL.md | Already defined, supervisor expects this exact structure |
| Skill content selection | Manual line counting | Sections 1, 6-7, 9 (NMR basics, LSD, HMBC, workflow) + supervisor Section 8 | Minimal viable knowledge for autonomous CASE execution |
| Agent permission mode | Custom validation | `model: inherit` + standard tool allowlist | Inherits parent permissions, no need for bypassPermissions or custom modes |

**Key insight:** Claude Code subagent system handles context isolation, spawning, and completion automatically. Focus on defining the right system prompt with correct knowledge inlining.

## Common Pitfalls

### Pitfall 1: Incorrect agent_type Syntax

**What goes wrong:** Task() call with wrong agent name fails to spawn agent
**Why it happens:** agent_type parameter must match YAML `name` field exactly (without .md extension)
**How to avoid:**
- YAML frontmatter: `name: lucy-case-agent`
- Task() call: `agent_type="lucy-case-agent"`
- File location: `~/.claude/agents/lucy-case-agent.md`

**Warning signs:** Task() fails with "agent not found" or spawns wrong agent

### Pitfall 2: Including Task in Subagent Tools

**What goes wrong:** Subagent tries to spawn other subagents, which is forbidden
**Why it happens:** Copying tool lists from main agents (which CAN spawn subagents)
**How to avoid:** Subagents use Read, Write, Bash, Glob, Grep only - NEVER Task
**Warning signs:** Tool configuration includes "Task" for a subagent definition

**Correct configuration:**
```yaml
# CASE agent (subagent) - NO Task tool
tools: Read, Write, Bash, Glob, Grep

# Orchestrator (main agent) - CAN use Task
tools: Read, Write, Bash, Task
```

### Pitfall 3: Over-Inlining Skill Content

**What goes wrong:** System prompt becomes too large (>1000 lines), agent loses focus
**Why it happens:** Trying to inline all 1,098 lines of skill/SKILL.md
**How to avoid:**
- Inline ONLY critical sections (~500-700 lines total)
- NMR background: Section 1 excerpt (key concepts only, not full 200 lines)
- LSD basics: Section 6 excerpt (command format, not full diagnostic manual)
- HMBC strategy: Section 7 (full section, ~150 lines)
- CASE workflow: Section 9 excerpt (key steps)
- Progress format: supervisor Section 8 (full section, ~200 lines)
- Provide file path references for detailed knowledge

**Warning signs:** Agent asks to read skill files immediately instead of using inlined knowledge

### Pitfall 4: Missing CASE-PROGRESS.md Format

**What goes wrong:** Agent writes unstructured progress, supervisor cannot parse it
**Why it happens:** Format not clearly specified in agent system prompt
**How to avoid:** Inline complete CASE-PROGRESS.md format from skill/supervisor/SKILL.md Section 8 with ALL required fields
**Warning signs:** Orchestrator cannot detect loops because progress log is missing required fields

### Pitfall 5: Attempting Dereplication

**What goes wrong:** CASE agent tries to run `lucy dereplicate c13` during workflow
**Why it happens:** Agent doesn't understand absolute separation between CASE and dereplication
**How to avoid:**
- Explicitly state in <role> section: "NEVER attempt dereplication"
- Reference CASE-04 requirement
- Include in inlined workflow: "Dereplication is SEPARATE - not your responsibility"

**Warning signs:** Agent output mentions running dereplication commands

## Code Examples

Verified patterns from official sources:

### YAML Frontmatter (Official Format)

```yaml
# Source: https://code.claude.com/docs/en/sub-agents
---
name: lucy-case-agent
description: Autonomous CASE agent for NMR structure elucidation from Bruker spectra. Use when user provides compound path and molecular formula for full structure determination. NEVER use for dereplication-only requests.
tools: Read, Write, Bash, Glob, Grep
model: inherit
color: blue
---
```

**Required fields:**
- `name` - Unique identifier (lowercase-with-hyphens)
- `description` - When to use this agent (Claude uses this for delegation decision)

**Optional but recommended:**
- `tools` - Allowlist of tools (default: inherit all from parent)
- `model` - `inherit`, `sonnet`, `opus`, or `haiku` (default: inherit)
- `color` - Visual badge identifier in UI

### Agent Role Definition (GSD Executor Pattern)

```markdown
# Source: /Users/steinbeck/.claude/agents/gsd-executor.md (lines 8-14)
<role>
You are an autonomous CASE (Computer-Assisted Structure Elucidation) agent.

You are spawned by `/lucy-ng:case` orchestrator.

Your job: Determine the molecular structure of an unknown organic compound
from NMR spectra. NEVER attempt dereplication (absolute separation).

You execute the full CASE workflow, commit progress after each iteration,
and write CASE-PROGRESS.md for supervisor monitoring.
</role>
```

### Critical Knowledge Inlining Structure

```markdown
<inlined_critical_knowledge>

This section contains essential domain knowledge for immediate reference.
For comprehensive details, see file path references at the end.

## 1. NMR Background (Essential Concepts)

### Experiment Types
[Excerpt from skill/SKILL.md Section 1 - key table only, ~50 lines]

### Common Pitfalls
[Excerpt from skill/SKILL.md Section 1.1 - critical warnings, ~100 lines]

## 2. CASE Workflow Overview

[Excerpt from skill/SKILL.md Section 9 - step-by-step procedure, ~150 lines]

## 3. LSD Command Basics

[Excerpt from skill/SKILL.md Section 6 - command format and rules, ~100 lines]

## 4. Incremental HMBC Strategy

[Full content from skill/SKILL.md Section 7, ~150 lines]

## 5. CASE-PROGRESS.md Format (MANDATORY)

[Full content from skill/supervisor/SKILL.md Section 8, ~200 lines]

Total: ~650 lines of critical knowledge

</inlined_critical_knowledge>

<detailed_references>

For comprehensive domain knowledge, consult these files as needed:

- **Full NMR spectroscopy knowledge**: /Users/steinbeck/Dropbox/develop/lucy-ng/skill/SKILL.md
  - Section 1: NMR Background (200 lines)
  - Section 2: Spectral Quality Assessment (150 lines)
  - Section 3: Peak Picking Strategy (100 lines)
  - Section 4: Symmetry Detection (50 lines)
  - Section 5: Dereplication (NOT your responsibility)
  - Section 6: LSD Reference (full manual, 200 lines)
  - Section 7: Incremental HMBC Strategy (inlined above)
  - Section 8: Ranking and Prediction (100 lines)
  - Section 9: CASE Workflow (inlined above)
  - Section 10: Error Tolerance and Ambiguity Detection (200 lines)
  - Section 11: Confidence Scoring (150 lines)

- **LSD diagnostics and troubleshooting**: /Users/steinbeck/Dropbox/develop/lucy-ng/skill/diagnostic/SKILL.md
  - Section 1: LSD Command Reference (500 lines)
  - Section 2: Systematic Diagnostic Procedures (1,000 lines)

- **CASE-specific workflow details**: /Users/steinbeck/Dropbox/develop/lucy-ng/skill/CASE/SKILL.md
  - Detailed step-by-step procedures (700 lines)
  - PDF report generation (200 lines)

Read these files when you need deeper detail on any topic.

</detailed_references>
```

### Task() Spawning Syntax (Orchestrator Side)

```python
# Source: Inferred from Claude Code documentation and GSD patterns
# This is what the orchestrator (case.md) will use to spawn the CASE agent

Task(
    agent_type="lucy-case-agent",  # Matches YAML name field
    instructions="""
    Perform CASE workflow for compound at {compound_path} with formula {formula}.

    Write CASE-PROGRESS.md in the compound directory after EVERY LSD iteration.

    Follow incremental HMBC strategy from your inlined knowledge.

    Stop when solution count ≤ 10 or after ~20 iterations maximum.
    """
)
```

**Key parameters:**
- `agent_type` - Must match YAML `name` field exactly
- `instructions` - Task-specific context and parameters
- Agent receives: inlined knowledge from markdown body + instructions + environment context

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MCP tools with embedded logic | Thin CLI wrappers + AI agent skills | v2.0 Phase 26 | Agent reasoning visible, testable, improvable |
| Monolithic /lucy-ng skill | Sub-command skills at ~/.claude/commands/lucy-ng/ | v2.1 Phase 27 | Modular, reusable, GSD-pattern |
| Paper architecture (defined but never invoked) | Working orchestration with Task() spawning | v2.1 Phase 28 | Critical: proves multi-agent works |
| Full skill content in system prompt | Hybrid inlining (~500-700 lines critical + file paths) | v2.1 CONTEXT decision | Balances immediate access with manageable prompt size |

**Deprecated/outdated:**
- MCP server for lucy-ng: Removed in v2.0 Phase 26, replaced with thin CLI + skills
- .claude/agents/supervisor.md: Will be deleted in v2.1 Phase 33 after logic migrates to case.md orchestrator
- Monolithic /lucy-ng skill: Replaced by sub-command structure in Phase 27

**Current best practice:**
- Agent definitions at ~/.claude/agents/ with YAML frontmatter + structured markdown
- Orchestrator skills at ~/.claude/commands/lucy-ng/ spawn agents via Task()
- Hybrid context inlining: 500-700 lines critical knowledge + file path references
- Mandatory progress logging in structured format for loop detection

## Open Questions

Things that couldn't be fully resolved:

1. **Exact line count for inlined sections**
   - What we know: Target is 500-700 lines total, include Sections 1 (excerpt), 6 (excerpt), 7 (full), 9 (excerpt), supervisor Section 8 (full)
   - What's unclear: Precise line ranges for excerpts from Sections 1, 6, 9
   - Recommendation: Start with key concepts only (50-100 lines each), agent can read full skill files if needed

2. **Agent continuation after intervention**
   - What we know: Orchestrator detects loops, provides advisory, needs to re-spawn agent with constraints
   - What's unclear: How to resume CASE agent at specific iteration (skip completed work)
   - Recommendation: Pass iteration number in Task() instructions, agent checks CASE-PROGRESS.md and skips to resume point

3. **Integration test scope**
   - What we know: VALD-01 requires end-to-end test (orchestrator spawns agent, agent writes progress, orchestrator monitors)
   - What's unclear: Should test use real Ibuprofen data or synthetic minimal case?
   - Recommendation: Use Ibuprofen (Phase 26-05 known working case) to ensure real-world validity

## Sources

### Primary (HIGH confidence)

- Claude Code Official Documentation - Subagent creation and configuration
  - https://code.claude.com/docs/en/sub-agents
  - Verified: YAML frontmatter format, Task() spawning syntax, tool configuration, permission modes
  - Date checked: 2026-02-08

- GSD Executor Agent Pattern
  - /Users/steinbeck/.claude/agents/gsd-executor.md (785 lines)
  - Verified: Structured markdown pattern, execution flow protocols, task commit workflow
  - Project file, local access

- lucy-ng Main Skill Document
  - /Users/steinbeck/Dropbox/develop/lucy-ng/skill/SKILL.md (1,098 lines)
  - Verified: Section structure, content for inlining, NMR background, CASE workflow, LSD basics
  - Project file, local access

- lucy-ng Supervisor Skill Document
  - /Users/steinbeck/Dropbox/develop/lucy-ng/skill/supervisor/SKILL.md (827 lines)
  - Verified: CASE-PROGRESS.md format (Section 8), loop detection patterns
  - Project file, local access

- v2.1 Requirements Document
  - /Users/steinbeck/Dropbox/develop/lucy-ng/.planning/REQUIREMENTS.md (200 lines)
  - Verified: CASE-01 through CASE-05 requirements, skill content expectations
  - Project file, local access

### Secondary (MEDIUM confidence)

- Claude Code Subagent Best Practices Article
  - https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/
  - Community patterns for subagent design
  - Date checked: 2026-02-08

- Claude Code Multiple Agent Systems Guide
  - https://www.eesel.ai/blog/claude-code-multiple-agent-systems-complete-2026-guide
  - Comprehensive 2026 guide to multi-agent patterns
  - Date checked: 2026-02-08

### Tertiary (LOW confidence)

- No low-confidence sources used - all findings verified with official docs or project files

## Metadata

**Confidence breakdown:**
- Agent definition format: HIGH - Official Claude Code documentation and existing GSD pattern
- Skill content inlining: HIGH - Requirements specify 500-700 lines, skill sections identified
- Task() spawning syntax: HIGH - Official docs and GSD executor pattern verification
- CASE-PROGRESS.md format: HIGH - Already defined in skill/supervisor/SKILL.md Section 8

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days - stable patterns, unlikely to change)

**Key validation sources:**
- Official Claude Code subagent docs: https://code.claude.com/docs/en/sub-agents
- Existing GSD agents as proven templates
- lucy-ng skill structure already defined in v2.0
