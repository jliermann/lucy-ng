---
phase: 75-skill-consolidation
verified: 2026-05-24T16:34:58Z
status: human_needed
score: 10/10
overrides_applied: 0
human_verification:
  - test: "Run a CASE session with ibuprofen (CASE1) using the updated skill team and confirm lsd-engineer writes DEFF F1/F2/FEXP (not DEFF NOT) and BOND/COSY equivalence (not SYME) in the first iteration's LSD file"
    expected: "iteration_01/compound.lsd contains DEFF F1 ring3, DEFF F2 ring4, FEXP NOT F1 AND NOT F2, and no DEFF NOT / SYME lines"
    why_human: "Skills are markdown files that an LLM reads at spawn time — static analysis confirms the instructions are correct, but only a live agent run proves the agent follows them"
  - test: "With pylsd_mode=true in the inventory, trigger a pylsd run and verify the DA issues G5 + G6 checks (inspect perm files for BOND/DEFF_F presence and check merged.smi vs solncounter)"
    expected: "DA posts [VALIDATION-PASSED] or [VALIDATION-BLOCKED] messages that include 'G5' and 'G6' pass/fail lines"
    why_human: "G5/G6 detection is post-pylsd-run behavior — cannot verify from static grep alone that the agent reads and applies the gate logic"
---

# Phase 75: Skill Consolidation Verification Report

**Phase Goal:** Consolidate CASE agent skills so the team writes NATIVE LSD commands (BOND/COSY + DEFF F/FEXP), follows ONE solver path, and the devils-advocate detects the v8.0 failure modes.

**Verified:** 2026-05-24T16:34:58Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Honest Scope Statement

Phase 75 is a documentation/skill consolidation phase. Its deliverables are markdown skill files that an LLM agent reads at spawn time. Verification of the files themselves (correct content, consistent vocabulary, no deprecated commands) is fully achievable by static analysis — and all 10 must-haves pass.

The TRUE proof that the consolidated skills cause the live CASE agent to solve via the intended native mechanism is the Phase-76 blind UAT. This report certifies: "skills are internally correct, consistent, and complete." Behavioral proof is deferred to Phase 76.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | lsd-engineer.md contains no instruction to write SYME (only "do NOT write SYME") | VERIFIED | `grep -n "^SYME\b"` with guidance-line filter returns empty; lines 76+77 contain "SYME causes LSD error 102 — NEVER write SYME" |
| 2 | lsd-engineer.md contains no DEFF NOT SMARTS pattern blocks (only "do NOT write DEFF NOT" guidance) | VERIFIED | Only match is line 164: "**NOT NATIVE:** `DEFF NOT C1CC1` causes LSD error 150. Do NOT write DEFF NOT." — this is a prohibition, not an instruction |
| 3 | lsd-engineer.md documents BOND/COSY as native equivalence encoding with ground-truth examples | VERIFIED | Lines 88-94: gem-dimethyl BOND example (lines 88-89), aromatic equiv-pair COSY examples (lines 90-91), `; equiv-pair` tagging requirement (line 94) |
| 4 | lsd-engineer.md documents DEFF F1 ring3 + DEFF F2 ring4 + FEXP as the ring exclusion block | VERIFIED | Lines 151-153: standard ring exclusion block verbatim; line 218: checklist item 8 requires it; line 475: initialization critical note |
| 5 | lsd-engineer.md step 11 has PRIMARY PATH (lucy lsd run) first, FALLBACK PATH (pylsd) as subordinate conditional | VERIFIED | Line 554: "**PRIMARY PATH (always run first)**" with unconditional `lucy lsd run`; line 561: "**FALLBACK PATH — use ONLY when ALL THREE conditions hold**" with explicit 3-condition gate |
| 6 | lsd-engineer.md has no manual `outlsd 5 < compound.sol > solutions.smi` instruction | VERIFIED | Only match is line 127: "No manual `outlsd 5 < compound.sol > solutions.smi` invocation is needed" — this is a prohibition/explanation, not an instruction |
| 7 | HMBC X Y 2 4 appears in the main HMBC correlations block (before pyLSD fallback section) | VERIFIED | Line 60: `HMBC 3 8 2 4   ; extended bond range 2-4: primary 4J mechanism (D-01)` — well before the fallback section at line 108 |
| 8 | pyLSD subsection heading demoted from ### to #### | VERIFIED | Line 108: `#### Fallback Path: Permutation Mode Commands (use ONLY when primary yields 0 solutions)` |
| 9 | devils-advocate G5/G6/G7/G8 gates detect the v8.0 failure modes with concrete detection commands and BLOCK/WARNING verdicts | VERIFIED | G5 (line 358): HMBC-only perm detection with bash loop, BLOCK verdict; G6 (line 384): empty-merge vs solncounter check with BLOCK verdict; G7 (line 420): hash-based post-validation edit check with CRITICAL verdict; G8 (line 444): reversion WARNING |
| 10 | No regression: pytest 1007 passed, 7 skipped, 1 xfailed | VERIFIED | Full test suite result: `1007 passed, 7 skipped, 1 xfailed` |

**Score:** 10/10 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `~/.claude/agents/lucy-lsd-engineer.md` | Native BOND/COSY, DEFF F1/F2/FEXP, PRIMARY/FALLBACK, HMBC X Y 2 4 in main block | VERIFIED | All 17 surgical edits confirmed by grep |
| `~/.claude/agents/lucy-devils-advocate.md` | G5-G8 gates, cosy_equiv_pairs, ring_exclusion_enabled | VERIFIED | 16 edits confirmed; G5/G6/G7/G8 headings at lines 358/384/420/444 |
| `~/.claude/commands/lucy-ng/case.md` | No manual outlsd pipe; native ring exclusion / COSY vocab in spawn prompts | VERIFIED | grep returns no `outlsd 5 < compound`; line 166 confirms native vocab |
| `~/.claude/commands/lucy-ng/references/progress-format.md` | ring_excl=enabled, COSY_equiv fields | VERIFIED | Lines 44/86/88 confirmed |
| `~/.claude/agents/lucy-solution-analyst.md` | Check 3 uses ring exclusion (DEFF F/FEXP) | VERIFIED | Line 105 confirmed |
| `~/.claude/agents/lucy-diagnostic.md` | No active SYME instructions; native BOND/COSY equiv-pair guidance | VERIFIED | Phase sign-off grep returns empty; native guidance at lines 254/257/793 |
| `src/lucy_ng/cli/fragment.py` | --filter-index default=3 (F3 reserved for fragment; F1/F2 for ring exclusion) | VERIFIED | Line 342: `default=3`; help text documents F1/F2 reservation |
| `tests/test_lsd_formatter.py` | 3 new filter-index tests (F3 default, F1 explicit, F5 arbitrary) | VERIFIED | `TestToLsdFilterIndex` class at line 332 with 3 tests, all passing |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| lsd-engineer.md §1 native equivalence | devils-advocate.md constraint diff | BOND/COSY fields the DA tracks | VERIFIED | DA Check 1/2/3 tables use `cosy_equiv_pairs` and `ring_exclusion_enabled` matching lsd-engineer schema |
| lsd-engineer.md F-number reservation | fragment.py --filter-index | F3 default convention | VERIFIED | lsd-engineer line 190 documents "DEFF F3 (F1/F2 reserved)"; fragment.py default=3 enforces it |
| DA [VALIDATION-PASSED] hash | lsd-engineer pre-run check | G7 hash field | VERIFIED | DA line 522: hash field in template; G7 at line 420 documents lsd-engineer self-check responsibility |
| G5/G6 v8.0 failure detection | pylsd_run/ directory structure | bash detection commands | VERIFIED | G5 bash loop checks BOND/COSY/DEFF_F=0 in perm files; G6 checks merged.smi vs per-perm solncounters |

---

## Deprecated File Scope Exclusion

`~/.claude/agents/lucy-case-agent.md` was explicitly excluded from Phase 75 scope. Verified:
- Line 14 (top banner): `> **DEPRECATED -- DO NOT USE**`
- Lines 15-20 document it is "NOT spawned by any active workflow" and is "Preserved as historical reference only"
- It still contains old DEFF NOT + outlsd-pipe examples — this is acceptable because it is unreachable from any active workflow path

This exclusion is intentional and correct. The stale content in the deprecated file cannot cause the v8.0 failure modes.

---

## DEFF NOT C1 Occurrences — Classification

Three files contain "DEFF NOT C1" strings:

| File | Line | Content | Classification |
|------|------|---------|---------------|
| `lucy-lsd-engineer.md` | 164 | "**NOT NATIVE:** `DEFF NOT C1CC1` causes LSD error 150. Do NOT write DEFF NOT." | PROHIBITION — explicitly forbids the command |
| `lucy-devils-advocate.md` | 97 | Legacy backward-compat guidance for compounds started before Phase 75 | LEGACY FALLBACK — DA accepts both native and legacy forms for old iterations |
| `lucy-devils-advocate.md` | 165 | Badlist completeness: accepts native OR legacy form | LEGACY FALLBACK — DA accepts both native and legacy forms for old iterations |

None of these are instructions to write DEFF NOT. All are either prohibitions or backward-compat acceptance rules. VERIFIED.

---

## Anti-Patterns Found

None. No TBD/FIXME/XXX markers found in any modified files. No stubs, no empty implementations. Python changes are fully implemented (click option with parameterized formatter calls). Test coverage is complete.

---

## Requirements Coverage

| Requirement | Plans | Description | Status |
|-------------|-------|-------------|--------|
| SKILL-01 | 75-01, 75-03, 75-05 | Active skill files correct against LSD-3.4.9 native commands — no SYME / DEFF NOT instructions | VERIFIED |
| SKILL-02 | 75-01 | Unambiguous single solver-path in lsd-engineer.md (PRIMARY normal-LSD, FALLBACK pylsd subordinate) | VERIFIED |
| SKILL-03 | 75-02 | Devils-advocate G5-G8 detect v8.0 failure modes with concrete checks and BLOCK/WARNING verdicts | VERIFIED |

---

## SKILL-02 Four-Rule Verification (D-02 Compliance)

| Rule | Check | Status |
|------|-------|--------|
| (1) Normal-LSD path documented as PRIMARY with full steps/examples | Line 554: PRIMARY PATH with unconditional `lucy lsd run` | VERIFIED |
| (2) pyLSD in subordinate "use ONLY when" section | Line 561: "FALLBACK PATH — use ONLY when ALL THREE conditions hold" | VERIFIED |
| (3) pyLSD heading demoted to #### | Line 108: `#### Fallback Path: Permutation Mode Commands` | VERIFIED |
| (4) Normal-LSD listed first | PRIMARY PATH block (line 554) precedes FALLBACK PATH block (line 561) | VERIFIED |

---

## SKILL-03 v8.0 Failure Mode Mapping

| Gate | v8.0 Failure Mode | Detection | Verdict |
|------|-------------------|-----------|---------|
| G5 | Silent constraint loss in permutation files (HMBC-only perms, BOND=0 COSY=0 DEFF_F=0) | Bash loop checking each perm dir | BLOCK |
| G6 | Empty merge despite per-permutation solutions (SolutionMerger collected 0) | Check merged.smi vs solncounter per perm | BLOCK |
| G7 | Post-validation file edit (lsd-engineer modifies LSD after DA approval) | MD5 hash in [VALIDATION-PASSED]; lsd-engineer re-checks before solver run | CRITICAL |
| G8 | Agent reversion (pylsd_mode=true but direct lsd run used without documentation) | Read CASE-PROGRESS.md [ITERATION-COMPLETE] messages | WARNING |

Writer/checker consistency: DA validates BOND/COSY equiv-pair lines and ring_exclusion_enabled — the exact encoding that lsd-engineer now writes. Verified across Check 1/2/3 tables and G5 detection bash (checks BOND/COSY/DEFF_F counts in perm files).

---

## Behavioral Spot-Checks

Step 7b: PARTIALLY APPLICABLE — skills are markdown files (not runnable entry points). Python components were spot-checked:

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `fragment to-lsd` default F3 | `python -m pytest tests/test_lsd_formatter.py::TestToLsdFilterIndex::test_to_lsd_default_filter_index_is_3` | 1 passed | PASS |
| `fragment to-lsd --filter-index 1` backward compat | `python -m pytest tests/test_lsd_formatter.py::TestToLsdFilterIndex::test_to_lsd_explicit_filter_index_1` | 1 passed | PASS |
| Full test suite (regression check) | `python -m pytest -q` | 1007 passed, 7 skipped, 1 xfailed | PASS |

---

## Human Verification Required

### 1. Live CASE Agent Writes Native LSD Commands

**Test:** Run a CASE session with CASE1 (sanitised ibuprofen) using the updated skill team. After iteration_01 completes, inspect `iteration_01/compound.lsd`.

**Expected:** File contains `DEFF F1 "ring3"`, `DEFF F2 "ring4"`, `FEXP "NOT F1 AND NOT F2"`, `BOND` gem-dimethyl lines, `COSY` equiv-pair lines. File must NOT contain `DEFF NOT C1...` or `SYME` lines.

**Why human:** Skill files are markdown — static analysis confirms the instructions are correctly written, but only a live agent run proves the spawned agent reads and follows them correctly (agent could hallucinate or misread the skill).

### 2. DA G5/G6 Gates Fire on pylsd Run

**Test:** Trigger a scenario with `pylsd_mode=true` in the inventory and inspect the DA's validation message in CASE-PROGRESS.md after `lucy pylsd run` completes.

**Expected:** [VALIDATION-PASSED] message includes G5 and G6 results. If permutation files exist, DA has run the bash loops. If any perm has BOND=0/COSY=0/DEFF_F=0, DA issues BLOCK.

**Why human:** G5/G6 are post-pylsd-run checks against a live `pylsd_run/` directory structure — grep on the static skill file confirms the detection logic is written, but only a live run with actual perm files proves the agent applies it correctly.

---

## Gaps Summary

No gaps. All 10 must-haves verified. The two human verification items are behavioral proof-of-execution checks that are normal for documentation/skill consolidation phases — they do not indicate missing implementation.

---

_Verified: 2026-05-24T16:34:58Z_
_Verifier: Claude (gsd-verifier)_
