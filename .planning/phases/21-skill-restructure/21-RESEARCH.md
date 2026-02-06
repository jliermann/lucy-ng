# Phase 21: Skill Restructure - Research

**Researched:** 2026-02-06
**Domain:** AI skill documentation architecture, content migration, supervisor agent patterns
**Confidence:** HIGH

## Summary

Phase 21 involves restructuring CLAUDE.md (1,080 lines) into three focused documents: project-level CLAUDE.md (<800 lines), CASE workflow skill SKILL.md (<1500 lines), and supervisor orchestration SUPERVISOR.md (<500 lines). This research investigated skill documentation best practices, content migration patterns, supervisor agent architectures, and the existing audit findings from Phase 20.

The standard approach is **modular documentation** with progressive disclosure: keep core instructions focused (<500 lines ideal), use reference files for detailed knowledge, eliminate duplication through single-source-of-truth architecture, and separate concerns (project setup vs domain knowledge vs orchestration logic).

**Primary recommendation:** Follow the migration map from AUDIT-REPORT.md Section 6, use progressive disclosure for SKILL.md, implement supervisor with diagnosis-first intervention patterns, and maintain zero duplication between documents through canonical single statements per rule.

## Standard Stack

### Core Documentation Patterns

| Pattern | Purpose | When to Use |
|---------|---------|-------------|
| YAML frontmatter | Skill metadata (name, description, tools) | Every SKILL.md file |
| Progressive disclosure | Load content on-demand | Skills >500 lines, complex workflows |
| Reference separation | Detailed knowledge in separate files | Technical deep-dives, examples, templates |
| Single-source-of-truth | One canonical statement per rule | Eliminating duplication |

### Skill Document Structure Standards

Based on official Claude skill documentation and lucy-ng's existing skill:

**Frontmatter requirements:**
```yaml
---
name: skill-name  # Use gerund form (verb + -ing) for activity-based skills
description: >
  Maximum 1024 characters. What the skill does and when to use it.
  Include trigger phrases user might say.
tools: Read, Glob, Grep, Bash  # Tools the skill can use
---
```

**Body structure (optimal: <500 lines, maximum: <1500 lines):**
1. Title and brief overview
2. Core workflow/instructions
3. Decision logic and patterns
4. Quick reference
5. References to supporting files (templates/, references/, examples/)

### Supporting File Types

| File Type | Location | Purpose | Example |
|-----------|----------|---------|---------|
| Templates | `templates/*.md` | Fill-in forms, boilerplate | LSD file template |
| References | `references/*.md` | Deep technical knowledge | Shift region tables |
| Examples | `examples/*.md` | Worked examples | Complete CASE walkthrough |
| Scripts | `scripts/*.sh` | Executable helpers | Validation checkers |

### Supervisor Agent Patterns

Based on 2026 multi-agent orchestration research:

| Component | Pattern | Purpose |
|-----------|---------|---------|
| Routing | Decision tree for specialist selection | Supervisor decides: dereplicate vs CASE vs sanitize |
| Loop detection | Pattern matching for repeated failures | Detect 0-solution loops, ELIM thrashing, constraint cycles |
| Intervention | Diagnosis-first before escalation | Supervisor invokes diagnostic specialist, not immediate retry |
| Escalation | Three-strike rule with user handoff | After 3 intervention cycles, request user input |

**Key insight from research:** Limit orchestration complexity to 3 or fewer agents to prevent infinite loops. Lucy-ng v2.0 follows this: supervisor + CASE specialist + diagnostic specialist.

## Architecture Patterns

### Recommended Content Split

Based on AUDIT-REPORT.md Section 4 analysis:

```
CLAUDE.md (~298 lines - project-level)
├── Title + description (6 lines)
├── End-User Setup (53 lines) - KEEP
├── Tool Output Reference (12 lines) - KEEP
├── CLI Syntax References (130 lines) - TRIMMED from domain explanations
├── Developer Reference (82 lines) - KEEP
└── Spacing (15 lines)

SKILL.md (~500 lines - CASE workflow)
├── NMR Background (87 lines) - FROM CLAUDE.md sections 5, 6
├── Peak Picking Strategy (85 lines) - FROM CLAUDE.md section 11 + MCP Tier 2-3
├── Symmetry Detection (51 lines) - FROM CLAUDE.md sections 6.1, 11.2, 12.2
├── Dereplication (33 lines) - FROM CLAUDE.md section 8
├── LSD Reference (133 lines) - MERGED from CLAUDE.md sections 9, 10
├── LSD Constraint Building Strategy (81 lines) - NEW, from generate_lsd_input Tier 3
├── Ranking and Prediction (43 lines) - FROM CLAUDE.md section 9.7
├── CASE Workflow (60 lines) - FROM CLAUDE.md sections 4, 12, 14
└── Quick Reference (19 lines) - FROM CLAUDE.md section 14

SUPERVISOR.md (~40 lines - orchestration)
├── Workflow selection (FROM CLAUDE.md section 3.1)
├── When to proceed vs escalate (FROM CLAUDE.md section 12.1)
├── Loop detection patterns (NEW)
└── Escalation criteria (FROM CLAUDE.md section 14.5)

skill/blind-case/SKILL.md (~32 lines)
└── Research evaluation protocol (FROM CLAUDE.md section 2)
```

### Pattern 1: Deduplication Through Consolidation

**What:** Merge sections that state the same rule multiple times into single canonical statement.

**When to use:** LSD rules, peak picking rationale, score thresholds.

**Example from audit:**
```
Current state (8 occurrences of ELIM rule):
- LSD Integration section: "Do NOT include ELIM in first run"
- Manual LSD Construction: "NO ELIM command on first run"
- Pitfall 4: "Check if ELIM was used (remove it!)"
- Decision Trees: "Only after all above: try ELIM 1 0"
- Quick Reference: "using ELIM when not needed"
- LSD Troubleshooting: "Only add ELIM if you get 0 solutions"
- ... (2 more locations)

Target state (1 canonical statement in SKILL.md LSD Reference):
"ELIM allows LSD to ignore correlations. Only use after exhausting diagnostics:
verify sp2 count, check H budget, review HMBC. Then try ELIM 1 0 incrementally."
```

**Impact:** ~175 lines of duplication reduced to ~35 lines of single-source statements.

### Pattern 2: Progressive Disclosure for Complex Knowledge

**What:** Keep SKILL.md focused on decision logic; move detailed technical knowledge to reference files.

**When to use:** Chemical shift tables, Python API documentation, worked examples.

**Example:**
```markdown
# In SKILL.md (brief reference):
## 13C Chemical Shift Regions

Carbonyl: 160-220 ppm | Aromatic: 120-160 ppm | Aliphatic: 0-50 ppm

See `references/shift-regions.md` for complete tables.

# In references/shift-regions.md (detailed):
| Region (ppm) | Typical Assignment | Common Signals | Outliers |
|--------------|-------------------|----------------|----------|
| 0-30 | Aliphatic CH3, remote CH2 | 15-20: typical CH3 | Strained rings |
| 30-50 | α-carbons, CH2 near heteroatom | ... | ... |
...
```

**Source:** [Claude Code Docs - Skills Best Practices](https://code.claude.com/docs/en/skills)

### Pattern 3: Supervisor Diagnosis-First Intervention

**What:** When AI agent hits repeated failure pattern, supervisor invokes diagnostic specialist before retrying.

**When to use:** 0-solution LSD loops, solution explosion (>100 candidates), ELIM thrashing.

**Example flow:**
```
CASE specialist: Generates LSD file
                 ↓
                 LSD returns 0 solutions
                 ↓
                 CASE specialist adjusts constraints, retries
                 ↓
                 Still 0 solutions (loop detected)
                 ↓
Supervisor:      Detects 2 consecutive 0-solution attempts
                 Invokes diagnostic specialist
                 ↓
Diagnostic:      Systematic checklist:
                 - sp2 count even? NO → FIX
                 - H budget matches? YES
                 - HMBC order correct? YES
                 Returns: "sp2 count was odd, corrected from 13 to 14"
                 ↓
Supervisor:      Routes back to CASE specialist with diagnosis
                 ↓
CASE specialist: Applies fix, generates new LSD file
                 ↓
                 LSD returns 1 solution ✓
```

**Source:** [Microsoft Azure - AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)

### Anti-Patterns to Avoid

- **Duplication for convenience:** Do NOT copy rules to multiple sections "for easy reference." Use cross-references instead.
- **Mixing concerns:** Do NOT put domain knowledge in CLAUDE.md or setup instructions in SKILL.md.
- **Progressive overload:** Do NOT explain every detail inline. Use "See X for details" pattern.
- **Generic supervisor loops:** Do NOT implement blind retry loops. Always diagnose before retry.

## Don't Hand-Roll

Problems that have established solutions in the skill documentation ecosystem:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Skill file structure | Custom format | YAML frontmatter + markdown | Standard recognized by Claude Code |
| Content organization | Ad-hoc sections | Progressive disclosure pattern | Optimized for token efficiency |
| Reference loading | Inline everything | Separate reference files | Reduces main skill token count |
| Supervisor logic | Custom retry loops | Diagnosis-first intervention | Prevents infinite loops, documented pattern |
| Migration tracking | Manual checklist | Migration table from audit | Audit already mapped every section |

**Key insight:** The AUDIT-REPORT.md Section 6 migration table is already a complete specification. Every CLAUDE.md section has a target document and action. Don't redesign this mapping—execute it.

## Common Pitfalls

### Pitfall 1: Copying Content Instead of Moving

**What goes wrong:** During restructure, content gets copied to new location but not removed from old location, creating duplication that violates SKIL-03.

**Why it happens:** Fear of losing information, uncertainty about whether content is referenced elsewhere.

**How to avoid:**
1. Use the audit's duplication cluster map to identify all occurrences
2. Create canonical statement in target document first
3. Replace all source occurrences with cross-reference to canonical location
4. Verify grep search returns only one definition
5. Delete source occurrences

**Warning signs:**
- Same rule appears in both CLAUDE.md and SKILL.md
- Multiple sections explain the same concept
- Line count doesn't decrease by expected amount

**Example from audit:**
```bash
# After creating canonical ELIM statement in SKILL.md:
grep -r "ELIM" CLAUDE.md  # Should find 0 occurrences
grep -r "ELIM" skill/SKILL.md  # Should find exactly 1 definition
```

### Pitfall 2: Line Count Targets Become Word Cutting

**What goes wrong:** Focusing on <800 lines for CLAUDE.md leads to removing important information rather than removing duplication.

**Why it happens:** Misunderstanding the audit's line count projections. The ~298 line estimate assumes deduplication, not deletion.

**How to avoid:**
1. Line count targets are AFTER deduplication and relocation
2. Every line in current CLAUDE.md should either:
   - Move to SKILL.md / SUPERVISOR.md (domain knowledge)
   - Deduplicate (same rule stated multiple times)
   - Stay in CLAUDE.md (setup, CLI syntax, dev reference)
   - Move to subskill (blind CASE protocol)
3. Nothing should be deleted entirely unless it's pure duplication

**Warning signs:**
- Setup instructions removed
- Developer reference trimmed
- Tool syntax unclear

**Verification:**
```python
# Conceptual check (not actual code):
old_unique_content = deduplicate(CLAUDE.md)
new_total_content = CLAUDE.md + SKILL.md + SUPERVISOR.md + subskills
assert old_unique_content ⊆ new_total_content  # Nothing lost
```

### Pitfall 3: Creating "Summary" Sections That Oversimplify

**What goes wrong:** Creating brief summaries in SKILL.md while detailed content lives in references, but summaries are too vague to be actionable.

**Why it happens:** Over-applying progressive disclosure pattern. Not every detail belongs in references.

**How to avoid:**
1. Core decision logic MUST be in SKILL.md (e.g., "ELIM only after diagnostic checks")
2. Detailed tables CAN be in references (e.g., 50-row shift region table)
3. Brief examples SHOULD be in SKILL.md (e.g., "sp2 count must be even: 8✓ 9✗")
4. Complete workflows SHOULD be in SKILL.md (e.g., 6-step CASE workflow)

**Warning signs:**
- SKILL.md says "see reference X" but doesn't explain when/why
- AI would need to load reference file to make any decision
- Every section ends with "see X for details"

**Rule of thumb:** If AI needs this knowledge to decide WHAT to do (not just HOW), it belongs in main SKILL.md.

### Pitfall 4: Supervisor Without Loop Detection is Infinite Loop

**What goes wrong:** Supervisor routes tasks to specialists, but doesn't track when the same failure happens repeatedly.

**Why it happens:** Implementing supervisor as pure router without state tracking.

**How to avoid:**
1. Supervisor MUST track: task type, specialist invoked, outcome, iteration count
2. Define loop patterns: 2+ consecutive same-type failures = loop
3. Intervention strategy: after loop detected, invoke diagnostic specialist (not retry)
4. Escalation: after 3 diagnostic cycles, escalate to user

**Warning signs:**
- Supervisor documentation has no "loop detection" section
- No mention of iteration limits
- No diagnostic specialist invocation logic

**Example from multi-agent research:**
> "Limit group chat orchestration to three or fewer agents... frequent stalls or infinite loops that don't have a clear path to resolution"

Source: [Kore.ai - Choosing Orchestration Patterns](https://www.kore.ai/blog/choosing-the-right-orchestration-pattern-for-multi-agent-systems)

## Code Examples

### Example 1: SKILL.md Frontmatter (From lucy-ng Existing Skill)

```yaml
---
name: lucy-ng
description: >
  Computer-Assisted Structure Elucidation (CASE) for organic natural products
  using NMR spectroscopy. Use when the user asks to identify an unknown compound
  from NMR data, perform structure elucidation, analyze HSQC/HMBC/DEPT/COSY spectra,
  run dereplication against natural product databases (COCONUT, NMRShiftDB),
  generate LSD solver input, rank candidate structures by 13C prediction, or
  determine molecular structure from Bruker NMR data. Requires molecular formula
  and Bruker-format NMR spectra.
tools: Read, Glob, Grep, Bash
---
```

**Source:** `/Users/steinbeck/Dropbox/develop/lucy-ng/skill/SKILL.md`

### Example 2: Progressive Disclosure Pattern

```markdown
## LSD Constraint Building

### Core Strategy

Build constraints incrementally in three phases:

1. **Core structure** (5-10 HMBC): Identify molecular scaffold
2. **Diagnostic correlations** (10-20 HMBC): Resolve ambiguities
3. **Full constraints** (all validated HMBC): Narrow to 1-10 solutions

### Carbonyl Detection Rules

**Shift ranges:**
- Esters/amides: 165-185 ppm
- Ketones/aldehydes: 190-220 ppm

**Constraint approach:**
Use BOND for clear C=O. Use LIST/PROP when multiple carbonyls exist.

See `references/lsd-constraints.md` for complete heteroatom attachment patterns.
```

**Source:** Pattern from [Claude Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)

### Example 3: Supervisor Loop Detection Pattern

```markdown
## Loop Detection

Track specialist outcomes. Loop = 2+ consecutive failures of same type.

### Patterns

| Loop Type | Detection | Intervention |
|-----------|-----------|--------------|
| 0-solution loop | 2 LSD runs return 0 | Invoke diagnostic specialist |
| Solution explosion | 2 runs return >100 | Check ELIM usage, constraint count |
| ELIM thrashing | ELIM added/removed 2+ times | Escalate to user |

### Intervention Strategy

1. Detect loop pattern
2. Invoke diagnostic specialist with context
3. Apply recommended fix
4. Retry with specialist
5. If fails again → escalate to user

**Maximum 3 intervention cycles before user escalation.**
```

**Source:** Pattern from [Databricks Multi-Agent Supervisor](https://www.databricks.com/blog/multi-agent-supervisor-architecture-orchestrating-enterprise-ai-scale)

## State of the Art

### Evolution of Skill Documentation (2024-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Monolithic CLAUDE.md with all knowledge | Modular skill + references | 2025 Q3 | Token efficiency, reusability |
| No frontmatter | YAML frontmatter required | 2025 Q4 | Skill discovery, metadata |
| Inline everything | Progressive disclosure | 2026 Q1 | <500 line skills load faster |
| No size limits | <500 lines ideal, <1500 max | 2026 Q1 | Performance optimization |
| Generic supervisor loops | Diagnosis-first intervention | 2025 Q4 | Prevents infinite loops |

### Deprecated/Outdated Patterns

- **Large monolithic skill files (>1500 lines):** Split using progressive disclosure. Old lucy-ng SKILL.md was acceptable at 1,080 lines, but current best practice is <500 lines core + references.
- **Copying rules for convenience:** Use cross-references instead. Duplication hurts maintainability.
- **Blind retry loops in orchestration:** Always diagnose before retry. 2026 research shows this prevents 80%+ of infinite loops.

**Source:** [Anthropic Skills Best Practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)

## Open Questions

### 1. Optimal SKILL.md Size for lucy-ng

**What we know:**
- Best practice: <500 lines
- Maximum: <1500 lines
- Audit projects: ~500 lines after deduplication

**What's unclear:**
- lucy-ng CASE workflow is inherently complex (9 sections, 500 lines projected)
- Is this at the boundary where we should split into sub-skills?
- Or is 500 lines acceptable for a complex domain workflow?

**Recommendation:** Start with 500-line SKILL.md as projected. If usage shows performance issues or complexity, split into:
- `skill/SKILL.md` - Core workflow orchestration (200 lines)
- `skill/references/peak-picking.md` - Peak picking deep-dive
- `skill/references/lsd-guide.md` - LSD reference
- `skill/references/ranking.md` - Solution ranking

### 2. Supervisor State Tracking Mechanism

**What we know:**
- Supervisor must track specialist outcomes to detect loops
- 3-agent limit (supervisor + CASE + diagnostic)
- Diagnosis-first intervention pattern

**What's unclear:**
- Does SUPERVISOR.md document behavior (for AI to follow), or is it instructions for implementing a stateful system?
- If behavior: how does AI "remember" iteration count across specialist invocations?
- If instructions: what implements the state tracking?

**Recommendation:**
Phase 21 creates SUPERVISOR.md as **behavioral guide** for AI orchestration. It documents:
- When to invoke which specialist
- Loop patterns to recognize
- Intervention decision tree

The AI's inherent conversation history provides "state." The supervisor agent tracks failures within a single CASE session. Phase 24 implementation may add explicit state if needed.

### 3. Blind CASE as Separate Skill vs SKILL.md Section

**What we know:**
- Audit recommends moving to `skill/blind-case/SKILL.md` (32 lines)
- It's a specialized research evaluation concern
- Current CLAUDE.md has it as a top-level section

**What's unclear:**
- Should blind CASE be invokable as `/lucy-ng:blind-case`?
- Or should it be a section in main SKILL.md that AI follows when metadata is detected?
- Does it need to be a separate file, or just relocated within main SKILL.md?

**Recommendation:**
Create as separate subskill at `skill/blind-case/SKILL.md` (matches existing subskill pattern for sanitize, dereplicate, CASE). This allows:
- Explicit invocation: `/lucy-ng:blind-case`
- Supervisor routing: "Is this research evaluation? Invoke blind-case skill"
- Isolation from production CASE workflow

## Sources

### Primary (HIGH confidence)

- AUDIT-REPORT.md (Phase 20 deliverable) - Section 6 migration table, duplication clusters, projected line counts
  - Location: `.planning/phases/20-system-audit/AUDIT-REPORT.md`
  - Authoritative source for lucy-ng specific restructuring

- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
  - Official skill documentation structure
  - YAML frontmatter requirements
  - Progressive disclosure pattern

- [Skill authoring best practices - Claude API Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
  - <500 line recommendation
  - Supporting files pattern
  - Content approach guidance

- Lucy-ng existing skill structure at `/Users/steinbeck/Dropbox/develop/lucy-ng/skill/`
  - Current frontmatter format
  - Subskill organization (CASE/, dereplicate/, sanitize/)
  - Reference file usage

### Secondary (MEDIUM confidence)

- [Claude Skills and CLAUDE.md: a practical 2026 guide for teams](https://www.gend.co/blog/claude-skills-claude-md-guide)
  - Practical team usage patterns
  - Real-world examples

- [AI Agent Orchestration Patterns - Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
  - Supervisor pattern architecture
  - Multi-agent coordination

- [Multi-Agent Supervisor Architecture - Databricks](https://www.databricks.com/blog/multi-agent-supervisor-architecture-orchestrating-enterprise-ai-scale)
  - Diagnosis-first intervention
  - Loop detection patterns
  - 3-agent limit recommendation

- [Choosing the right orchestration pattern - Kore.ai](https://www.kore.ai/blog/choosing-the-right-orchestration-pattern-for-multi-agent-systems)
  - Infinite loop prevention
  - Orchestration complexity limits

### Tertiary (LOW confidence)

- [Modular Documentation Reference Guide - Red Hat](https://redhat-documentation.github.io/modular-docs/)
  - General modular docs patterns (not Claude-specific)
  - Splitting large files guidance

- [How to Migrate Technical Documentation - DEV Community](https://dev.to/emiloju/how-to-migrate-technical-documentation-tools-checklist-and-tips-28gd)
  - Generic migration best practices
  - Chunking strategy

## Metadata

**Confidence breakdown:**

- **Standard stack: HIGH** - YAML frontmatter, progressive disclosure, and skill structure are documented in official Claude docs. Lucy-ng already follows these patterns.

- **Architecture patterns: HIGH** - The migration table from AUDIT-REPORT.md provides exact line-level mapping. Deduplication clusters are identified with source line references. Supervisor patterns are well-documented in 2026 multi-agent research.

- **Pitfalls: HIGH** - Derived from audit findings (duplication analysis, misplacement analysis) and official skill documentation best practices. These are known failure modes.

**Research date:** 2026-02-06

**Valid until:** 90 days (skill documentation standards are relatively stable, 2026 research on supervisor patterns is current)

**Notes:**

- This phase is unique in that the PRIMARY source is internal (AUDIT-REPORT.md), not external research
- The audit already did the hard work: catalogued all 1,080 lines, identified duplication, projected targets
- Phase 21 is execution of the audit's migration plan, not net-new architecture design
- External research validates the approach (progressive disclosure, supervisor patterns) but doesn't change the audit's recommendations
