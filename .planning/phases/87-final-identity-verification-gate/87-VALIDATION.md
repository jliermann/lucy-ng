---
phase: 87
slug: final-identity-verification-gate
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-23
---

# Phase 87 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/test_verify_case_identity.py -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~quick subset <30s; full suite per existing baseline |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_verify_case_identity.py -q`
- **After every plan wave:** Run `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds (quick subset)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 87-01 / Task 0 | 87-01 | 1 | IDENT-01/02/03 | T-87-01/02 | malformed SMILES → graceful; parameterized SQL | unit+regression scaffold | `pytest tests/test_verify_case_identity.py --co -q` | ❌ W0 (creates `tests/test_verify_case_identity.py`) | ⬜ pending |
| 87-01 / Task 1 | 87-01 | 1 | IDENT-01, IDENT-03 | T-87-01 | parameterized `?` SQL; read-only DB | unit | `pytest tests/test_verify_case_identity.py -k "inchikey or novel or coconut or indigo_found" -x -q` | ✅ after Task 0 | ⬜ pending |
| 87-01 / Task 1 | 87-01 | 1 | IDENT-02 (binding) | T-87-02 | mismatch → verdict tentative + warning, no crash | unit+regression | `pytest tests/test_verify_case_identity.py -k "indigo_mislabel or chamazulene_asserted" -x -q` | ✅ after Task 0 | ⬜ pending |
| 87-01 / Task 1 | 87-01 | 1 | IDENT-02 (binding) | T-87-01 | name_match tolerant (no false-fail / no false-substring-pass) | unit | `pytest tests/test_verify_case_identity.py -k "tolerant or false_substring" -x -q` | ✅ after Task 0 | ⬜ pending |
| 87-01 / Task 1 | 87-01 | 1 | IDENT-01/02/03 | — | existing behavior preserved | regression | `pytest tests/test_verify_case_solution.py -q` | ✅ existing | ⬜ pending |
| 87-02 / Task 1 | 87-02 | 2 | IDENT-01, IDENT-03 | T-87-02 | analyst reads verdict/warning | source-assertion (grep) | `grep -q "check-identity" .claude/agents/lucy-solution-analyst.md && grep -q "(tentative, unverified)" .claude/agents/lucy-solution-analyst.md` | ✅ file exists | ⬜ pending |
| 87-02 / Task 2 | 87-02 | 2 | IDENT-02 (advisory) | T-87-04 | advisory only, never blocks | source-assertion (grep) | `grep -q "G-IDENT" .claude/agents/lucy-devils-advocate.md && grep -qi "post-solution" .claude/agents/lucy-devils-advocate.md` | ✅ file exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note: gate-effectiveness on CASE4 (chamazulene) / CASE5 (indigo↔isoindigo, indirubin) is the Success-Criterion-4 regression fixture — pinned as deterministic test cases in `tests/test_verify_case_identity.py`: chamazulene `FVZVDQVUOAAMCG-UHFFFAOYSA-N` no-hit (asserted name → tentative, test `*chamazulene_asserted*`); indigo `COHYTHOBJLSHDF-BUHFOSPRSA-N` InChIKey hit + isoindigo mislabel mismatch (test `test_indigo_mislabel_mismatch`); tolerant token-match against the ';'-delimited DB name "2,2'-Bis(...); Indigo" (test `*tolerant*`).*

---

## Wave 0 Requirements

- [ ] `tests/test_verify_case_identity.py` — stubs for IDENT-01/02/03 + CASE4/CASE5 fixtures + tolerant-match / no-false-substring cases (created in 87-01 Task 0)
- [ ] DB-dependent tests guarded with `skipif(DatabaseFinder.find_derep_database() is None)` so CI without the 2.8 GB DB still passes
- [ ] Existing pytest infrastructure (pyproject.toml) covers framework — no new install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Solution-analyst calls the check-identity tool and renders tentative names in a real CASE run | IDENT-01/03 | LLM-agent prompt behavior; reload needs a fresh session | In a FRESH Claude Code session, run a CASE on a no-DB-hit structure; confirm the report uses InChIKey + canonical SMILES as primary identity and marks the trivial name "(tentative, unverified)" |
| Devils-advocate G-IDENT advisory gate fires post-solution on CASE4/CASE5 | IDENT-02 | LLM-agent prompt behavior; not unit-testable | Re-run CASE4/CASE5 blind in a fresh session (Phase 89); confirm the DA flags the name↔structure mismatch after final_results.md |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (`tests/test_verify_case_identity.py` created in 87-01 Task 0)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** planner — 2026-06-23
