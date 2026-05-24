---
phase: 75-skill-consolidation
plan: "02"
subsystem: agent-skills
tags: [devils-advocate, native-lsd, ring-exclusion, cosy-equiv, g5-g8, v8.0-failure-modes, skill-consolidation]

# Dependency graph
requires:
  - phase: 75-01
    provides: "lsd-engineer now writes BOND/COSY native SYME replacement and DEFF F1/F2+FEXP native ring exclusion"
provides:
  - "lucy-devils-advocate.md validates COSY equiv-pair lines (not SYME) and ring_exclusion_enabled (not deff_not_patterns)"
  - "lucy-devils-advocate.md Check 1/2/3 tables use ring_exclusion_enabled and cosy_equiv_pairs inventory fields"
  - "lucy-devils-advocate.md G5-G8 gates detect v8.0 failure modes (HMBC-only perms, empty merge, hash drift, reversion)"
  - "G7 hash protocol added to [VALIDATION-PASSED] template"
affects:
  - "75-03 (case.md references must match cosy_equiv_pairs field name, COSY-equiv in progress-format.md)"
  - "CASE team agent — DA reads this skill at spawn time, now aligned with lsd-engineer output"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "COSY equivalence lines tagged ; equiv-pair are the native SYME replacement — DA now validates these"
    - "ring_exclusion_enabled boolean in inventory replaces deff_not_patterns array for DA checks"
    - "G5/G6/G7/G8 additive gates — G1-G4 numbering unchanged"
    - "G7: DA computes md5 hash in [VALIDATION-PASSED], lsd-engineer re-checks before running solver"

key-files:
  created: []
  modified:
    - "~/.claude/agents/lucy-devils-advocate.md - 16 surgical edits: Task-1 Edits A-I (native sync), Task-2 Edits I-P (inventory fields + G5-G8)"

key-decisions:
  - "syme_pairs removed from all DA Check 1/2/3 tables; replaced with cosy_equiv_pairs (consistent with 75-01 lsd-engineer schema)"
  - "deff_not_patterns removed from DA Check 1/2/3 tables; replaced with ring_exclusion_enabled boolean with legacy fallback"
  - "G8 is WARNING not CRITICAL — deliberate fallback to direct lsd run after 0 pylsd solutions is valid; only undocumented reversion is flagged"
  - "G7 is lsd-engineer self-check (DA outputs hash, engineer verifies); DA is read-only and does not verify at run time"

requirements-completed: [SKILL-01, SKILL-03]

# Metrics
duration: ~8 min
completed: 2026-05-24
---

# Phase 75 Plan 02: Devils-Advocate Native Gates Summary

**lucy-devils-advocate.md synchronized to native LSD commands and extended with G5-G8 failure-mode gates matching v8.0 UAT postmortem findings**

## Performance

- **Duration:** ~8 min
- **Started:** ~2026-05-24T16:06:00Z
- **Completed:** 2026-05-24T16:14:45Z
- **Tasks:** 2 (Task 1: Edits A-I native sync; Task 2: Edits I-P inventory fields + G5-G8)
- **Files modified:** 1 (~/.claude/agents/lucy-devils-advocate.md — outside git repo, not committed)

## Accomplishments

- Replaced SYME row in Count Comparison table with "COSY equivalence lines (`; equiv-pair` tagged)" row
- Replaced DEFF NOT row in Count Comparison table with "Ring exclusion (DEFF F1 + DEFF F2 + FEXP)" row
- Rewrote Bug 1 section: now checks for DEFF F1/F2/FEXP (native) with legacy DEFF NOT fallback for pre-Phase-74 compounds
- Updated Bug 2 check: now validates COSY equiv-pair constraints or parenthesized HMBC (not SYME)
- Updated Badlist Completeness: accepts both native (DEFF F) and legacy (DEFF NOT) forms
- Updated Content Comparison: checks DEFF F1/F2/FEXP lines (not DEFF NOT)
- Updated Expected (Normal) Changes: COSY aromatic-pair constraints instead of SYME
- Updated Check 1 table: `ring_exclusion_enabled` and `cosy_equiv_pairs` replace `deff_not_patterns` and `syme_pairs`
- Updated Check 2 table: same field replacements for regression check
- Updated Check 3: `cosy_equiv_pairs` replaces `syme_pairs` in content preservation check
- Updated Bug 1 (D section): `ring_exclusion_enabled` field as source of truth with legacy backward compat
- Updated [VALIDATION-PASSED] template: "Ring exclusion" and "COSY-equiv" fields replace "DEFF NOT" and "SYME"
- Updated [VALIDATION-BLOCKED] template: "Ring exclusion" field replaces "DEFF NOT"
- Fixed line 362 legacy fallback: SYME reference replaced with "COSY equiv-pair constraints / parenthesized HMBC"
- Added Check 5 section with G5/G6/G7/G8 gates (G1-G4 numbering unchanged)
- Added G7 hash line to [VALIDATION-PASSED] template

## Task Commits

No git commits for this plan — ~/.claude/agents/lucy-devils-advocate.md is outside the git repo (user-global skill file). Only the SUMMARY.md is committed to the repo.

## Files Created/Modified

- `/Users/steinbeck/.claude/agents/lucy-devils-advocate.md` - 16 surgical edits applied; outside git repo

## Edits Applied

| Edit | Description | Status |
|------|-------------|--------|
| A | Count Comparison: DEFF NOT row → Ring exclusion row | Clean |
| B | Count Comparison: SYME row → COSY equivalence row | Clean |
| C | Content Comparison: DEFF NOT exact-match → DEFF F1/F2/FEXP exact-match | Clean |
| D | Expected Changes: SYME → COSY aromatic-pair constraints | Clean |
| E | Bug 1: Full section rewrite — DEFF NOT → DEFF F/FEXP with legacy fallback | Clean |
| F | Bug 2: SYME mention → COSY equivalence constraints | Clean |
| G | Bug 2 check: SYME → COSY equiv-pair | Clean |
| H | Badlist Completeness: DEFF NOT only → native OR legacy form accepted | Clean |
| I (Task 1) | Line 362 legacy fallback: SYME → COSY equiv-pair / grouped HMBC | Clean |
| I (Task 2) | Check 1 table: deff_not_patterns + syme_pairs → ring_exclusion_enabled + cosy_equiv_pairs | Clean |
| J | Check 2 table: same replacements for regression check | Clean |
| K | Check 3: syme_pairs removed, cosy_equiv_pairs added, ring_exclusion verbatim note added | Clean |
| L | Bug 1 enhanced inventory check: deff_not_patterns → ring_exclusion_enabled + legacy fallback | Clean |
| M | [VALIDATION-PASSED] template: DEFF NOT + SYME → Ring exclusion + COSY-equiv | Clean |
| N | [VALIDATION-BLOCKED] template: DEFF NOT → Ring exclusion | Clean |
| O | Add G5-G8 gates after G4 closing line | Clean |
| P | Add G7 hash line to [VALIDATION-PASSED] template | Clean |

All 16+ edits applied on first attempt with exact old_string matches.

## Decisions Made

- G8 is WARNING severity (not CRITICAL) — plan specifies this explicitly; deliberate pylsd fallback after 0 solutions is valid, only undocumented reversion warrants attention
- G7 is a lsd-engineer self-check, not a DA-run check — DA only outputs the hash in [VALIDATION-PASSED]; this keeps DA read-only (no Write tool needed)
- Legacy fallback in Bug 1 and Badlist uses DEFF NOT grep as backward compat for compounds started before Phase 75 (both native and legacy forms accepted)

## Deviations from Plan

None — plan executed exactly as written. All old_string matches were exact.

## Verification Results

| Check | Result |
|-------|--------|
| No bare SYME row (`grep "^| SYME"`) | PASS — empty |
| COSY equivalence row present | PASS — 3 lines |
| Ring exclusion count >= 5 | PASS — 7 occurrences |
| G5/G6/G7/G8 gate headings (`grep -cE "^\*\*G[5678]:"`) | PASS — 4 |
| G5 detection command (HMBC-only check) | PASS — lines 362, 373, 378, 380 |
| G6 solncounter check | PASS — lines 384, 393-414 |
| equiv-pair in Check 1 table | PASS — line 272 |
| ring_exclusion_enabled occurrences >= 3 | PASS — 4 occurrences |
| cosy_equiv_pairs occurrences >= 3 | PASS — 3 occurrences |
| No bare syme_pairs references | PASS — empty |
| [VALIDATION-PASSED] Ring exclusion + COSY-equiv | PASS — lines 511, 512 |
| [VALIDATION-BLOCKED] Ring exclusion | PASS — line 538 |
| File hash G7 line in [VALIDATION-PASSED] | PASS — line 513 |
| DEFF NOT C1CC1 (only legacy fallback notes, not mandatory check) | PASS — 2 lines, both legacy fallback context |

## Known Stubs

None.

## Threat Flags

None — pure markdown edits to a skill file outside the git repo. No new network endpoints, auth paths, or schema changes.

---

## Self-Check: PASSED

- `~/.claude/agents/lucy-devils-advocate.md` exists and was modified (16 edits)
- All grep checks confirm expected content
- No bare SYME or syme_pairs references remain
- G5/G6/G7/G8 all present with correct headings

*Phase: 75-skill-consolidation*
*Completed: 2026-05-24*
