# Phase 30: Diagnostic Specialist Integration - Research

**Researched:** 2026-02-08
**Domain:** Multi-agent delegation with structured diagnostic reporting
**Confidence:** HIGH

## Summary

Phase 30 integrates the diagnostic specialist agent into the CASE orchestrator workflow built in Phase 29. The orchestrator already has basic diagnosis capability (sp2 count, H budget, 1J artifact checks). When basic interventions fail twice for the same loop pattern, the orchestrator delegates to the diagnostic specialist via the Task tool for deep root cause analysis.

The diagnostic specialist runs systematic LSD checks, produces a structured DIAGNOSTIC-REPORT.md with findings/root cause/fixes, and the orchestrator extracts key information to inform the next CASE agent advisory. The phase requires three changes: (1) rename diagnostic-specialist.md to lucy-diagnostic.md with updated frontmatter, (2) wire the delegation trigger into case.md, (3) add DIAGNOSTIC-REPORT.md parsing and extraction logic.

The architecture follows established Claude Code patterns: Task tool for agent spawning, file-based structured reporting for cross-agent communication, and per-pattern tracking for delegation thresholds.

**Primary recommendation:** Follow the delegation pattern from skill/supervisor/SKILL.md Section 5. Use Task tool spawning with same pattern as case.md uses for CASE agent. Parse DIAGNOSTIC-REPORT.md sections (Root Cause, Recommended Fixes) using Read tool and markdown structure. Test with forced zero-solution loop to verify full delegation workflow.

## Standard Stack

The established tools for this domain:

### Core
| Tool/Pattern | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Task tool | Claude Code 2.1+ | Spawn diagnostic specialist agent | Official multi-agent orchestration mechanism, used for CASE agent in Phase 29 |
| DIAGNOSTIC-REPORT.md | skill/diagnostic/SKILL.md Section 3 | Structured diagnostic output consumed by orchestrator | File-based cross-agent communication, defined in v2.0 Phase 25 |
| Read tool | built-in | Parse DIAGNOSTIC-REPORT.md sections | Markdown parsing for root cause and fix extraction |
| Per-pattern counters | orchestrator state | Track failures per loop pattern | Enables "2 failed interventions with SAME pattern" threshold |

### Supporting
| Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Bash | system | File operations (check existence of DIAGNOSTIC-REPORT.md) | Before parsing report, verify file exists |
| Write tool | built-in | Update case.md with delegation logic | Replace placeholder with working delegation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Task tool delegation | Inline diagnostic logic in orchestrator | Task tool is correct—diagnostic specialist has 455 lines of specialized knowledge, would bloat orchestrator |
| DIAGNOSTIC-REPORT.md | JSON output | Markdown is human-readable and AI-parseable; JSON would require schema definition and validation |
| Per-pattern delegation threshold | Global 2-failure threshold | Per-pattern tracking identifies which specific loop pattern needs deep diagnosis; global masks root causes |

**Installation:**
No external dependencies. Uses existing diagnostic-specialist.md agent (renamed to lucy-diagnostic.md) and DIAGNOSTIC-REPORT.md format from Phase 25.

## Architecture Patterns

### Recommended Integration Structure

The integration follows this flow (adding to Phase 29 orchestrator):

```
case.md orchestration loop (from Phase 29)
├── spawn_case_agent → agent runs iterations
├── monitor_progress → read CASE-PROGRESS.md
├── detect_loops → 4 patterns (ELIM thrashing, zero-solution, explosion, churning)
├── diagnose → basic checks (sp2, H budget, 1J artifacts)
├── track_and_decide → per-pattern counters
│   ├── counter < 2 for this pattern? → intervene (basic advisory)
│   ├── counter == 2 for this pattern? → delegate_to_specialist (NEW IN PHASE 30)
│   └── counter >= 10 for this pattern? → escalate to user
├── delegate_to_specialist (NEW STEP)
│   ├── Spawn diagnostic specialist via Task tool
│   ├── Wait for DIAGNOSTIC-REPORT.md
│   ├── Read and parse report
│   └── Extract root cause + primary fix for advisory
└── respawn_case_agent → with specialist-informed advisory
```

### Pattern 1: Delegation Trigger Logic

**What:** Check per-pattern intervention counter to decide when to delegate to specialist.

**When to use:** After basic diagnosis completes, before generating advisory intervention.

**Example from skill/supervisor/SKILL.md Section 5:**
```markdown
**Threshold criteria for delegation:**

1. After 2 failed supervisor interventions with the SAME loop pattern
   - Supervisor diagnosed, advised CASE agent, but pattern recurred twice
   - Basic diagnosis is not resolving the issue

**When NOT to delegate:**
- First detection of a loop pattern — supervisor basic diagnosis is sufficient
- When root cause is obvious from basic checks (e.g., odd sp2 count)
```

**Implementation in case.md track_and_decide step:**
```markdown
**Decision logic:**
- If counter for this pattern == 0 or 1: basic intervention (current Phase 29 behavior)
- If counter for this pattern == 2: delegate to diagnostic specialist (NEW)
- If counter for this pattern >= 3 and < 10: use specialist-informed advisory or basic if no specialist report
- If counter for this pattern >= 10: escalate to user

**Why threshold = 2:**
- First intervention: basic diagnosis sufficient for common issues (odd sp2, missing H)
- Second intervention: pattern recurred despite basic fix, needs deeper analysis
- Specialist after 2 failures prevents wasted cycles on difficult root causes
```

**Source:** skill/supervisor/SKILL.md Section 5 "When to Delegate"

### Pattern 2: Task Tool Spawning for Diagnostic Specialist

**What:** Spawn diagnostic specialist agent via Task tool with specific diagnostic instructions.

**When to use:** When delegation trigger threshold is met (2 failed basic interventions, same pattern).

**Example from skill/supervisor/SKILL.md Section 5:**
```markdown
Task(
  agent_type="diagnostic-specialist",  # Will be "lucy-diagnostic" after rename
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

**Inputs to provide:**
- Compound path (working directory)
- Latest LSD filename (extract from CASE-PROGRESS.md last iteration)
- Failure type (0 solutions, 1000+ solutions, or other)
- CASE-PROGRESS.md path for iteration history

**Key points:**
- Agent type will be "lucy-diagnostic" after DIAG-06 rename
- Spawning pattern identical to case.md spawning CASE agent (Phase 29)
- Agent has 455 lines of inlined knowledge, orchestrator only provides task-specific context
- Agent writes DIAGNOSTIC-REPORT.md, orchestrator reads it after Task completes

**Source:** skill/supervisor/SKILL.md Section 5 "How to Spawn Diagnostic Specialist"

### Pattern 3: DIAGNOSTIC-REPORT.md Parsing and Extraction

**What:** Read DIAGNOSTIC-REPORT.md, extract root cause and primary fix to inform CASE agent advisory.

**When to use:** After diagnostic specialist Task completes successfully.

**DIAGNOSTIC-REPORT.md structure (from skill/diagnostic/SKILL.md Section 3):**
```markdown
# Diagnostic Report: <Compound Name> LSD Failure

**Compound:** <path>
**Formula:** <formula>
**Failure Type:** <0 solutions | 1000+ solutions>
**Diagnostic Date:** <timestamp>
**Diagnostic Agent:** diagnostic-specialist

---

## Summary
[Executive summary]
[Root cause one-liner]
[Confidence level]

---

## Findings
### Finding 1: <Title> (CRITICAL | MAJOR | MINOR)
**What:** [description]
**Evidence:** [quantitative data]
**Impact:** [why it matters]
**Confidence:** HIGH | MEDIUM | LOW

---

## Root Cause
**Primary:** [main cause with mechanism]
**Why it caused failure:** [detailed explanation]
**Contributing factors:** [secondary causes or "None"]

---

## Recommended Fixes
### Fix 1: <Title> (PRIMARY | SECONDARY)
**Action:** [specific steps with LSD commands]
```
[LSD command examples]
```
**Verification:** [how to confirm fix worked]
**Confidence:** HIGH | MEDIUM | LOW

---
[...more sections...]
```

**Extraction procedure:**
1. Read DIAGNOSTIC-REPORT.md from compound directory
2. Locate "## Root Cause" section
3. Extract "Primary:" line and "Why it caused failure:" paragraph
4. Locate "## Recommended Fixes" section
5. Find first fix marked "(PRIMARY)"
6. Extract "Action:" and code block with LSD commands
7. Extract "Verification:" line

**Example extraction result:**
```
Root cause: 1J artifact in HMBC C155.2-H2.1 (within ±1.5 ppm C, ±0.3 ppm H of HSQC position)

Primary fix:
Remove HMBC correlation C155.2-H2.1 from LSD file.

; Before:
HMBC 5 12    ; C155.2-H2.1 (ARTIFACT)

; After:
; HMBC 5 12 removed (1J artifact)

Verification: After removal, re-run LSD, expect solutions > 0
```

**Generate specialist-informed advisory (from skill/supervisor/SKILL.md Section 5):**
```markdown
Diagnostic specialist identified root cause: 1J artifact in HMBC C155.2-H2.1.

See DIAGNOSTIC-REPORT.md for full analysis.

Fix: Remove HMBC correlation C155.2-H2.1 from LSD file.
This correlation is within artifact tolerance (±1.5 ppm C, ±0.3 ppm H) of HSQC position.

Verification: After removal, re-run LSD. Expect solutions > 0.

Also review other iteration 3 correlations (C155.2-H4.3, C172.4-H2.1) for artifacts.
```

**Key points:**
- Parse markdown structure, don't use regex (fragile)
- Root cause extraction: look for "## Root Cause" header, extract content until next "##"
- Fix extraction: look for "## Recommended Fixes", find first "(PRIMARY)", extract full fix section
- Include reference to DIAGNOSTIC-REPORT.md in advisory so CASE agent can read full report if needed
- Verification steps are critical—CASE agent needs to know expected outcome

**Source:** skill/supervisor/SKILL.md Section 5 "After Diagnostic Specialist Completes"

### Pattern 4: Specialist-Informed Advisory Generation

**What:** Generate CASE agent advisory that incorporates diagnostic specialist findings.

**When to use:** After successful DIAGNOSTIC-REPORT.md parsing.

**Template (different from basic advisory):**
```markdown
Diagnostic specialist identified root cause: <extracted_root_cause>

See DIAGNOSTIC-REPORT.md for full analysis.

Fix: <extracted_primary_fix_action>
<extracted_LSD_commands_if_present>

Verification: <extracted_verification_steps>

<optional_additional_guidance_based_on_pattern>
```

**Contrast with basic advisory (Phase 29):**
```markdown
Basic advisory (Phase 29):
---
ELIM thrashing detected. Before retrying:

1. Verify sp2 count is even (current count: <N>)
2. Verify hydrogen budget matches formula
3. Check last batch of HMBC correlations for 1J artifacts

Do NOT add ELIM again until all checks pass.
---

Specialist-informed advisory (Phase 30):
---
Diagnostic specialist identified root cause: Odd sp2 count (9 atoms).
Ether oxygen O7 marked sp2 instead of sp3.

See DIAGNOSTIC-REPORT.md for full analysis.

Fix: Change MULT 7 from sp2 to sp3.

; Before (WRONG):
MULT 7 O 2 0    ; ether oxygen marked sp2

; After (CORRECT):
MULT 7 O 3 0    ; ether oxygen marked sp3

Verification: After change, re-run LSD, expect solutions > 0.

Ether oxygens are always sp3 (single bonds only).
---
```

**Key differences:**
- Specialist advisory is SPECIFIC (exact atom, exact command)
- Basic advisory is PROCEDURAL (check these things, verify conditions)
- Specialist references DIAGNOSTIC-REPORT.md for full evidence
- Both preserve agent autonomy (WHAT not HOW), but specialist can be more prescriptive because it has evidence

**Source:** skill/supervisor/SKILL.md Section 5 "After Diagnostic Specialist Completes"

### Anti-Patterns to Avoid

**Never delegate on first loop detection:**
- Pattern detected for first time → basic diagnosis sufficient
- Only delegate after 2 failed basic interventions with SAME pattern

**Never parse DIAGNOSTIC-REPORT.md with regex:**
- Markdown structure can vary slightly (spacing, formatting)
- Use Read tool to get full content, locate section headers, extract blocks
- Robust parsing: find "## Root Cause", read until next "##" or EOF

**Never overwrite per-pattern counter after delegation:**
- Delegation counts as 1 intervention cycle for that pattern
- If specialist-informed advisory fails, counter increments to 3, then 4, etc.
- Same escalation threshold: 10 total cycles (basic + specialist-informed combined)

**Never duplicate diagnostic knowledge in orchestrator:**
- Diagnostic specialist has 455 lines of systematic check procedures
- Orchestrator only does basic checks (sp2, H budget, 1J artifacts)
- Delegation is precisely because deeper analysis is needed

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent orchestration | Custom subprocess spawning, API calls | Task tool | Official Claude Code mechanism, handles context passing, async execution, result retrieval |
| Structured report parsing | Regex patterns for extracting sections | Read full file + section header search | Markdown formatting varies, regex brittle; section headers ("## Root Cause") are stable markers |
| Delegation threshold logic | Global intervention counter | Per-pattern counters (from Phase 29) | Different patterns have different root causes; global counter masks which specific failure mode is recurring |
| Cross-agent communication | Shared memory, message queues | File-based reporting (DIAGNOSTIC-REPORT.md) | Claude Code agents communicate via filesystem; structured markdown is human-readable and AI-parseable |

**Key insight:** Multi-agent orchestration in Claude Code uses filesystem for state sharing and Task tool for spawning. Don't implement custom IPC mechanisms—the existing pattern is proven and integrated.

## Common Pitfalls

### Pitfall 1: Delegating Too Early

**What goes wrong:** Orchestrator delegates to specialist on first loop detection, wasting specialist cycles on simple issues.

**Why it happens:** Threshold misunderstood—"after 2 failed interventions" means pattern recurred twice despite fixes, not "2 iterations total."

**How to avoid:**
- Track per-pattern intervention counter
- Delegate only when `counter_for_this_pattern == 2`
- First detection (counter = 0) → basic diagnosis
- First recurrence (counter = 1) → basic diagnosis again
- Second recurrence (counter = 2) → delegate to specialist

**Warning signs:**
- Specialist spawned frequently (every 2-3 CASE iterations)
- DIAGNOSTIC-REPORT.md shows simple findings (odd sp2, missing H)
- Basic diagnosis could have caught these issues

**Example of correct delegation:**
```
Iteration 1: Zero solutions (ZERO_SOLUTION_LOOP detected)
  → Basic diagnosis: sp2 count even ✓, H budget correct ✓, 1J artifact check → found 1 artifact
  → Advisory: Remove 1J artifact HMBC C155.2-H2.1
  → counter[ZERO_SOLUTION_LOOP] = 1

Iteration 2: Zero solutions (ZERO_SOLUTION_LOOP recurred)
  → Basic diagnosis: sp2 even ✓, H budget ✓, 1J check → found another artifact C172.4-H3.2
  → Advisory: Remove 1J artifact HMBC C172.4-H3.2
  → counter[ZERO_SOLUTION_LOOP] = 2

Iteration 3: Zero solutions (ZERO_SOLUTION_LOOP recurred AGAIN)
  → counter[ZERO_SOLUTION_LOOP] == 2 → DELEGATE TO SPECIALIST
  → Specialist runs systematic checks, finds: close carbon ambiguity (C155.08 and C155.32 within 0.24 ppm)
  → Specialist-informed advisory: Use LIST/PROP to encode ambiguity
```

**Source:** skill/supervisor/SKILL.md Section 5 "When to Delegate"

### Pitfall 2: Parsing DIAGNOSTIC-REPORT.md Incompletely

**What goes wrong:** Orchestrator extracts root cause but misses primary fix details, resulting in vague advisory.

**Why it happens:** Only reading Summary section, not navigating to Recommended Fixes section.

**How to avoid:**
- Parse complete report structure
- Extract from multiple sections:
  - "## Root Cause" → primary cause + mechanism
  - "## Recommended Fixes" → find "(PRIMARY)" fix
  - "Fix 1" section → extract Action, code block, Verification
- Validate extraction: ensure all three components present before generating advisory

**Warning signs:**
- Advisory says "See DIAGNOSTIC-REPORT.md" but provides no actionable guidance
- CASE agent reads report itself and implements fix (should happen via orchestrator advisory)
- Advisory missing LSD command examples that specialist provided

**Example of incomplete extraction:**
```
BAD advisory (incomplete extraction):
---
Diagnostic specialist identified root cause: 1J artifact detected.

See DIAGNOSTIC-REPORT.md for details.
---

GOOD advisory (complete extraction):
---
Diagnostic specialist identified root cause: 1J artifact in HMBC C155.2-H2.1.

See DIAGNOSTIC-REPORT.md for full analysis.

Fix: Remove HMBC correlation C155.2-H2.1 from LSD file.

; Before:
HMBC 5 12    ; C155.2-H2.1 (ARTIFACT)

; After:
; HMBC 5 12 removed (1J artifact)

Verification: After removal, re-run LSD, expect solutions > 0.
---
```

**Source:** skill/supervisor/SKILL.md Section 5 "After Diagnostic Specialist Completes"

### Pitfall 3: Not Incrementing Counter After Specialist Delegation

**What goes wrong:** Orchestrator delegates at counter = 2, specialist fixes issue, but pattern recurs. Orchestrator delegates AGAIN at counter = 2 (still) instead of incrementing.

**Why it happens:** Counter increment logic only applies to basic interventions, specialist delegation not counted.

**How to avoid:**
- Delegate when counter == 2
- After delegation, increment counter to 3
- If pattern recurs, counter increments to 4, 5, ... until 10 (escalation threshold)
- Specialist delegation counts as 1 intervention cycle

**Warning signs:**
- Specialist spawned multiple times for same pattern
- Counter stuck at 2 despite multiple delegation cycles
- Escalation threshold never reached despite persistent failures

**Example of correct counter management:**
```
counter[ZERO_SOLUTION_LOOP] = 0  # Initial state
Iteration 1: Zero solutions → basic intervention → counter = 1
Iteration 2: Zero solutions → basic intervention → counter = 2
Iteration 3: Zero solutions → delegate to specialist → counter = 3
Iteration 4: Zero solutions → use specialist advisory or basic → counter = 4
...
Iteration 10: Zero solutions → counter = 10 → escalate to user
```

**Source:** skill/supervisor/SKILL.md Section 5 "Escalation After Diagnostic Specialist"

### Pitfall 4: Wrong Agent Type After Rename

**What goes wrong:** After renaming diagnostic-specialist.md to lucy-diagnostic.md, orchestrator still spawns "diagnostic-specialist" agent type, causing Task tool error.

**Why it happens:** Orchestrator code references old agent name, not updated to match renamed file.

**How to avoid:**
- DIAG-06 requires both rename AND frontmatter update
- File: `~/.claude/agents/lucy-diagnostic.md`
- Frontmatter: `name: lucy-diagnostic` (must match filename without .md)
- Orchestrator Task call: `agent_type="lucy-diagnostic"`
- All three must align

**Warning signs:**
- Task tool error: "Agent type 'diagnostic-specialist' not found"
- Delegation hangs or fails silently
- DIAGNOSTIC-REPORT.md not created despite delegation

**Example of correct alignment:**
```
File: ~/.claude/agents/lucy-diagnostic.md

Frontmatter:
---
name: lucy-diagnostic
description: >
  LSD failure diagnostic specialist. ...
---

Orchestrator delegation:
Task(
  agent_type="lucy-diagnostic",  # Must match frontmatter name
  instructions="Analyze LSD failure..."
)
```

**Source:** DIAG-06 requirement "Agent definition renamed from ~/.claude/agents/diagnostic-specialist.md to ~/.claude/agents/lucy-diagnostic.md with updated frontmatter (agent name matches new file)"

### Pitfall 5: Not Handling Missing DIAGNOSTIC-REPORT.md

**What goes wrong:** Specialist Task completes but DIAGNOSTIC-REPORT.md doesn't exist (specialist error, permission issue, wrong path).

**Why it happens:** Orchestrator assumes successful Task completion means report exists, no validation.

**How to avoid:**
- After Task completes, check file existence: `[ -f "$COMPOUND_PATH/DIAGNOSTIC-REPORT.md" ]`
- If missing:
  - Log error: "Diagnostic specialist completed but DIAGNOSTIC-REPORT.md not found"
  - Fall back to basic advisory (counter still increments)
  - Or escalate early: "Specialist delegation failed, manual review required"
- Only parse report if file exists

**Warning signs:**
- Read tool error: "File does not exist: .../DIAGNOSTIC-REPORT.md"
- Orchestrator hangs trying to parse non-existent file
- Advisory generation fails silently

**Example of defensive check:**
```bash
# After specialist Task completes
if [ -f "$COMPOUND_PATH/DIAGNOSTIC-REPORT.md" ]; then
  # Parse report, extract root cause and fix
  generate_specialist_informed_advisory
else
  echo "ERROR: Diagnostic specialist completed but DIAGNOSTIC-REPORT.md not found"
  echo "Falling back to basic advisory"
  generate_basic_advisory
fi
```

**Source:** Defensive programming best practice for file-based cross-agent communication

## Code Examples

Verified patterns from skill documents and existing Phase 29 orchestrator:

### Delegation Trigger in track_and_decide Step

Source: skill/supervisor/SKILL.md Section 5 + case.md track_and_decide step

```markdown
<step name="track_and_decide">
Track intervention count for this specific pattern and decide whether to use basic intervention, delegate to specialist, or escalate.

**Per-pattern intervention counters:**
Maintain separate counters for each pattern:
- ELIM_THRASHING: count_elim
- ZERO_SOLUTION_LOOP: count_zero
- SOLUTION_EXPLOSION: count_explosion
- CONSTRAINT_CHURNING: count_churning

**After diagnosis completes:**
Increment the counter for THIS pattern only.

**Decision logic:**
- **If counter for this pattern == 0 or 1:** Basic intervention (Phase 29 diagnose step)
- **If counter for this pattern == 2:** Delegate to diagnostic specialist (proceed to delegate_specialist step)
- **If counter for this pattern >= 3 and < 10:** Use specialist-informed advisory if DIAGNOSTIC-REPORT.md exists, else basic
- **If counter for this pattern >= 10:** Escalate to user (proceed to escalate step)

**Why threshold = 2:**
- First intervention: Basic diagnosis sufficient for common issues (odd sp2, missing H)
- Second intervention: Pattern recurred despite basic fix, needs deeper analysis
- Specialist after 2 failures prevents wasted cycles on difficult root causes

After decision, proceed to appropriate next step.
</step>
```

### Diagnostic Specialist Delegation Step

Source: skill/supervisor/SKILL.md Section 5 "How to Spawn Diagnostic Specialist"

```markdown
<step name="delegate_specialist">
Delegate to diagnostic specialist agent for deep root cause analysis.

**This step only executes when:** counter for detected pattern == 2 (threshold from track_and_decide)

**Identify failure type:**
- ZERO_SOLUTION_LOOP → failure_type = "0 solutions"
- SOLUTION_EXPLOSION → failure_type = "1000+ solutions"
- ELIM_THRASHING → failure_type = "0 solutions" (ELIM usually causes 0)
- CONSTRAINT_CHURNING → failure_type = "other"

**Extract latest LSD filename:**
Read CASE-PROGRESS.md, find most recent iteration, extract "LSD file:" field value.

**Spawn diagnostic specialist via Task tool:**
```
Task(
  agent_type="lucy-diagnostic",
  instructions="Analyze LSD failure for compound at <compound_path>.

  Read:
  - <compound_path>/CASE-PROGRESS.md (iteration history)
  - <compound_path>/<latest_lsd_file> (latest LSD file)

  Failure type: <failure_type>

  Run systematic diagnostic checks per skill/diagnostic/SKILL.md.
  Document ALL checks (PASS and FAIL).
  Identify root cause with evidence.

  Write structured report to <compound_path>/DIAGNOSTIC-REPORT.md.
  Include: findings, root cause, recommended fixes with LSD command examples.
  Rate all findings and recommendations as HIGH/MEDIUM/LOW confidence.
  "
)
```

**Wait for specialist to complete** (Task tool handles async execution).

After completion, proceed to extract_diagnostic_findings step.
</step>
```

### DIAGNOSTIC-REPORT.md Extraction Step

Source: skill/supervisor/SKILL.md Section 5 "After Diagnostic Specialist Completes"

```markdown
<step name="extract_diagnostic_findings">
Read and parse DIAGNOSTIC-REPORT.md to extract root cause and primary fix for advisory generation.

**Check report exists:**
```bash
if [ ! -f "<compound_path>/DIAGNOSTIC-REPORT.md" ]; then
  echo "ERROR: DIAGNOSTIC-REPORT.md not found after specialist delegation"
  echo "Falling back to basic advisory"
  # Set flag: use_basic_advisory = true
  # Proceed to intervene step
fi
```

**Read full report:**
```
Read: <compound_path>/DIAGNOSTIC-REPORT.md
```

**Extract root cause:**
1. Locate "## Root Cause" section header
2. Extract content from "**Primary:**" line until "**Why it caused failure:**" line (or next section)
3. Store as: root_cause_primary

**Extract primary fix:**
1. Locate "## Recommended Fixes" section header
2. Find first subsection marked "(PRIMARY)"
3. Extract "**Action:**" content (may include code block)
4. Extract "**Verification:**" content
5. Store as: fix_action, fix_verification

**Generate specialist-informed advisory:**
```
Diagnostic specialist identified root cause: <root_cause_primary>

See DIAGNOSTIC-REPORT.md for full analysis.

Fix: <fix_action>

Verification: <fix_verification>

<pattern-specific additional guidance if applicable>
```

Proceed to respawn step with specialist-informed advisory.
</step>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic supervisor agent (v2.0) | Orchestrator skill + delegated specialist (v2.1) | Phase 29-30 (Feb 2026) | Supervisor logic dissolved into case.md sub-command, diagnostic specialist becomes delegated expert |
| Global intervention counter | Per-pattern intervention counters | Phase 29 (Feb 2026) | Identifies which specific failure mode is recurring, enables pattern-specific delegation |
| Immediate specialist delegation | 2-failure threshold | Phase 30 (Feb 2026) | Prevents specialist delegation for simple issues caught by basic diagnosis |
| Directive interventions (v2.0) | Advisory interventions (v2.1) | Phase 29 (Feb 2026) | Preserves CASE agent autonomy—supervisor says WHAT, agent decides HOW |

**Deprecated/outdated:**
- ~/.claude/agents/supervisor.md (v2.0): Being dissolved into case.md orchestrator in Phase 29, will be deleted in Phase 33
- diagnostic-specialist agent name: Renamed to lucy-diagnostic in Phase 30 for naming consistency (lucy-case-agent, lucy-diagnostic)
- skill/supervisor/SKILL.md: Still exists in Phase 30 but being superseded by case.md orchestrator inline documentation

**Current state (Phase 30):**
- Task tool with multi-agent orchestration is standard pattern (2026)
- File-based structured reporting (DIAGNOSTIC-REPORT.md) for cross-agent communication
- Hierarchical supervision pattern: orchestrator monitors, delegates to specialist when basic diagnosis insufficient
- Per-pattern intervention tracking enables targeted delegation

## Open Questions

Things that couldn't be fully resolved:

1. **Should DIAGNOSTIC-REPORT.md be timestamped for multiple diagnostics?**
   - What we know: skill/diagnostic/SKILL.md says single file overwrites previous, use CASE-PROGRESS.md for history
   - What's unclear: In Phase 30, only 1 specialist delegation per 10-cycle window likely, but edge case exists
   - Recommendation: Follow skill document—single file DIAGNOSTIC-REPORT.md. If multiple diagnostics needed, orchestrator can add timestamp in delegation instructions: "Write to DIAGNOSTIC-REPORT-<timestamp>.md"

2. **What if diagnostic specialist fails to complete (timeout, error)?**
   - What we know: Task tool handles async execution, returns when complete
   - What's unclear: Error handling if specialist crashes or hangs
   - Recommendation: Add timeout handling in orchestrator—if Task doesn't complete within reasonable time (5-10 minutes for deep diagnosis), fall back to basic advisory and log failure. Increment counter normally (specialist delegation attempted).

3. **Should orchestrator cache specialist findings across patterns?**
   - What we know: Specialist analyzes LSD file state, findings specific to that iteration
   - What's unclear: If ZERO_SOLUTION_LOOP at iteration 5 diagnosed, then SOLUTION_EXPLOSION at iteration 8, are findings still relevant?
   - Recommendation: No caching—each delegation is fresh analysis of current state. Different patterns have different root causes. DIAGNOSTIC-REPORT.md is single-file so it naturally replaces previous findings.

## Sources

### Primary (HIGH confidence)
- skill/supervisor/SKILL.md Section 5 (Diagnostic Specialist Delegation) - v2.0 documentation being superseded by Phase 29-30 orchestrator
- skill/diagnostic/SKILL.md Section 3 (DIAGNOSTIC-REPORT.md Template) - defines structured report format
- .claude/agents/diagnostic-specialist.md - existing 455-line agent definition (to be renamed)
- ~/.claude/commands/lucy-ng/case.md lines 577-591 - Phase 29 placeholder for specialist delegation
- .planning/phases/29-case-orchestrator-skill/29-RESEARCH.md - Phase 29 patterns for Task tool spawning

### Secondary (MEDIUM confidence)
- [Claude Code Swarm Orchestration](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea) - multi-agent coordination patterns with Task tool
- [The Task Tool: Claude Code's Agent Orchestration](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2) - Task tool delegation patterns
- [AI Agent Orchestration Patterns - Azure](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) - hierarchical supervision pattern with specialist delegation

### Tertiary (LOW confidence)
- Web search results on multi-agent orchestration (2026) - general patterns, not Claude Code specific

## Metadata

**Confidence breakdown:**
- Delegation trigger logic: HIGH - clearly defined in skill/supervisor/SKILL.md with threshold = 2
- Task tool spawning pattern: HIGH - identical to Phase 29 CASE agent spawning, proven in case.md
- DIAGNOSTIC-REPORT.md parsing: HIGH - structured format with stable section headers, file-based cross-agent communication is standard
- Integration testing approach: MEDIUM - forced failure testing requires mocking loop patterns, complexity medium

**Research date:** 2026-02-08
**Valid until:** 60 days (stable patterns, Task tool API unlikely to change, diagnostic specialist agent already exists)
