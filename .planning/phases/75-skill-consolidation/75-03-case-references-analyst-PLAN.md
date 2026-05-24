---
phase: "75"
plan: "03"
slug: case-references-analyst
type: execute
wave: 2
depends_on: ["75-01"]
files_modified:
  - ~/.claude/commands/lucy-ng/case.md
  - ~/.claude/commands/lucy-ng/references/progress-format.md
  - ~/.claude/agents/lucy-solution-analyst.md
autonomous: true
requirements: [SKILL-01]

must_haves:
  truths:
    - "case.md has no 'outlsd 5 < compound.sol > solutions.smi' in any TaskCreate description"
    - "case.md devils-advocate spawn prompt references ring exclusion and COSY equivalence instead of DEFF NOT and SYME"
    - "progress-format.md initialization line uses COSY_equiv=0 and ring_excl=enabled instead of SYME=0 and DEFF NOT=0"
    - "progress-format.md Devils-Advocate template uses 'Ring exclusion' and 'COSY-equiv' fields"
    - "solution-analyst.md uses 'ring exclusion (DEFF F/FEXP)' instead of DEFF NOT"
  artifacts:
    - path: ~/.claude/commands/lucy-ng/case.md
      provides: "Updated orchestrator with native vocabulary in spawn prompts and task descriptions"
      contains: "ring exclusion"
    - path: ~/.claude/commands/lucy-ng/references/progress-format.md
      provides: "Updated progress log format with native constraint tracking fields"
      contains: "COSY_equiv"
  key_links:
    - from: "case.md spawn prompt for devils-advocate"
      to: "devils-advocate.md §2 Bug checklist"
      via: "spawn prompt vocabulary must match what the DA checks"
      pattern: "ring exclusion.*DEFF F"
---

<objective>
Update case.md, progress-format.md, and solution-analyst.md to use native-command vocabulary consistent with the changes in plans 75-01 and 75-02. Remove remaining outlsd manual pipe instructions from case.md TaskCreate descriptions.

Purpose: After 75-01 changes lsd-engineer's skill and 75-02 changes the DA's skill, case.md's spawn prompts and progress-format.md's templates still contain the old vocabulary (SYME, DEFF NOT, manual outlsd pipe). These are the orchestrator-facing instructions that a future CASE run will receive. This plan closes that gap.

Output: Three updated skill files using native-command vocabulary throughout.
</objective>

<execution_context>
@/Users/steinbeck/.claude/get-shit-done/workflows/execute-plan.md
@/Users/steinbeck/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/PROJECT.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-RESEARCH.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-01-SUMMARY.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Remove outlsd pipe and fix spawn prompt in case.md</name>
  <files>~/.claude/commands/lucy-ng/case.md</files>
  <action>
Read the full ~/.claude/commands/lucy-ng/case.md. Then apply these surgical edits:

**Edit A — Line 108: Remove outlsd from iteration-01 TaskCreate description**

Old text (exact):
```
               Convert solutions: outlsd 5 < compound.sol > solutions.smi",
```

New text:
```
               solutions.smi is produced automatically by lucy lsd run (no manual outlsd step).",
```

**Edit B — Line 138: Remove outlsd from lsd-engineer spawn prompt**

Old text (exact):
```
          Convert solutions: outlsd 5 < compound.sol > solutions.smi
```

New text: remove that line entirely. The lsd-engineer spawn prompt paragraph should flow from "Send [ITERATION-COMPLETE]..." directly to "CRITICAL: Read previous LSD file..." without the outlsd line.

**Edit C — Line 300: Remove outlsd from subsequent iteration TaskCreate description**

Old text (exact):
```
                  Convert solutions: outlsd 5 < compound.sol > solutions.smi
```

New text: remove that line entirely.

**Edit D — Line 167: Update devils-advocate spawn prompt — DEFF NOT and SYME references**

Old text (exact):
```
          2. Check for dropped constraints (DEFF NOT, SYME, grouped notation)
```

New text:
```
          2. Check for dropped constraints (ring exclusion DEFF F/FEXP, COSY equivalence pairs, grouped notation)
```
  </action>
  <verify>
    <automated>
# No manual outlsd pipe in case.md
grep -n "outlsd 5 < compound" ~/.claude/commands/lucy-ng/case.md || echo "0 - good"
# Must return 0

# DA spawn prompt updated
grep -n "DEFF NOT, SYME" ~/.claude/commands/lucy-ng/case.md || echo "0 - good"
# Must return 0

grep -n "ring exclusion.*DEFF F\|COSY equivalence" ~/.claude/commands/lucy-ng/case.md
# Must return >= 1 line
    </automated>
  </verify>
  <done>All three outlsd 5 < compound.sol references removed from case.md. Devils-advocate spawn prompt uses native vocabulary (ring exclusion DEFF F/FEXP, COSY equivalence pairs).</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update progress-format.md and solution-analyst.md native vocabulary</name>
  <files>~/.claude/commands/lucy-ng/references/progress-format.md
~/.claude/agents/lucy-solution-analyst.md</files>
  <action>
Read progress-format.md and solution-analyst.md fully. Apply these surgical edits:

**progress-format.md — Edit A — Line 44: Initialization line**

Old text (exact):
```
**Constraint inventory (iteration 0):** MULT=0, HSQC=0, HMBC=0, DEFF NOT=0, SYME=0, BOND=0
```

New text:
```
**Constraint inventory (iteration 0):** MULT=0, HSQC=0, HMBC=0, ring_excl=enabled, COSY_equiv=0, BOND=0
```

**progress-format.md — Edit B — Line 86: Devils-Advocate template DEFF NOT field**

Old text (exact):
```
**DEFF NOT:** <from message>
```

New text:
```
**Ring exclusion:** <from message>
```

**progress-format.md — Edit C — Line 88: Devils-Advocate template SYME field**

Old text (exact):
```
**SYME:** <from message>
```

New text:
```
**COSY-equiv:** <from message>
```

**solution-analyst.md — Edit D — DEFF NOT reference**

Find and replace the DEFF NOT reference at line 105 (per 75-RESEARCH.md Finding 2c):

Old text (exact):
```
Natural products almost never contain cyclopropane or cyclobutane. If **DEFF NOT** was properly applied, this should already be filtered.
```

New text:
```
Natural products almost never contain cyclopropane or cyclobutane. If **ring exclusion (DEFF F/FEXP)** was properly applied, this should already be filtered.
```
  </action>
  <verify>
    <automated>
# progress-format.md: SYME and DEFF NOT gone
grep -n "SYME=\|DEFF NOT=" ~/.claude/commands/lucy-ng/references/progress-format.md || echo "0 - good"
# Must return 0

# progress-format.md: new fields present
grep -n "ring_excl=enabled\|COSY_equiv" ~/.claude/commands/lucy-ng/references/progress-format.md
# Must return >= 2 lines (lines 44 + 88 or nearby)

# solution-analyst.md: DEFF NOT reference updated
grep -n "DEFF NOT" ~/.claude/agents/lucy-solution-analyst.md || echo "0 - good"
# Must return 0

grep -n "ring exclusion.*DEFF F\|DEFF F.*FEXP" ~/.claude/agents/lucy-solution-analyst.md
# Must return >= 1 line
    </automated>
  </verify>
  <done>progress-format.md initialization line uses ring_excl=enabled and COSY_equiv=0. DA template uses Ring exclusion and COSY-equiv fields. solution-analyst.md uses ring exclusion (DEFF F/FEXP) vocabulary. Zero SYME or DEFF NOT instructions remain in any of the three files.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| case.md TaskCreate description → lsd-engineer spawn | Spawn hints must not contradict lsd-engineer's updated skill (outlsd removed in 75-01) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-75-03-01 | Tampering | Removing outlsd line breaks spawn prompt structure | mitigate | Edit removes single line, verified by grep for absence of outlsd 5 < compound |
| T-75-SC | Tampering | npm/pip/cargo installs | accept | No package installs — pure markdown edits |
</threat_model>

<verification>
Full grep suite across all three files:

```bash
# case.md: no manual outlsd pipe
grep -n "outlsd 5 <" ~/.claude/commands/lucy-ng/case.md || echo "PASS: no outlsd pipe"

# case.md: native spawn prompt
grep -n "ring exclusion" ~/.claude/commands/lucy-ng/case.md

# progress-format.md: native fields
grep -n "ring_excl\|COSY_equiv" ~/.claude/commands/lucy-ng/references/progress-format.md

# progress-format.md: old fields gone
grep -n "SYME=\|DEFF NOT=" ~/.claude/commands/lucy-ng/references/progress-format.md || echo "PASS: old fields gone"

# solution-analyst.md: DEFF NOT gone
grep -n "DEFF NOT" ~/.claude/agents/lucy-solution-analyst.md || echo "PASS: no DEFF NOT"
```
</verification>

<success_criteria>
1. Zero "outlsd 5 < compound" occurrences in case.md
2. DA spawn prompt uses "ring exclusion DEFF F/FEXP" and "COSY equivalence pairs"
3. progress-format.md initialization line has ring_excl=enabled and COSY_equiv=0
4. progress-format.md DA template has Ring exclusion and COSY-equiv fields
5. solution-analyst.md has zero DEFF NOT references (only "ring exclusion (DEFF F/FEXP)")
</success_criteria>

<output>
Create /Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-03-SUMMARY.md when done.
NOTE: ~/.claude/ files are NOT committed to the lucy-ng git repo. Only SUMMARY.md is committed.
</output>
