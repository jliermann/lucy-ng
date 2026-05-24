---
phase: "75"
plan: "02"
slug: devils-advocate-native-gates
type: execute
wave: 2
depends_on: ["75-01"]
files_modified:
  - ~/.claude/agents/lucy-devils-advocate.md
autonomous: true
requirements: [SKILL-01, SKILL-03]

must_haves:
  truths:
    - "devils-advocate.md constraint diff table has no SYME row — replaced with COSY equivalence lines row"
    - "DA Bug 1 check targets DEFF F1+F2+FEXP absence, not DEFF NOT SMARTS absence"
    - "DA Check 1 table uses ring_exclusion_enabled and cosy_equiv_pairs, not deff_not_patterns and syme_pairs"
    - "DA Check 2 and Check 3 tables use ring_exclusion_enabled and cosy_equiv_pairs"
    - "DA [VALIDATION-PASSED] template uses 'Ring exclusion' and 'COSY-equiv' fields"
    - "DA [VALIDATION-BLOCKED] template uses 'Ring exclusion' field"
    - "DA has G5 gate for permutation HMBC-only detection (BOND=0, COSY=0, DEFF_F=0)"
    - "DA has G6 gate for empty merged.smi despite non-zero solncounter"
    - "DA has G8 gate (WARNING severity) for agent reversion to direct run when pylsd_mode=true"
    - "DA G7 is documented as lsd-engineer self-check (hash in [VALIDATION-PASSED])"
    - "BOND/COSY equivalence (not SYME) must persist per constraint diff protocol"
  artifacts:
    - path: ~/.claude/agents/lucy-devils-advocate.md
      provides: "Updated DA skill with native-command validation and v8.0 failure mode gates"
      contains: "G5.*perm\|HMBC-only"
  key_links:
    - from: "lsd-engineer.md (plan 75-01 output)"
      to: "devils-advocate.md §1 Count Comparison table"
      via: "native commands lsd-engineer now writes must match what DA validates"
      pattern: "COSY.*equiv-pair|DEFF F1.*ring3"
---

<objective>
Update lucy-devils-advocate.md to: (1) synchronize native-command validation with lsd-engineer's new output (BOND/COSY instead of SYME, DEFF F/FEXP instead of DEFF NOT) and (2) add G5/G6/G7/G8 gates that detect the four v8.0 failure modes.

Purpose: The DA is the writer-checker pair for lsd-engineer. After plan 75-01 changes what lsd-engineer WRITES, the DA must validate the new commands, not the old ones. Without this sync, the DA will flag every valid native-command LSD file as CRITICAL because it finds no SYME or DEFF NOT lines.

Additionally: the v8.0 bypass went undetected because no DA gate checked for HMBC-only permutation files, empty merges, or post-approval file edits. G5-G8 close these gaps.

Output: Updated ~/.claude/agents/lucy-devils-advocate.md with native-command sync in §1/§2/§5 and new Check 5 section (G5/G6/G7/G8).
</objective>

<execution_context>
@/Users/steinbeck/.claude/get-shit-done/workflows/execute-plan.md
@/Users/steinbeck/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/PROJECT.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/ROADMAP.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-RESEARCH.md
@/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-01-SUMMARY.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Native-command sync in §1 Count Comparison, Content Comparison, and Bug 1/Bug 2</name>
  <files>~/.claude/agents/lucy-devils-advocate.md</files>
  <action>
Read the full ~/.claude/agents/lucy-devils-advocate.md. Then apply these surgical edits:

**Edit A — Line 56: Count Comparison table — DEFF NOT row**

Old text (exact):
```
| DEFF NOT patterns | **ALWAYS persist** | Any decrease -> CRITICAL |
```

New text:
```
| Ring exclusion (DEFF F1 + DEFF F2 + FEXP) | **ALWAYS persist** | Absent or any line removed -> CRITICAL |
```

**Edit B — Line 57: Count Comparison table — SYME row**

Old text (exact):
```
| SYME constraints | Persist once added | Removed -> CRITICAL |
```

New text:
```
| COSY equivalence lines (`; equiv-pair` tagged) | Persist once added | Removed -> CRITICAL |
```

**Edit C — Line 63: Content Comparison — DEFF NOT exact-match rule**

Old text (exact):
```
- Every DEFF NOT line in iteration N-1 must appear in iteration N (exact string match)
```

New text:
```
- Every `DEFF F1 "ring3"`, `DEFF F2 "ring4"`, and `FEXP "NOT F1 AND NOT F2"` line in iteration N-1 must appear in iteration N (exact string match)
```

**Edit D — Line 72: Expected (Normal) Changes — SYME mention**

Old text (exact):
```
- SYME added from grouping detection
```

New text:
```
- COSY aromatic-pair constraints (`COSY atom1 atom2  ; equiv-pair`) added from grouping detection
```

**Edit E — Lines 79-94: Bug 1 — rewrite entire Bug 1 section**

Old text (exact):
```
### Bug 1: DEFF NOT Patterns Dropped (CRITICAL)

**What happened:** Agent wrote 6 DEFF NOT patterns in iteration 1, forgot to carry forward to iterations 2-4. Result: strained-ring solutions survived.

**Check:** Count DEFF NOT lines. If iteration > 1 and count < iteration 1 count, flag CRITICAL.

**Expected patterns** (natural products, minimum set):
```
DEFF NOT C1CC1      ; cyclopropane
DEFF NOT C1CCC1     ; cyclobutane
DEFF NOT C1NC1      ; aziridine
DEFF NOT C1NCC1     ; azetidine
DEFF NOT C1SC1      ; thiirane
DEFF NOT C1SCC1     ; thietane
DEFF NOT C1OC1      ; epoxide
DEFF NOT C1OCC1     ; oxetane
```
```

New text:
```
### Bug 1: Ring Exclusion Block Dropped (CRITICAL)

**What happened:** Agent wrote ring exclusion (DEFF NOT or DEFF F/FEXP) in iteration 1, forgot to carry it forward. Result: strained-ring solutions survived.

**Check:** Verify DEFF F1, DEFF F2, and FEXP are all present. If any are missing: CRITICAL.

```bash
grep -c "^DEFF F" compound.lsd   # Must be >= 2
grep -c "^FEXP" compound.lsd     # Must be >= 1
```

**Expected minimum block (native form, Phase 74+):**
```
DEFF F1 "ring3"
DEFF F2 "ring4"
FEXP "NOT F1 AND NOT F2"
```

**Legacy form (pre-Phase-74 iterations):** If iterating on a compound where early iterations used `DEFF NOT C1CC1` / `DEFF NOT C1CCC1` syntax, accept the legacy form for those early iterations: verify `grep -c "^DEFF NOT" compound.lsd >= 2`. Do not flag CRITICAL on old files for lacking DEFF F — use legacy grep as fallback check.
```

**Edit F — Line 99: Bug 2 — SYME reference**

Old text (exact):
```
**What happened:** Grouping detection found close signals [44.90, 45.03] but agent never translated to SYME or parenthesized HMBC.
```

New text:
```
**What happened:** Grouping detection found close signals [44.90, 45.03] but agent never translated to COSY equivalence constraints or parenthesized HMBC.
```

**Edit G — Lines 101-103: Bug 2 check criteria**

Old text (exact):
```
**Check:** If nmr-chemist reported signal groups, verify either:
- SYME constraint exists for grouped atoms, OR
- Parenthesized HMBC syntax `HMBC (N M)` exists for grouped atoms
```

New text:
```
**Check:** If nmr-chemist reported signal groups, verify either:
- COSY equivalence constraint (`COSY atom1 atom2  ; equiv-pair`) exists for grouped atoms, OR
- Parenthesized HMBC syntax `HMBC (N M)` exists for grouped atoms
```

**Edit H — Line 163: Badlist Completeness check**

Old text (exact):
```
For natural products, expect minimum: C1CC1 and C1CCC1 DEFF NOT patterns. If missing: flag WARNING.
```

New text:
```
For natural products, expect DEFF F1 "ring3" + DEFF F2 "ring4" + FEXP (native form) OR DEFF NOT C1CC1 + DEFF NOT C1CCC1 (legacy form). `grep -c "^DEFF F" compound.lsd` must be >= 2 (native) OR `grep -c "^DEFF NOT" compound.lsd` must be >= 2 (legacy). If neither condition holds: flag WARNING.
```
  </action>
  <verify>
    <automated>
# No SYME row in constraint diff
grep -n "^| SYME" ~/.claude/agents/lucy-devils-advocate.md || echo "0 - good"
# Must return 0 (no bare SYME row)

# COSY equivalence row present
grep -n "COSY equivalence" ~/.claude/agents/lucy-devils-advocate.md
# Must return at least 1 line

# Ring exclusion row in count comparison
grep -n "Ring exclusion" ~/.claude/agents/lucy-devils-advocate.md
# Must return at least 2 lines (table row + Bug 1 heading)

# No "DEFF NOT C1" instruction (legacy fallback note is acceptable but not an instruction)
grep -n "DEFF NOT C1CC1" ~/.claude/agents/lucy-devils-advocate.md
# Must return only the legacy fallback note, not a mandatory check instruction
    </automated>
  </verify>
  <done>DA Count Comparison table has no SYME row; has COSY equivalence row. DA Bug 1 checks for DEFF F1+F2+FEXP absence, not DEFF NOT absence (with legacy fallback). DA Bug 2 checks COSY equiv-pair or parenthesized HMBC. Content Comparison checks DEFF F lines not DEFF NOT lines. Badlist completeness check accepts both native and legacy forms.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Update Check 1/2/3 inventory fields and message templates, add G5-G8 gates</name>
  <files>~/.claude/agents/lucy-devils-advocate.md</files>
  <action>
Continue editing lucy-devils-advocate.md. Read relevant sections before editing.

**Edit I — Line 269: Check 1 table — deff_not_patterns and syme_pairs rows**

Old text (exact):
```
| `deff_not_patterns` (array length) | `grep -c "^DEFF NOT" compound.lsd` | Exact |
| `syme_pairs` (array length) | `grep -c "^SYME" compound.lsd` | Exact |
```

New text:
```
| `ring_exclusion_enabled` | `grep -c "^DEFF F" compound.lsd` >= 2 AND `grep -c "^FEXP" compound.lsd` >= 1 | Must be true when enabled |
| `cosy_equiv_pairs` (array length) | `grep -c "^COSY.*; equiv-pair" compound.lsd` | Exact — counts only equivalence-derived COSY, not peak-data COSY |
```

**Edit J — Line 285: Check 2 table — deff_not_patterns and syme_pairs regression rows**

Old text (exact):
```
| `deff_not_patterns` length | >= previous | Decrease -> CRITICAL |
| `syme_pairs` length | >= previous | Decrease -> CRITICAL |
```

New text:
```
| `ring_exclusion_enabled` | Must remain true if it was true | False after true -> CRITICAL |
| `cosy_equiv_pairs` length | >= previous | Decrease -> CRITICAL |
```

**Edit K — Line 294: Check 3 array listing — syme_pairs**

Old text (exact):
```
For array fields (`deff_not_patterns`, `bond_constraints`, `syme_pairs`, `grouped_hmbc`, each batch in `hmbc_batches`): verify every string in the previous array appears in the current array. Missing item = CRITICAL.
```

New text:
```
For array fields (`bond_constraints`, `cosy_equiv_pairs`, `grouped_hmbc`, each batch in `hmbc_batches`): verify every string in the previous array appears in the current array. Missing item = CRITICAL. For ring exclusion: verify `ring_exclusion_enabled` stays true across iterations; verify the three DEFF F1/F2/FEXP lines are present verbatim.
```

**Edit L — Line 358-359: Bug 1 enhanced check via inventory**

Old text (exact):
```
- **Bug 1 (DEFF NOT dropped):** Use inventory `deff_not_patterns` array as source of truth. Check 1 validates inventory matches actual file. Check 2 validates no regression vs previous iteration. This catches drops at ANY iteration (not just after iteration 1).
```

New text:
```
- **Bug 1 (Ring exclusion dropped):** Use inventory `ring_exclusion_enabled` field as source of truth. Check 1 validates `grep -c "^DEFF F"` >= 2 AND `grep -c "^FEXP"` >= 1 when enabled. Check 2 validates `ring_exclusion_enabled` does not revert from true to false. Legacy fallback: if `deff_not_patterns` array is non-empty and `ring_exclusion_enabled` absent, use `grep -c "^DEFF NOT"` >= 2 for that iteration (backward compat for compounds started before Phase 75).
```

**Edit M — Line 383: [VALIDATION-PASSED] template — DEFF NOT and SYME fields**

Old text (exact):
```
DEFF NOT: N patterns (preserved from iteration N-1 / initialized)
SYME: N constraints (preserved / N/A)
```

New text:
```
Ring exclusion: DEFF F1+F2+FEXP (present / MISSING — CRITICAL)
COSY-equiv: N pairs (preserved / N/A)
```

**Edit N — Line 408: [VALIDATION-BLOCKED] template — DEFF NOT field**

Old text (exact):
```
DEFF NOT: N patterns (DROPPED from N-1 count of M / preserved)
```

New text:
```
Ring exclusion: DEFF F/FEXP (MISSING / present)
```

**Edit O — Add G5/G6/G7/G8 after the G4 block (after line 346)**

Find the end of the G4 block. The G4 block ends with:

```
**All four gates G1/G2/G3/G4 are CRITICAL severity and blocking.**
```

After that closing line, add the new Check 5 section:

```
**Check 5: v8.0 Failure Mode Detection**

These four checks (G5-G8) detect the specific failure modes identified in the v8.0 UAT postmortem.
G5 and G6 are post-run checks (run when pylsd_run/ directory exists). G7 is a hash-verification
self-check performed by lsd-engineer. G8 is a WARNING-severity reversion check.

---

**G5: Permutation Constraint Completeness (CRITICAL, blocking — post-run)**

*When:* After `lucy pylsd run` completes and pylsd_run/ directory exists in the iteration dir.

*Purpose:* Detect the exact v8.0 failure — HMBC-only permutation files (BOND=0, COSY=0, DEFF_F=0).
The v8.0 per-permutation files were 542 bytes and contained only HMBC lines — all BOND/COSY/DEFF
constraints were silently dropped by PyLSDOrchestrator._build_permutation().

*Detection:*
```bash
for perm_dir in analysis/iteration_NN/pylsd_run/perm_*/; do
  bond_count=$(grep -c "^BOND" "$perm_dir/compound.lsd" 2>/dev/null || echo 0)
  cosy_count=$(grep -c "^COSY" "$perm_dir/compound.lsd" 2>/dev/null || echo 0)
  deff_count=$(grep -c "^DEFF F" "$perm_dir/compound.lsd" 2>/dev/null || echo 0)
  if [ "$bond_count" -eq 0 ] && [ "$cosy_count" -eq 0 ] && [ "$deff_count" -eq 0 ]; then
    echo "CRITICAL: $perm_dir/compound.lsd appears HMBC-only (BOND=$bond_count COSY=$cosy_count DEFF_F=$deff_count)"
  fi
done
```

*Trigger:* Any perm file with BOND=0 AND COSY=0 AND DEFF_F=0 → CRITICAL.

*Action:* BLOCK with message: "Permutation file {perm_dir}/compound.lsd is HMBC-only (BOND=0, COSY=0, DEFF F=0). This is the v8.0 constraint-loss failure pattern. Check that PyLSDOrchestrator._build_permutation() receives a fully-populated LSDProblem. Do not proceed with merge until perm files carry the full constraint set."

---

**G6: Empty merged.smi Despite Non-Zero solncounter (CRITICAL, blocking — post-run)**

*When:* After `lucy pylsd run` completes and pylsd_run/ directory exists.

*Purpose:* Detect the v8.0 keystone bug — thousands of per-permutation solutions that failed to
merge into merged.smi, causing the run to report 0 solutions despite finding the correct structure.

*Detection:*
```bash
for solncounter in analysis/iteration_NN/pylsd_run/perm_*/solncounter; do
  count=$(cat "$solncounter" 2>/dev/null || echo 0)
  if [ "$count" -gt 0 ]; then
    merged="analysis/iteration_NN/pylsd_run/merged.smi"
    if [ ! -s "$merged" ]; then
      echo "CRITICAL: solncounter=$count in $solncounter but merged.smi is empty or missing"
    fi
  fi
done
# Also check run_report.json
python3 -c "
import json, sys
try:
  r = json.load(open('analysis/iteration_NN/pylsd_run/run_report.json'))
  total = r.get('total_raw_solutions', 0)
  if total == 0:
    print('WARNING: run_report.json reports total_raw_solutions=0 — check per-perm solncounters')
except: pass
"
```

*Trigger:* Any perm has solncounter > 0 AND (merged.smi missing OR merged.smi empty OR run_report total_raw_solutions = 0) → CRITICAL.

*Action:* BLOCK with message: "Empty merge despite solutions in permutations — this was the v8.0 keystone bug (SolutionMerger collected 0 despite per-permutation solutions). Check: (1) solutions.smi in each perm dir is non-empty. (2) SolutionMerger collected from the correct path. Phase 73 should have fixed this — if it recurs, escalate to coordinator."

---

**G7: Post-Validation File Modification (CRITICAL — lsd-engineer self-check)**

*This check is performed by lsd-engineer, not by DA directly.* DA encodes the file hash in its
[VALIDATION-PASSED] message. lsd-engineer verifies the hash before invoking the solver.

**DA responsibility:** After issuing [VALIDATION-PASSED], compute and include the file hash:
```bash
FILE_HASH=$(md5sum analysis/iteration_NN/compound.lsd 2>/dev/null \
  || md5 -q analysis/iteration_NN/compound.lsd 2>/dev/null)
```

Add to [VALIDATION-PASSED] message:
```
File hash at approval: <FILE_HASH>  (md5)
```

**lsd-engineer responsibility (step 11, before running solver):** Re-compute the file hash and compare against the hash embedded in the [DA-APPROVED] relay message from coordinator. If hashes differ: do NOT run solver; send CRITICAL error to coordinator.

*Trigger:* Hash at solver invocation != hash at DA approval → CRITICAL (lsd-engineer blocks run).

*Rationale:* v8.0 postmortem item 8 — the LSD file was modified after DA approval during the bypass episode. This check detects that scenario.

---

**G8: Agent Reversion Detection (WARNING — post-run)**

*When:* After each iteration, DA reads the [ITERATION-COMPLETE] message in CASE-PROGRESS.md.

*Detection:* If `pylsd_mode=true` in the inventory but [ITERATION-COMPLETE] reports `lucy lsd run`
was used (not `lucy pylsd run`), flag WARNING.

```bash
# Compare inventory pylsd_mode against iteration routing
inventory_mode=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")
# Then check [ITERATION-COMPLETE] message (from CASE-PROGRESS.md or coordinator relay)
# for whether lucy lsd run or lucy pylsd run was reported
```

*Trigger:* inventory `pylsd_mode=true` BUT iteration used `lucy lsd run` without documented
fallback justification → WARNING (not CRITICAL — deliberate fallback is valid after 0 pylsd solutions).

*Action:* WARNING with message: "pylsd_mode=true in inventory but direct lucy lsd run was used. This was the v8.0 reversion pattern (bypass after failed merge). If this was a deliberate fallback after 0 solutions from pylsd, document the reason in [ITERATION-COMPLETE] under 'Why'. If undocumented: WARNING — review and confirm intentional."

---

**Summary of Check 5 gates:**

| Gate | When | Severity | Trigger |
|------|------|----------|---------|
| G5 | Post-run, perm files exist | CRITICAL | Any perm file BOND=0 AND COSY=0 AND DEFF F=0 |
| G6 | Post-run, perm files exist | CRITICAL | solncounter > 0 but merged.smi empty/missing |
| G7 | Pre-run, lsd-engineer self-check | CRITICAL | File hash changed after DA approval |
| G8 | Post-run, read CASE-PROGRESS.md | WARNING | pylsd_mode=true but lucy lsd run used without documented reason |

**Note:** G1-G4 numbering is unchanged. G5-G8 are additive. Do not renumber existing gates.
```

**Edit P — Also add G7 hash requirement to [VALIDATION-PASSED] template**

Find the [VALIDATION-PASSED] template block and add the hash line. After:
```
Aromatic ring check: N/A (no ranking yet or no aromatic expectation) / PASS (solutions contain aromatic ring) / WARNING: all solutions non-aromatic despite aromatic expectation from NMR
```

Add:
```
File hash (md5): <hash>  (lsd-engineer must verify this before running solver — G7)
```
  </action>
  <verify>
    <automated>
# Check 1 table: new field names
grep -n "ring_exclusion_enabled" ~/.claude/agents/lucy-devils-advocate.md
# Must return >= 3 (Check 1, Check 2, Bug 1 enhanced)

grep -n "cosy_equiv_pairs" ~/.claude/agents/lucy-devils-advocate.md
# Must return >= 3 (Check 1, Check 2, Check 3)

# No bare syme_pairs field references remain
grep -n "syme_pairs" ~/.claude/agents/lucy-devils-advocate.md | grep -v "cosy_equiv_pairs"
# Must return 0

# G5-G8 present
grep -n "G5\|G6\|G7\|G8" ~/.claude/agents/lucy-devils-advocate.md | head -10
# Must show all four gates

# [VALIDATION-PASSED] template updated
grep -n "Ring exclusion.*DEFF\|COSY-equiv" ~/.claude/agents/lucy-devils-advocate.md
# Must return >= 2 lines (PASSED template + BLOCKED template)
    </automated>
  </verify>
  <done>DA Check 1/2/3 tables use ring_exclusion_enabled and cosy_equiv_pairs (no bare syme_pairs). [VALIDATION-PASSED] and [VALIDATION-BLOCKED] templates use Ring exclusion and COSY-equiv fields. New Check 5 section present with G5, G6, G7, G8 sub-gates, each with detection command + trigger + action. G1-G4 numbering unchanged. G7 hash line added to [VALIDATION-PASSED] template.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Plan 75-01 output → Plan 75-02 input | DA changes must be consistent with what lsd-engineer now writes; consistency is enforced by reading 75-01-SUMMARY.md |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-75-02-01 | Tampering | Renumbering existing G1-G4 | mitigate | Instructions explicitly state "G1-G4 numbering is unchanged" and new gates are additive G5-G8 |
| T-75-02-02 | Information Disclosure | DA gets Write tool capability via G7 | accept | G7 is a lsd-engineer self-check; DA is read-only and only outputs hash as text in message |
| T-75-SC | Tampering | npm/pip/cargo installs | accept | No package installs — pure markdown edits |
</threat_model>

<verification>
After both tasks complete:

```bash
# SKILL-01: SYME gone from DA (only as "COSY equivalence" guidance)
grep -n "^| SYME" ~/.claude/agents/lucy-devils-advocate.md || echo "good: no bare SYME row"

# SKILL-01: COSY equivalence row present in count comparison
grep -n "COSY equivalence" ~/.claude/agents/lucy-devils-advocate.md

# SKILL-01: Ring exclusion in multiple DA locations
grep -n "Ring exclusion\|ring_exclusion_enabled" ~/.claude/agents/lucy-devils-advocate.md | wc -l
# Expect >= 5

# SKILL-03: All four new gates present
grep -cE "^\*\*G[5678]:" ~/.claude/agents/lucy-devils-advocate.md
# Expect 4

# SKILL-03: G5 has detection command
grep -n "perm.*HMBC-only\|HMBC-only.*perm\|BOND.*COSY.*DEFF_F" ~/.claude/agents/lucy-devils-advocate.md

# SKILL-03: G6 has solncounter check
grep -n "solncounter\|merged.smi.*empty" ~/.claude/agents/lucy-devils-advocate.md

# Cross-file consistency: what lsd-engineer writes, DA validates
# lsd-engineer now writes COSY ... ; equiv-pair → DA must check grep -c "^COSY.*; equiv-pair"
grep -n "equiv-pair" ~/.claude/agents/lucy-devils-advocate.md
# Must return >= 1 line in the Check 1 table
```
</verification>

<success_criteria>
1. No SYME row in DA §1 Count Comparison table
2. COSY equivalence row (equiv-pair) in Count Comparison table
3. Ring exclusion (DEFF F1+F2+FEXP) in Count Comparison table and Bug 1 check
4. Check 1, 2, 3 tables use ring_exclusion_enabled and cosy_equiv_pairs
5. [VALIDATION-PASSED] template uses Ring exclusion and COSY-equiv fields
6. grep returns exactly 4 for G5/G6/G7/G8 gate headings
7. G5 has bash loop checking BOND/COSY/DEFF F counts per perm file
8. G6 has bash check comparing solncounter vs merged.smi size
9. G7 documents hash self-check and adds hash line to [VALIDATION-PASSED] template
10. G8 has WARNING severity and documents reversion pattern
</success_criteria>

<output>
Create /Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/75-skill-consolidation/75-02-SUMMARY.md when done.
NOTE: ~/.claude/ files are NOT committed to the lucy-ng git repo. Only SUMMARY.md is committed.
</output>
