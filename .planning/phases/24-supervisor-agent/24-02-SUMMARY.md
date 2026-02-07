---
phase: 24-supervisor-agent
plan: 02
subsystem: ai-supervision
tags: [supervisor, agent-definition, claude-code, subagent, multi-agent]
requires:
  - 24-01-PLAN.md  # Supervisor skill expanded (678 lines) with complete domain knowledge
  - 21-02-PLAN.md  # skill/supervisor/SKILL.md foundation (78 lines)
  - 23-02-PLAN.md  # Confidence scoring framework for convergence assessment
provides:
  - Supervisor agent definition (.claude/agents/supervisor.md, 383 lines)
  - Production-ready Claude Code subagent for lucy-ng orchestration
  - Single entry point for all lucy-ng invocations
affects:
  - 25-*-PLAN.md   # Diagnostic specialist will integrate with this supervisor
  - 26-*-PLAN.md   # MCP refactoring will use supervisor as entry point
tech-stack:
  added: []
  patterns:
    - Claude Code subagent with YAML frontmatter
    - Task tool for spawning specialist agents
    - Markdown-based progress monitoring (CASE-PROGRESS.md)
key-files:
  created:
    - .claude/agents/supervisor.md  # Supervisor agent definition (383 lines)
  modified: []
decisions:
  - decision: "Supervisor as Claude Code subagent (not Python/MCP tool)"
    rationale: "Claude Code's Task tool enables true multi-agent architecture with subagent spawning"
    location: ".claude/agents/supervisor.md frontmatter"
  - decision: "Tools: Task, Read, Write, Bash, Glob, Grep (no MCP tools)"
    rationale: "Supervisor orchestrates via Task and Bash CLI, doesn't need direct MCP access"
    location: ".claude/agents/supervisor.md YAML frontmatter"
  - decision: "Model: sonnet (not opus)"
    rationale: "Supervisor is orchestration logic, not complex NMR analysis; sonnet is sufficient"
    location: ".claude/agents/supervisor.md YAML frontmatter"
  - decision: "System prompt: 383 lines with summaries and cross-references"
    rationale: "Comprehensive enough for autonomous operation, concise enough via references to skill docs"
    location: ".claude/agents/supervisor.md body"
metrics:
  duration: "2m 10s"
  completed: "2026-02-07"
---

# Phase 24 Plan 02: Supervisor Agent Definition Summary

**One-liner:** Created production-ready supervisor agent as Claude Code subagent (.claude/agents/supervisor.md, 383 lines) with YAML frontmatter, complete routing logic, CASE spawning via Task tool, loop detection summaries, advisory intervention procedures, and 10-cycle escalation protocol.

---

## What Was Built

### 1. Supervisor Agent Definition (.claude/agents/supervisor.md)

A complete Claude Code subagent definition with:

**YAML Frontmatter:**
- `name: lucy-supervisor`
- `description:` Full orchestration role and capabilities (82 words)
- `tools:` Task, Read, Write, Bash, Glob, Grep
- `model: sonnet`

**System Prompt (383 lines total):**

1. **Identity and Role** (17 lines)
   - Single entry point for all lucy-ng invocations
   - Orchestrator, not executor
   - Domain knowledge references (skill/SKILL.md, skill/supervisor/SKILL.md)

2. **Workflow Routing** (31 lines)
   - Decision tree for sanitize/dereplication/CASE
   - Default: try dereplication first
   - Bash CLI for sync operations, Task tool for async CASE

3. **Spawning the CASE Agent** (37 lines)
   - Complete Task tool invocation template
   - Progress reporting instructions
   - CASE-PROGRESS.md format requirements
   - Incremental HMBC strategy reference
   - Stopping criteria (<=10 solutions or ~20 iterations)

4. **Monitoring CASE Progress** (21 lines)
   - Read CASE-PROGRESS.md workflow
   - Loop detection check procedure
   - Intervention decision logic
   - Per-pattern counter tracking

5. **Loop Detection Patterns** (107 lines)
   - Quick reference table (4 patterns × 2 columns)
   - ELIM thrashing advisory example
   - Zero-solution loop advisory example
   - Solution explosion advisory example
   - Constraint churning advisory example

6. **Convergence Criteria** (52 lines)
   - Solution count trends
   - Constraint effectiveness thresholds
   - Flexible success targets
   - Hard safety cap (~20 iterations)
   - Plateau handling strategies

7. **Intervention Tracking and Escalation** (60 lines)
   - Per-pattern tracking (count_elim, count_zero, count_explosion, count_churning)
   - Intervention cycle procedure
   - Escalation report format template
   - Non-pattern escalation triggers

8. **Important Rules** (17 lines)
   - Never perform CASE yourself
   - Never give directive instructions
   - Never skip diagnosis
   - Track per pattern
   - CASE agent writes progress, supervisor reads
   - Reference skill docs

9. **CASE-PROGRESS.md Format** (25 lines)
   - Format: markdown, structured sections
   - Location: compound directory
   - Rule: append-only
   - Required fields summary
   - Reference to complete specification in skill/supervisor/SKILL.md Section 7

10. **Summary** (16 lines)
    - 9-step orchestration workflow recap
    - Domain knowledge references

---

## Supervisor Agent Structure

```yaml
---
name: lucy-supervisor
description: Orchestrates all lucy-ng workflows...
tools: [Task, Read, Write, Bash, Glob, Grep]
model: sonnet
---

# System prompt (383 lines)
- Your Role (orchestrator and supervisor)
- Domain Knowledge References
- Workflow Routing (decision tree)
- Spawning the CASE Agent (Task tool)
- Monitoring CASE Progress
- Loop Detection Patterns (4 patterns with advisories)
- Convergence Criteria
- Intervention Tracking and Escalation
- Important Rules
- CASE-PROGRESS.md Format
- Summary
```

---

## Cross-References

The supervisor agent properly delegates detailed knowledge to skill documents:

| Agent Section | References |
|--------------|-----------|
| Domain knowledge | skill/SKILL.md (9 refs), skill/supervisor/SKILL.md (6 refs) |
| Loop detection patterns | skill/supervisor/SKILL.md Section 4 |
| CASE-PROGRESS.md format | skill/supervisor/SKILL.md Section 7 |
| Incremental HMBC strategy | skill/SKILL.md Section 7 |
| 13C prediction ranking | skill/SKILL.md Section 8 |
| Confidence scoring | skill/SKILL.md Section 11 |
| Hybridization rules | skill/SKILL.md Section 5.3 |
| 1J artifact detection | skill/SKILL.md Section 2.3 |
| Digital resolution | skill/SKILL.md Section 2.2 |
| Quaternary carbon handling | skill/SKILL.md Section 10.3 |
| Ambiguity encoding (LIST/PROP) | skill/SKILL.md Section 10.2 |

**Total cross-references:** 15 (verified via grep).

**Zero duplication** — agent focuses on orchestration; skill documents contain methodology.

---

## SUPV Requirements Coverage

All SUPV requirements from Phase 24 context are addressed:

| Requirement | Implementation |
|------------|---------------|
| **SUPV-01** | Agent file exists at .claude/agents/supervisor.md with YAML frontmatter |
| **SUPV-02** | ELIM thrashing pattern summarized with detection criteria and advisory |
| **SUPV-03** | Zero-solution loop pattern summarized with detection criteria and advisory |
| **SUPV-04** | Solution explosion pattern summarized with detection criteria and advisory |
| **SUPV-05** | Constraint churning pattern summarized with detection criteria and advisory |
| **SUPV-06** | Advisory intervention model documented: WHAT to fix, not HOW |
| **SUPV-07** | Escalation after 10 failed intervention cycles per pattern |

---

## Advisory Intervention Examples

The agent includes four complete advisory message templates showing the advisory model (WHAT to fix, not HOW):

**ELIM thrashing:**
- Verify sp2 count is even
- Verify hydrogen budget matches formula
- Check for 1J artifacts
- Check for close carbons
- "Do NOT add ELIM again until all checks pass"

**Zero-solution loop:**
- Remove last HMBC batch
- Confirm solutions return
- Test each correlation individually
- Check for close carbons (within 3 ppm)
- Check for 1J artifacts

**Solution explosion:**
- Remove ELIM if present
- Verify correlations connect NEW fragments
- Add heteroatom constraints (BOND or LIST/PROP)
- Check quaternary carbons, add shift constraints

**Constraint churning:**
- Reset to last known-good state
- Follow incremental HMBC strategy
- Select 3-5 high-confidence correlations per batch
- Use criteria: isolated carbons, unique protons, strong intensity
- "Do NOT add/remove randomly. Be systematic."

---

## Tools Configuration

**Included tools:**
- **Task:** Spawn CASE agent and other specialists
- **Read:** Read CASE-PROGRESS.md, experiment data
- **Write:** Write escalation reports (not CASE-PROGRESS.md — that's CASE agent's job)
- **Bash:** Execute CLI commands (lucy dereplicate, lucy sanitize, lucy lsd)
- **Glob:** Find experiments, locate files
- **Grep:** Search progress logs for patterns

**NOT included:**
- MCP tools (supervisor orchestrates via Bash CLI and spawned agents, doesn't need direct MCP access)

**Model:**
- `sonnet` (orchestration logic, not complex NMR analysis; sonnet sufficient)

---

## Routing Decision Tree

The supervisor implements this default workflow:

```
1. Check if blind CASE evaluation (public data)
   YES -> lucy sanitize, then fresh session
   NO  -> Continue

2. Check if dereplication first (default: YES)
   YES -> lucy dereplicate c13
          Match >= 0.95? -> Report, DONE
          Match 0.65-0.85? -> Report, ask user
          Match < 0.50? -> Proceed to CASE
   NO (user skip) -> Proceed to CASE

3. Full CASE workflow
   Spawn CASE agent via Task tool
   Monitor CASE-PROGRESS.md
   Detect loops, diagnose, intervene
   Escalate after 10 cycles or data conflicts
```

---

## Convergence and Safety

**Solution count trends:**
- Baseline: hundreds to thousands
- After batch 1: tens to low hundreds
- After batch 2-3: single digits to low tens
- Final: 1-10 solutions

**Constraint effectiveness:**
- Effective: >= 30% reduction
- Marginally effective: 10-30%
- Ineffective: < 10%
- Over-constrained: 0 solutions

**Success targets:**
- Ideal: 1-5 solutions, high confidence (MAE < 2.0)
- Acceptable: <10 solutions, good differentiation (MAE spread > 1.0)
- Conditional: 10-20 if MAE gap >= 2 ppm

**Safety cap:** ~20 total LSD iterations maximum

---

## Escalation Triggers

**Per-pattern (after 10 cycles):**
- ELIM thrashing × 10
- Zero-solution loop × 10
- Solution explosion × 10
- Constraint churning × 10

**Immediate (no iteration):**
- Conflicting data between experiments
- Unusual chemical shifts outside normal ranges
- Molecular formula mismatch with observed data

**Escalation report includes:**
- Pattern detected
- Diagnostics attempted
- Current state (solution count, HMBC used, iterations)
- Supervisor recommendation

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Commits

| Commit | Message | Files |
|--------|---------|-------|
| f486e49 | feat(24-02): create supervisor agent definition | .claude/agents/supervisor.md |

---

## Next Phase Readiness

**Phase 24 complete:**
- Plan 01: Supervisor skill expanded (678 lines) ✓
- Plan 02: Supervisor agent defined (383 lines) ✓

**Phase 25 (Diagnostic Specialist)** is ready:
- Supervisor agent exists as entry point
- Basic diagnostic procedures documented in supervisor skill
- Clear delegation points for specialist integration
- Intervention cycle established for specialist collaboration

**Phase 26 (MCP Refactoring)** foundation ready:
- Supervisor uses Task tool (works with any MCP tool set)
- CASE agent spawned as general-purpose agent (can use new MCP tools)
- No hard dependency on current MCP tool structure

---

## Lessons Learned

### What Worked Well

1. **YAML frontmatter approach** — Clean separation of metadata and system prompt
2. **Cross-referencing strategy** — 15 references prevented 600+ lines of duplication
3. **Advisory message examples** — Four complete templates demonstrate advisory model clearly
4. **Quick reference table** — 4-pattern summary table provides fast loop detection lookup
5. **Tool selection rationale** — Task + Bash CLI sufficient; no MCP tools needed for orchestration

### What Could Be Better

1. **Length vs. detail tradeoff** — 383 lines is comprehensive but long for a system prompt; might benefit from more aggressive summarization
2. **Advisory message verbosity** — Each advisory is ~10 lines; could compress to 5-line templates
3. **Convergence criteria complexity** — Multiple success targets (ideal/acceptable/conditional) may cause decision paralysis

### For Future Reference

- Claude Code subagent architecture enables true multi-agent orchestration via Task tool
- Advisory model (constraints not directives) works well in system prompts via examples
- Per-pattern tracking prevents global counter issues (different root causes need different counts)
- Sonnet model choice for orchestration (vs. opus for analysis) is appropriate differentiation
- Cross-referencing to skill documents keeps system prompts focused on role/procedure, not domain knowledge

---

*Summary completed: 2026-02-07*
*Execution duration: 2m 10s*
