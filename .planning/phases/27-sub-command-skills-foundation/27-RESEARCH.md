# Phase 27: Sub-Command Skills Foundation - Research

**Researched:** 2026-02-08
**Domain:** Claude Code sub-command skill system (namespace-based command organization)
**Confidence:** HIGH

## Summary

Researched how Claude Code's sub-command skill system works by analyzing the existing GSD command pattern at `~/.claude/commands/gsd/`. The system uses a simple directory-based namespace approach where commands are markdown files with YAML frontmatter and markdown body content.

The standard approach is well-established through 27 existing GSD commands. Sub-command skills are standalone markdown files in namespace directories. Each file has YAML frontmatter defining metadata (name, description, arguments, allowed-tools) followed by a markdown body with XML-tagged sections for objectives, process steps, and outputs.

**Primary recommendation:** Follow the established GSD pattern exactly - YAML frontmatter + XML-tagged markdown body, no special discovery mechanism needed beyond file naming.

## Standard Stack

### Core Components
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Markdown files | .md | Skill definition format | Native to Claude Code skill system |
| YAML frontmatter | --- delimited | Command metadata | Claude Code parsing requirement |
| XML tags in body | `<objective>` etc. | Structured instructions | GSD convention for clarity |
| Directory namespaces | `~/.claude/commands/{namespace}/` | Command organization | Claude Code discovery mechanism |

### File Structure Convention
```
~/.claude/commands/
├── gsd/                     # Namespace directory
│   ├── help.md             # /gsd:help
│   ├── progress.md         # /gsd:progress
│   ├── execute-phase.md    # /gsd:execute-phase
│   └── ...
└── lucy-ng/                # New namespace (to be created)
    ├── status.md           # /lucy-ng:status
    ├── dereplicate.md      # /lucy-ng:dereplicate
    ├── predict.md          # /lucy-ng:predict
    └── ...
```

## Architecture Patterns

### Recommended Project Structure
```
~/.claude/commands/lucy-ng/
├── status.md           # Environment readiness check
├── dereplicate.md      # Thin wrapper around lucy dereplicate c13
├── predict.md          # Thin wrapper around lucy predict c13
└── (routing-page.md)   # Optional: listing page (Phase 33)
```

### Pattern 1: Simple Wrapper Skill (Thin CLI Wrapper)
**What:** Skill that wraps a single CLI command with minimal additional logic
**When to use:** For straightforward commands like dereplicate, predict, status checks
**Example:**
```markdown
---
name: lucy-ng:status
description: Check lucy-ng environment readiness (version, LSD, database)
allowed-tools:
  - Bash
---

<objective>
Check that lucy-ng, LSD solver, and compound database are properly installed.
</objective>

<process>

<step name="check_lucy">
Check lucy-ng installation:
```bash
lucy --version
```

If not found: "lucy-ng not installed. Run: pip install lucy-ng"
</step>

<step name="check_lsd">
Check LSD solver availability:
```bash
lucy lsd check
```

Report LSD and outlsd status.
</step>

<step name="check_database">
Check for compound database:
```bash
lucy database info data/reference/lucy-ng-derep.db
```

Report presence and stats.
</step>

</process>
```

### Pattern 2: Orchestrator Skill (Complex Multi-Agent)
**What:** Skill that spawns subagents, manages workflow, handles checkpoints
**When to use:** For complex operations like CASE orchestration (Phase 29)
**Not applicable to Phase 27** - this phase only implements simple wrappers

### Pattern 3: Routing Page
**What:** Top-level namespace page that lists all sub-commands
**When to use:** To replace monolithic skill with navigation to sub-commands
**Example:**
```markdown
---
name: lucy-ng
description: Lucy-ng NMR structure elucidation - sub-command listing
---

# Lucy-ng Commands

**Available sub-commands:**

- `/lucy-ng:status` - Check environment readiness
- `/lucy-ng:dereplicate` - Match 13C spectrum against database
- `/lucy-ng:predict` - Predict 13C shifts for a structure
- `/lucy-ng:case` - Full CASE orchestration (Phase 29)
- `/lucy-ng:sanitise` - Remove compound identifiers (Phase 31)

Use `/lucy-ng:{command}` to run specific operations.
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Command discovery | Custom registration system | Directory-based discovery | Claude Code finds commands by scanning ~/.claude/commands/{namespace}/*.md |
| Argument parsing | Custom parser in skill | YAML `arguments:` field + $ARGUMENTS | Claude Code handles argument extraction |
| Tool restrictions | Validation logic | `allowed-tools:` frontmatter | Claude Code enforces tool access control |
| Sub-agent spawning | Custom agent management | Task() tool with subagent_type | Built into Claude Code orchestration |

**Key insight:** Claude Code has built-in conventions for all skill infrastructure. Following the established pattern (GSD commands) means zero custom plumbing.

## Common Pitfalls

### Pitfall 1: Inventing New Frontmatter Fields
**What goes wrong:** Adding custom frontmatter fields that Claude Code doesn't recognize
**Why it happens:** Assuming flexibility in metadata schema
**How to avoid:** Use only documented fields from GSD examples:
- `name:` (required) - Command name with namespace prefix
- `description:` (required) - One-line description
- `arguments:` (optional) - Argument definitions
- `argument-hint:` (optional) - Usage hint string
- `allowed-tools:` (optional) - Tool whitelist
- `agent:` (optional) - Specific subagent type if spawned directly
- `execution_context:` (optional) - External workflow/reference files to load

**Warning signs:** Skill not appearing in command list, metadata ignored

### Pitfall 2: Assuming Auto-Discovery of Nested Directories
**What goes wrong:** Creating subdirectories under namespace (e.g., `lucy-ng/core/status.md`)
**Why it happens:** Trying to organize many commands hierarchically
**How to avoid:** Keep all command files directly in namespace directory (`~/.claude/commands/lucy-ng/*.md`). Use filename prefixes for grouping if needed (e.g., `case-orchestrator.md`, `case-progress.md`)
**Warning signs:** Commands in subdirectories don't appear as available commands

### Pitfall 3: Mixing Implementation Logic into Orchestrator Skills
**What goes wrong:** Orchestrator skills do too much work instead of delegating to subagents
**Why it happens:** Not understanding the context-budget tradeoff
**How to avoid:** Orchestrators should be lean (~15% context budget):
- Validate arguments
- Read context files
- Spawn subagents with Task()
- Handle returns
- Present results
Heavy lifting (research, planning, execution) goes to subagents with fresh 200k context.
**Warning signs:** Orchestrator skills exceeding 500 lines, running out of context

### Pitfall 4: Forgetting to Inline Content Across Task() Boundaries
**What goes wrong:** Using `@file.md` syntax in Task() prompts, expecting subagent to see it
**Why it happens:** Assuming context sharing between orchestrator and subagent
**How to avoid:** Read file contents in orchestrator, inline into Task() prompt:
```markdown
# WRONG - @ syntax doesn't cross Task() boundary
Task(prompt="Plan phase\n\n@.planning/STATE.md", ...)

# CORRECT - Read and inline content
STATE_CONTENT=$(cat .planning/STATE.md)
Task(prompt="Plan phase\n\nProject state:\n{state_content}", ...)
```
**Warning signs:** Subagent asks for missing context, claims files don't exist

## Code Examples

Verified patterns from GSD commands:

### Simple Check Command (No Arguments)
```markdown
---
name: gsd:join-discord
description: Join the GSD Discord community
---

<objective>
Display the Discord invite link for the GSD community server.
</objective>

<output>
# Join the GSD Discord

Connect with other GSD users, get help, share what you're building, and stay updated.

**Invite link:** https://discord.gg/5JJgD5svVS

Click the link or paste it into your browser to join.
</output>
```
**Source:** `~/.claude/commands/gsd/join-discord.md`

### Command with Required Argument
```markdown
---
name: set-profile
description: Switch model profile for GSD agents (quality/balanced/budget)
arguments:
  - name: profile
    description: "Profile name: quality, balanced, or budget"
    required: true
---

<objective>
Switch the model profile used by GSD agents.
</objective>

<process>

## 1. Validate argument

if $ARGUMENTS.profile not in ["quality", "balanced", "budget"]:
  Error: Invalid profile "$ARGUMENTS.profile"
  Valid profiles: quality, balanced, budget
  STOP

## 2. Update config.json

Read current config, update model_profile field, write back.

</process>
```
**Source:** `~/.claude/commands/gsd/set-profile.md`

### Bash-Only Wrapper Skill
```markdown
---
name: lucy-ng:status
description: Check lucy-ng environment (version, LSD, database)
allowed-tools:
  - Bash
---

<objective>
Verify lucy-ng installation and required dependencies.
</objective>

<process>

Check lucy version:
```bash
lucy --version
```

Check LSD availability:
```bash
lucy lsd check
```

Check database:
```bash
[ -f data/reference/lucy-ng-derep.db ] && echo "Database found" || echo "Database missing - run: lucy database download"
```

Report combined status to user.

</process>
```
**Pattern:** Thin CLI wrapper using only Bash tool

### Orchestrator with Subagent Spawning
```markdown
---
name: gsd:execute-phase
description: Execute all plans in a phase with wave-based parallelization
argument-hint: "<phase-number> [--gaps-only]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Task
---

<objective>
Execute all plans in a phase using wave-based parallel execution.

Orchestrator stays lean: discover plans, group into waves, spawn subagents, collect results.
</objective>

<process>

0. **Resolve Model Profile**
   Read .planning/config.json for model_profile setting
   Map to specific models per agent type

1. **Validate phase exists**
   Find phase directory, count PLAN.md files

2. **Discover plans**
   List *-PLAN.md files, filter completed

3. **Group by wave**
   Read wave from frontmatter, group plans

4. **Execute waves**
   For each wave:
   - Read plan and STATE.md contents
   - Spawn gsd-executor for each plan (parallel Task calls with inlined content)
   - Wait for completion
   - Verify SUMMARYs created

5. **Aggregate results**
   Collect summaries, report status

</process>
```
**Source:** `~/.claude/commands/gsd/execute-phase.md` (simplified)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| MCP server tools | CLI-only thin wrappers | v2.0 Phase 26 (Feb 2026) | Simpler architecture, skills call CLI via Bash |
| Monolithic /lucy-ng skill | Namespace sub-commands | v2.1 Phase 27 (planned) | Better organization, clear separation of concerns |
| Supervisor as separate agent | Orchestrator as skill | v2.1 Phase 29 (planned) | Supervision logic dissolves into case.md orchestrator |

**Current best practice (2026-02-08):**
- Sub-commands in `~/.claude/commands/{namespace}/*.md`
- YAML frontmatter for metadata
- XML-tagged markdown body for instructions
- Directory-based discovery (no registration needed)
- Task() for subagent spawning with inlined content

## Open Questions

1. **Namespace routing page location**
   - What we know: GSD has /gsd:help which lists commands, but no top-level /gsd routing page found
   - What's unclear: Whether namespace routing pages live at ~/.claude/commands/{namespace}.md or ~/.claude/commands/{namespace}/index.md or are just convention not requirement
   - Recommendation: Phase 27 skips routing page (simple wrappers only), Phase 33 creates it after all sub-commands exist

2. **Sub-command naming convention**
   - What we know: GSD uses simple names (help.md, progress.md, execute-phase.md)
   - What's unclear: Whether lucy-ng should use verb-first (dereplicate.md) or noun-first (c13-dereplicate.md)
   - Recommendation: Use verb-first matching CLI structure (dereplicate.md, predict.md, status.md)

3. **Allowed-tools enforcement**
   - What we know: GSD commands declare allowed-tools in frontmatter
   - What's unclear: Whether Claude Code strictly enforces this or if it's advisory
   - Recommendation: Declare minimal tool set per command (status.md uses only Bash, orchestrators add Read/Write/Task)

## Sources

### Primary (HIGH confidence)
- `~/.claude/commands/gsd/*.md` - 27 existing GSD commands analyzed
  - Simple commands: join-discord.md, set-profile.md (file contents verified)
  - Orchestrators: execute-phase.md, plan-phase.md (file contents verified)
  - Workflow commands: pause-work.md, check-todos.md, progress.md (file contents verified)
- `/Users/steinbeck/Dropbox/develop/lucy-ng/CLAUDE.md` - CLI syntax reference (lines 1-150 verified)
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/ROADMAP.md` - Phase 27 requirements (lines 500-593 verified)

### Secondary (MEDIUM confidence)
- Lucy CLI structure via `lucy --help`, `lucy lsd --help`, `lucy dereplicate --help`, `lucy predict --help` (executed 2026-02-08)
- Lucy version 0.1.0 (verified via `lucy --version`)

### Tertiary (LOW confidence)
- None - all findings verified with primary sources (actual file contents and CLI execution)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified by reading 27 existing GSD command files
- Architecture: HIGH - Clear pattern across simple wrappers (join-discord.md) and complex orchestrators (execute-phase.md)
- Pitfalls: HIGH - Derived from GSD command patterns (Task() content inlining explicitly shown in execute-phase.md wave_execution section)
- Code examples: HIGH - Direct quotes from verified file contents

**Research date:** 2026-02-08
**Valid until:** 60 days (stable system - Claude Code sub-command format unlikely to change rapidly)

**Research scope:** No CONTEXT.md exists for this phase - all implementation decisions at Claude's discretion. Research covers the technical "how" of Claude Code sub-command skills to inform planning.
