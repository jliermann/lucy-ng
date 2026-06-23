---
phase: 87-final-identity-verification-gate
verified: 2026-06-23T00:00:00Z
status: human_needed
score: 13/13 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
human_verification:
  - test: "Reload edited CASE agents in a fresh Claude Code session and run a blind CASE re-run (CASE5 sanitised = IDENT acceptance)."
    expected: "solution-analyst calls `check-identity` on the top SMILES, renders the derived identity (never a recalled name), and marks non-confirmed trivial names '(tentative, unverified)'; devils-advocate runs the G-IDENT post-solution advisory gate and flags any name<->structure mismatch."
    why_human: "87-02 edits are CASE-agent MARKDOWN prompts. A fresh Claude Code session is required to reload edited agents; live agent runtime behavior is not executable-testable this session. Source assertions (grep) all pass; functional validation is the Phase-89 blind UAT."
---

# Phase 87: Final Identity-Verification Gate Verification Report

**Phase Goal:** The reported compound name is derived from the structure by a tool and independently checked, so a recalled-from-memory wrong trivial name can no longer be asserted as fact.
**Verified:** 2026-06-23
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

The deterministic gate is fully implemented, tested (22 passed), and behaviorally confirmed against the CASE4/CASE5 hallucination patterns via live CLI. The code-review warnings (WR-01/02/03) were genuinely fixed in commit `2867dc4` (regex widened to `^CNP\d+(?:\.\d+)?$`, empty-name handling, +3 regression tests). The consumer-side agent prompts (87-02) carry every required workflow step, rendering rule, and the G-IDENT gate. Status is `human_needed` (not `passed`) solely because live agent runtime behavior requires a fresh-session reload and a blind CASE re-run — an explicitly-documented Phase-89 UAT item, not a failed must-have.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | D-01: derive_identity returns deterministic InChIKey + canonical SMILES, never a recalled name | ✓ VERIFIED | `scripts/verify_case_solution.py:132` `def derive_identity`; `Chem.MolToSmiles`/`Chem.MolToInchiKey` (lines 161-162); `test_inchikey_and_canonical_smiles_derived` PASS |
| 2 | D-02: NMRShiftDB structure found via InChIKey path (indigo) | ✓ VERIFIED | Path 1 `WHERE inchi_key = ? AND inchi_key != ''` (line 180); live CLI returns `source: nmrshiftdb`, InChIKey `COHYTHOBJLSHDF-...`; `test_indigo_found_via_inchikey` PASS |
| 3 | D-02: COCONUT structure found via canonical-SMILES fallback | ✓ VERIFIED | Path 2 `WHERE smiles = ? AND smiles != ''` (line 187); `test_coconut_found_via_smiles_fallback` + `test_dotsuffixed_coconut_row_is_structure_only` PASS |
| 4 | D-03: Structure absent from DB returns 'novel', not a guessed name | ✓ VERIFIED | chamazulene CLI → `matched:false, confidence:novel`, only InChIKey+SMILES; `test_chamazulene_no_hit`, `test_ibuprofen_no_hit` PASS |
| 5 | D-06: reported-name disagreement → verdict 'tentative' + warning, no hard-fail | ✓ VERIFIED | CLI isoindigo→tentative+warning, exit 0; `sys.exit(0)` unconditional in `_check_identity` (line 327); `test_indigo_mislabel_mismatch` PASS |
| 6 | D-05: single shared deterministic path in verify_case_solution.py; CASE4/CASE5 caught | ✓ VERIFIED | One module, no new lucy CLI subcommand; all 4 CASE4/CASE5 CLI scenarios produce exact expected verdicts |
| 7 | Existing aromatic-ring + formula default mode unchanged | ✓ VERIFIED | `test_verify_case_solution.py` 8/8 PASS; legacy positional dispatch intact (line 339 gates only on literal `check-identity`) |
| 8 | D-01 (87-02): analyst derives identity by calling check-identity, not from memory | ✓ VERIFIED | `lucy-solution-analyst.md:302` step 6a MANDATORY, runs check-identity before report; explicit "NEVER from recalled/parametric knowledge" |
| 9 | D-07: no-hit/COCONUT-accession → InChIKey+SMILES primary, name '(tentative, unverified)' | ✓ VERIFIED | Section 6.1 verdict-keyed rule; `(tentative, unverified)` ×7, `confirmed-structure` ×5, `novel` ×9 |
| 10 | D-07: NMRShiftDB confirmed name may be stated plainly | ✓ VERIFIED | Verdict-keyed rule: `confirmed` branch states DB name plainly |
| 11 | D-04: devils-advocate runs post-solution G-IDENT gate after final_results.md, independent of the script | ✓ VERIFIED | `lucy-devils-advocate.md:416` G-IDENT gate + lifecycle note (POST-SOLUTION) + step 13; explicitly does NOT call check-identity (line 569) |
| 12 | D-03 (87-02): no-hit reported as novel, not under a recalled trivial name | ✓ VERIFIED | Analyst novel-verdict rendering rule; no surviving instruction to name from recalled knowledge as fact |
| 13 | Both edited agent files note fresh-session reload required | ✓ VERIFIED | Both files line 17 "FRESH Claude Code session is required to reload" |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/verify_case_solution.py` | derive_identity + check-identity + identity JSON | ✓ VERIFIED | `def derive_identity` (132), `_name_match` (261), `_normalize_name` (222), `check-identity` dispatch (339); contains `def derive_identity` |
| `tests/test_verify_case_identity.py` | unit + regression tests, CASE4/CASE5 fixtures | ✓ VERIFIED | 14 tests; contains `FVZVDQVUOAAMCG` + `COHYTHOBJLSHDF`; 22 passed combined |
| `.claude/agents/lucy-solution-analyst.md` | derivation step + tentative rendering | ✓ VERIFIED | Contains `(tentative, unverified)`, `check-identity`, `confirmed-structure`, `novel`, reload note |
| `.claude/agents/lucy-devils-advocate.md` | G-IDENT post-solution gate | ✓ VERIFIED | Contains `G-IDENT`, `final_results.md`, `post-solution`, `indigo`/`isoindigo`, reload note |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| derive_identity | lucy-ng-derep.db compounds | DatabaseFinder + parameterized sqlite3 | ✓ WIRED | `find_derep_database()` (line 110) + inline LUCY_DATABASE fallback; `WHERE inchi_key = ?` / `WHERE smiles = ?` |
| derive_identity | RDKit | MolToInchiKey + MolToSmiles | ✓ WIRED | Lines 161-162, default flags (byte-equality requirement) |
| analyst workflow | check-identity | subprocess on top SMILES before report header | ✓ WIRED | Step 6a (line 302) ordered before report write |
| devils-advocate G-IDENT | final_results.md | post-solution review | ✓ WIRED | Step 13 + gate body inspects final_results.md |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Test suite | `pytest tests/test_verify_case_identity.py tests/test_verify_case_solution.py -q` | 22 passed | ✓ PASS |
| CASE5 mislabel (indigo→isoindigo) | `check-identity --smiles <indigo> --reported-name isoindigo` | name_match:false, verdict:tentative, warning present, exit 0 | ✓ PASS |
| CASE5 correct (tolerant match) | `check-identity --smiles <indigo> --reported-name Indigo` | name_match:true (vs ';'-delimited DB name), verdict:confirmed, exit 0 | ✓ PASS |
| CASE4 asserted name no-hit | `check-identity --smiles <chamazulene> --reported-name chamazulene` | matched:false, verdict:tentative, warning present, exit 0 | ✓ PASS |
| CASE4 no asserted name | `check-identity --smiles <chamazulene>` | matched:false, verdict:novel, warning:null, exit 0 | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| IDENT-01 | 87-01, 87-02 | Analyst derives identity from SMILES via tool, never asserts recalled name | ✓ SATISFIED | derive_identity (deterministic); analyst step 6a calls check-identity |
| IDENT-02 | 87-01, 87-02 | Independent final gate checks name↔structure; mismatch flags report | ✓ SATISFIED | check-identity verdict 'tentative'+warning (binding); G-IDENT advisory (independent) |
| IDENT-03 | 87-01, 87-02 | Non-confirmed identity marked tentative with confidence | ✓ SATISFIED | verdict-keyed rendering; `(tentative, unverified)` + confidence note |

No orphaned requirements: REQUIREMENTS.md maps IDENT-01/02/03 to Phase 87; all three appear in both plans' `requirements` frontmatter.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | No TBD/FIXME/XXX/stub markers in any of the 4 modified files | ℹ️ Info | Clean |

Code-review IN-01/02/03 (info-only: redundant re-parse, lazy `import os`, test wrapper shim) are pre-existing/cosmetic and out of scope — not gaps.

### Human Verification Required

#### 1. Blind CASE re-run with reloaded agents (Phase-89 UAT)

**Test:** Reload the edited CASE agents in a fresh Claude Code session and run a blind CASE re-run (CASE5 sanitised = the IDENT acceptance test).
**Expected:** The solution-analyst calls `check-identity` on the top SMILES, renders the tool-derived identity (never a recalled name), and marks non-confirmed trivial names `(tentative, unverified)`; the devils-advocate runs the G-IDENT post-solution advisory gate and flags any name↔structure mismatch.
**Why human:** 87-02 edits are CASE-agent markdown prompts. A fresh Claude Code session is required to reload edited agents (CLAUDE.md convention); live agent runtime behavior is not executable-testable this session. All source assertions (grep) pass and the deterministic tool the agents consume is fully verified — only the agents' live invocation behavior remains for blind UAT.

### Gaps Summary

No gaps. The deterministic binding gate (87-01) is implemented, fully tested (22/22 passing, DB present), behaviorally confirmed against both CASE4 (no-hit asserted name → tentative; no name → novel) and CASE5 (mislabel → tentative; correct name → tolerant confirmed) — satisfying Success Criterion 4. The code-review warnings WR-01/02/03 are genuinely fixed in commit `2867dc4` (regex `^CNP\d+(?:\.\d+)?$` confirmed at line 36; empty-name handling at line 214; 3 added regression tests present and passing). SQL is parameterized (T-87-01 mitigated, no interpolation). The consumer-side agent prompts (87-02) carry every required workflow step, verdict-keyed rendering rule, G-IDENT post-solution gate with lifecycle note and independence rationale, and the fresh-session reload note.

The only outstanding item is the live agent behavior, which by design cannot be verified without a fresh-session reload + blind CASE re-run — this is the documented Phase-89 UAT acceptance (UAT-02), surfaced here as a human verification item, not a failed must-have.

---

_Verified: 2026-06-23_
_Verifier: Claude (gsd-verifier)_
