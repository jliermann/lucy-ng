---
phase: "75"
plan: "01"
slug: lsd-engineer-native-singlepath
type: execute
wave: 1
depends_on: []
files_modified:
  - ~/.claude/agents/lucy-lsd-engineer.md
autonomous: true
requirements: [SKILL-01, SKILL-02]

must_haves:
  truths:
    - "lsd-engineer.md contains no instruction to write SYME to an LSD file (only 'do NOT write SYME')"
    - "lsd-engineer.md contains no DEFF NOT SMARTS pattern blocks (only 'do NOT write DEFF NOT' guidance)"
    - "lsd-engineer.md documents BOND/COSY as the native equivalence encoding with ground-truth examples"
    - "lsd-engineer.md documents DEFF F1 ring3 + DEFF F2 ring4 + FEXP as the ring exclusion block"
    - "lsd-engineer.md step 11 has PRIMARY PATH (lucy lsd run) first, FALLBACK PATH (pylsd) as subordinate conditional"
    - "lsd-engineer.md has no manual outlsd 5 < compound.sol > solutions.smi instruction in the main workflow"
    - "HMBC X Y 2 4 appears in the main HMBC correlations block, not only inside the pyLSD subsection"
    - "The pyLSD subsection heading is demoted from ### to ####"
    - "lsd-engineer.md states SKEL benzene is escalation-only, not routine"
  artifacts:
    - path: ~/.claude/agents/lucy-lsd-engineer.md
      provides: "Updated LSD engineer skill with native-only commands and single-path guidance"
      contains: "BOND.*gem-dimethyl"
  key_links:
    - from: "lsd-engineer.md §1 native equivalence"
      to: "devils-advocate.md §1 constraint diff"
      via: "BOND/COSY commands the DA must now track instead of SYME"
      pattern: "BOND.*gem-dimethyl|COSY.*aromatic"
---

<objective>
Rewrite lucy-lsd-engineer.md to eliminate all non-native LSD command instructions and establish unambiguous single-path solver guidance per decisions D-01, D-02, D-03, D-04 (locked in 72-DECISIONS.md).

Purpose: The CASE agent writes LSD files by hand using this skill as its command reference. If the skill teaches SYME and DEFF NOT, the agent emits them — causing LSD error 102 and error 150 respectively and preventing solution generation. This plan fixes the root instruction, not just the code generator (Phase 74 fixed the code path; this plan fixes the hand-writing path).

Output: Updated ~/.claude/agents/lucy-lsd-engineer.md with native BOND/COSY equivalence, DEFF F/FEXP ring exclusion, single PRIMARY/FALLBACK solver path, no manual outlsd pipe, and SKEL-as-escalation note.
</objective>

<execution_context>
@/Users/steinbeck/.claude/get-shit-done/workflows/execute-plan.md
@/Users/steinbeck/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/PROJECT.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/ROADMAP.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/72-design-re-validation/72-DECISIONS.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-RESEARCH.md

Ground truth native LSD file (verified ibuprofen correct):
/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/compound_native.lsd
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Replace SYME with BOND/COSY native equivalence in §1 and constraint inventory</name>
  <files>~/.claude/agents/lucy-lsd-engineer.md</files>
  <action>
Read the full ~/.claude/agents/lucy-lsd-engineer.md. Then make the following SURGICAL edits (use Edit tool with exact old text → new text for each):

**Edit A — Line 71: Replace SYME example in Bond and Property Constraints block**

Old text (exact):
```
PROP L1 1 L2    ; each atom in L1 has at least 1 neighbor from L2
SYME 5 6        ; atoms 5 and 6 are equivalent (symmetry)
```

New text:
```
PROP L1 1 L2    ; each atom in L1 has at least 1 neighbor from L2
```

Then, immediately AFTER the closing ``` of the Bond and Property Constraints code block, add this new block:

```
**NATIVE EQUIVALENCE COMMANDS (replaces non-native SYME):**

SYME causes LSD error 102 (unknown command) — NEVER write SYME to an LSD file.

Use structural BOND/COSY constraints instead:

| Equivalence type | Native encoding | Ground truth |
|------------------|-----------------|--------------|
| Gem-dimethyl / isopropyl (2 CH3 on same parent CH) | `BOND parent CH3_1` + `BOND parent CH3_2` | compound_native.lsd iter3 lines 23-24 |
| Aromatic CH equivalent pair (para-disubstituted ring) | `COSY atom1 atom2  ; equiv-pair` | compound_native.lsd iter3 lines 26-27 |
| Homotopic CH2 (both H on same carbon) | No action — MULT defines both protons at same atom index | — |

Examples (from ibuprofen compound_native.lsd):
```
BOND 10 11      ; gem-dimethyl: both CH3 groups on isobutyl CH (atom 10)
BOND 10 12      ; gem-dimethyl: second CH3 (same parent atom 10)
COSY 4 7        ; aromatic CH pair equivalence  ; equiv-pair
COSY 5 6        ; aromatic CH pair equivalence  ; equiv-pair
```

Tag ALL equivalence-derived COSY lines with `; equiv-pair` comment. This lets the devils-advocate grep distinguish equivalence COSY from peak-data COSY: `grep -c "^COSY.*; equiv-pair" compound.lsd`.
```

**Edit B — Line 308: Replace SYME=N in [ITERATION-COMPLETE] message template**

Old text (exact):
```
Constraint inventory delta: MULT=N, HSQC=N, HMBC=+N (total N), DEFF NOT=N, SYME=N, BOND=N, DEFF_FEXP=applied/none/discarded
```

New text:
```
Constraint inventory delta: MULT=N, HSQC=N, HMBC=+N (total N), ring_excl=enabled/disabled, COSY_equiv=N, BOND=N, DEFF_FEXP=applied/none/discarded
```

**Edit C — Line 373: Replace syme_pairs field in inventory schema table**

Old text (exact):
```
| `syme_pairs` | string array | SYME pairs: `"5 6"` |
```

New text:
```
| `cosy_equiv_pairs` | string array | COSY aromatic-CH equivalence pairs (tagged `; equiv-pair`): e.g. `"4 7"` — these are equivalence-derived COSY lines only, not peak-data COSY |
```

**Edit D — Line 430: Replace SYME in pending_from_detection example**

Old text (exact):
```
;   "pending_from_detection": ["SYME for grouped [44.90, 45.03] -- NOT YET APPLIED"]
```

New text:
```
;   "pending_from_detection": ["COSY-equivalence BOND/COSY for grouped [44.90, 45.03] -- NOT YET APPLIED"]
```

**Edit E — Line 403 area: Replace syme_pairs in inventory JSON example and add cosy_equiv_pairs**

Old text (exact):
```
;   "bond_constraints": ["1 14"], "syme_pairs": [],
```

New text:
```
;   "bond_constraints": ["1 14"], "cosy_equiv_pairs": [],
```
  </action>
  <verify>
    <automated>
grep -rn "^SYME\b" ~/.claude/agents/lucy-lsd-engineer.md | grep -v "NOT native\|error 102\|Do NOT write\|NEVER write" || true
# Must return 0 (the grep -v filters out legitimate "SYME causes... NEVER write" guidance lines)
grep -c "BOND.*gem-dimethyl" ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 1
grep -c "COSY.*equiv-pair" ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 1
grep -c "cosy_equiv_pairs" ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 2 (schema table + JSON example)
    </automated>
  </verify>
  <done>No SYME command in skill instruction blocks (only "do NOT write SYME" guidance). BOND/COSY equivalence table with ground-truth examples present. cosy_equiv_pairs field in schema table and JSON example. [ITERATION-COMPLETE] template uses COSY_equiv=N and ring_excl= instead of SYME=N and DEFF NOT=N.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Replace DEFF NOT section with native DEFF F/FEXP ring exclusion, remove outlsd pipe, single-path step 11, SKEL note</name>
  <files>~/.claude/agents/lucy-lsd-engineer.md</files>
  <action>
This task makes multiple surgical edits to lsd-engineer.md. Read the file again to confirm current line content before each edit, then apply edits in order.

**Edit F — Lines 120-138: Replace entire "Badlist Filters (DEFF NOT)" section**

Old text (exact, lines 120-138):
```
### Badlist Filters (DEFF NOT)

Add to EVERY LSD file after correlations, before ELIM:

```
; Exclude strained rings
DEFF NOT C1CC1      ; no cyclopropane
DEFF NOT C1CCC1     ; no cyclobutane
DEFF NOT C1NC1      ; no aziridine
DEFF NOT C1NCC1     ; no azetidine
DEFF NOT C1SC1      ; no thiirane
DEFF NOT C1SCC1     ; no thietane
DEFF NOT C1OC1      ; no epoxide
DEFF NOT C1OCC1     ; no oxetane
```

Exception: Remove epoxide exclusion if 13C shows 45-55 ppm + formula has O.

**CRITICAL: These DEFF NOT lines MUST persist across ALL iterations. Dropping them was v3.0 bug #1.**
```

New text:
```
### Badlist Filters (Native Ring Exclusion via DEFF F / FEXP)

Add to EVERY LSD file after correlations, before EXIT. Ring exclusion uses pre-built filter
files distributed with the lucy-ng package (Phase 74: bundled in src/lucy_ng/lsd/filters/).
lucy lsd run / LSDInputGenerator.write_file() copies ring3 and ring4 to the iteration directory
automatically — the relative paths below resolve correctly when LSD is run from iteration_NN/.

**Standard ring exclusion block (ALWAYS include):**
```
DEFF F1 "ring3"    ; exclude 3-membered rings (cyclopropane, aziridine, thiirane, epoxide)
DEFF F2 "ring4"    ; exclude 4-membered rings (cyclobutane, azetidine, thietane, oxetane)
FEXP "NOT F1 AND NOT F2"
```

**F-number reservation:** F1 and F2 are RESERVED for ring exclusion. Fragment goodlist uses F3
and above. Do not assign F1 or F2 to fragment goodlist DEFF commands.

Exception: Remove DEFF F1/ring3 exclusion only if 13C shows 45-55 ppm + formula has O
(possible epoxide — let LSD explore). Adjust FEXP accordingly: `FEXP "NOT F2"`.

**CRITICAL: These DEFF F / FEXP lines MUST persist across ALL iterations. Dropping them was v3.0 bug #1.**

**NOT NATIVE:** `DEFF NOT C1CC1` (SMARTS syntax) causes LSD error 150. Do NOT write DEFF NOT.
```

**Edit G — Line 167: Fragment Goodlist DEFF NOT reference**

Old text (exact):
```
This is different from `DEFF NOT` which goes after correlations.
```

New text:
```
This is different from ring-exclusion DEFF F / FEXP which also goes after correlations.
```

**Edit H — Line 192: Manual checklist item 8**

Old text (exact):
```
8. Badlist DEFF NOT patterns present
```

New text:
```
8. Ring exclusion DEFF F1 "ring3" + DEFF F2 "ring4" + FEXP "NOT F1 AND NOT F2" present
```

**Edit I — Line 222: Adaptive loop step 1**

Old text (exact):
```
1. Start with MULT + HSQC + heteroatom constraints + DEFF NOT + first batch 3-5 HMBC
```

New text:
```
1. Start with MULT + HSQC + heteroatom constraints + DEFF F/FEXP ring exclusion + first batch 3-5 HMBC
```

**Edit J — Line 376: deff_not_patterns schema field description**

Old text (exact):
```
| `deff_not_patterns` | string array | SMARTS strings for each DEFF NOT command |
```

New text:
```
| `deff_not_patterns` | string array | **Deprecated.** Set to `[]` — ring exclusion is now emitted as DEFF F1/F2 + FEXP (tracked by `ring_exclusion_enabled`). Kept for backward-compat with DA legacy checks on old iterations. |
| `ring_exclusion_enabled` | boolean | True when DEFF F1+F2+FEXP ring exclusion block is present. New field as of Phase 75. |
```

**Edit K — Line 405 area: Replace deff_not_patterns populated example with ring_exclusion_enabled**

Old text (exact):
```
;   "deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1", "C1SC1", "C1SCC1", "C1OC1", "C1OCC1"],
```

New text:
```
;   "deff_not_patterns": [],
;   "ring_exclusion_enabled": true,
```

**Edit L — Line 443: Initialization Procedure "DEFF NOT" reference**

Old text (exact):
```
After writing all MULT, HSQC, first HMBC batch, BOND, and DEFF NOT to the file:
```

New text:
```
After writing all MULT, HSQC, first HMBC batch, BOND, and ring exclusion (DEFF F/FEXP) to the file:
```

**Edit M — Lines 447: "Populate deff_not_patterns" critical note**

Old text (exact):
```
3. **CRITICAL:** Populate `deff_not_patterns` from the full badlist set (Section 1 -- these are constant). This is the primary defense against Bug 1 (DEFF NOT never written).
```

New text:
```
3. **CRITICAL:** Set `ring_exclusion_enabled: true` and `deff_not_patterns: []` in inventory. Verify DEFF F1 "ring3" + DEFF F2 "ring4" + FEXP "NOT F1 AND NOT F2" appear in the LSD file. This is the primary defense against Bug 1 (ring exclusion dropped).
```

**Edit N — Line 519: Workflow step 6 "DEFF NOT" reference**

Old text (exact):
```
6. Build/update LSD file: inventory block first (initialized or updated per Section 5C/5D), then DEFF F1/FEXP (if fragment applied), then MULT defs, HSQC, HMBC batch, BOND/LIST/PROP, DEFF NOT
```

New text:
```
6. Build/update LSD file: inventory block first (initialized or updated per Section 5C/5D), then DEFF F1/FEXP (if fragment applied), then MULT defs, HSQC, HMBC batch, BOND/LIST/PROP, DEFF F1+F2/FEXP ring exclusion
```

**Edit O — Lines 102-108: Remove "Solution Conversion" block (outlsd manual pipe)**

Old text (exact):
```
### Solution Conversion

```bash
outlsd 5 < compound.sol > solutions.smi
```

Parameter `5` = max fused rings (required for natural products). Run from iteration directory.
```

New text:
```
### Solution Conversion (Phase 73 — automatic)

`lucy lsd run` produces `solutions.smi` automatically (Phase 73 fix — `_invoke_outlsd` runs
internally after the solver completes). No manual `outlsd 5 < compound.sol > solutions.smi`
invocation is needed for the primary path.

`outlsd` is still used internally by the runner; `lucy lsd check` verifies it is available.
```

**Edit P — Lines 526-543: Replace symmetric if/else step 11 with PRIMARY/FALLBACK structure**

Old text (exact):
```
```bash
# Read inventory to determine solver mode
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
PYLSD_MODE=$(echo "$RESULT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")

if [ "$PYLSD_MODE" = "True" ]; then
  # Multi-run mode: use PyLSDOrchestrator via lucy pylsd run
  lucy pylsd run analysis/iteration_NN/compound.lsd \
    --shifts "<comma_separated_13C_shifts>" \
    --format json | tee analysis/iteration_NN/pylsd_output.json
else
  # Single-run mode: classic lucy lsd run (also the silent fallback for ABSENT inventory per D-19)
  cd analysis/iteration_NN && lucy lsd run compound.lsd
fi
```

**Note:** If `validate-inventory` returns `valid: false` with "No v2 inventory block found" (ABSENT case), `pylsd_mode` defaults to `False` via `.get('inventory',{}).get('pylsd_mode', False)` — the silent fallback to `lucy lsd run` is automatic (D-19). MALFORMED inventory is caught by G2/G3 gates before this step is reached (D-19a).
```

New text:
```
**PRIMARY PATH (always run first):**
```bash
cd analysis/iteration_NN && lucy lsd run compound.lsd
# lucy lsd run produces compound.sol AND solutions.smi automatically (Phase 73 fix).
# No manual outlsd invocation needed.
```

**FALLBACK PATH — use ONLY when ALL THREE conditions hold:**
(a) primary path yields 0 solutions, AND
(b) K ≤ 3 deferred 4J suspects exist in the constraint inventory, AND
(c) `pylsd_mode=true` in the inventory

```bash
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
PYLSD_MODE=$(echo "$RESULT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")

if [ "$PYLSD_MODE" = "True" ]; then
  # Permutation fallback: PyLSDOrchestrator explores 4J correlation combinations
  lucy pylsd run analysis/iteration_NN/compound.lsd \
    --shifts "<comma_separated_13C_shifts>" \
    --format json | tee analysis/iteration_NN/pylsd_output.json
  # After pylsd run: send validation request to DA — include G5 check (perm constraint completeness)
fi
```

**D-02 (locked decision):** Normal LSD + extended HMBC bond range is the primary solver path.
Permutation fallback is a narrow escape hatch, not a co-equal path. Do NOT default to pylsd_mode.
```

**Edit Q — Line 86: Demote pyLSD section heading from ### to ####**

Old text (exact):
```
### pyLSD Commands (pylsd_mode only)
```

New text:
```
#### Fallback Path: Permutation Mode Commands (use ONLY when primary yields 0 solutions)
```

**Edit R — Add HMBC X Y 2 4 to the main HMBC correlations block**

In the "### Correlations -- HSQC and HMBC" section (around line 54-64), find:

Old text (exact):
```
HMBC (5 6) 10  ; H10 correlates to either C5 or C6 (ambiguous/grouped)
```

New text:
```
HMBC (5 6) 10  ; H10 correlates to either C5 or C6 (ambiguous/grouped)
HMBC 3 8 2 4   ; extended bond range 2-4: primary 4J mechanism (D-01); normal HMBC uses default 2-3
```

**Edit S — After step 12 (post-solver), remove manual outlsd step 13**

Old text (exact):
```
13. If solutions <= 10: `outlsd 5 < compound.sol > solutions.smi`
```

New text:
```
13. solutions.smi is produced automatically by `lucy lsd run` (Phase 73). Proceed directly to ranking or next iteration.
```

**Edit T — Add SKEL-as-escalation note after the step 11 solver block**

After the fallback path block (new step 11 text), add:

```
**D-04 (locked decision — SKEL benzene):** Do NOT add a SKEL benzene fragment in the normal CASE flow. Correct BOND/COSY equivalence constraints + DEFF F/FEXP ring exclusion yield the aromatic ring without fragment forcing (verified: Arm A, 2/2 aromatic solutions, ibuprofen found). SKEL benzene is an ESCALATION OPTION ONLY for compounds where: (a) fewer than 3 HMBC correlations to the aromatic ring AND (b) solutions contain no aromatic carbons after 3+ iterations with full constraints. Do not use as first-line response.
```
  </action>
  <verify>
    <automated>
# No DEFF NOT SMARTS patterns remain as instructions
grep -c "DEFF NOT C1" ~/.claude/agents/lucy-lsd-engineer.md || echo "0"
# Must return 0

# Native ring exclusion documented
grep -c "DEFF F1.*ring3" ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 1
grep -c 'FEXP.*NOT F1 AND NOT F2' ~/.claude/agents/lucy-lsd-engineer.md
# Must return >= 1

# No manual outlsd pipe in workflow
grep -c "outlsd 5 < compound" ~/.claude/agents/lucy-lsd-engineer.md || echo "0"
# Must return 0

# Single-path structure present
grep -n "PRIMARY PATH\|FALLBACK PATH" ~/.claude/agents/lucy-lsd-engineer.md
# Must return both lines

# pyLSD heading demoted
grep -n "#### Fallback Path" ~/.claude/agents/lucy-lsd-engineer.md
# Must return a line

# HMBC X Y 2 4 in main HMBC block (before the fallback section)
grep -n "HMBC.*2 4" ~/.claude/agents/lucy-lsd-engineer.md | head -5
# Must show at least one line in the main correlations section (line < 86)
    </automated>
  </verify>
  <done>lsd-engineer.md has zero DEFF NOT SMARTS instructions, zero manual outlsd pipe instructions, and zero instructions to write SYME. DEFF F1/F2/FEXP ring exclusion block documented with F-number reservation note. Step 11 has PRIMARY PATH (no condition, lucy lsd run first) and subordinate FALLBACK PATH (if PYLSD_MODE=True). pyLSD section heading demoted to ####. HMBC X Y 2 4 present in main HMBC correlations block. SKEL-as-escalation note present. D-04 note present.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| skill file → CASE agent | Agent reads skill at spawn time and treats it as authoritative command vocabulary |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-75-01 | Tampering | Skill file edit (wrong old text) | mitigate | Executor reads file before each Edit; line-exact old text match required by Edit tool |
| T-75-02 | Denial of Service | Edit removes too much context | mitigate | Surgical edits only — specify exact old text; task 2 edits are independent sections |
| T-75-SC | Tampering | npm/pip/cargo installs | accept | No package installs in this plan — pure markdown edits |
</threat_model>

<verification>
After both tasks complete, run full grep suite:

```bash
# SKILL-01: SYME gone (only "do NOT write" guidance may remain)
grep -rn "^SYME\b" ~/.claude/agents/lucy-lsd-engineer.md | grep -v "NOT native\|error 102\|Do NOT write\|NEVER write"
# Must return empty

# SKILL-01: DEFF NOT SMARTS gone
grep -n "DEFF NOT C1" ~/.claude/agents/lucy-lsd-engineer.md
# Must return empty

# SKILL-01: BOND/COSY native equivalence documented
grep -n "BOND.*gem-dimethyl" ~/.claude/agents/lucy-lsd-engineer.md
grep -n "COSY.*equiv-pair" ~/.claude/agents/lucy-lsd-engineer.md

# SKILL-01: Ring exclusion native
grep -n "DEFF F1.*ring3" ~/.claude/agents/lucy-lsd-engineer.md
grep -n 'FEXP.*NOT F1 AND NOT F2' ~/.claude/agents/lucy-lsd-engineer.md

# SKILL-01: No manual outlsd pipe
grep -n "outlsd 5 < compound" ~/.claude/agents/lucy-lsd-engineer.md
# Must return empty

# SKILL-02: Single-path structure
grep -n "PRIMARY PATH\|FALLBACK PATH" ~/.claude/agents/lucy-lsd-engineer.md

# SKILL-02: pyLSD heading demoted
grep -n "#### Fallback Path" ~/.claude/agents/lucy-lsd-engineer.md

# SKILL-02: HMBC X Y 2 4 in main block (before line 86)
grep -n "HMBC.*2 4" ~/.claude/agents/lucy-lsd-engineer.md
```
</verification>

<success_criteria>
1. grep confirms zero SYME command instructions (excluding "do NOT" guidance lines)
2. grep confirms zero DEFF NOT C1... SMARTS pattern instructions
3. grep confirms BOND/COSY native equivalence table present with gem-dimethyl example
4. grep confirms DEFF F1 "ring3" + FEXP "NOT F1 AND NOT F2" present
5. grep confirms zero "outlsd 5 < compound" instructions
6. grep confirms "PRIMARY PATH" and "FALLBACK PATH" both present in step 11
7. grep confirms "#### Fallback Path" heading (pyLSD demoted from ###)
8. grep confirms HMBC X Y 2 4 appears in the main correlations section
9. grep confirms D-04 SKEL escalation-only note present
</success_criteria>

<output>
Create /Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-01-SUMMARY.md when done.
NOTE: ~/.claude/ files are user-global and NOT committed to the lucy-ng git repo. Do NOT run git add / git commit on the skill files. Only the SUMMARY.md (in .planning/) is committed.
</output>
