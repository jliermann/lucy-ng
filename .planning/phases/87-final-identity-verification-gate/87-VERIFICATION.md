---
phase: 87-final-identity-verification-gate
verified: 2026-06-24T00:00:00Z
status: human_needed
score: 13/13 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 13/13
  gaps_closed:
    - "GAP-87-A: deterministic identity tool unreachable from a CASE data dir — closed by 87-03 (lucy identify installed subcommand + lucy_ng.identity package core) and 87-04 (both agents repointed)."
    - "CR-01: corrupt/non-DB --database file crashed lucy identify with a traceback (violated D-06 always-exits-0) — fixed in commit 10ce6e7 (graceful sqlite3.Error degrade to db_unavailable+novel)."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "In a FRESH Claude Code session (required to reload the edited CASE agents), run a blind CASE5 (sanitised) re-run — the IDENT acceptance test (Phase-89 UAT-02)."
    expected: "solution-analyst calls `lucy identify --format json` on the top SMILES at runtime (now reachable from the NMR data dir), renders the tool-derived identity as PRIMARY (never a recalled name), marks non-confirmed trivial names `(tentative, unverified)`; devils-advocate runs the post-solution G-IDENT advisory gate on final_results.md and flags any name<->structure mismatch independently."
    why_human: "87-04 edits are CASE-agent MARKDOWN prompts; a fresh Claude Code session is required to reload them and live agent runtime behavior is not executable-testable this session. The gap-closure made the tool ACTUALLY REACHABLE (verified: `cd /tmp && lucy identify` exits 0 with the full JSON contract), so the next blind UAT can finally exercise IDENT-01/02 end-to-end — previously they FAILED at runtime because the tool lived only in the repo working tree."
---

# Phase 87: Final Identity-Verification Gate Verification Report

**Phase Goal:** The reported compound name is derived from the structure by a tool and independently checked, so a recalled-from-memory wrong trivial name can no longer be asserted as fact.
**Verified:** 2026-06-24
**Status:** human_needed
**Re-verification:** Yes — after GAP-87-A closure (plans 87-03/87-04) and CR-01 fix

## Goal Achievement

GAP-87-A is closed and executable-confirmed. The blind CASE5 UAT (87-HUMAN-UAT.md, 2026-06-24) found the deterministic identity tool was unreachable at CASE runtime — it lived only in `scripts/verify_case_solution.py` in the repo working tree, while a CASE run executes from an NMR data dir outside the repo. IDENT-01/02 therefore FAILED at runtime even though all source assertions passed.

Gap-closure 87-03 moved the identity core verbatim into the installed package (`src/lucy_ng/identity.py`, D-05 single implementation) and exposed it as the installed `lucy identify --format json` subcommand. 87-04 repointed both CASE agents from the repo-relative script to `lucy identify`. A deep code review found and FIXED a blocker (CR-01: corrupt/non-DB `--database` crashed the command with a traceback, violating the D-06 always-exits-0 contract); commit `10ce6e7` degrades gracefully.

I independently confirmed the closure by EXECUTING `lucy identify` from `/tmp` (outside the repo): exit 0, full JSON contract emitted. D-05 single-implementation, the WR-01/02/03 fixes, the CR-01 graceful corrupt-DB handling, and the agent repoint all verified. 28/28 tests pass.

Status remains `human_needed` (not `passed`) for exactly one reason: the live agent runtime behavior (IDENT-01/02 firing `lucy identify` inside a real CASE run, IDENT-03 tentative rendering, the G-IDENT post-solution gate) requires a fresh-session agent reload + a blind CASE5 re-run. That is Phase-89 UAT-02 — a documented human-verification acceptance item, not a failed must-have. The point of this gap-closure is precisely that the tool is now reachable so the next blind UAT can exercise it.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GAP-87-A closed: `lucy identify --smiles 'CCO' --format json` from OUTSIDE the repo (/tmp) exits 0 and emits the JSON contract (mode/reported_name/derived{inchi_key,...}/name_match/verdict/warning) | ✓ VERIFIED | Executed `cd /tmp && lucy identify --smiles 'CCO' --format json` → EXIT=0; emitted `{mode:"identity", reported_name:null, derived:{matched:true, name:"ethanol", source:"nmrshiftdb", inchi_key:"LFQSCWFLJHTTHZ-...", canonical_smiles:"CCO", confidence:"confirmed"}, name_match:null, verdict:"confirmed", warning:null}`; `lucy --help` lists `identify` |
| 2 | D-05: exactly one implementation — `scripts/verify_case_solution.py` imports from `lucy_ng.identity`, no duplicate identity logic | ✓ VERIFIED | `grep -c "^def derive_identity" scripts/...` = 0; `from lucy_ng.identity import (...)` at line 31; zero local defs of `_name_match`/`check_identity_result`/`derive_identity`/`_normalize_name`/`_synonym_token_sets`/`_resolve_db_path` in script; `_COCONUT_ACCESSION_RE = re.compile` exists ONLY in `identity.py:33` |
| 3 | WR-01/02 fix survives: COCONUT dot-suffix regex `^CNP\d+(?:\.\d+)?$` recognises `CNP0220816.1` and does not leak the accession into the name token set | ✓ VERIFIED | `identity.py:33` regex confirmed; behavioral: `_COCONUT_ACCESSION_RE.match('CNP0220816.1')` = True, `_normalize_name('CNP0220816.1')` = `set()`; locked by `test_dotsuffixed_coconut_accession_is_recognised` + `test_dotsuffixed_coconut_row_is_structure_only` |
| 4 | WR-03 fix survives: matched hit with empty/None name → `confirmed-structure`, mismatch warning says "structure in DB but no trivial name stored" (not the old false "not in DB") | ✓ VERIFIED | `identity.py:170-173` empty-name branch; behavioral: empty-name hit + reported "ethanol" → verdict `tentative`, warning `...does not match tool-derived identity 'none (structure in DB but no trivial name stored)'...`; locked by `test_empty_name_match_warns_in_db_not_absent` |
| 5 | CR-01 fix survives: corrupt/non-DB `--database` file degrades gracefully (exit 0, db_unavailable+novel) instead of crashing with a traceback | ✓ VERIFIED | `identity.py:136-148` `except sqlite3.Error` → `db_unavailable:true`; executed from /tmp with a non-DB file → EXIT=0, `{verdict:"novel", derived:{db_unavailable:true, error:"db read failed: file is not a database"}}`; locked by `test_corrupt_db_degrades_gracefully` |
| 6 | Test suite passes: `pytest tests/test_verify_case_identity.py tests/test_cli_identify.py tests/test_verify_case_solution.py` | ✓ VERIFIED | 28 passed, 26 warnings in 15.90s (DB present locally) |
| 7 | Analyst agent (87-04) repointed to `lucy identify`; no live `scripts/verify_case_solution.py check-identity` call; keeps `(tentative, unverified)`; reload note present | ✓ VERIFIED | `grep -c "lucy identify"` = 4; zero `scripts/verify_case_solution.py check-identity` matches; `(tentative, unverified)` ×7; reload note line 17 "a FRESH Claude Code session is required" |
| 8 | Devils-advocate agent (87-04) repointed; keeps `G-IDENT` + `post-solution`; independence (does NOT call lucy identify); no live script call; reload note | ✓ VERIFIED | `grep -c "lucy identify"` = 2; `G-IDENT` ×8; `post-solution` ×7; line 569 "do NOT call the deterministic `lucy identify` tool — that is the analyst's binding layer"; zero `scripts/verify_case_solution.py check-identity` matches; reload note line 17 |
| 9 | Move integrity (D-05): COCONUT regex, empty-name branch, filler tokens, two-path lookup, tolerant token-set match all moved verbatim into the package core | ✓ VERIFIED | REVIEW gap-closure section confirms byte-level diff faithful (only type annotations + pure check_identity_result refactor); `identity.py` carries `_COCONUT_ACCESSION_RE` (33), empty-name branch (170-173), `_NAME_FILLER_TOKENS` (36), `_name_match` (218-235), two-path SQL (122-133) |
| 10 | D-06 preserved: identity never hard-fails — always exits 0 across all paths (confirmed/tentative/novel/db_unavailable) | ✓ VERIFIED | `cli/identify.py` always exits 0 (no sys.exit on mismatch); `check_identity_result` is pure (no print/exit); confirmed exit 0 on CCO-confirmed AND corrupt-DB-novel runs from /tmp |
| 11 | `lucy identify` registered in CLI group and importable without import cycle | ✓ VERIFIED | `cli/identify.py:20` imports `check_identity_result`; `lucy --help` lists `identify`; REVIEW confirms `python -c "import lucy_ng.identity; import lucy_ng.cli.identify"` no cycle (DatabaseFinder imported lazily) |
| 12 | All gap-closure + CR-01 commits exist | ✓ VERIFIED | `git log` confirms 2549eb5, 648f62c, d04aaa7 (87-03), 602f54c, 8cb6ef5 (87-04), 10ce6e7 (CR-01) |
| 13 | SQL still parameterized after the move (no injection surface introduced) | ✓ VERIFIED | `identity.py:122-133` `?` placeholders + RO `file:` URI connection; no string interpolation |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/identity.py` | installed shared identity core (derive_identity, check_identity_result, name matching, two-path lookup) + CR-01 graceful DB handling | ✓ VERIFIED | All functions present; CR-01 `except sqlite3.Error` at 136-148; WR-01/02/03 fixes at 33/170-173; pure (no print/sys.exit) |
| `src/lucy_ng/cli/identify.py` | `lucy identify` Click command, --format json, always exits 0, no own logic | ✓ VERIFIED | Imports `check_identity_result` only; `--smiles/--reported-name/--database/--format`; registered in main.py |
| `scripts/verify_case_solution.py` | thin adapter importing the core; legacy positional mode intact | ✓ VERIFIED | `from lucy_ng.identity import (...)`; zero duplicate logic; legacy `<merged_smi> <formula>` mode untouched (test_verify_case_solution.py green) |
| `tests/test_cli_identify.py` | CliRunner schema/invalid-SMILES/text tests | ✓ VERIFIED | 8 tests incl. `test_identify_invalid_smiles_exits_zero`; combined suite 28 passed |
| `tests/test_verify_case_identity.py` | repointed to lucy_ng.identity + WR/CR-01 regression tests | ✓ VERIFIED | `test_dotsuffixed_*`, `test_empty_name_match_warns_in_db_not_absent`, `test_corrupt_db_degrades_gracefully` present and passing |
| `.claude/agents/lucy-solution-analyst.md` | repointed to `lucy identify`, tentative rendering, reload note | ✓ VERIFIED | 4× `lucy identify`, 7× `(tentative, unverified)`, reload note, zero live script call |
| `.claude/agents/lucy-devils-advocate.md` | G-IDENT post-solution gate naming `lucy identify`, independence preserved | ✓ VERIFIED | 8× G-IDENT, 7× post-solution, independence "do NOT call... lucy identify", reload note, zero live script call |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `lucy identify` CLI | `lucy_ng.identity.check_identity_result` | import + call | ✓ WIRED | `cli/identify.py:20,66` |
| `scripts/verify_case_solution.py` | `lucy_ng.identity` | import (no dup logic) | ✓ WIRED | line 31 import, adapter `_check_identity` wraps `check_identity_result` |
| `derive_identity` | dereplication DB | DatabaseFinder + parameterized RO sqlite3 | ✓ WIRED | `_resolve_db_path` + two-path `WHERE inchi_key=? / WHERE smiles=?`; graceful on corrupt DB |
| analyst workflow | `lucy identify --format json` | runtime CLI call from CASE data dir | ✓ WIRED (source) | Section 6.0 fenced bash + step 6a; runtime firing is the human-UAT item |
| devils-advocate G-IDENT | final_results.md | post-solution independent review (does NOT call tool) | ✓ WIRED (source) | step 13 + G-IDENT gate body; runtime firing is the human-UAT item |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| GAP-87-A: tool reachable from outside repo | `cd /tmp && lucy identify --smiles 'CCO' --format json` | exit 0, full JSON contract, derived ethanol/nmrshiftdb/InChIKey | ✓ PASS |
| CR-01: corrupt DB graceful | `cd /tmp && lucy identify --smiles 'CCO' --database /tmp/notadb.db --format json` | exit 0, verdict novel, db_unavailable:true, no traceback | ✓ PASS |
| `lucy --help` lists subcommand | `cd /tmp && lucy --help \| grep identify` | "identify  Derive + verify compound identity..." | ✓ PASS |
| WR-01/02 dot-suffix regex | `python -c "...match('CNP0220816.1'); _normalize_name('CNP0220816.1')"` | match True, normalize set() | ✓ PASS |
| WR-03 empty-name verdict | `check_identity_result` w/ empty-name hit | verdict tentative, warning "structure in DB but no trivial name stored" | ✓ PASS |
| Test suite | `pytest test_verify_case_identity.py test_cli_identify.py test_verify_case_solution.py -q` | 28 passed | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| IDENT-01 | 87-01/02/03/04 | Analyst derives identity via tool, never asserts recalled name | ✓ SATISFIED (source + reachable) | `lucy identify` deterministic (RDKit InChIKey/canonical SMILES); analyst step 6a repointed; tool now reachable at runtime (GAP-87-A closed). Runtime firing = UAT-02 human item |
| IDENT-02 | 87-01/02/03/04 | Independent final gate checks name↔structure; mismatch flags report | ✓ SATISFIED (source + reachable) | `lucy identify` verdict tentative+warning (binding); G-IDENT post-solution advisory (independent). Runtime firing = UAT-02 human item |
| IDENT-03 | 87-01/02/03/04 | Non-confirmed identity marked tentative with confidence | ✓ SATISFIED | verdict-keyed rendering + `(tentative, unverified)` in analyst; the blind CASE5 UAT (87-HUMAN-UAT.md) already observed IDENT-03 PASS at runtime |

No orphaned requirements: REQUIREMENTS.md maps IDENT-01/02/03 to Phase 87; all three appear in plan `requirements` frontmatter. UAT-02 (blind CASE5 acceptance) is a separate UAT requirement, surfaced here as the human-verification item.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | No TBD/FIXME/XXX/unreferenced debt markers in identity.py, cli/identify.py, verify_case_solution.py, or either agent file | ℹ️ Info | Clean |

REVIEW IN-01 (re-parse), IN-02 (lazy `import os` in fallback), IN-03 (resolved) are cosmetic/pre-existing — not gaps. GAP-87-B (lsd-engineer completion-signal stall) is out of phase-87 scope and captured as a separate todo (`2026-06-24-case-completion-signal-stall`) — not an IDENT gap.

### Human Verification Required

#### 1. Blind CASE5 re-run with reloaded agents (Phase-89 UAT-02)

**Test:** In a FRESH Claude Code session (required to reload the edited CASE agents), run a blind CASE5 (sanitised) re-run — the IDENT acceptance test.
**Expected:** The solution-analyst calls `lucy identify --format json` on the top SMILES at runtime (now reachable from the NMR data dir), renders the tool-derived identity as the PRIMARY identity (never a recalled name), and marks non-confirmed trivial names `(tentative, unverified)`; the devils-advocate runs the post-solution G-IDENT advisory gate on `final_results.md` and independently flags any name↔structure mismatch.
**Why human:** 87-04 edits are CASE-agent markdown prompts; a fresh Claude Code session is required to reload them, and live agent runtime behavior is not executable-testable this session. Crucially, the gap-closure made the tool ACTUALLY REACHABLE (independently confirmed: `cd /tmp && lucy identify` exits 0 with the full JSON contract; `lucy --help` lists it) — so the prior runtime FAIL ("verify_case_solution.py not present in repo") cannot recur, and the next blind UAT can finally exercise IDENT-01/02 end to end.

### Gaps Summary

No gaps. The single blocking item from the prior cycle — GAP-87-A (deterministic identity tool unreachable from a CASE data dir) — is closed: the identity core was moved verbatim into the installed `lucy_ng.identity` package (D-05, exactly one implementation, no duplicate logic in the script) and exposed as the installed `lucy identify --format json` subcommand, which I confirmed runs from `/tmp` outside the repo (exit 0, full JSON contract). Both CASE agents are repointed with the binding/advisory split, IDENT-03 rendering, and reload notes intact. The code-review blocker CR-01 (corrupt-DB traceback) is fixed (commit 10ce6e7) and confirmed graceful from outside the repo. The WR-01/02/03 fixes survive the move (verified behaviorally). 28/28 tests pass.

The only outstanding item is the live agent runtime behavior, which by design cannot be verified without a fresh-session reload + blind CASE5 re-run — this is the documented Phase-89 UAT-02 acceptance, surfaced as a human-verification item, not a failed must-have. This gap-closure's whole purpose was to make the tool reachable so that UAT can now actually exercise it.

---

_Verified: 2026-06-24_
_Verifier: Claude (gsd-verifier)_
_Re-verification: after GAP-87-A closure (87-03/87-04) + CR-01 fix_
