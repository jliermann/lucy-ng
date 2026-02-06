# Domain Pitfalls: Multi-Agent CASE Integration

**Domain:** Computer-Assisted Structure Elucidation (CASE) with Multi-Agent Architecture
**Researched:** 2026-02-06

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Tool-Heavy Architecture Doesn't Scale

**What goes wrong:** Embedding intelligence in Python tools creates a brittle system that degrades as tool count grows and prevents AI from reasoning about errors.

**Why it happens:**
- Developer instinct: "Put validation in code, not documentation"
- Seems safer: "Python ensures consistency"
- Path of least resistance: "Easier to write code than teach AI"

**Consequences:**
- AI bypasses "smart" tools when they don't match its reasoning (seen in Virgiline case)
- Tool count grows as each edge case gets its own tool
- System degrades beyond ~50-100 tools (semantic confusion, cognitive overload)
- AI can't explain WHY a tool failed (opaque Python logic)
- User can't adjust behavior without code changes

**Prevention:**
1. **Categorize tools by intelligence level:**
   - Tier 1 (keep): Pure data access (read files, run solver, query database)
   - Tier 2 (migrate): Moderate intelligence (strategies, tolerances, heuristics)
   - Tier 3 (refactor later): Complex logic (LSD generation, constraint building)

2. **Encode domain knowledge in skill, not code:**
   - Tolerances (±1.5 ppm for HMBC C matching) → Document in skill with rationale
   - Strategies (DEPT-guided adaptive thresholding) → Teach concept, not just call tool
   - Error handling (close shift detection) → Give AI reasoning pattern, not numeric check

3. **Keep tools thin and composable:**
   - Tools return raw data, AI interprets
   - Multiple thin tools > One smart tool
   - Example: `read_spectrum` + skill interpretation > `analyze_spectrum_with_validation`

**Detection:**
- AI says "I'll construct the LSD file directly" instead of using `generate_lsd_input`
- Tools have multiple if/else branches for edge cases
- Tool documentation says "handles X, Y, and Z automatically"
- Adding new feature requires new tool instead of skill update

**Example from lucy-ng:**
```python
# WRONG (v1.x approach):
def pick_hmbc_peaks(...):
    peaks = raw_pick(hmbc)
    filtered = validate_against_c13(peaks, c13, tolerance=1.5)
    filtered = validate_against_hsqc(filtered, hsqc, tolerance=0.1)
    return filtered, rejected, warnings

# RIGHT (v2.0 approach):
def read_hmbc_peaks(hmbc):
    return raw_pick(hmbc)  # Just data access

# Skill teaches:
# "After picking HMBC, validate correlations:
# - Carbon must match a known carbon (13C or DEPT) within ±1.5 ppm
# - Proton must match HSQC proton within ±0.1 ppm
# - Reject correlations outside these tolerances (likely artifacts)"
```

**References:**
- [AI Agent Architectures: Efficiency vs. Scaling Limits in 2026](https://beta.hyper.ai/en/stories/53d4fafdd3b77c15bc7008b4122bc84c) - Tool-heavy systems degrade beyond 50-100 tools

### Pitfall 2: Supervisor Without Clear Intervention Criteria

**What goes wrong:** Supervisor monitors but doesn't intervene, or intervenes too broadly ("try again"), creating supervisor-in-name-only or overly aggressive termination.

**Why it happens:**
- Unclear what counts as a "loop" vs legitimate iteration
- Generic interventions ("Something's wrong, restart") don't help
- Fear of terminating productive exploration

**Consequences:**
- Supervisor becomes passive observer, doesn't prevent loops
- OR: Supervisor terminates legitimate multi-step reasoning
- CASE agent continues unproductive patterns for dozens of iterations
- User loses trust in multi-agent system

**Prevention:**
1. **Define specific loop patterns:**
   ```markdown
   Loop detected when:
   - Same error message appears 3+ consecutive times
   - ELIM parameter adjusted 3+ times without solution change
   - sp2 count corrected for same atom 2+ times
   - Same HMBC correlation added/removed 2+ times
   ```

2. **Require multiple signals before intervention:**
   ```markdown
   Intervention threshold:
   - Single signal + 5 iterations → warn
   - Two signals + 3 iterations → intervene
   - Three signals + any iterations → immediate intervention
   ```

3. **Interventions must be specific, not generic:**
   ```markdown
   BAD: "You seem stuck. Try a different approach."

   GOOD: "Loop detected: Three ELIM adjustments (1, 2, 3) without solutions.

   Root cause: ELIM masks the real issue (likely missing or incorrect constraints).

   Redirect: Remove ELIM. Check these in order:
   1. sp2 count even? (must be even)
   2. Hydrogen count matches formula?
   3. Any HMBC correlations to quaternary carbons without corresponding 13C peaks?

   Fix the root cause, then retry WITHOUT ELIM."
   ```

4. **Allow CASE agent to suppress intervention:**
   ```markdown
   In progress.md:
   ## LSD Attempt 3
   Status: 0 solutions
   Note: Exploring alternative sp2 assignments (not stuck, need 2 more attempts)
   ```

**Detection:**
- Supervisor intervenes on first failed attempt (too aggressive)
- Supervisor watches 10+ failed attempts without intervention (too passive)
- Intervention message is vague or generic
- CASE agent doesn't change behavior after intervention

**Example:**
```markdown
# Detected in progress.md:
## LSD Attempt 1
Status: 0 solutions
Issue: sp2 count odd, corrected C5 from sp3 to sp2

## LSD Attempt 2
Status: 0 solutions
Issue: sp2 count still odd, corrected C5 back to sp3

## LSD Attempt 3
Status: 0 solutions
Issue: sp2 count odd, corrected C8 from sp3 to sp2

[SUPERVISOR SHOULD INTERVENE HERE]
Specific redirect: "You're uncertain about hybridization.
Use chemical shift ranges to determine sp2 vs sp3:
- sp2 carbons: 90-180 ppm (aromatic, C=O, C=C)
- sp3 carbons: 0-90 ppm (saturated)
Check each carbon's shift before assigning hybridization."
```

### Pitfall 3: State Tracking Fragility

**What goes wrong:** Progress files become inconsistent or unparseable, supervisor can't monitor, multi-agent coordination fails.

**Why it happens:**
- No structured format for progress.md (CASE agent writes freeform text)
- CASE agent forgets to update progress after steps
- Multiple agents write to same file concurrently (race conditions)

**Consequences:**
- Supervisor can't detect loops (missing progress data)
- User can't understand CASE state from files
- Resume fails (state inconsistent)
- Debugging impossible (no audit trail)

**Prevention:**
1. **Enforce structured format in skill:**
   ```markdown
   Progress file format (analysis/progress.md):

   ## [Step Name]
   Status: [Complete|In Progress|Failed]
   [Key outputs]
   [Issues if any]
   Next: [Planned next step]
   ```

2. **Validate structure in skill:**
   ```markdown
   After writing progress.md, verify:
   - Each step has ## heading
   - Status field present
   - If Failed, Issue field present
   ```

3. **Use file locking for concurrent access:**
   ```markdown
   If multiple agents write to progress.md:
   1. Read current content
   2. Append new section
   3. Write atomically (overwrite entire file)
   ```

4. **Provide progress template:**
   ```bash
   # In .planning/templates/progress.md:
   # CASE Progress

   ## Dereplication
   Status:
   Result:

   ## Symmetry Analysis
   Status:
   Expected carbons:
   Observed carbons:

   ## LSD Execution
   Attempt:
   Status:
   Solution count:
   Changes made:
   ```

**Detection:**
- progress.md exists but supervisor can't parse loop signals
- Missing sections (symmetry analysis skipped, no record)
- Inconsistent formatting (some steps use ##, others use ###)
- User asks "What's the current state?" and no one can answer from files

## Moderate Pitfalls

Mistakes that cause delays or technical debt.

### Pitfall 4: Premature Specialist Agent Proliferation

**What goes wrong:** Creating specialist subagents for every subtask before validating supervisor pattern, resulting in over-engineered system with coordination overhead exceeding benefit.

**Prevention:**
- Start with supervisor + single CASE agent
- Only add specialists when CASE agent demonstrably struggles with subtask
- Each specialist must justify existence (what does it do that CASE agent can't?)

**When to add specialist:**
- CASE agent context overflows on specific subtask (peak picking produces too much data)
- Subtask requires domain expertise beyond main CASE skill (constraint debugging)
- Parallel exploration valuable (multiple hypothesis paths)

**When NOT to add specialist:**
- "Feels cleaner" architecturally
- Subtask is logically separate but not complex
- Coordination overhead (spawning, messaging) exceeds time saved

### Pitfall 5: Skill Duplication Across Subagents

**What goes wrong:** Domain knowledge duplicated in multiple subagent skills, causing inconsistencies and maintenance burden.

**Prevention:**
- Central CLAUDE.md for shared domain knowledge (NMR interpretation, LSD rules)
- Subagent skills focus on workflow and role-specific instructions
- Use `skills: [lucy-ng]` in subagent frontmatter to inherit domain knowledge

**Example:**
```yaml
# .claude/agents/case-worker.md
---
name: case-worker
skills: [lucy-ng]  # Inherits domain knowledge from CLAUDE.md
---

You execute the CASE workflow. Domain knowledge is in lucy-ng skill.
Your role: Follow workflow steps, report progress, handle errors.
```

### Pitfall 6: Background Subagents Without Pre-Approved Permissions

**What goes wrong:** Background subagent encounters permission prompt (file write, tool use), auto-denies because user isn't present, subtask fails silently.

**Prevention:**
- Use foreground subagents for tasks requiring new permissions
- Background subagents only for read-only or pre-approved operations
- Set `permissionMode: acceptAll` in subagent config (use cautiously)
- Document which tools are pre-approved in subagent description

### Pitfall 7: Context Overflow Without Compaction Strategy

**What goes wrong:** CASE subagent context fills with verbose tool outputs (hundreds of HMBC correlations), runs out of space before completing workflow.

**Prevention:**
- Write summaries to progress files (persistent), not full data to conversation
- Use external files for large datasets (picked_hmbc.json), reference in conversation
- Claude Code auto-compaction at ~95% capacity (built-in mitigation)
- Break long CASE workflow into sequential subagents if single agent can't complete

**Example:**
```markdown
# Instead of:
"Here are all 247 HMBC correlations: [massive list]"

# Write:
"Picked 247 HMBC correlations. Validated 89 against 13C and HSQC.
Detailed list written to analysis/hmbc_correlations.json.
Summary: 89 valid, 158 rejected (104 no C match, 54 no H match)."
```

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### Pitfall 8: Unclear Subagent Descriptions

**What goes wrong:** Main conversation doesn't know when to spawn which subagent because descriptions are vague.

**Prevention:**
```yaml
# BAD:
description: Helps with HMBC analysis

# GOOD:
description: Validates HMBC correlations and flags artifacts (t1 noise, 1J bleeding). Use when LSD produces >100 solutions or correlations look suspicious.
```

### Pitfall 9: Subagent Transcript Bloat

**What goes wrong:** Subagent transcripts fill disk space, hard to find relevant conversation.

**Prevention:**
- Transcripts auto-managed by Claude Code (not a real problem)
- Use descriptive subagent names for easy identification
- Clean up old transcripts periodically if needed

### Pitfall 10: Over-Reliance on File Watching

**What goes wrong:** Supervisor constantly reads progress.md looking for changes instead of waiting for subagent completion.

**Prevention:**
- Use foreground subagents (blocking) when supervisor needs immediate results
- Supervisor checks progress.md at defined checkpoints, not continuously
- Background subagents for truly async work (long LSD runs)

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Supervisor Infrastructure | Unclear intervention criteria | Define specific loop patterns with thresholds |
| Skill Restructure | Duplication between main and subagent skills | Use skills inheritance, DRY principle |
| Supervisor Integration | Too aggressive (terminates legitimate iteration) | Require multiple signals, allow suppression |
| Supervisor Integration | Too passive (doesn't intervene on real loops) | Test with known failure cases, tune thresholds |
| Tool Migration | Breaking backward compatibility | Dual mode: CLI gets smart tools, MCP gets thin |
| Tool Migration | Migrating too much too fast | Incremental: one tool at a time, validate each |

## CASE-Specific Pitfalls (Domain Knowledge)

### Pitfall 11: Symmetry Misinterpretation

**What goes wrong:** AI incorrectly identifies which carbons are equivalent, leading to wrong LSD constraints.

**Skill knowledge needed:**
```markdown
Symmetry detection checklist:
1. Compare expected (formula) vs observed (13C peak count)
2. Check HSQC intensities (equivalent positions have ~2x intensity)
3. Verify with chemical structure knowledge:
   - Para-disubstituted benzene: 2 pairs of equivalent CH
   - Isopropyl: 2 equivalent CH3
   - tert-Butyl: 3 equivalent CH3
4. Hydrogen budget: total H from multiplicities must equal formula
```

### Pitfall 12: ELIM as First Resort

**What goes wrong:** AI immediately adds ELIM when LSD returns 0 solutions, masking real constraint errors.

**Skill knowledge needed:**
```markdown
ELIM decision tree:
- 0 solutions → Check sp2 count (even?), H count (matches?), constraints (valid?)
- If all correct and still 0 → Try ELIM 1 0 (eliminate at most 1 correlation)
- If ELIM 1 0 still fails → Question molecular formula
- NEVER start with ELIM 2+ (masks too many issues)
```

### Pitfall 13: Quaternary Carbon Ghost Signals

**What goes wrong:** AI tries to find HSQC correlations for quaternary carbons (impossible), confusing lack of signal with missing data.

**Skill knowledge needed:**
```markdown
Quaternary carbons:
- Appear in 13C spectrum
- DO NOT appear in DEPT or HSQC (no attached H)
- Only connected via HMBC correlations
- Typical shifts: 160-220 ppm (C=O), 120-160 ppm (aromatic junction)
```

### Pitfall 14: Close Shift Ambiguity

**What goes wrong:** Two peaks 0.2 ppm apart treated as separate carbons when they're likely one carbon with temperature/impurity effects.

**Skill knowledge needed:**
```markdown
Close shift handling:
- Peaks within 0.3 ppm: Investigate
  - Same multiplicity (DEPT)? → Likely impurity or equilibrium
  - Different multiplicity? → Separate carbons (unusual but possible)
- Peaks within 0.1 ppm: Treat as one carbon (use average)
- Document ambiguity in findings.md
```

## Sources

**Tool-Heavy Architecture:**
- [AI Agent Architectures: Efficiency vs. Scaling Limits in 2026](https://beta.hyper.ai/en/stories/53d4fafdd3b77c15bc7008b4122bc84c)
- [Multi-Agent AI Systems: The Complete Enterprise Guide for 2026](https://neomanex.com/posts/multi-agent-ai-systems-orchestration)

**Loop Detection:**
- [Our Agent Had A 4 Minute Loop. Here's How We Fixed It.](https://medium.com/data-science-collective/our-agent-had-a-4-minute-loop-heres-how-we-fixed-it-40a8142ef1a9)
- [Ralph Wiggum AI Agents: The Coding Loop of 2026](https://www.leanware.co/insights/ralph-wiggum-ai-coding)

**Subagent Patterns:**
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code's Hidden Multi-Agent System](https://paddo.dev/blog/claude-code-hidden-swarm/)

**Skill Engineering:**
- [awesome-claude-skills - GitHub](https://github.com/travisvn/awesome-claude-skills)
- Manus workflow (task_plan.md, findings.md pattern)

**CASE Domain:**
- Existing lucy-ng CLAUDE.md (1080 lines of domain knowledge)
- LSD manual: https://nuzillard.github.io/LSD/MANUAL_ENG.html
