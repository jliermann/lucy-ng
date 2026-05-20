---
phase: 72-design-re-validation
verified: 2026-05-20T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Confirm 72-DECISIONS.md APPROVED status reflects explicit sign-off"
    expected: "User reviewed the 4 verdicts and typed 'approved' to lock them on 2026-05-20"
    resolved: "CONFIRMED — user reviewed the verdicts presented in the interactive session and approved them; the orchestrator then resumed the checkpoint agent which set the doc to APPROVED. Human gate satisfied; status upgraded to passed."
---

# Phase 72: Design Re-Validation Verification Report

**Phase Goal:** Answer the 4 open design questions from the postmortem before any fix is built; executable core is one controlled experiment on CASE1.
**Verified:** 2026-05-20
**Status:** passed (human gate confirmed — user approved the verdicts interactively 2026-05-20)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Decision document with explicit YES/NO or named verdicts on all 4 open design questions exists | VERIFIED | `72-DECISIONS.md` Status=APPROVED. Q1-Q4 Answer sections present with bold Verdict lines. Q1=primary extended bond range, Q2=single path CONFIRMED, Q3=native-only generator, Q4=EMERGENT. |
| 2  | Phase-65 hypothesis re-evaluated against v8.0 UAT evidence | VERIFIED | Q1 section corrects "0/90" to "5/90" with RDKit-verified source. Explains constraint-loss confound. Arm A controlled test (2/2 aromatic) is the corrected re-evaluation. |
| 3  | DESIGN-02 decision addresses the agent-reversion-to-normal-LSD pattern with a concrete remedy | VERIFIED | Q2 states "Agent-reversion hypothesis (CONFIRMED)" citing iter3 used direct lsd binary K=0 after merge=0 failures. Concrete remedy: one prominently-documented path, permutation fallback in subordinate section. Phase 75 skill rewrite named explicitly. |
| 4  | Each decision is actionable with direct implications for Phases 73-75 | VERIFIED | Every Q section contains at least one "→ Phase N:" line. Q1→Phase 73+74, Q2→Phase 75, Q3→Phase 74, Q4→Phase 74+75. Direct Phase Implications table at end maps all 8 decision rows to specific phases and named changes. |

**Score: 4/4 truths verified**

---

### Specified Must-Haves from PLAN Frontmatter

#### Plan 01 Must-Haves

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | D-01: Arm C (HMBC X Y 2 4 for 3 known 4J suspects) runs end-to-end and its aromatic/ibuprofen result is recorded | VERIFIED | results.json arm_c: solution_count=1, any_aromatic=true, ibuprofen_found=false. arm_c_solutions.smi contains 1 SMILES. RDKit independently confirms aromatic_ring=True. |
| 2 | D-04: Arm A (no SKEL, full native constraints) runs end-to-end and the aromatic-ring presence is definitively determined by RDKit | VERIFIED | results.json arm_a: solution_count=2, any_aromatic=true, ibuprofen_found=true. Independent RDKit re-run on arm_a_solutions.smi confirms both SMILES pass has_aromatic_ring(). InChI key HEFNNWSXXWATRW confirmed for solution 2. |
| 3 | D-05: Three arm files are built from the known-working iter3 baseline with only the specified modifications | VERIFIED | arm_a.lsd: 0 SKEL commands (2 in comments only), FEXP "NOT F1 AND NOT F2", 2 DEFF lines. arm_b.lsd: contains SKEL F3 "benzene" + PATH + FEXP with F3. arm_c.lsd: arm_a base + 3 HMBC X Y 2 4 lines, 0 SKEL commands. |
| 4 | The experiment script uses the CORRECT outlsd invocation (outlsd 5 < compound.sol, NOT the runner.py anti-pattern) | VERIFIED | run_experiment.py line 162-163: `[str(OUTLSD_BIN), "5"]` with `stdin=sol_file.open()`. The .lsd file is never passed to outlsd stdin. "5" argument present. SUMMARY documents the stdin-vs-file-argument correction discovered during execution. |
| 5 | results.json exists and contains per-arm solution_count, any_aromatic, and ibuprofen_found fields | VERIFIED | File exists with 3 entries. All required fields present in each entry. |

#### Plan 02 Must-Haves

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | D-01: Q1 answer has a YES/NO verdict line and cites Arm C result as evidence | VERIFIED | Bold Verdict line present. Arm C evidence: "Arm C adds HMBC 3 8 2 4 … and still produces 1 aromatic solution." |
| 2 | D-02: Q2 answer has a YES/NO verdict line and specifies the Phase-75 skill-doc strategy | VERIFIED | Verdict: "ONE primary solver path". Phase 75 strategy in "Skill-documentation strategy (D-02a)" subsection with 4 specific bullet points. |
| 3 | D-03: Q3 answer explicitly states DUPL != SYME and documents the native equivalence mechanism (BOND/COSY structural) | VERIFIED | "SYME → DUPL is INCORRECT" stated explicitly. DUPL defined as output-dedup. "The correct native mechanism is structural connectivity constraints" with BOND+COSY examples from iter3. |
| 4 | D-04: Q4 answer has EMERGENT or FORCE-REQUIRED verdict driven by Arm A result | VERIFIED | "Verdict: EMERGENT". Arm A result: "2 solutions, both aromatic (2/2), ibuprofen present — all without a SKEL benzene fragment." Decision rule applied correctly (any_aromatic=true → EMERGENT). |
| 5 | D-05: Phase-65 hypothesis re-evaluated honestly, noting iter2 5/90 count and constraint-loss confound | VERIFIED | "Correct figure: 5/90 solutions in iter2 had >= 6 aromatic atoms (RDKit-verified)". "Critical confound: iter2 ran WITHOUT SYME/DEFF NOT (the constraint-loss bug stripped them)". |
| 6 | Every Q1-Q4 decision has a direct per-phase implication line | VERIFIED | Q1→Phase 73+74, Q2→Phase 75, Q3→Phase 74, Q4→Phase 74+75. All confirmed by automated parse. |
| 7 | 72-DECISIONS.md is approved by the user before being treated as locked | UNCERTAIN | Status field reads "APPROVED — 2026-05-20". SUMMARY metadata records "checkpoint approved by user 2026-05-20". However tasks_completed=1 / tasks_total=2 in frontmatter — the checkpoint task is not reflected as completed. Requires human confirmation. |

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `experiment/arm_a.lsd` | Emergent test: iter3 baseline minus SKEL/PATH/F3 | VERIFIED | 57 lines. 0 SKEL commands (comments only). FEXP "NOT F1 AND NOT F2". 2 DEFF F1/F2 lines. |
| `experiment/arm_b.lsd` | Forced comparison: verbatim iter3 baseline | VERIFIED | Contains PATH + SKEL F3 "benzene" + FEXP with F3. 2 DEFF lines. |
| `experiment/arm_c.lsd` | Bond-range 4J test: arm_a + 3 HMBC X Y 2 4 | VERIFIED | arm_a content + HMBC 3 8 2 4 / HMBC 3 13 2 4 / HMBC 3 9 2 4. 0 SKEL. |
| `experiment/run_experiment.py` | Experiment runner with correct outlsd invocation | VERIFIED | 284 lines. LSD file-argument mode. outlsd with "5" + stdin=sol_file. RDKit aromatic check. InChI key ibuprofen detection. |
| `experiment/results.json` | Machine-readable per-arm results | VERIFIED | 3 arms. All required fields present. Values match arm_a_solutions.smi and arm_c_solutions.smi. |
| `experiment/arm_a_solutions.smi` | SMILES output from Arm A | VERIFIED | 2 SMILES lines. Both confirmed aromatic by independent RDKit check. |
| `experiment/arm_c_solutions.smi` | SMILES output from Arm C | VERIFIED | 1 SMILES line. Confirmed aromatic, not ibuprofen (ortho-isomer). |
| `72-DECISIONS.md` | Locked architecture decisions for Phases 73-76 | VERIFIED | 152 lines. Status APPROVED. All 4 Q-sections. DUPL≠SYME correction. 5/90 correction. Per-phase implications. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `72-DECISIONS.md` Q4 verdict | Arm A result in results.json | empirical: any_aromatic field | VERIFIED | any_aromatic=true → verdict EMERGENT. Decision rule applied correctly. |
| `72-DECISIONS.md` Q3 | DUPL semantics | explicit correction of SYME→DUPL | VERIFIED | "SYME → DUPL is INCORRECT" with definition of what DUPL actually does. |
| `run_experiment.py` | outlsd binary | `[str(OUTLSD_BIN), "5"]` with sol stdin | VERIFIED | Lines 161-168 match the required pattern. |
| `arm_a.lsd` | ring3 filter | DEFF F1 absolute path | VERIFIED | Line 54: DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3" |
| `run_experiment.py` | RDKit | GetRingInfo().AtomRings() | VERIFIED | Lines 59-63 implement the canonical has_aromatic_ring() function. |

---

### Data-Flow Trace (Level 4 — Experiment Results)

| Source | Produces Real Data | Status |
|--------|--------------------|--------|
| arm_a.sol (LSD binary output) | LSD binary ran; solncounter=2; arm_a.sol 92+ lines | FLOWING |
| arm_a_solutions.smi (outlsd output) | 2 SMILES lines from actual outlsd invocation | FLOWING |
| results.json (run_experiment.py output) | Populated from RDKit analysis of real SMILES | FLOWING |
| 72-DECISIONS.md Arm A any_aromatic | Driven by results.json arm_a.any_aromatic=true | FLOWING |

Independent RDKit spot-check confirms: both SMILES in arm_a_solutions.smi return aromatic_ring=True and one matches ibuprofen InChI key HEFNNWSXXWATRW-UHFFFAOYSA-N. The data chain is unbroken.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Arm A SMILES 1 is aromatic | RDKit has_aromatic_ring("C1=CC=C(C(C)C(O)=O)C(=C1)CC(C)C") | True | PASS |
| Arm A SMILES 2 is ibuprofen | InchiToInchiKey(MolToInchi(...)) == "HEFNNWSXXWATRW-UHFFFAOYSA-N" | True | PASS |
| Arm C SMILES is aromatic but not ibuprofen | aromatic_ring=True, inchi_key=UYHNNWQKLGPQQX | Confirmed | PASS |
| results.json structure valid | 3 arms, all fields present | 3/3 | PASS |
| arm_a.lsd has no active SKEL command | grep -c "^SKEL" arm_a.lsd | 0 | PASS |
| arm_c.lsd has HMBC 3 8 2 4 | grep -c "HMBC 3 8 2 4" arm_c.lsd | 1 | PASS |
| No src/ files modified | git log --name-only phase-72 commits | 0 src/ files | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| DESIGN-01 | 72-01-PLAN, 72-02-PLAN | 4J-handling and aromatic-ring approach decided; Phase-65 hypothesis re-evaluated | SATISFIED | Q1 and Q4 sections in 72-DECISIONS.md answer both parts. 5/90 correction present. Arm A = controlled re-evaluation. |
| DESIGN-02 | 72-02-PLAN | Solver-path architecture decided; skill-doc strategy prevents agent reversion | SATISFIED | Q2 section: single primary path, agent-reversion CONFIRMED, Phase 75 skill strategy specified. |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | No TBD/FIXME/XXX/placeholder markers in any phase-72 artifact. No production src/ files modified. |

---

### Human Verification Required

#### 1. Human-Checkpoint Approval Confirmation

**Test:** Confirm that the `checkpoint:human-verify` task in Plan 02 received an explicit "approved" signal from an interactive session. The SUMMARY.md records `tasks_completed: 1 / tasks_total: 2` and a note "checkpoint approved by user 2026-05-20" — but the task count indicates the checkpoint task itself was not counted as complete in the metrics.

**Expected:** User confirms they reviewed 72-DECISIONS.md and typed "approved" to lock the decisions, and that all six verification checks in the checkpoint task passed (Arm B = 2 solutions, all four Q verdicts present, all per-phase implications present).

**Why human:** The verifier cannot distinguish between (a) a user who manually reviewed the document and approved it vs (b) the executor marking it approved without an interactive checkpoint. The task_count discrepancy (1/2) makes this ambiguous. The decisions gate all of Phases 73-76, so false approval would be high-impact.

---

### Gaps Summary

No blocking gaps found. All four roadmap success criteria are satisfied by actual evidence in the codebase (not just SUMMARY.md claims):

1. Decision document with Q1-Q4 verdicts — exists, APPROVED, all verdicts present and named.
2. Phase-65 hypothesis re-evaluated — 5/90 correction documented, constraint-loss confound explained, Arm A provides the controlled counter-evidence.
3. DESIGN-02 addresses agent-reversion — hypothesis CONFIRMED, single-path remedy named, Phase 75 scope explicit.
4. Each decision actionable with per-phase implications — all four Q sections have → Phase N lines; Direct Phase Implications table maps 8 rows.

The one open item is a human confirmation that the approval checkpoint was interactive, not assumed. This does not constitute a gap in the deliverables themselves.

---

_Verified: 2026-05-20_
_Verifier: Claude (gsd-verifier)_
