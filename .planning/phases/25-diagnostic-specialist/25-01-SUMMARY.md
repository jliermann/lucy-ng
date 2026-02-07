---
phase: 25-diagnostic-specialist
plan: 01
subsystem: ai-agents
tags: [diagnostic, lsd, systematic-checks, root-cause-analysis, claude-code-subagents]

requires:
  - 24-02  # Supervisor agent definition (spawns diagnostic specialist)

provides:
  - diagnostic-specialist-skill  # Deep LSD diagnostic knowledge
  - diagnostic-specialist-agent  # Claude Code subagent for failure analysis

affects:
  - future-case-workflows  # Enables deep diagnostic when supervisor basic diagnosis insufficient

tech-stack:
  added: []  # No new tech, uses existing Claude Code subagent framework
  patterns:
    - systematic-diagnostic-procedures  # Ordered checklist approach for 0-solution and 1000+ failures
    - structured-diagnostic-reports  # Markdown template with findings/root-cause/fixes
    - quantitative-evidence-based-diagnosis  # No generic advice, specific measurements required

key-files:
  created:
    - skill/diagnostic/SKILL.md  # 1,874 lines of LSD diagnostic domain knowledge
    - .claude/agents/diagnostic-specialist.md  # 455 lines agent definition

decisions:
  - id: DIAG-01
    what: Diagnostic specialist is Claude Code subagent with deep LSD manual knowledge
    why: Separation of concerns — supervisor does basic diagnosis, specialist handles deep analysis when stuck
    impact: Enables systematic root cause analysis without bloating supervisor
    alternatives: [Supervisor does all diagnosis (rejected - skill bloat), Python diagnostic scripts (rejected - less flexible than AI reasoning)]

  - id: DIAG-02
    what: Zero-solution procedure has 5 systematic checks (sp2 count, H budget, 1J artifacts, correlation order, close carbons)
    why: Ordered checklist ensures complete diagnostic coverage, not ad-hoc guessing
    impact: All common 0-solution causes detected with quantitative evidence
    alternatives: [Single root cause check (rejected - misses multi-factor failures), Generic retry advice (rejected - not actionable)]

  - id: DIAG-03
    what: Solution explosion procedure has 5 systematic checks (ELIM, constraint ratio, quaternary, heteroatoms, symmetry)
    why: Under-constrained structures have multiple contributing factors requiring systematic analysis
    impact: Identifies both primary (low constraint count) and contributing (quaternary floating atoms) causes
    alternatives: [Generic "add more constraints" (rejected - not specific), Focus only on ELIM (rejected - misses other causes)]

  - id: DIAG-04
    what: Structured diagnostic report format with findings/root-cause/fixes sections in DIAGNOSTIC-REPORT.md
    why: Human-readable, AI-parseable, consumed by supervisor and CASE agent for actionable next steps
    impact: Clear communication of diagnosis with specific LSD command examples
    alternatives: [JSON format (rejected - less readable), Free-form narrative (rejected - hard to parse), Inline annotations in LSD file (rejected - loses audit trail)]

  - id: DIAG-05
    what: Agent has full LSD manual knowledge via skill/diagnostic/SKILL.md (MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM)
    why: Diagnostic recommendations require deep command knowledge to provide specific fixes with correct syntax
    impact: Reports include exact LSD commands (not "fix sp2 count" but "change MULT 7 from sp2 to sp3")
    alternatives: [Basic command knowledge only (rejected - generic advice), Link to external LSD manual (rejected - context switching)]

  - id: DIAG-06
    what: Model is sonnet (diagnostic reasoning, not NMR analysis)
    why: Same rationale as supervisor — orchestration and diagnostic logic, not domain-specific NMR inference
    impact: Cost-effective, appropriate model tier for systematic check execution
    alternatives: [Opus (rejected - overkill for checklist execution), Haiku (rejected - may lack reasoning depth)]

metrics:
  duration: 10 minutes
  completed: 2026-02-07
---

# Phase 25 Plan 01: Diagnostic Specialist Summary

**One-liner:** Created diagnostic specialist agent with systematic LSD failure analysis procedures (5 checks for 0-solution, 5 for 1000+), producing structured reports with quantitative evidence and specific LSD command fixes.

---

## What Was Built

### 1. Diagnostic Specialist Skill Document (skill/diagnostic/SKILL.md)

**Size:** 1,874 lines

**Structure:**
1. LSD Command Reference (DIAG-05) — deep diagnostic-relevant details for all commands
2. Systematic Diagnostic Procedures — zero-solution (5 checks) and solution-explosion (5 checks)
3. Structured Diagnostic Report Template (DIAG-04) — complete markdown format
4. Example Diagnostic Reports — 3 complete examples (1J artifact, odd sp2, solution explosion)
5. Anti-Patterns — 6 common mistakes to avoid
6. Cross-References — to skill/SKILL.md without duplication

**Key content:**

**LSD Command Reference (Section 1):**
- MULT: Edge cases (bridgehead carbons, nitrogen hybridization), common errors
- HSQC/HMQC: Proton position semantics, ordering requirement
- HMBC: 1J artifact detection, ambiguous assignment from close carbons
- BOND, LIST, PROP, ELEM, SYME: When to use, what happens when wrong
- ELIM: Last resort only, diagnostic checklist before use

**Zero-Solution Procedure (Section 2.1, DIAG-02):**
1. sp2 count check (MUST be even)
2. Hydrogen budget check (matches formula)
3. 1J artifact detection (HMBC vs HSQC, ±1.5 ppm C, ±0.3 ppm H)
4. Correlation order check (HSQC before HMBC)
5. Close carbon ambiguity check (resolution-based, min_spacing = 1.5 / pts_per_ppm)

**Solution Explosion Procedure (Section 2.2, DIAG-03):**
1. ELIM presence check (remove if found)
2. Constraint/atom ratio (target 0.5-1.0, < 0.5 = insufficient)
3. Quaternary carbon connectivity (0 HMBC = floating atom)
4. Heteroatom position constraints (BOND or LIST/PROP for O, N, S)
5. Symmetry encoding (SYME or LIST/PROP fallback)

**Report Template (Section 3, DIAG-04):**
- Summary: 1-2 paragraphs, root cause one-liner, confidence
- Findings: 2-5 findings with evidence, impact, confidence (CRITICAL/MAJOR/MINOR)
- Root Cause: primary + contributing factors, mechanism explanation
- Recommended Fixes: 1-3 fixes with LSD commands, verification, priority (PRIMARY/SECONDARY)
- Supporting Data: LSD file stats, iteration history, spectral quality
- Next Steps: immediate action, verification, follow-up
- Diagnostic Methodology: all systematic checks (PASS/FAIL), time, tools
- Metadata: confidence breakdown per finding/fix

**Example Reports (Section 4):**
1. Virgiline 1J artifact (0 solutions) — C155.2-H2.1 matches HSQC within tolerance, fix: remove HMBC command
2. Caffeine odd sp2 (0 solutions) — 9 sp2 atoms (ether O marked sp2), fix: change to sp3
3. Unknown compound solution explosion (1,234 solutions) — ratio 0.19 + 3 quaternary 0 HMBC, fix: add 5-8 HMBC targeting quaternaries

### 2. Diagnostic Specialist Agent Definition (.claude/agents/diagnostic-specialist.md)

**Size:** 455 lines

**YAML frontmatter:**
- name: diagnostic-specialist
- description: LSD failure diagnostic specialist with deep manual knowledge
- tools: Read, Bash (no Write — report via output mechanism)
- model: sonnet (DIAG-06)

**Structure:**
1. Role statement
2. Domain knowledge references (skill/diagnostic/SKILL.md, skill/SKILL.md)
3. Diagnostic workflow (5 steps)
4. Important rules (6 rules)
5. Input specification (from supervisor)
6. Output specification (DIAGNOSTIC-REPORT.md)
7. Example diagnostic outputs (3 scenarios)
8. Anti-patterns to avoid (6 anti-patterns)

**5-Step Workflow:**
1. Gather Context — read CASE-PROGRESS.md, LSD file, spectral quality
2. Run Systematic Checks — zero-solution or solution-explosion procedure, document ALL checks
3. Identify Root Cause — primary + contributing, rate confidence HIGH/MEDIUM/LOW
4. Recommend Fixes — specific LSD commands, verification, priority
5. Write Structured Report — DIAGNOSTIC-REPORT.md with template format

**6 Important Rules:**
1. ALWAYS run full systematic procedure (not stop at first PASS)
2. NEVER give generic advice (provide specific LSD commands)
3. ALWAYS include quantitative evidence (not hunches)
4. Rate confidence honestly (LOW flags need for manual verification)
5. Prioritize fixes (PRIMARY first, SECONDARY optional)
6. Reference skill documents (don't duplicate content)

**Input from supervisor:**
- Compound path
- Latest LSD file path
- CASE-PROGRESS.md path
- Failure type (0 solutions, 1000+ solutions, other)

**Output to supervisor:**
- DIAGNOSTIC-REPORT.md in compound directory
- Structured markdown with findings, root cause, fixes
- Consumed by supervisor to advise CASE agent

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Key Outcomes

1. **Systematic diagnostic capability** — supervisor can delegate deep analysis to specialist when basic diagnosis insufficient

2. **Quantitative evidence requirement** — all findings must include measurements (sp2 count, constraint ratio, carbon spacing, etc.)

3. **Actionable recommendations** — LSD command examples in every fix (not "add constraints" but "HMBC 5 12" with specific atoms)

4. **Complete audit trail** — all systematic checks documented (PASS and FAIL) in diagnostic report

5. **Structured report format** — supervisor and CASE agent consume consistent markdown structure

6. **Multi-cause handling** — procedures identify both primary root cause and contributing factors

7. **Confidence transparency** — HIGH/MEDIUM/LOW ratings with reasoning, enables user to assess diagnostic certainty

---

## Integration Points

### Supervisor → Diagnostic Specialist

**Trigger conditions** (from skill/supervisor/SKILL.md Section 4):
- Zero-solution loop (3+ iterations, 0 solutions) AND basic checks pass
- Solution explosion (3+ iterations, >100 solutions, <10% reduction) AND basic checks pass
- Constraint churning (5+ iterations, high churn, no convergence) AND unclear root cause

**Spawning mechanism:**
```
Task(
  agent_type="diagnostic-specialist",
  instructions="Analyze LSD failure for compound at <path>.

  Read:
  - <path>/CASE-PROGRESS.md (iteration history)
  - <path>/<filename>.lsd (latest LSD file)

  Diagnose:
  - Why did LSD return <0 solutions | 1000+ solutions>?
  - Run systematic checks for <failure type>
  - Identify root cause with evidence

  Output:
  - Write structured report to <path>/DIAGNOSTIC-REPORT.md
  - Include: findings, root cause, recommended fixes with LSD command examples

  Confidence: Rate all findings and recommendations as HIGH/MEDIUM/LOW
  "
)
```

**After diagnostic:**
1. Supervisor reads DIAGNOSTIC-REPORT.md
2. Extracts root cause and primary fix
3. Advises CASE agent with specific constraints based on diagnostic
4. Includes reference: "See DIAGNOSTIC-REPORT.md for full analysis"

### Diagnostic Specialist → Skill Documents

**skill/diagnostic/SKILL.md:**
- Full LSD command reference with diagnostic details
- Systematic procedures for 0-solution and 1000+ failures
- Report template and example reports
- Anti-patterns

**skill/SKILL.md:**
- Section 2: Spectral quality assessment (S/N, resolution, artifacts)
- Section 6: Basic LSD command format (cross-referenced, not duplicated)
- Section 7: Incremental HMBC strategy (referenced for fix recommendations)
- Section 10: Error tolerance and ambiguity (close carbons, DEPT/HSQC, quaternary)

**No duplication** — diagnostic skill focuses on deep diagnostic knowledge, main skill provides NMR context

---

## Testing Notes

Diagnostic specialist can be tested with known failure cases:

**Test Case 1: 1J Artifact (Virgiline)**
- Input: LSD file with HMBC C155.2-H2.1 matching HSQC C155.08-H2.08
- Expected: Finding 1 = 1J artifact, root cause = impossible constraint, fix = remove HMBC command, confidence = HIGH
- Verification: After fix, solutions > 0

**Test Case 2: Odd sp2 Count (Caffeine)**
- Input: LSD file with ether oxygen marked sp2 (9 sp2 atoms total)
- Expected: Finding 1 = odd sp2 count, root cause = ether O hybridization, fix = change MULT 7 to sp3, confidence = HIGH
- Verification: After fix, sp2 count = 8 (even), solutions > 0

**Test Case 3: Solution Explosion (Under-Constrained)**
- Input: LSD file with 3 HMBC for 16 atoms, 3 quaternary with 0 HMBC each
- Expected: Finding 1 = low ratio (0.19), Finding 2 = quaternary floating, root cause = insufficient constraints, fix = add 5-8 HMBC targeting quaternaries, confidence = HIGH
- Verification: After fix, solution count < 100

---

## Future Enhancements

**Phase 26 foundation:**
- Diagnostic specialist integrates with any MCP tool set (supervisor uses Task tool, agnostic to underlying MCP tools)
- Diagnostic procedures reference skill/SKILL.md for domain knowledge (future skill expansion automatically benefits diagnostic)

**Potential extensions:**
1. **SYME fallback logic** — if LSD version doesn't support SYME, auto-generate LIST/PROP encoding for symmetry
2. **Atom environment database integration** — replace shift-based constraint mapping (Section 10.3, skill/diagnostic/SKILL.md) with learned model
3. **Multi-diagnostic tracking** — compare multiple diagnostic reports over iterations to detect pattern evolution
4. **Diagnostic confidence calibration** — track actual fix success rate vs predicted confidence, refine thresholds
5. **Integration with spectral quality specialist** — delegate spectral quality re-assessment if diagnostic finds poor S/N is root cause

---

## Success Criteria Verification

- [x] DIAG-01: Diagnostic specialist agent defined as Claude Code subagent with deep LSD manual knowledge
  - ✓ .claude/agents/diagnostic-specialist.md created (455 lines)
  - ✓ YAML frontmatter with tools: Read, Bash, model: sonnet
  - ✓ References skill/diagnostic/SKILL.md for full LSD command knowledge

- [x] DIAG-02: Zero-solution procedure covers sp2 count, H budget, HMBC conflicts (1J artifacts), correlation order, close carbons
  - ✓ Section 2.1 has all 5 checks with procedures and examples
  - ✓ Quantitative evidence required for each check
  - ✓ All checks documented (PASS or FAIL), not stop at first

- [x] DIAG-03: Solution explosion procedure covers ELIM check, constraint count, quaternary connectivity, heteroatom constraints, symmetry
  - ✓ Section 2.2 has all 5 checks with procedures and examples
  - ✓ Constraint/atom ratio threshold (0.5 target) specified
  - ✓ Quaternary floating atom detection with targeted threshold reduction reference

- [x] DIAG-04: Structured diagnostic report format with findings, root cause, recommended fixes with LSD command examples
  - ✓ Section 3 defines complete template
  - ✓ All required sections specified (Summary, Findings, Root Cause, Fixes, Supporting Data, Methodology, Metadata)
  - ✓ Fix examples include exact LSD commands (MULT changes, BOND additions, LIST/PROP encodings)

- [x] DIAG-05: Agent has internalized full LSD manual via skill/diagnostic/SKILL.md (MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM)
  - ✓ Section 1 covers all commands with diagnostic-relevant details
  - ✓ Edge cases documented (bridgehead carbons, nitrogen hybridization)
  - ✓ Common errors and detection methods specified

---

## Files Modified

**Created:**
- `skill/diagnostic/SKILL.md` (1,874 lines) — diagnostic domain knowledge
- `.claude/agents/diagnostic-specialist.md` (455 lines) — agent definition

**Total:** 2,329 lines created

---

## Commits

1. `bfae6c6` — feat(25-01): create diagnostic specialist skill document
   - Full LSD command reference with diagnostic details
   - Systematic 0-solution and 1000+ procedures
   - Structured report template and examples
   - Anti-patterns and cross-references

2. `8b35784` — feat(25-01): create diagnostic specialist agent definition
   - Claude Code subagent with workflow and rules
   - References skill docs without duplication
   - Input/output specification for supervisor integration
   - Example scenarios and anti-patterns

---

## Next Phase Readiness

**Phase 26 (MCP Tool Finalization):**
- Diagnostic specialist uses Task tool delegation (already implemented in supervisor)
- No MCP tool dependencies for diagnostic specialist (uses Read and Bash only)
- Diagnostic procedures reference skill/SKILL.md (any future MCP tool changes in skill don't affect diagnostic agent)
- Ready for integration testing with supervisor loop detection

**Blockers:** None

**Concerns:** None

---

*Completed: 2026-02-07 in 10 minutes*
*Task commits: 2 (bfae6c6, 8b35784)*
*Agent: gsd-executor*
