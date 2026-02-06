# Technology Stack: Multi-Agent CASE Architecture

**Project:** lucy-ng v2.0
**Research Date:** 2026-02-06
**Focus:** Multi-agent orchestration additions for robust CASE workflow

---

## Executive Summary

The v2.0 multi-agent architecture requires **zero additional dependencies**. All orchestration capabilities are native to Claude Code via the Task tool and subagent system. The implementation strategy is: use Claude Code's built-in orchestration primitives, implement supervision logic in the skill (CLAUDE.md), and use persistent markdown files for state management.

**Key Insight:** This is a skill architecture problem, not a library/framework problem. Claude Code already has the primitives. We need to teach the skill how to orchestrate effectively.

---

## Core Stack (Unchanged)

### Existing Validated Components

These remain unchanged from v1.2. No modifications needed for multi-agent work.

| Component | Version | Purpose | Status |
|-----------|---------|---------|--------|
| Python | 3.10+ | Runtime | Unchanged |
| Pydantic | v2 | Data models | Unchanged |
| nmrglue | Latest | Bruker NMR parsing | Unchanged |
| NumPy/SciPy | Latest | Numerical processing | Unchanged |
| RDKit | Latest | Molecular operations, HOSE codes | Unchanged |
| SQLite | 3.x | Compound database | Unchanged |
| Click | 8.x | CLI framework | Unchanged |
| FastMCP | Latest | MCP server | Unchanged |
| pytest | Latest | Testing | Unchanged |
| ruff | Latest | Linting | Unchanged |
| mypy | Latest | Type checking | Unchanged |

**Rationale:** The existing stack is thin tool wrappers. Multi-agent orchestration happens at the Claude Code level, not in Python code.

---

## Multi-Agent Orchestration: Native Claude Code

### Claude Code Task Tool (Built-in)

**What it is:** Claude Code's native subagent spawning and coordination system. Available out-of-the-box with no additional setup.

**Key capabilities:**
- Spawn subagents with custom prompts and tool access
- Run subagents in foreground (blocking) or background (concurrent)
- Isolate context (subagent context separate from main conversation)
- Auto-compaction when context fills (same as main conversation)
- Resume previous subagents with full conversation history

**How to use:**
```markdown
# In main conversation (implicit):
"Use a subagent to explore the HMBC correlations and report which look suspicious"

# Claude spawns subagent, waits for completion, receives summary
```

**Background execution:**
```markdown
# For long-running tasks:
"Use a background subagent to run LSD with these constraints"

# Claude spawns subagent, continues main conversation
# Background subagent completes independently, results available later
```

**Limitations:**
- Subagents cannot spawn other subagents (no nesting)
- MCP tools not available in background subagents
- Background subagents auto-deny permission prompts not pre-approved

**References:**
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [The Task Tool: Claude Code's Agent Orchestration System](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2)

### Subagent Configuration (Markdown Files)

**Format:** YAML frontmatter + Markdown system prompt

**Example subagent definition** (.claude/agents/hmbc-validator.md):
```yaml
---
name: hmbc-validator
description: Validates HMBC correlations and flags suspicious peaks. Use proactively when LSD produces too many solutions.
tools: Read, Grep, Bash
model: sonnet
permissionMode: acceptEdits
---

You are an HMBC correlation validator. Your job:
1. Read picked HMBC peaks from analysis folder
2. Check for common artifacts (t1 noise, 1J bleeding)
3. Flag suspicious correlations based on:
   - Carbon shift in typical quaternary range but no DEPT confirmation
   - Proton shift doesn't match any HSQC peak
   - Correlation count dramatically higher than expected

Report findings as structured output.
```

**Locations:**
- `.claude/agents/` - Project-specific (version controlled)
- `~/.claude/agents/` - User-global (all projects)
- `--agents` CLI flag - Session-only (testing)

**Why this matters:** Subagents are defined as files, not code. The skill instructs Claude when to use them. No Python orchestration framework needed.

### Agent Teams (Experimental, Available Now)

**Status:** Officially launched Feb 2026 with Claude Opus 4.6. Enable with:
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**What it is:** Multiple independent Claude Code sessions working on same task list, communicating via shared file system.

**Key capabilities:**
- Multiple agents with independent context windows
- Shared task list (TaskCreate, TaskUpdate, TaskList)
- Direct messaging between agents (write, broadcast)
- Graceful shutdown protocol (requestShutdown, approveShutdown)

**When to use:**
- CASE tasks requiring sustained parallelism (e.g., exploring multiple HMBC interpretation strategies)
- Tasks exceeding single context window
- True concurrent exploration (multiple hypothesis paths)

**When NOT to use:**
- Simple linear CASE workflows (subagents sufficient)
- Tasks requiring tight coordination (subagent chaining better)
- Initial v2.0 implementation (defer to future milestone)

**Recommendation for v2.0:** Start with subagents. Agent teams are more complex and may be overkill for initial supervisor pattern.

**References:**
- [Claude Code's Hidden Multi-Agent System](https://paddo.dev/blog/claude-code-hidden-swarm/)
- [Claude Code Swarm Orchestration Skill](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea)

---

## Orchestration Patterns for CASE

### Pattern 1: Supervisor + Worker (Recommended for v2.0)

**Architecture:**
```
Main Conversation (Supervisor)
  ├─> Spawns: CASE Agent (subagent)
  │     └─> Executes CASE workflow
  │     └─> Reports progress via markdown files
  ├─> Monitors: analysis/progress.md
  └─> Intervenes: When loop detected
```

**How it works:**
1. Main conversation spawns CASE subagent with full CASE skill loaded
2. CASE subagent writes progress to `analysis/progress.md` after each major step
3. Main conversation monitors progress file (or receives summary when subagent completes)
4. If CASE subagent is stuck (detected via progress indicators), main conversation terminates and respawns with modified constraints

**Implementation:** Pure skill-based. No code changes needed.

**Skill structure:**
```markdown
# In CLAUDE.md (main conversation):
## Supervisor Responsibilities
When user requests CASE:
1. Spawn CASE subagent with analysis folder path
2. Monitor progress indicators
3. Detect loops:
   - Three consecutive LSD attempts with ELIM adjustments
   - Repeated sp2 count errors
   - Same constraint added/removed multiple times
4. Intervene: Terminate subagent, provide redirect instructions, respawn

# In .claude/agents/case-worker.md:
[Full CASE workflow from current CLAUDE.md]
Write progress.md after each step.
```

**Why this works:**
- Subagent isolation prevents supervisor context pollution
- Progress file provides clear signal for loop detection
- Resume capability allows continuation if interrupted
- No nesting issues (supervisor doesn't spawn other supervisors)

### Pattern 2: Sequential Specialists

**Architecture:**
```
Main Conversation
  ├─> Subagent: Dereplication specialist
  │     └─> Returns: Match status + confidence
  ├─> Subagent: Peak picking specialist (if no match)
  │     └─> Returns: Picked correlations summary
  ├─> Subagent: LSD constraint builder
  │     └─> Returns: Generated LSD file
  └─> Subagent: Solution ranker
        └─> Returns: Top candidates
```

**When to use:** When CASE workflow is divided into independent, non-iterative phases.

**Trade-offs:**
- Pro: Clean separation of concerns
- Pro: Each specialist can have domain-specific tool restrictions
- Con: More overhead than single CASE agent
- Con: Context doesn't flow between specialists (must use files)

**Recommendation:** Defer to future milestone. Single supervised CASE agent simpler for v2.0.

### Pattern 3: Parallel Hypothesis Exploration

**Architecture:**
```
Main Conversation
  ├─> Background Subagent A: Assume symmetry explanation X
  ├─> Background Subagent B: Assume symmetry explanation Y
  └─> Synthesize results when both complete
```

**When to use:** When multiple viable interpretations exist and exploring them sequentially is too slow.

**Requirements:**
- Background execution (blocks main conversation otherwise)
- Clear hypothesis separation (agents don't overlap)
- Pre-approved tool permissions (background agents auto-deny new prompts)

**Recommendation:** Defer to future milestone. Loop prevention is higher priority than parallel exploration.

---

## Loop Detection Strategy (Skill-Based)

### Detection Signals

The supervisor detects loops by monitoring these indicators in `analysis/progress.md`:

| Signal | Indicates Loop | Threshold |
|--------|---------------|-----------|
| Repeated ELIM adjustments | Constraint thrashing | 3+ consecutive ELIM changes |
| sp2 count corrections | Misunderstanding hybridization | Same atom corrected 2+ times |
| Same HMBC added/removed | Uncertainty about correlation validity | 2+ toggles of same correlation |
| No LSD solutions despite valid constraints | Over-constraining | 3+ attempts with correct sp2/H counts |
| Thousands of solutions despite constraints | Under-constraining | 2+ attempts with >1000 solutions |

### Intervention Actions

When loop detected, supervisor:
1. Terminates CASE subagent
2. Analyzes progress file to identify root cause
3. Provides specific redirect (not generic "try again")
4. Spawns fresh CASE subagent with corrected instructions

**Example intervention:**
```markdown
Loop detected: Three ELIM adjustments without progress.

Root cause: Uncertain which HMBC correlations are artifacts.

Redirect: Instead of adjusting ELIM, use hmbc-validator subagent to
identify suspicious correlations. Remove them from constraints file,
then retry LSD without ELIM.
```

### Progress File Format

**Location:** `analysis/progress.md`

**Structure:**
```markdown
# CASE Progress

## Dereplication
Status: Complete
Result: No match (score < 0.50)

## Peak Picking
Status: Complete
- 13C: 11 peaks
- HSQC: 11 correlations (all carbons matched)
- HMBC: 47 validated correlations

## Symmetry Analysis
Status: Complete
Expected: 13 carbons
Observed: 11 carbons
Symmetry: Likely (2 equivalent positions)

## LSD Generation
Status: Complete
File: analysis/compound.lsd
sp2 count: 8 (even ✓)
H count: 18 (matches formula ✓)

## LSD Execution
Attempt: 1
Status: 0 solutions
Issue: Likely over-constrained (sp2 and H counts correct)
Next: Reviewing HMBC correlations for artifacts

## LSD Execution
Attempt: 2
Status: 0 solutions
Change: Added ELIM 1 0
Issue: Still 0 solutions
Next: Will try ELIM 2 0

## LSD Execution
Attempt: 3
Status: 0 solutions
Change: ELIM 2 0
Issue: Still 0 solutions

[SUPERVISOR WOULD DETECT LOOP HERE]
```

**Why this works:** Structured progress log makes loop detection straightforward. Supervisor can pattern-match on repeated attempt types.

---

## State Management (File-Based)

### Persistent State Pattern

**Problem:** Subagents have independent context. Shared state must be external.

**Solution:** Use markdown files in `analysis/` folder as shared state.

| File | Purpose | Writer | Reader |
|------|---------|--------|--------|
| progress.md | Workflow state | CASE subagent | Supervisor |
| constraints.md | Current LSD constraints | CASE subagent | CASE subagent (resume) |
| findings.md | Interim discoveries | CASE subagent | Supervisor, user |
| hypothesis.md | Current structural hypothesis | CASE subagent | Supervisor |

**Pattern inspired by:**
- [Manus workflow](https://github.com/travisvn/awesome-claude-skills) - Uses task_plan.md, findings.md for multi-step tasks
- Scientific best practice - "Write lots of files" for AI context management

**Skill instructions:**
```markdown
After each major step, update progress.md with:
- Step name
- Status (Complete/In Progress/Failed)
- Key outputs
- Any issues encountered
- Next planned step

This allows the supervisor to monitor your progress and intervene if needed.
```

---

## What NOT to Add

### ❌ Multi-Agent Frameworks (LangGraph, CrewAI, etc.)

**Why not:**
- Claude Code Task tool provides orchestration natively
- External frameworks add complexity without benefit
- Frameworks assume API-based LLM calls; Claude Code uses different model
- Skill-based orchestration is more maintainable

**Exception:** None. Native Claude Code capabilities are sufficient.

### ❌ Message Queue Systems (RabbitMQ, Redis, etc.)

**Why not:**
- File-based state management sufficient for CASE workflows
- Adds deployment complexity
- Subagents communicate via files; no need for message passing
- CASE is not real-time; latency tolerance is high

**Exception:** None for v2.0. Future distributed deployment might reconsider.

### ❌ Workflow Engines (Airflow, Prefect, etc.)

**Why not:**
- CASE workflow is dynamic, not static DAG
- AI agent decides next steps based on results
- Workflow engines assume predefined task graph
- Supervisor + subagent pattern handles dynamic routing

**Exception:** None. Skill-based control flow is more flexible.

### ❌ Agent Monitoring Platforms (LangSmith, Helicone, etc.)

**Why not:**
- Progress file provides observability for CASE workflow
- External platforms assume API-based LLM calls
- Adds vendor dependency
- Transcript files (`~/.claude/projects/{project}/{sessionId}/subagents/`) already provide full history

**Exception:** Consider for production deployment with analytics requirements (future milestone).

---

## Loop Control Patterns (from AI SDK research)

### Applicable Patterns

These patterns from [AI SDK loop control docs](https://ai-sdk.dev/docs/agents/loop-control) apply to CASE skill design:

**1. Step Count Limits**
```markdown
# In skill:
Maximum LSD attempts: 5
After 5 attempts without progress, request supervisor intervention
```

**2. Done Tool Pattern**
```markdown
# Teach skill to recognize completion:
- 1-10 solutions with good MAE scores → DONE
- Dereplication match >0.85 → DONE
- 5 LSD attempts without solutions → STUCK (escalate)
```

**3. Custom Loop Conditions**
```markdown
# Skill should monitor:
- "Output hasn't changed in 3 iterations" → STUCK
- "Same error message 2+ times" → STUCK
- "Step count exceeded without calling done tool" → STUCK
```

### Not Applicable (API-Based Patterns)

These patterns assume direct API control over LLM calls. Not applicable to Claude Code:
- `prepareStep` callbacks - No code access to step lifecycle
- Dynamic model switching - Model set in subagent config
- Message transformation - Handled by Claude Code compaction

**Alternative:** Encode similar logic in skill instructions.

---

## Error Tolerance (Skill Knowledge, Not Code)

### Philosophy Shift for v2.0

**v1.x approach:**
```python
# Python code handles ambiguity
def check_close_shifts(shifts):
    for i, s1 in enumerate(shifts):
        for j, s2 in enumerate(shifts[i+1:]):
            if abs(s1 - s2) < 0.3:
                return "WARNING: Close shifts detected"
```

**v2.0 approach:**
```markdown
# Skill teaches AI to recognize:
## Close Shift Detection

When analyzing 13C spectra, check for peaks within 0.3 ppm:
- Expected: Molecular symmetry causes exact overlaps
- Warning: Close but not identical peaks (0.1-0.5 ppm apart)
  - May indicate impurity
  - May indicate temperature-dependent equilibrium
  - Should not be treated as separate carbons

If close shifts detected:
1. Verify with DEPT (do both have same multiplicity?)
2. Check HSQC (do intensities match expected multiplicity?)
3. Document ambiguity in findings.md
4. For LSD constraints, use peak position average
```

**Why this works:**
- AI can reason about ambiguity, not just detect it
- Handles novel cases not in training data
- Easier to maintain (edit markdown, not Python)
- Agent can explain reasoning to user

### Error Patterns to Encode in Skill

| Error Type | Current Python Handling | v2.0 Skill Handling |
|------------|------------------------|---------------------|
| Close shifts | Numeric threshold check | Teach reasoning about symmetry vs impurity |
| DEPT phase ambiguity | Hard-coded heuristics | Teach spectroscopic interpretation |
| HMBC artifacts | Guided picker filters | Teach t1 noise / 1J bleeding patterns |
| sp2 count parity | Python validation | Teach hybridization chemistry |
| Missing DEPT | Fallback to manual | Teach APT interpretation alternative |

**Implementation:** Expand CLAUDE.md sections with deeper domain knowledge. Strip validation from Python CLI tools.

---

## Integration Points

### Existing Architecture (Unchanged)

```
User Input
   ↓
Claude Code (with lucy-ng skill)
   ↓
MCP Server (fastmcp)
   ↓
Lucy CLI (Click)
   ↓
Core Library (Pydantic models, nmrglue, RDKit)
   ↓
External Tools (LSD solver)
```

### v2.0 Multi-Agent Architecture

```
User Input
   ↓
Claude Code Main Session (Supervisor)
   ↓
Spawn Subagent: CASE Worker
   │
   ├─> MCP Server (fastmcp)
   ├─> Lucy CLI (Click)
   ├─> Core Library
   ├─> External Tools
   │
   └─> Writes: analysis/progress.md

Main Session Monitors: analysis/progress.md
Main Session Intervenes: If loop detected
```

**Key insight:** The multi-agent architecture sits ABOVE the existing stack. No changes to MCP/CLI/Library layers needed.

---

## Skill Structure for v2.0

### File Organization

```
CLAUDE.md (main skill)
   ├─ Setup instructions (unchanged)
   ├─ Supervisor responsibilities (NEW)
   │   ├─ When to spawn CASE subagent
   │   ├─ How to monitor progress
   │   └─ Loop detection patterns
   ├─ CASE workflow (moved to subagent)
   └─ Domain knowledge (expanded)

.claude/agents/case-worker.md (NEW)
   ├─ Full CASE workflow
   ├─ Progress reporting requirements
   └─ Error handling patterns

.claude/agents/hmbc-validator.md (NEW)
   ├─ Artifact detection logic
   └─ Correlation filtering

.claude/agents/constraint-builder.md (OPTIONAL)
   ├─ LSD file generation
   └─ Heteroatom constraint strategies
```

### Skill Loading Strategy

**Main conversation:** Loads CLAUDE.md (supervisor role + domain knowledge)
**CASE subagent:** Loads case-worker.md (includes relevant sections from CLAUDE.md via skills field)

**Example case-worker.md frontmatter:**
```yaml
---
name: case-worker
description: Executes full CASE workflow from dereplication through solution ranking. Use when user requests structure elucidation.
tools: Read, Write, Bash, Grep, Glob
model: inherit
skills:
  - lucy-ng  # Loads domain knowledge from CLAUDE.md
---

You are a CASE workflow executor. Follow the workflow in the lucy-ng skill,
writing progress to analysis/progress.md after each major step.

If you encounter an unrecoverable error or get stuck, clearly document the
issue in progress.md so the supervisor can intervene.
```

**Why this works:** Domain knowledge (NMR interpretation, LSD rules, etc.) lives in main CLAUDE.md. CASE workflow and progress reporting live in case-worker.md. Subagent gets both via skills preload.

---

## Development Workflow

### Testing Multi-Agent Patterns

**1. Subagent creation:**
```bash
# Use Claude Code /agents command:
/agents

# Or manually create:
mkdir -p .claude/agents
cat > .claude/agents/case-worker.md << 'EOF'
---
name: case-worker
description: Test CASE subagent
tools: Bash, Read, Write
---
You are a test CASE worker.
EOF
```

**2. Supervisor testing:**
```markdown
# In main conversation:
"Spawn the case-worker subagent and have it analyze the test dataset"

# Claude spawns subagent, waits for completion
# Check: ~/.claude/projects/{project}/{session}/subagents/agent-{id}.jsonl
```

**3. Loop detection testing:**
```markdown
# Manually create progress.md with loop pattern:
cat > analysis/progress.md << 'EOF'
## LSD Attempt 1
Status: 0 solutions
Change: None

## LSD Attempt 2
Status: 0 solutions
Change: Added ELIM 1 0

## LSD Attempt 3
Status: 0 solutions
Change: ELIM 2 0
EOF

# Ask supervisor to analyze:
"Review analysis/progress.md and determine if the CASE agent is stuck in a loop"
```

### Debugging Subagent Issues

**Transcript inspection:**
```bash
# Find subagent transcript:
ls -la ~/.claude/projects/$(basename $PWD)/*/subagents/

# View full conversation:
cat ~/.claude/projects/$(basename $PWD)/latest/subagents/agent-abc123.jsonl | jq
```

**Progress monitoring:**
```bash
# Watch progress file during execution:
tail -f analysis/progress.md
```

**Subagent resume:**
```markdown
# If subagent interrupted:
"Resume the previous case-worker subagent and continue from where it stopped"

# Claude loads full conversation history from transcript
```

---

## Confidence Assessment

| Component | Confidence | Evidence |
|-----------|------------|----------|
| Task tool availability | HIGH | Official docs, Jan 2026 release |
| Subagent configuration | HIGH | Official docs with examples |
| File-based state management | HIGH | Common pattern in agent workflows |
| Loop detection via progress files | MEDIUM | Pattern exists, needs validation in CASE domain |
| Skill-based orchestration | MEDIUM | Novel approach, less precedent |
| Agent Teams (defer to future) | LOW | Experimental, may be overkill |

**Overall confidence:** MEDIUM-HIGH. The primitives exist and are well-documented. The CASE-specific application needs validation.

---

## Risks and Mitigations

### Risk 1: Subagent Context Overflow

**Problem:** CASE subagent context fills with verbose tool outputs (HMBC correlations, LSD attempts).

**Mitigation:**
- Claude Code auto-compaction at ~95% capacity
- Subagent writes summaries to progress file (persistent)
- Supervisor can resume with compressed history

**Fallback:** If single subagent can't complete, supervisor breaks into sequential specialists.

### Risk 2: Loop Detection False Positives

**Problem:** Supervisor terminates subagent during legitimate exploration.

**Mitigation:**
- Clear thresholds (3+ identical attempts, not 2)
- Require multiple signals before intervention
- Subagent can document "exploring alternatives" to suppress intervention

**Fallback:** User can override supervisor and direct CASE agent explicitly.

### Risk 3: Skill Complexity

**Problem:** CLAUDE.md becomes too large, overwhelming context.

**Mitigation:**
- Split into main skill (CLAUDE.md) + specialist subagent files
- Use skills preload to inject only relevant sections
- Compress reference tables (shift ranges, error codes) into concise format

**Fallback:** Break into multiple skills (lucy-ng:supervisor, lucy-ng:case, lucy-ng:validation).

---

## Migration Path from v1.2

### Phase 1: File-Based State (No Multi-Agent Yet)

**Goal:** Teach current CASE skill to write progress files.

**Changes:**
- Add progress.md writing instructions to CLAUDE.md
- No subagents yet
- Single-agent workflow with better observability

**Validation:** Can user inspect progress.md and understand CASE state?

### Phase 2: Supervisor + Single Subagent

**Goal:** Split supervisor and CASE worker.

**Changes:**
- Create case-worker.md subagent definition
- Update CLAUDE.md with supervisor responsibilities
- Test subagent spawning and monitoring

**Validation:** Does supervisor correctly spawn CASE subagent?

### Phase 3: Loop Detection and Intervention

**Goal:** Supervisor detects and breaks loops.

**Changes:**
- Add loop detection patterns to supervisor skill
- Test with known loop scenarios (repeated ELIM, sp2 errors)
- Validate intervention messages are helpful

**Validation:** Does supervisor prevent unproductive loops?

### Phase 4: Specialist Subagents (Optional)

**Goal:** Add hmbc-validator, constraint-builder specialists.

**Changes:**
- Create specialist subagent definitions
- Update CASE worker to spawn specialists when needed
- Test specialist isolation and reporting

**Validation:** Do specialists improve CASE success rate?

---

## Future Enhancements (Post-v2.0)

### Agent Teams for Parallel Hypothesis

**When:** After supervisor pattern validated.

**Why:** Explore multiple symmetry interpretations simultaneously.

**Requirements:**
- Shared task list configuration
- Hypothesis serialization format
- Synthesis strategy for conflicting results

### Persistent Memory for Domain Learning

**When:** After multi-agent CASE validated.

**Why:** CASE agent learns compound class patterns across sessions.

**Implementation:**
```yaml
# In case-worker.md:
memory: user  # ~/.claude/agent-memory/case-worker/
```

**Learning targets:**
- Common aromatic substitution patterns
- Heteroatom constraint strategies by formula type
- Artifact recognition patterns

### MCP Tool Simplification

**When:** After skill proves it can handle complexity.

**Why:** Existing MCP tools do too much (validation, heuristics). Strip to pure I/O.

**Example:**
```python
# Current (v1.2):
@mcp.tool()
def pick_hmbc_peaks(...):
    # Validation, filtering, heuristics
    # Returns: validated_peaks, rejected_peaks, warnings

# Future (v3.0):
@mcp.tool()
def read_hmbc_spectrum(...):
    # Pure reading, no interpretation
    # Returns: raw_peak_list
```

---

## Recommended Stack for v2.0

### Add

**Nothing.** All capabilities are native to Claude Code.

### Modify

**CLAUDE.md skill structure:**
- Split supervisor and CASE worker responsibilities
- Add progress file format specification
- Add loop detection patterns
- Expand error tolerance knowledge

**New files:**
- `.claude/agents/case-worker.md` - Main CASE workflow subagent
- `.claude/agents/hmbc-validator.md` - Optional specialist
- `analysis/progress.md` - Generated during CASE execution

### Remove

**Future consideration (not v2.0):**
- Intelligence from CLI tools (after skill proves capable)
- Validation heuristics from Python (teach skill instead)

---

## Key Takeaways

1. **Zero additional dependencies** - Claude Code Task tool provides all orchestration primitives
2. **Skill-based architecture** - Orchestration logic in markdown, not Python
3. **File-based state** - progress.md and similar files enable supervisor monitoring
4. **Subagents for isolation** - CASE worker context separate from supervisor
5. **Loop detection via patterns** - Monitor progress indicators, not tool call sequences
6. **Progressive enhancement** - Start simple (single subagent), add specialists later
7. **Agent Teams deferred** - Complexity not justified for v2.0 needs

**Bottom line:** This is a skill engineering problem. The stack is already complete.

---

## Sources

### Official Documentation
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Agent loop control - AI SDK](https://ai-sdk.dev/docs/agents/loop-control)

### Multi-Agent Orchestration
- [Claude Code Swarm Orchestration Skill](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea)
- [Claude Code's Hidden Multi-Agent System](https://paddo.dev/blog/claude-code-hidden-swarm/)
- [The Task Tool: Claude Code's Agent Orchestration System](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2)
- [Shipyard | Multi-agent orchestration for Claude Code in 2026](https://shipyard.build/blog/claude-code-multi-agent/)

### Agent Patterns and Loop Detection
- [Ralph Wiggum AI Agents: The Coding Loop of 2026](https://www.leanware.co/insights/ralph-wiggum-ai-coding)
- [Our Agent Had A 4 Minute Loop. Here's How We Fixed It.](https://medium.com/data-science-collective/our-agent-had-a-4-minute-loop-heres-how-we-fixed-it-40a8142ef1a9)
- [Agents At Work: The 2026 Playbook for Building Reliable Agentic Workflows](https://promptengineering.org/agents-at-work-the-2026-playbook-for-building-reliable-agentic-workflows/)

### Skills and Prompt Engineering
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [awesome-claude-skills - GitHub](https://github.com/travisvn/awesome-claude-skills)
- [Claude Code for Scientists](https://www.neuroai.science/p/claude-code-for-scientists)

### Background Tasks and Coordination
- [Claude Code Tasks: Complete Guide to AI Agent Workflow](https://www.dplooy.com/blog/claude-code-tasks-complete-guide-to-ai-agent-workflow)
- [Claude Code's 'Tasks' update lets agents work longer and coordinate across sessions](https://venturebeat.com/orchestration/claude-codes-tasks-update-lets-agents-work-longer-and-coordinate-across)
