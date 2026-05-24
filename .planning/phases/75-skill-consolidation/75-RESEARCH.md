# Phase 75: Skill Consolidation — Research

**Researched:** 2026-05-24
**Domain:** Agent skill files (lsd-engineer, devils-advocate, case.md, references, nmr-chemist, solution-analyst, diagnostic/SKILL.md) — correct native-command instruction, single-path solver documentation, v8.0-failure-mode DA gates
**Confidence:** HIGH — all findings from direct file inspection with line numbers

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SKILL-01 | All agent skills correct against LSD-3.4.9 — no commands taught that the binary rejects; native equivalents documented | SYME inventory: 7 locations; DEFF NOT inventory: 10+ locations; each maps to BOND/COSY or DEFF F/FEXP replacement per verified ground truth |
| SKILL-02 | Single-solver-path guidance per D-02 — resolve normal-LSD vs pyLSD documentation imbalance | Imbalance is structural in lsd-engineer §1 (pyLSD subsection is explicit but subordinate); D-02 requires further subordination with "use ONLY when" gate and removal of co-equal headings |
| SKILL-03 | DA gates detect v8.0 failure modes: silent constraint loss, empty merge despite per-run solutions, post-validation file edits, agent reversion | Four new DA checks identified; current DA has no equivalent; exact check logic specified below |
</phase_requirements>

---

## Summary

Phase 75 is a pure skill-documentation edit phase — no Python code changes, no tests to write beyond grep-based validation. The work falls into three non-overlapping streams:

**Stream 1 (SKILL-01): Native-command rewrites.** The agent currently writes `SYME` (non-native, LSD error 102) and `DEFF NOT <SMARTS>` (non-native, LSD error 150) in hand-built LSD files. These must be replaced everywhere they appear in skill instruction text with their verified native equivalents: `BOND`/`COSY` for SYME, `DEFF F<n> "<filter_file>"` + `FEXP "NOT F1 AND NOT F2"` for DEFF NOT. The native translations are established ground truth from `iteration_03/compound_native.lsd` (2 aromatic solutions, ibuprofen found). The complete inventory of all SYME and DEFF NOT mentions across all skill files is in Finding 1 below.

**Stream 2 (SKILL-02): Single-path restructuring.** `lucy-lsd-engineer.md` currently has a `### pyLSD Commands (pylsd_mode only)` subsection (lines 86-101) that is already framed as subordinate — "lsd-engineer does NOT write these directly." However, the routing logic at step 11 (lines 526-543) gives `lucy pylsd run` co-equal weight in a symmetric if/else. D-02 requires the permutation fallback to be in a clearly subordinate "Fallback path (use ONLY when...)" section with an explicit gate condition. The current `case.md` orchestrator is already CLI-agnostic enough that it needs no structural changes — the routing lives entirely in lsd-engineer and its step 11.

**Stream 3 (SKILL-03): New DA gates.** The devils-advocate currently catches constraint-count regressions and format issues, but has no gates for the four v8.0 failure modes. Four new checks must be added: (a) perm-file constraint completeness check (non-HMBC lines present in each perm dir), (b) empty merged.smi despite non-zero solncounter check, (c) post-validation file modification check, (d) agent-reversion-to-direct-binary detection.

**Primary recommendation:** Edit three files (lsd-engineer, devils-advocate, case.md task prompts) and one reference file (progress-format.md). Changes are surgical — quote-and-replace targeted sections, not full rewrites. Total edit surface: ~30 lines in lsd-engineer, ~25 lines in devils-advocate, ~6 lines in case.md, ~4 lines in progress-format.md.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LSD file command vocabulary | lsd-engineer.md §1 | diagnostic/SKILL.md §SYME | lsd-engineer is the sole LSD file writer; diagnostic reads but does not write |
| Badlist/ring-exclusion syntax | lsd-engineer.md §1 Badlist | devils-advocate §2 Bug 1 | engineer writes; DA validates persistence |
| Solver-path routing | lsd-engineer.md step 11 | case.md spawn prompts | routing decision is lsd-engineer's; case.md prompts reinforce it |
| Constraint persistence across iterations | lsd-engineer.md CRITICAL RULE + §5 | devils-advocate §1, §5B | engineer carries constraints forward; DA audits the result |
| DA gate definitions | devils-advocate.md | lsd-engineer.md (indirect, through knowing what DA checks) | DA is authoritative; lsd-engineer does not duplicate DA gate logic |
| CASE-PROGRESS.md constraint inventory line | progress-format.md + case.md | lsd-engineer §4 | orchestrator writes from lsd-engineer's message field |

---

## Finding 1: Complete SYME Inventory Across All Skill Files

[VERIFIED: direct file inspection with grep -n]

### 1a. lsd-engineer.md

| Line | Text | Action |
|------|------|--------|
| 71 | `SYME 5 6        ; atoms 5 and 6 are equivalent (symmetry)` — in the **Bond and Property Constraints** command reference block | Replace with BOND and COSY equivalent; add explanatory comment. See §Architecture Patterns for exact replacement text. |
| 308 | `Constraint inventory delta: MULT=N, HSQC=N, HMBC=+N (total N), DEFF NOT=N, **SYME=N**, BOND=N, DEFF_FEXP=applied/none/discarded` — in the [ITERATION-COMPLETE] message template | Replace `SYME=N` with `COSY_equiv=N` (count of COSY aromatic-pair lines) to reflect native tracking |
| 373 | `"syme_pairs"` field in constraint inventory v2 schema table | Rename to `"cosy_equiv_pairs"` with description "COSY-encoded aromatic CH equivalence pairs: `"4 7"`" |
| 430 | `"pending_from_detection": ["SYME for grouped [44.90, 45.03] -- NOT YET APPLIED"]` — in the inline inventory example | Replace `SYME` with `COSY-equivalence BOND/COSY` in the example |

### 1b. devils-advocate.md

| Line | Text | Action |
|------|------|--------|
| 57 | `SYME constraints | Persist once added | Removed -> CRITICAL` — in the Count Comparison table | Replace `SYME constraints` with `COSY equivalence lines (aromatic CH pairs)` |
| 63 | `Every BOND line in iteration N-1 must appear in iteration N (unless advisory says remove)` — adjacent content that refers to SYME in context | No direct SYME text here but row above it references SYME; covered by row 57 change |
| 72 | `SYME added from grouping detection` — in Expected (Normal) Changes list | Replace with `COSY aromatic-pair constraints added from grouping detection` |
| 99 | Bug 2 text: `agent never translated to **SYME** or parenthesized HMBC` | Replace `SYME` with `COSY equivalence constraints (COSY atom1 atom2)` |
| 102 | `SYME constraint exists for grouped atoms, OR` | Replace with `COSY equivalence constraint (COSY atom1 atom2) exists for grouped atoms, OR` |
| 270 | `"syme_pairs" (array length) | grep -c "^SYME" compound.lsd | Exact` — in Check 1 table | Replace with `"cosy_equiv_pairs" (array length) | grep -c "^COSY" compound.lsd | Exact` — note: this counts ALL COSY lines; if COSY peak data is also present, the inventory field must count only equivalence-derived COSY. Recommend: use a distinct comment `; COSY-equiv` suffix or separate inventory field. See Open Questions. |
| 285 | `"syme_pairs" length | >= previous | Decrease -> CRITICAL` — in Check 2 table | Replace field name with `"cosy_equiv_pairs"` |
| 294 | `"syme_pairs"` in Check 3 array listing | Replace with `"cosy_equiv_pairs"` |
| 383 | `SYME: N constraints (preserved / N/A)` — in [VALIDATION-PASSED] template | Replace with `COSY-equiv: N pairs (preserved / N/A)` |
| 408 | Implied SYME tracking (not explicit text, but `## 1 Count Comparison` table drives validation messages) | Covered by table change at line 57 |

### 1c. diagnostic/SKILL.md (legacy skill file, not agent skill — currently NOT read by CASE team agents)

| Lines | Text | Action |
|-------|------|--------|
| 229-255 | Full `### SYME - Symmetry Equivalence` section with `SYME atom_index_1 atom_index_2` syntax, fallback `LIST/PROP`, example `SYME 5 6` / `SYME 7 8` | This file is in `skill/diagnostic/SKILL.md` (repo). The diagnostic agent is spawned via Task() and reads its own `lucy-diagnostic.md` agent definition, NOT this skill/ directory directly. However, lsd-engineer's CRITICAL RULE references `skill/SKILL.md` sections. Per 74-RESEARCH Finding 6: "diagnostic/SKILL.md lines 229-255" is where SYME is documented. The diagnostic agent should be updated to reflect native commands. **Scope:** document SYME as non-native, document BOND/COSY as the correct encoding. This is a lower-priority edit (diagnostic agent is rarely spawned); mark as Phase 75 scope but Wave 2 after lsd-engineer/DA. |
| 806-845 | Symmetry failure analysis section with `grep -i "SYME" compound.lsd` and explicit `SYME atom_idx_1 atom_idx_2` fix instructions | Replace grep with `grep -c "^COSY" compound.lsd`; replace SYME fix instructions with BOND/COSY native instructions |

### 1d. case.md orchestrator

Line 167 (spawn prompt for devils-advocate agent):
```
"2. Check for dropped constraints (DEFF NOT, SYME, grouped notation)"
```
Action: Replace `SYME` with `COSY equivalence pairs (BOND/COSY for gem-dimethyl and aromatic CH)`.

### 1e. progress-format.md (references directory)

| Line | Text | Action |
|------|------|--------|
| 44 | `**Constraint inventory (iteration 0):** MULT=0, HSQC=0, HMBC=0, DEFF NOT=0, SYME=0, BOND=0` | Replace `SYME=0` with `COSY_equiv=0` |
| 88 | `**SYME:** <from message>` — in Devils-Advocate section template | Replace with `**COSY-equiv:** <from message>` |

### 1f. solution-analyst.md, nmr-chemist.md

No SYME references found in these files. [VERIFIED: grep confirmed]

### Summary: SYME mention count by file

| File | SYME mentions | All require replacement |
|------|--------------|------------------------|
| lsd-engineer.md | 4 (lines 71, 308, 373, 430) | Yes |
| devils-advocate.md | 8 (lines 57, 72, 99, 102, 270, 285, 294, 383) | Yes |
| diagnostic/SKILL.md | 10+ (lines 229-255, 806-845) | Yes (Wave 2) |
| case.md | 1 (line 167) | Yes |
| progress-format.md | 2 (lines 44, 88) | Yes |
| nmr-chemist.md | 0 | N/A |
| solution-analyst.md | 0 | N/A |

---

## Finding 2: Complete DEFF NOT Inventory Across All Skill Files

[VERIFIED: direct file inspection with grep -n]

### 2a. lsd-engineer.md — THE critical section (lines 120-138)

Current text (lines 120-138):
```
### Badlist Filters (DEFF NOT)

Add to EVERY LSD file after correlations, before ELIM:

DEFF NOT C1CC1      ; no cyclopropane
DEFF NOT C1CCC1     ; no cyclobutane
DEFF NOT C1NC1      ; no aziridine
DEFF NOT C1NCC1     ; no azetidine
DEFF NOT C1SC1      ; no thiirane
DEFF NOT C1SCC1     ; no thietane
DEFF NOT C1OC1      ; no epoxide
DEFF NOT C1OCC1     ; no oxetane

Exception: Remove epoxide exclusion if 13C shows 45-55 ppm + formula has O.

**CRITICAL: These DEFF NOT lines MUST persist across ALL iterations. Dropping them was v3.0 bug #1.**
```

**Required replacement:** The entire `### Badlist Filters (DEFF NOT)` section becomes `### Badlist Filters (Native Ring Exclusion)` with the DEFF F/FEXP pattern. Full replacement text in §Architecture Patterns below.

Additional DEFF NOT mentions in lsd-engineer.md:

| Line | Text | Action |
|------|------|--------|
| 167 | `This is different from \`DEFF NOT\` which goes after correlations.` — in Fragment Goodlist ordering rule | Update to: `This is different from ring-exclusion DEFF F / FEXP which also goes after correlations.` |
| 192 | `8. Badlist DEFF NOT patterns present` — in Manual Checklist | Replace with `8. Ring exclusion DEFF F1/F2 + FEXP present` |
| 222 | `1. Start with MULT + HSQC + heteroatom constraints + **DEFF NOT** + first batch 3-5 HMBC` | Replace `DEFF NOT` with `DEFF F/FEXP ring exclusion` |
| 376 | `"deff_not_patterns"` field in inventory schema table | Keep field name for backward-compat BUT update description: "Deprecated: was SMARTS strings for each DEFF NOT command. Now: empty array [] — ring exclusion is emitted as DEFF F / FEXP (see ring_exclusion_enabled field)" — see Open Questions on inventory schema migration |
| 405 | `"deff_not_patterns": ["C1CC1", "C1CCC1", ...]` — in inline inventory example | Replace with `"deff_not_patterns": []  ; deprecated — ring exclusion now via DEFF F/FEXP` and add `"ring_exclusion_enabled": true` |
| 443 | `After writing all MULT, HSQC, first HMBC batch, BOND, and DEFF NOT to the file:` — in Initialization Procedure | Replace `DEFF NOT` with `ring exclusion (DEFF F/FEXP)` |
| 447 | `3. **CRITICAL:** Populate \`deff_not_patterns\` from the full badlist set (Section 1 -- these are constant).` | Update to reflect `ring_exclusion_enabled: true` as the new tracking mechanism |
| 519 | `then MULT defs, HSQC, HMBC batch, BOND/LIST/PROP, DEFF NOT` — step 6 in workflow | Replace `DEFF NOT` with `DEFF F/FEXP ring exclusion` |

### 2b. devils-advocate.md — DEFF NOT validation

| Lines | Text | Action |
|-------|------|--------|
| 56 | `DEFF NOT patterns | **ALWAYS persist** | Any decrease -> CRITICAL` — Count Comparison table | Update row description. Replace with `Ring exclusion (DEFF F + FEXP) | **ALWAYS persist** | Absent or removed -> CRITICAL` |
| 63 | `Every DEFF NOT line in iteration N-1 must appear in iteration N (exact string match)` — Content Comparison | Replace with `DEFF F1 / DEFF F2 / FEXP lines in iteration N-1 must appear in iteration N` |
| 79-94 | Entire `### Bug 1: DEFF NOT Patterns Dropped (CRITICAL)` block including the 8-line SMARTS block | Rewrite completely. New Bug 1 check is absence of `DEFF F1 / DEFF F2 / FEXP` block. Expected minimum: `DEFF F1 "ring3"`, `DEFF F2 "ring4"`, `FEXP "NOT F1 AND NOT F2"`. Grep: `grep -c "^DEFF F" compound.lsd` must be >= 2 and `grep -c "^FEXP" compound.lsd` must be >= 1. |
| 163 | `For natural products, expect minimum: C1CC1 and C1CCC1 DEFF NOT patterns.` — Badlist Completeness check | Replace with `For natural products, expect DEFF F1 ring3 + DEFF F2 ring4 + FEXP. grep -c "^DEFF F" must be >= 2.` |
| 269 | `\`deff_not_patterns\` (array length) | \`grep -c "^DEFF NOT" compound.lsd\` | Exact` — Check 1 table | Replace with `ring_exclusion_enabled | grep -c "^DEFF F" >= 2 AND grep -c "^FEXP" >= 1 | Must be true when enabled` |
| 358-359 | Bug 1 enhanced check via inventory | Replace `deff_not_patterns` reference with `ring_exclusion_enabled` + `grep -c "^DEFF F"` |
| 382 | `DEFF NOT: N patterns (preserved from iteration N-1 / initialized)` — [VALIDATION-PASSED] template | Replace with `Ring exclusion: DEFF F1+F2+FEXP (present / MISSING)` |
| 408 | `DEFF NOT: N patterns (DROPPED from N-1 count of M / preserved)` — [VALIDATION-BLOCKED] template | Replace with `Ring exclusion: DEFF F/FEXP (MISSING / present)` |

### 2c. solution-analyst.md

Line 105: `Natural products almost never contain cyclopropane or cyclobutane. If **DEFF NOT** was properly applied, this should already be filtered.`
Action: Replace `DEFF NOT` with `ring exclusion (DEFF F/FEXP)`. Cosmetic — this doesn't affect agent behavior but keeps vocabulary consistent.

### 2d. progress-format.md

Line 44: `DEFF NOT=0` — in constraint inventory initialization.
Action: Replace `DEFF NOT=0` with `ring_excl=enabled`. This is the orchestrator-written log field; must match lsd-engineer's updated [ITERATION-COMPLETE] message template.

Line 86: `**DEFF NOT:** <from message>` — in Devils-Advocate section template.
Action: Replace with `**Ring exclusion:** <from message>`.

### 2e. diagnostic/SKILL.md

Lines 257-263: `### DEFF - Deff Angle Constraint` — this is a different DEFF (stereochemical angle) and does NOT need changing.

No `DEFF NOT` pattern found in diagnostic/SKILL.md. [VERIFIED: grep confirmed no output]

### 2f. case.md orchestrator

Line 167: `DEFF NOT, SYME, grouped notation` — spawn prompt.
Action: Replace `DEFF NOT` with `ring exclusion (DEFF F/FEXP)`, and `SYME` with `COSY equivalence pairs`. Full replacement: `Check for dropped constraints (ring exclusion DEFF F/FEXP, COSY equivalence pairs, grouped notation)`.

---

## Finding 3: Normal-LSD vs pyLSD Documentation Imbalance in lsd-engineer.md

[VERIFIED: direct inspection of lsd-engineer.md lines 86-101 and step 11 lines 526-543]

### Current state (the imbalance)

**Section `### pyLSD Commands (pylsd_mode only)` (lines 86-101, 16 lines):**
- Explicitly labeled "pylsd_mode only"
- Contains `HMBC X Y 2 4` (correct 4J mechanism) and `HMBC X Y 2 4 ; ELIM` (orchestrator parsing annotation)
- Followed by ELIM-in-pylsd_mode prohibition
- The framing "lsd-engineer does NOT write these directly" correctly positions pyLSD as a tool used by the orchestrator, NOT the agent

This section is already somewhat demoted in framing. The imbalance is not severe in §1 — it's worse in **step 11** and in the **heading level**.

**Step 11 routing block (lines 526-543) — symmetric if/else structure:**
```bash
if [ "$PYLSD_MODE" = "True" ]; then
  # Multi-run mode: use PyLSDOrchestrator via lucy pylsd run
  lucy pylsd run analysis/iteration_NN/compound.lsd ...
else
  # Single-run mode: classic lucy lsd run
  cd analysis/iteration_NN && lucy lsd run compound.lsd
fi
```

The `if` branch (pyLSD) gets the same prominence as the `else` branch (normal LSD). D-02 requires normal LSD to be the primary case — it should be the `if`-less default with pyLSD as the clearly-secondary fallback.

**The heading-level problem:** In §1 Command Reference, the structure is:
- `### pyLSD Commands (pylsd_mode only)` — a `###` heading, same level as `### Badlist Filters`, `### Fragment Goodlist`, `### Solution Conversion`

D-02 rule 4: "normal-LSD skill listed first, top of doc" and rule 3: "no skill section gives pyLSD equal weight, equal heading level." The `###` heading for pyLSD is co-equal. It should be reduced to an unlabeled note or a clearly subordinate `#### Fallback: pyLSD permutation mode` under normal LSD.

### D-02 restructuring required in lsd-engineer.md

1. **Rename and demote the heading** (line 86): `### pyLSD Commands (pylsd_mode only)` → `#### Fallback Path: Permutation Mode Commands (use ONLY when primary path yields 0 solutions or >threshold solutions)`

2. **Rewrite step 11** to make normal LSD the primary (no-condition) path, pyLSD the exception. New structure:
```bash
# PRIMARY PATH: single-run LSD with extended bond range
cd analysis/iteration_NN && lucy lsd run compound.lsd
# solutions.smi is produced automatically by lucy lsd run (Phase-73 fix)

# FALLBACK PATH (use ONLY when primary yields 0 solutions AND K<=3 deferred 4J suspects exist):
# Read inventory to check pylsd_mode flag
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
PYLSD_MODE=$(echo "$RESULT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")
if [ "$PYLSD_MODE" = "True" ]; then
  lucy pylsd run analysis/iteration_NN/compound.lsd \
    --shifts "<comma_separated_13C_shifts>" \
    --format json | tee analysis/iteration_NN/pylsd_output.json
fi
```

3. **Remove the note** "also the silent fallback for ABSENT inventory per D-19" from step 11 — this was a v8.0 routing subtlety that no longer applies when pylsd_mode is explicitly a fallback.

4. **In §1 Command Reference**, move `HMBC X Y 2 4` (the extended bond range command) OUT of the pyLSD subsection and INTO the main HMBC correlations block as a first-class command. This is the primary 4J mechanism per D-01, not a pyLSD detail.

### Current state in case.md

`case.md` does NOT contain any routing logic for pylsd_mode vs normal LSD. The routing lives entirely in lsd-engineer's step 11. The case.md spawn prompts (lines 108, 138, 300) repeat `outlsd 5 < compound.sol > solutions.smi` — see Finding 5 below.

Case.md does NOT need structural single-path restructuring. It is already CLI-agnostic at the orchestrator level.

---

## Finding 4: devils-advocate Current Gates G1-G4 — Full Text and SKILL-03 Additions

[VERIFIED: direct inspection of devils-advocate.md lines 296-346]

### Current G1-G4 (lines 296-346)

**G1: FORM/MULT Consistency** (lines 302-308): When `pylsd_mode=true`, extract carbon count from `; FORM` comment line, compare to MULT C atom count. Mismatch → BLOCK "FORM/MULT mismatch: FORM declares N carbons, MULT defines M carbons."

**G2: No Bare ELIM Command in pylsd_mode** (lines 310-318): `grep -n "^ELIM"` — if any match with pylsd_mode=true → BLOCK.

**G3: Annotation-vs-Mode Consistency** (lines 325-331): `grep -cE "^HMBC.*; ELIM"` — if any exist, all of `pylsd_mode=true, elim_annotated=true, len(deferred_4j)>0` must hold. CRITICAL with anchored grep.

**G4: Permutation Count Cap** (lines 334-342): K = len(deferred_4j). K > 3 → BLOCK with escalation guidance.

**Check 4 framing issue:** G1-G4 are bundled in a section called `**Check 4: pyLSD Mode Consistency**`. With D-02's single-path decision, G1-G4 are still valid (the fallback path still exists, it just runs less often). G1-G4 do not need to be removed — they guard the fallback path correctly.

**SYME reference in G-gates:** None of G1-G4 directly reference SYME. The SYME/DEFF NOT references in the DA are in §1, §2, §5B inventory checks — all covered in Findings 1-2.

### SKILL-03: Four New DA Checks Required

These are the v8.0 failure modes that were not caught. Each becomes a new DA gate.

**New Check G5: Permutation File Constraint Completeness**

*When:* `pylsd_mode=true` and `lucy pylsd run` has been invoked (post-run check, runs on the perm files, not on compound.lsd pre-run).

*Note on timing:* The DA currently validates BEFORE the solver run. This gate checks AFTER `lucy pylsd run` produces permutation files but BEFORE the merge is accepted. The orchestrator should route a post-run check to DA via SendMessage when pylsd_mode is true. Add to DA workflow step: "If pylsd_run/ directory exists in the iteration dir, run G5 check."

*Detection:*
```bash
# Check each perm_NN directory for non-HMBC constraint lines
for perm_dir in analysis/iteration_NN/pylsd_run/perm_*/; do
  bond_count=$(grep -c "^BOND" "$perm_dir/compound.lsd" 2>/dev/null || echo 0)
  cosy_count=$(grep -c "^COSY" "$perm_dir/compound.lsd" 2>/dev/null || echo 0)
  deff_count=$(grep -c "^DEFF F" "$perm_dir/compound.lsd" 2>/dev/null || echo 0)
  if [ "$bond_count" -eq 0 ] && [ "$cosy_count" -eq 0 ] && [ "$deff_count" -eq 0 ]; then
    echo "CRITICAL: $perm_dir/compound.lsd appears HMBC-only (BOND=$bond_count COSY=$cosy_count DEFF_F=$deff_count)"
  fi
done
```

*Trigger:* Any perm file with BOND=0 AND COSY=0 AND DEFF_F=0 → CRITICAL. This was the exact v8.0 "542-byte HMBC-only perm file" failure pattern.

*Action:* BLOCK with message: "Permutation file {perm_dir}/compound.lsd is HMBC-only — BOND={N}, COSY={N}, DEFF F={N}. This was the v8.0 constraint-loss failure. Check that PyLSDOrchestrator._build_permutation() is receiving a fully-populated LSDProblem (not HMBC-only). Do not proceed with merge until perm files carry the full constraint set."

**New Check G6: Empty merged.smi Despite Non-Zero solncounter**

*When:* After `lucy pylsd run` completes (post-run check).

*Detection:*
```bash
# Check solncounter files
for solncounter in analysis/iteration_NN/pylsd_run/perm_*/solncounter; do
  count=$(cat "$solncounter" 2>/dev/null || echo 0)
  if [ "$count" -gt 0 ]; then
    # Solutions exist — check merged.smi
    merged="analysis/iteration_NN/pylsd_run/merged.smi"
    if [ ! -s "$merged" ]; then
      echo "CRITICAL: solncounter=$count in $solncounter but merged.smi is empty/missing"
    fi
  fi
done
```

*Also check:* `run_report.json` for `"total_raw_solutions": 0` when any solncounter > 0.

*Trigger:* Any perm has solncounter > 0 AND (merged.smi missing OR merged.smi empty OR run_report total_raw_solutions = 0) → CRITICAL.

*Action:* BLOCK with message: "Empty merge despite solutions in permutations — this was the v8.0 keystone bug (outlsd conversion failure). Check: (1) solutions.smi in each perm dir is non-empty. (2) _invoke_outlsd ran correctly. (3) SolutionMerger collected from correct path. Phase 73 should have fixed this — if it recurs, escalate."

**New Check G7: Post-Validation File Modification**

*When:* DA runs pre-run validation AND issues APPROVED. Check at the moment lsd-engineer reports the solver is about to run (or just ran).

*Detection:*
```bash
# Record file modification time at approval time, compare at run time
approval_time=$(date +%s)
# ... (lsd-engineer runs solver) ...
file_mtime=$(stat -f %m analysis/iteration_NN/compound.lsd 2>/dev/null || stat -c %Y analysis/iteration_NN/compound.lsd)
if [ "$file_mtime" -gt "$approval_time" ]; then
  echo "CRITICAL: compound.lsd modified after DA approval (mtime > approval_time)"
fi
```

*Practical implementation:* DA records the file hash (md5 or sha256) at approval time and includes it in the [VALIDATION-PASSED] message. The orchestrator includes the expected hash in the [DA-APPROVED] relay. lsd-engineer verifies the file hasn't changed before running the solver.

*Trigger:* File hash at solver invocation != file hash at DA approval time → CRITICAL.

*Action:* BLOCK with message: "LSD file {path} was modified after DA approval (hash mismatch). This was item 8 in the v8.0 UAT postmortem. Re-validate before running solver."

*Implementation note:* This check requires DA to output a hash in [VALIDATION-PASSED] and lsd-engineer to verify it in step 11 before running. The check is simpler as a self-check by lsd-engineer than a DA gate — recommend implementing as a lsd-engineer pre-run assertion rather than a DA gate. See Open Questions.

**New Check G8: Agent Reversion Detection (post-run, DA reads CASE-PROGRESS.md)**

*When:* After each iteration, DA reads the [ITERATION-COMPLETE] message routing block.

*Detection:* If `pylsd_mode=true` in the inventory but the [ITERATION-COMPLETE] message shows `lucy lsd run` was used (not `lucy pylsd run`), flag as CRITICAL reversion.

*Detection via inventory:*
```bash
# Check that routing matched inventory
inventory_mode=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")
# Compare against what lsd-engineer reported in ITERATION-COMPLETE (orchestrator should embed this)
```

*Trigger:* inventory says `pylsd_mode=true` but iteration used `lucy lsd run` without explicit fallback justification → WARNING (not CRITICAL — reversion may be valid if all non-4J correlations are exhausted and the agent is doing a final direct run).

*Action:* WARNING with message: "pylsd_mode=true in inventory but direct lucy lsd run was used. This was the v8.0 reversion pattern that caused ibuprofen to be found via bypass. If this was a deliberate fallback (0 solutions from pylsd), document the reason in ITERATION-COMPLETE."

---

## Finding 5: Phase-73 Obsoletes the Manual `outlsd 5 <` Pipe

[VERIFIED: Phase-73-VERIFICATION.md + direct inspection of runner.py]

Phase 73 fixed `runner.run_file()` (called by `lucy lsd run`) to internally invoke `_invoke_outlsd` and produce `solutions.smi` as part of the `lucy lsd run` command. After Phase 73:

- `lucy lsd run compound.lsd` → produces `compound.sol` AND `solutions.smi` in the output directory
- The manual pipeline `outlsd 5 < compound.sol > solutions.smi` is **no longer needed** for the primary path
- The manual invocation can still be used for debugging but should not be instructed as the standard flow

**Files where `outlsd 5 < compound.sol > solutions.smi` appears and must be updated:**

| File | Lines | Action |
|------|-------|--------|
| lsd-engineer.md | 105 (`### Solution Conversion` block), 545 (step 13: `If solutions <= 10: outlsd 5 < compound.sol > solutions.smi`) | Remove the `### Solution Conversion` block entirely. Replace step 13 with: "solutions.smi is produced automatically by `lucy lsd run`. No manual outlsd invocation needed." |
| case.md | 108, 138, 300 (all three TaskCreate description strings) | Remove `Convert solutions: outlsd 5 < compound.sol > solutions.smi` from all three task descriptions. |
| case.md | 75 (in validate_prerequisites: `lucy lsd check` verifies LSD and outlsd available) | Keep this check — `outlsd` is still used internally by the runner |

**Why this matters for SKILL-02:** Removing the manual pipe simplifies the workflow — agents no longer need a separate step after the solver run. This is also a SKILL-01 fix: the old instruction hardcoded stdin redirection that was the root of the v8.0 outlsd conversion bug.

---

## Finding 6: case.md Routing — No Structural Change Needed

[VERIFIED: direct inspection of case.md]

`case.md` orchestrator does NOT contain routing logic for pylsd_mode vs normal LSD. The routing decision is entirely in lsd-engineer's step 11. Case.md's job is to spawn agents and manage progress — it is already CLI-agnostic.

**What case.md DOES contain that needs updating:**
1. Three `outlsd 5 < compound.sol > solutions.smi` lines in TaskCreate descriptions (see Finding 5 — remove)
2. One SYME reference in spawn prompt (line 167 — update to BOND/COSY, per Finding 1d)
3. One `DEFF NOT` reference in spawn prompt (line 167 — update to ring exclusion, per Finding 2f)

**What case.md does NOT need:**
- No routing restructure
- No pyLSD demotion (routing lives in lsd-engineer)
- No heading changes

---

## Finding 7: SKILL-01/02/03 → File Map

| Requirement | Primary File | Secondary Files | Edit Type |
|------------|-------------|-----------------|-----------|
| SKILL-01 (SYME) | lsd-engineer.md lines 71, 308, 373, 430 | devils-advocate.md lines 57, 72, 99, 102, 270, 285, 294, 383; case.md line 167; progress-format.md lines 44, 88 | Targeted text replacements |
| SKILL-01 (DEFF NOT) | lsd-engineer.md lines 120-138 (full section rewrite), 167, 192, 222, 376, 405, 443, 447, 519 | devils-advocate.md lines 56, 63, 79-94, 163, 269, 358-359, 382, 408; solution-analyst.md line 105; progress-format.md lines 44, 86; case.md line 167 | Section rewrite + targeted replacements |
| SKILL-01 (outlsd pipe) | lsd-engineer.md line 105 block + line 545 | case.md lines 108, 138, 300 | Remove/replace specific lines |
| SKILL-01 (diagnostic/SKILL.md) | skill/diagnostic/SKILL.md lines 229-255, 806-845 | — | Wave 2: rewrite SYME section to BOND/COSY |
| SKILL-02 (single path) | lsd-engineer.md lines 86 (heading), 526-543 (step 11 routing block) | — | Rename heading; restructure if/else to primary-then-fallback; move HMBC X Y 2 4 to main HMBC block |
| SKILL-03 (G5 perm completeness) | devils-advocate.md: add after G4 | — | New gate section (10-15 lines) |
| SKILL-03 (G6 empty merge) | devils-advocate.md: add after G5 | — | New gate section (10-15 lines) |
| SKILL-03 (G7 post-validation edit) | lsd-engineer.md step 11: add file-hash check | devils-advocate.md: add hash to [VALIDATION-PASSED] template | Self-check in lsd-engineer (simpler than DA gate) |
| SKILL-03 (G8 reversion detection) | devils-advocate.md: add warning check | — | New WARNING-severity check (10 lines) |

---

## Architecture Patterns

### Replacement Text for SYME → BOND/COSY in lsd-engineer.md §1

Replace line 71 (`SYME 5 6 ; atoms 5 and 6 are equivalent (symmetry)`) with:

```
; --- Equivalence constraints (SYME is NOT native — use BOND/COSY instead) ---
BOND 10 11      ; gem-dimethyl: force both CH3 onto same isobutyl CH (equiv of SYME 11 12)
BOND 10 12      ; gem-dimethyl: second CH3 (same parent atom 10)
COSY 4 7        ; aromatic CH pair equivalence: 3J H-H coupling encodes ring adjacency
COSY 5 6        ; aromatic CH pair equivalence (second equivalent pair)
; Rule: gem-dimethyl/isopropyl -> BOND parent methyl1 + BOND parent methyl2
; Rule: aromatic CH equivalent pair -> COSY atom1 atom2
; SYME causes LSD error 102 (unknown command) — NEVER write SYME to an LSD file
```

Add a note immediately after the BOND/PROP block:

```
**NATIVE EQUIVALENCE COMMANDS (replaces SYME):**
| Equivalence type | Native encoding | Source |
|-----------------|-----------------|--------|
| Gem-dimethyl (2 CH3 on same parent) | BOND parent CH3_1 + BOND parent CH3_2 | compound_native.lsd iter3 |
| Aromatic CH pair (equivalent ring positions) | COSY atom1 atom2 | compound_native.lsd iter3 |
| Isopropyl (2 CH3, same CH) | same as gem-dimethyl | same |
Homotopic CH2 (same carbon): no action needed — MULT defines both protons at same atom index.
SYME is NOT native in LSD-3.4.9 and causes error 102. Do NOT write SYME.
```

### Replacement Text for DEFF NOT → DEFF F/FEXP in lsd-engineer.md §1

Replace `### Badlist Filters (DEFF NOT)` section (lines 120-138) with:

```
### Badlist Filters (Native Ring Exclusion via DEFF F / FEXP)

Add to EVERY LSD file after correlations, before EXIT. Ring exclusion uses pre-built filter files
distributed with the lucy-ng package (Phase 74: bundled in src/lucy_ng/lsd/filters/).

**Standard ring exclusion block (ALWAYS include):**
```
DEFF F1 "ring3"    ; exclude 3-membered rings (cyclopropane etc.)
DEFF F2 "ring4"    ; exclude 4-membered rings (cyclobutane etc.)
FEXP "NOT F1 AND NOT F2"
```

**Note:** Paths are relative — LSD resolves them from its working directory (the iteration dir).
The filter files ring3 and ring4 are written there automatically by lucy lsd run / LSDInputGenerator.

Exception: Remove DEFF F1/ring3 exclusion only if 13C shows 45-55 ppm + formula has O
(possible epoxide — let LSD explore). Adjust FEXP accordingly: `FEXP "NOT F2"`.

**CRITICAL: These DEFF F / FEXP lines MUST persist across ALL iterations. Dropping them was v3.0 bug #1.**

**NOT NATIVE:** `DEFF NOT C1CC1` (SMARTS syntax) causes LSD error 150. Do NOT write DEFF NOT.
```

### Replacement Text for step 11 routing (lsd-engineer.md) — SKILL-02

Replace lines 526-543 (the symmetric if/else) with:

```bash
11. Run LSD — PRIMARY PATH (single-run, always):

cd analysis/iteration_NN && lucy lsd run compound.lsd
# lucy lsd run produces compound.sol AND solutions.smi automatically (Phase 73 fix).
# No manual outlsd invocation needed.

# FALLBACK PATH — use ONLY when:
# (a) primary path yields 0 solutions, AND
# (b) K <= 3 deferred 4J suspects exist in the constraint inventory
# (c) pylsd_mode=true in the inventory

RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
PYLSD_MODE=$(echo "$RESULT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")

if [ "$PYLSD_MODE" = "True" ]; then
  # Permutation fallback: PyLSDOrchestrator explores 4J correlation combinations
  lucy pylsd run analysis/iteration_NN/compound.lsd \
    --shifts "<comma_separated_13C_shifts>" \
    --format json | tee analysis/iteration_NN/pylsd_output.json
  # After pylsd run: verify perm files are not HMBC-only (G5 check, send to DA)
fi
```

**D-04 reminder:** Do NOT add SKEL benzene fragment. Correct BOND/COSY constraints yield the aromatic ring without forcing. SKEL is an escalation option for monosubstituted/highly-symmetric aromatics (few HMBC correlations, insufficient COSY pressure) — document as last resort, not standard practice.

### New SKILL-03 Gates to Add to devils-advocate.md

Add as `**Check 5: v8.0 Failure Mode Detection**` (new section, after the existing Check 4) with subsections G5, G6, G7, G8 per the text in Finding 4. Summary of placement and content:

- Section header: `## 5a. Permutation Constraint Completeness (G5)`
- Section header: `## 5b. Empty-Merge Detection (G6)`
- Section header: `## 5c. Post-Validation Edit Detection (G7)` — frame as self-check instruction to lsd-engineer (DA records hash in [VALIDATION-PASSED], lsd-engineer verifies before invoking solver)
- Section header: `## 5d. Reversion Detection (G8)` — WARNING severity only

Add to DA workflow (after step 9): "9a. If pylsd_run/ directory exists in the current iteration directory, run G5 and G6 post-run checks before approving the iteration."

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File hash for post-validation check | Custom hash implementation | `md5sum` / `sha256sum` CLI; or Python `hashlib.md5(open(path,'rb').read()).hexdigest()` | Portable; one-liner in Bash or Python; no new dependency |
| Ring filter file distribution | Writing SMARTS patterns to iteration dir | Bundled ring3/ring4 files (Phase 74 put them in src/lucy_ng/lsd/filters/) | Already done; the files exist; agent uses relative paths |
| Aromatic ring verification in DA | DA running RDKit SMILES analysis | This is solution-analyst's job (Check 6 in solution-analyst.md) | Already implemented; DA has no RDKit tools |

---

## Common Pitfalls

### Pitfall 1: DEFF F numbering conflict with fragment goodlist

**What goes wrong:** Ring exclusion uses `DEFF F1` / `DEFF F2`. Fragment goodlist ALSO uses `DEFF F1`. If both are present, one overwrites the other's F1 reference.

**Why it happens:** Two separate sections of the skill independently assign F1/F2. The fragment goodlist (from `lucy fragment to-lsd`) also produces `DEFF F1 "fragment_xxx.lsd"`.

**How to avoid:** Reserve F1/F2 for ring exclusion. Fragment goodlist starts at F3. The `lucy fragment to-lsd` CLI must be made to produce `DEFF F3` instead of `DEFF F1`. This is a Phase 74/75 implementation detail. The skill instruction must state: "Ring exclusion always uses F1 (ring3) and F2 (ring4). Fragment goodlist uses F3 and above. FEXP must include all relevant filter references."

**Warning signs:** LSD error about redefined filter name, or unexpectedly zero solutions when both badlist and fragment are active.

### Pitfall 2: Partial SYME replacement (BOND without COSY or vice versa)

**What goes wrong:** Agent writes BOND constraints for gem-dimethyl but forgets COSY for aromatic CH pairs (or vice versa). The aromatic ring may not emerge.

**Why it happens:** The two use cases look different. BOND = structural connectivity (gem-dimethyl). COSY = ring adjacency (aromatic). Without COSY on aromatic CH pairs, the topological pressure toward the 6-membered ring is reduced.

**How to avoid:** The skill must document BOTH translations and their use cases in the same table. DA Bug 2 check (signal grouping) should verify both BOND and COSY are written when symmetry is detected.

### Pitfall 3: Constraint inventory schema migration breaks DA Check 1

**What goes wrong:** Changing `deff_not_patterns` to `ring_exclusion_enabled` in the inventory schema invalidates existing DA Check 1 grep (`grep -c "^DEFF NOT" compound.lsd`). Old LSD files from prior iterations still have the v2 schema with `deff_not_patterns` populated.

**Why it happens:** Iterative workflow — old LSD files from previous iterations are read by DA in subsequent iterations. If the DA expects `ring_exclusion_enabled` but finds `deff_not_patterns`, the check fails incorrectly.

**How to avoid:** DA must handle both forms: if `deff_not_patterns` array is non-empty AND `ring_exclusion_enabled` is absent, fall back to the old `grep -c "^DEFF NOT"` check (legacy compatibility). Add migration note to DA: "If iterating on a compound where early iterations used DEFF NOT syntax, use legacy grep for those early iterations."

### Pitfall 4: Breaking G1-G4 while adding G5-G8

**What goes wrong:** Adding new gates in a way that displaces the existing G1-G4 numbering, causing references in existing skill text to be wrong.

**Why it happens:** G1-G4 are referenced by name elsewhere in the skill (e.g., "G2 blocks runs with non-null elim_value"). If they become G2-G5, those cross-references break.

**How to avoid:** Keep G1-G4 numbering identical. Add new gates as G5/G6/G7/G8 in a new section. No renumbering of existing gates.

### Pitfall 5: case.md TaskCreate descriptions are spawn hints, not agent skill

**What goes wrong:** Removing `outlsd 5 < compound.sol > solutions.smi` from case.md task descriptions causes confusion if lsd-engineer's skill still mentions the manual step.

**Why it happens:** Two sources of truth — skill file (lsd-engineer.md) and orchestrator (case.md task descriptions). They must be updated in sync.

**How to avoid:** Update BOTH simultaneously. Phase 75 plans should include both files as a single Wave 1 task.

---

## Validation Architecture

### Test Framework (for this phase)

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (existing); skill validation is grep-based |
| Config file | `pyproject.toml` |
| Quick run command | `pytest -x -q` (regression check — no Python changes) |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

Phase 75 edits only markdown files. No Python code changes. Validation is grep-based verification of the skill files themselves.

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| SKILL-01 (SYME gone) | No skill file contains the instruction to write SYME | grep | `grep -r "^SYME\b" ~/.claude/agents/lucy-*.md ~/.claude/commands/lucy-ng/ \| grep -v "NOT native\|error 102\|Do NOT write"` must return empty | Pattern anchored to line start so COSY-equiv documentation isn't false-positive |
| SKILL-01 (DEFF NOT gone) | No skill file instructs writing DEFF NOT | grep | `grep -r "DEFF NOT C1" ~/.claude/agents/lucy-*.md ~/.claude/commands/lucy-ng/` must return empty | C1 pattern targets SMARTS patterns only, not meta-commentary |
| SKILL-01 (BOND/COSY native) | lsd-engineer.md documents BOND/COSY as native equivalence mechanism | grep | `grep "BOND.*gem-dimethyl\|COSY.*aromatic CH pair" ~/.claude/agents/lucy-lsd-engineer.md` must return non-empty | |
| SKILL-01 (DEFF F/FEXP native) | lsd-engineer.md documents DEFF F + FEXP as ring exclusion | grep | `grep "DEFF F1.*ring3\|FEXP.*NOT F1 AND NOT F2" ~/.claude/agents/lucy-lsd-engineer.md` must return non-empty | |
| SKILL-01 (outlsd pipe) | No skill file instructs `outlsd 5 <` pipe | grep | `grep -r "outlsd 5 < compound" ~/.claude/agents/ ~/.claude/commands/lucy-ng/` must return empty | |
| SKILL-02 (single path) | lsd-engineer.md step 11 has normal LSD as primary, pyLSD in fallback conditional | grep | `grep -n "PRIMARY PATH\|FALLBACK PATH" ~/.claude/agents/lucy-lsd-engineer.md` must return both | |
| SKILL-03 (G5) | devils-advocate.md contains permutation constraint completeness check | grep | `grep -n "G5\|perm.*HMBC-only\|HMBC-only.*perm" ~/.claude/agents/lucy-devils-advocate.md` must return non-empty | |
| SKILL-03 (G6) | devils-advocate.md contains empty-merge detection | grep | `grep -n "G6\|merged.smi.*empty\|empty.*merge\|solncounter" ~/.claude/agents/lucy-devils-advocate.md` must return non-empty | |
| RELI-02/03 (pytest) | Existing pytest suite stays green (no Python touched) | unit | `pytest -x -q` must pass | Regression check only |

### Wave 0 Gaps

None — no new test files needed. Skill validation uses grep against file content. pytest is only run to confirm no Python regression.

### Sampling Rate

- Per task commit: `pytest -x -q` (confirm no accidental Python breakage) + grep spot-check of the edited section
- Per wave merge: full grep validation suite
- Phase gate: all grep validations green + manual read of lsd-engineer.md step 11 and DA G5-G6-G8 sections

---

## Runtime State Inventory

Step 2.6 applies: this phase edits agent skill files. No rename/refactor, no stored data, no service config.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no databases store skill file content | None |
| Live service config | None | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | None — skill files are Markdown, no compilation | None |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python/pytest | Regression check | Yes | 3.10+ | — |
| LSD binary | Not needed for skill edits | Yes | 3.4.9 | skip (no code changes) |
| grep | Skill validation | Yes | any | — |

---

## Open Questions

1. **DEFF F numbering conflict between ring exclusion and fragment goodlist**
   - What we know: Both use DEFF F1. Ring exclusion wants F1=ring3, F2=ring4. Fragment goodlist uses F1 for the fragment file.
   - What's unclear: Does `lucy fragment to-lsd` hardcode F1? If so, Phase 74 must update the CLI to start at F3 when ring exclusion is enabled.
   - Recommendation: Skill instructs "ring exclusion = F1/F2, fragment = F3+". Planner must add a task to check/update `lucy fragment to-lsd` CLI output if needed.

2. **Constraint inventory schema migration: `deff_not_patterns` → `ring_exclusion_enabled`**
   - What we know: The v2 schema has `deff_not_patterns` as a string array. Phase 74 generator uses `ring_exclusion_enabled` boolean. The CASE agent hand-writes the inventory.
   - What's unclear: Should the agent still populate `deff_not_patterns` (for backward compat with DA legacy checks) or set it to `[]` and add `ring_exclusion_enabled`?
   - Recommendation: Add `ring_exclusion_enabled` as a new field. Set `deff_not_patterns` to `[]` (not removed — removing would break v2 schema validation). DA handles both via the fallback logic described in Pitfall 3.

3. **G7 (post-validation edit) — DA gate vs lsd-engineer self-check**
   - What we know: The DA has Read tool only (no timing information). Recording a file hash at approval time and verifying it later requires the DA to output the hash AND lsd-engineer to verify it.
   - Recommendation: Implement as a lsd-engineer self-check in step 11: compute md5 of compound.lsd, compare to the hash from the [DA-APPROVED] relay message. If mismatch, do NOT run solver, send error to coordinator. This avoids adding Write capability to DA and makes the check more reliable.

4. **COSY equivalence pairs vs COSY peak data — deduplication**
   - What we know: DA Check 1 proposes `grep -c "^COSY"` to count COSY lines. But COSY peak data from the NMR spectrum also generates COSY lines.
   - What's unclear: Can the DA distinguish equivalence-derived COSY from peak-data COSY?
   - Recommendation: Tag equivalence-derived COSY with a trailing comment: `COSY 4 7  ; equiv-pair`. DA grep: `grep -c "^COSY.*; equiv-pair"`. Inventory field `cosy_equiv_pairs` stores only the equiv pairs. This distinguishes the two types cleanly.

5. **diagnostic/SKILL.md wave priority**
   - The diagnostic agent is rarely spawned (only after 2 failed basic interventions). SYME fix in diagnostic/SKILL.md affects only this rare path.
   - Recommendation: Wave 2. Primary wave 1 targets lsd-engineer + DA + case.md + references (the agents run on every CASE iteration).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `lucy lsd run` automatically produces `solutions.smi` after Phase 73 — manual `outlsd 5 <` pipe is obsolete | Finding 5 | If lsd run does NOT auto-produce solutions.smi, removing the manual step breaks the workflow |
| A2 | `ring3` and `ring4` filter files are written to the iteration directory alongside `compound.lsd` by `lucy lsd run` / `LSDInputGenerator.write_file()` (Phase 74 deliverable) | Finding 2 | If Phase 74 did not implement this, DEFF F1 "ring3" will not be found by LSD |
| A3 | The `deff_not_patterns` inventory field can coexist with a new `ring_exclusion_enabled` field without breaking schema validation | Finding 2, Open Q 2 | Schema may need updating to allow `ring_exclusion_enabled`; need to check `schemas/constraint_inventory_v2.json` |

**A1 risk mitigation:** Phase 73 verification explicitly confirms `runner.run_file()` internally calls `_invoke_outlsd` and writes `solutions.smi` (73-VERIFICATION.md Truth 2). HIGH confidence. [VERIFIED: 73-VERIFICATION.md]

**A2 risk mitigation:** Phase 74 research documents the filter-file bundling and `write_file()` filter-writing design (74-RESEARCH Finding 3, Pattern 3). Whether Phase 74 actually implemented this is confirmed by Phase 74 completion status (ROADMAP.md: Phase 74 Complete 2026-05-24). [ASSUMED until Phase 74 verification is read]

**A3 risk mitigation:** `schemas/constraint_inventory_v2.json` needs to be checked for field extensibility. If it uses `additionalProperties: false`, adding `ring_exclusion_enabled` will fail validation. The planner should add a task to update the schema.

---

## Sources

### Primary (HIGH confidence)

- Direct inspection: `~/.claude/agents/lucy-lsd-engineer.md` (549 lines, complete)
- Direct inspection: `~/.claude/agents/lucy-devils-advocate.md` (453 lines, complete)
- Direct inspection: `~/.claude/commands/lucy-ng/case.md` (595 lines, complete)
- Direct inspection: `~/.claude/commands/lucy-ng/references/progress-format.md`, `advisory-templates.md`, `loop-patterns.md`, `nmr-basics.md`
- Direct inspection: `~/.claude/agents/lucy-nmr-chemist.md`, `lucy-solution-analyst.md`
- Direct inspection: `skill/diagnostic/SKILL.md` (lines 229-255, 806-845)
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — locked D-02 (single path), D-03 (native commands), D-04 (EMERGENT aromatic)
- `.planning/phases/74-constraint-preservation-and-merge/74-RESEARCH.md` — Finding 6 (agent bypass scope gap), Finding 2 (SYME use cases and native translations)
- `.planning/phases/73-solution-plumbing-fix/73-VERIFICATION.md` — Truth 2 (solutions.smi auto-produced by lucy lsd run)
- `data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_03/compound_native.lsd` — ground-truth native LSD file
- `.planning/v8.0-UAT-POSTMORTEM.md` — v8.0 failure modes (postmortem items 3, 4, 8 map to G5/G6/G7/G8)
- `.planning/REQUIREMENTS.md` — SKILL-01, SKILL-02, SKILL-03 definitions

### Secondary (MEDIUM confidence)

- `src/lucy_ng/lsd/runner.py` — verified `run_file()` auto-produces `solutions.smi` (line 275, 283, 397)

---

## Metadata

**Confidence breakdown:**
- SYME/DEFF NOT full inventory: HIGH — grep with line numbers from direct inspection
- SKILL-02 single-path analysis: HIGH — step 11 directly read and quoted
- SKILL-03 new DA gate logic: HIGH — derived from postmortem + existing DA gate patterns
- Phase 73 solutions.smi obsoleting outlsd pipe: HIGH — verification report confirms
- Phase 74 filter-file auto-write: ASSUMED (A2) — Phase 74 completed but verification not yet read

**Research date:** 2026-05-24
**Valid until:** 60 days (skill files don't change independently; valid until next skill-editing phase)
