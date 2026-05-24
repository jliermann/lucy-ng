---
phase: "75"
plan: "05"
slug: diagnostic-native
type: execute
wave: 2
depends_on: ["75-01"]
files_modified:
  - ~/.claude/agents/lucy-diagnostic.md
autonomous: true
requirements: [SKILL-01]

must_haves:
  truths:
    - "lucy-diagnostic.md contains no instruction to write SYME (only 'do NOT write SYME / not native' guidance)"
    - "lucy-diagnostic.md documents BOND (gem-dimethyl) and COSY (aromatic equiv-pair) as the native symmetry encoding"
    - "lucy-diagnostic.md grep check uses COSY.*equiv-pair / BOND.*gem-dimethyl instead of grep -i SYME"
    - "lucy-diagnostic.md fix template says 'Add BOND/COSY equivalence constraints' not 'Add SYME constraints'"
    - "No DEFF NOT or outlsd pipe instructions in lucy-diagnostic.md (confirmed absent — no edits needed)"
  artifacts:
    - path: ~/.claude/agents/lucy-diagnostic.md
      provides: "Updated diagnostic skill with native-only symmetry encoding instructions"
      contains: "SYME.*NOT native\\|NEVER write SYME"
  key_links:
    - from: "lucy-diagnostic.md symmetry section"
      to: "lsd-engineer.md native equivalence table (75-01 output)"
      via: "diagnostic agent's fix guidance must match what lsd-engineer will write"
      pattern: "BOND.*gem-dimethyl|COSY.*equiv-pair"
---

<objective>
Update ~/.claude/agents/lucy-diagnostic.md to remove active SYME command teaching and replace it with native BOND/COSY equivalence guidance, consistent with plans 75-01 and 75-02.

Purpose: The validation sign-off glob `! grep -rIl "SYME|DEFF NOT" ~/.claude/agents/lucy-*.md` matches lucy-diagnostic.md (20 SYME references, including direct `SYME atom_index_1 atom_index_2` command instruction at line 249 and the fix template at line 832). Without this fix, the phase verification would always fail even if all other skill files are correctly updated.

The diagnostic agent is spawned only after 2 failed basic interventions (rare path), but it must not instruct SYME either — consistency across all agent skills is required.

No DEFF NOT or outlsd pipe found in lucy-diagnostic.md (confirmed by grep — no edits needed for those).

Output: Updated ~/.claude/agents/lucy-diagnostic.md with SYME section rewritten to BOND/COSY native guidance.
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
  <name>Task 1: Replace SYME section heading, command syntax, and fallback guidance (lines 245-271)</name>
  <files>~/.claude/agents/lucy-diagnostic.md</files>
  <action>
Read the full ~/.claude/agents/lucy-diagnostic.md. Then apply these surgical edits:

**Edit A — Lines 245-271: Replace the entire "### SYME - Symmetry Equivalence" section**

Old text (exact):
```
### SYME - Symmetry Equivalence

**Full syntax:**
```
SYME atom_index_1 atom_index_2
```

**Semantics:** Forces atoms to be topologically equivalent (same environment)

**Note on LSD version support:** SYME may not be supported in all LSD versions. If unsupported, use LIST/PROP as fallback to encode symmetry constraints.

**When to use:**
- Para-substituted benzene (2 pairs of equivalent CH)
- Isopropyl groups (2 equivalent CH3)
- Gem-dimethyl groups (2 equivalent CH3)
- Any detected molecular symmetry

**What this constrains:** Topological equivalence (reduces solution space by enforcing symmetry)

**What happens when wrong:**
- SYME not used when symmetry exists → inflated solution space → 1000+ solutions
- SYME used incorrectly (atoms not actually equivalent) → 0 solutions or wrong structure

**How to detect errors:**
- Check CASE-PROGRESS.md for symmetry detection notes
- Verify atoms have same multiplicity (both CH, both CH3, etc.)
- If LSD errors on SYME command → fallback to LIST/PROP encoding
```

New text:
```
### Symmetry Equivalence (native: BOND/COSY — NOT SYME)

**SYME is NOT a native LSD-3.4.9 command.** Writing `SYME atom1 atom2` causes LSD error 102 (unknown command). Do NOT write SYME to an LSD file.

**Native encoding (use these instead):**

| Symmetry case | Native command | Example |
|---------------|----------------|---------|
| Gem-dimethyl or isopropyl (2 CH3 on same parent CH) | `BOND parent CH3_1` + `BOND parent CH3_2` | `BOND 10 11` + `BOND 10 12` (ibuprofen iter3) |
| Aromatic CH equivalent pair (para-disubstituted ring) | `COSY atom1 atom2  ; equiv-pair` | `COSY 4 7  ; equiv-pair` + `COSY 5 6  ; equiv-pair` (ibuprofen iter3) |
| Homotopic CH2 | No action needed — MULT defines both H at same atom index | — |

The `; equiv-pair` comment tag is required on all equivalence-derived COSY lines so the devils-advocate can distinguish them from peak-data COSY (`grep -c "^COSY.*; equiv-pair" compound.lsd`).

**Why symmetry matters:**
- Equivalent atoms not encoded → LSD treats them as independent → permutation explosion → 1000+ solutions
- Correct BOND/COSY constraints apply the same topological pressure as SYME intended — but natively

**How to detect errors:**
- Check CASE-PROGRESS.md for symmetry/grouping detection notes
- Verify atoms have same multiplicity (both CH, both CH3, etc.)
- If no `COSY.*; equiv-pair` or `BOND.*gem-dimethyl` lines in compound.lsd when symmetry detected → encoding missing
```
  </action>
  <verify>
    <automated>
# SYME command syntax gone (only "do NOT write SYME" guidance may remain)
grep -n "^SYME\b\|SYME atom_index" ~/.claude/agents/lucy-diagnostic.md | grep -v "NOT native\|error 102\|Do NOT\|NEVER write\|not a native"
# Must return 0

# Native guidance present
grep -n "BOND.*gem-dimethyl\|COSY.*equiv-pair" ~/.claude/agents/lucy-diagnostic.md
# Must return >= 2 lines
    </automated>
  </verify>
  <done>The "### SYME - Symmetry Equivalence" section replaced with "### Symmetry Equivalence (native: BOND/COSY)". No SYME command syntax instruction remains. Native BOND (gem-dimethyl) and COSY (aromatic equiv-pair) table present.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Replace SYME fix template in symmetry failure analysis (lines 797-832)</name>
  <files>~/.claude/agents/lucy-diagnostic.md</files>
  <action>
This task fixes the symmetry failure analysis section where SYME is taught as the fix command (around lines 797-832). Read the file again to confirm current text, then apply these edits:

**Edit B — Line 798: Replace grep -i "SYME" check command**

Old text (exact):
```
Check LSD file for SYME:
grep -i "SYME" compound.lsd
; No SYME commands found ✗ FAIL
```

New text:
```
Check LSD file for native symmetry encoding:
grep -cE "^COSY.*; equiv-pair|^BOND" compound.lsd
; Returns 0 → no symmetry constraints found ✗ FAIL
; Returns > 0 → symmetry encoded (verify it matches detected equivalent atoms)
```

**Edit C — Lines 808 area: Replace SYME mention in solution inflation explanation**

Old text (exact):
```
- Example: Para-substituted benzene (2 pairs of equivalent CH) without SYME → LSD tries all 4! permutations → 24× solution inflation
```

New text:
```
- Example: Para-substituted benzene (2 pairs of equivalent CH) without COSY equiv-pair constraints → LSD tries all 4! permutations → 24× solution inflation
```

**Edit D — Lines 812-819: Replace "Attempt SYME" fix block**

Old text (exact):
```
**Attempt SYME (if supported by LSD version):**
```
SYME atom_idx_1 atom_idx_2    ; Force topological equivalence

; Example for para-benzene:
SYME 5 6    ; Equivalent CH pair
SYME 7 8    ; Equivalent CH pair
```

**Fallback with LIST/PROP (if SYME unsupported):**
```
; Example for isopropyl (2 equivalent CH3):
LIST L_iprCH3 9 10     ; Two equivalent methyls
; Constrain both to have same connectivity pattern (requires careful design)
```
```

New text:
```
**Native BOND/COSY equivalence encoding (required — SYME is NOT native in LSD-3.4.9):**
```
; For aromatic CH equivalent pairs (para-disubstituted ring):
COSY 5 6    ; aromatic CH pair equivalence  ; equiv-pair
COSY 7 8    ; aromatic CH pair equivalence  ; equiv-pair

; For gem-dimethyl / isopropyl (2 CH3 on same parent CH at atom 10):
BOND 10 9   ; gem-dimethyl: first CH3 (atom 9) on parent CH (atom 10)
BOND 10 11  ; gem-dimethyl: second CH3 (atom 11) on parent CH (atom 10)
```

Tag ALL equivalence-derived COSY lines with `; equiv-pair`. This is mandatory — it lets the
devils-advocate distinguish equivalence COSY from peak-data COSY.
```

**Edit E — Line 832: Replace fix template summary**

Old text (exact):
```
- Fix: "Add SYME constraints (or LIST/PROP fallback)" (with LSD commands and symmetry pattern description)
```

New text:
```
- Fix: "Add BOND/COSY equivalence constraints (COSY atom1 atom2 ; equiv-pair for aromatic CH pairs; BOND parent CH3_1 + BOND parent CH3_2 for gem-dimethyl/isopropyl)" — SYME is not native in LSD-3.4.9
```
  </action>
  <verify>
    <automated>
# Full SYME command instruction scan — must be zero active instructions
grep -nE "^SYME\b|SYME atom_idx|SYME 5 6|SYME 7 8|Add SYME" ~/.claude/agents/lucy-diagnostic.md | grep -v "NOT native\|error 102\|Do NOT\|NEVER write\|not a native"
# Must return 0

# Native fix commands present
grep -n "COSY.*; equiv-pair\|BOND.*gem-dimethyl\|BOND.*CH3" ~/.claude/agents/lucy-diagnostic.md
# Must return >= 2 lines

# Fix template updated
grep -n "Add BOND/COSY equivalence" ~/.claude/agents/lucy-diagnostic.md
# Must return >= 1 line

# Phase-level sign-off check passes
grep -rn "^SYME\b" ~/.claude/agents/lucy-diagnostic.md | grep -v "NOT native\|error 102\|Do NOT write\|NEVER write\|not a native" || echo "PASS: no active SYME instructions"
# Must return 0 / PASS
    </automated>
  </verify>
  <done>Both fix-guidance locations updated: grep check uses COSY/BOND pattern, solution inflation explanation references COSY equiv-pair, fix block uses native BOND/COSY instead of SYME, fix template summary says BOND/COSY. Full grep scan of lucy-diagnostic.md returns 0 active SYME command instructions.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| diagnostic agent fix guidance | Diagnostic agent is spawned rarely but must give correct native commands when it does run |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-75-05-01 | Tampering | Replacing SYME fix block removes LIST/PROP fallback | accept | LIST/PROP is a valid LSD construct but was a SYME fallback; the native BOND/COSY is the correct primary; diagnostic now teaches native path |
| T-75-SC | Tampering | npm/pip/cargo installs | accept | No package installs — pure markdown edits |
</threat_model>

<verification>
After both tasks complete, run the full sign-off grep:

```bash
# Phase-level validation check (the glob that would have failed)
grep -rn "^SYME\b" ~/.claude/agents/lucy-diagnostic.md | grep -v "NOT native\|error 102\|Do NOT write\|NEVER write\|not a native"
# Must return 0 (PASS)

# Active SYME fix instructions gone
grep -nE "SYME atom_idx|SYME 5 6|SYME 7 8|Add SYME constraints" ~/.claude/agents/lucy-diagnostic.md
# Must return 0

# Native guidance confirmed
grep -n "COSY.*; equiv-pair\|BOND.*gem-dimethyl" ~/.claude/agents/lucy-diagnostic.md

# Fix template updated
grep -n "Add BOND/COSY equivalence" ~/.claude/agents/lucy-diagnostic.md

# Full phase sign-off (all five skill files)
grep -rn "^SYME\b" ~/.claude/agents/lucy-*.md ~/.claude/commands/lucy-ng/ \
  | grep -v "NOT native\|error 102\|Do NOT write\|NEVER write\|not a native"
# Must return 0 across ALL files
```
</verification>

<success_criteria>
1. No line in lucy-diagnostic.md starting with `SYME` followed by atom indices (only "SYME is NOT native" guidance lines remain)
2. Native BOND/COSY equivalence table present (section heading updated to "Symmetry Equivalence (native: BOND/COSY)")
3. Grep check in symmetry failure analysis uses `^COSY.*; equiv-pair|^BOND` not `grep -i "SYME"`
4. Fix guidance blocks use COSY/BOND examples, not SYME commands
5. Fix template summary says "Add BOND/COSY equivalence constraints — SYME is not native"
6. Full phase sign-off grep returns 0 across all five agent skill files
</success_criteria>

<output>
Create /Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-05-SUMMARY.md when done.
NOTE: ~/.claude/ files are NOT committed to the lucy-ng git repo. Only SUMMARY.md is committed.
</output>
