# 78 — CASE1 Blind UAT Evidence Record (UAT-03)

**Run date:** 2026-06-02 (14:22–14:58 local, blind session)
**Compound:** CASE1 — C13H18O2 (sanitised ibuprofen; identity bookkeeper-only)
**Blind handoff:** `/lucy-ng:case ~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1 C13H18O2`
**Bookkeeper:** tainted orchestrating session — all four criteria measured from on-disk
artifacts, never from agent self-report (D-78-03).

---

## Run narrative (from on-disk artifacts)

Three iterations, monotone convergence **57 → 17 → 5** solutions. The blind `/lucy-ng:case`
team (coordinator + nmr-chemist + lsd-engineer + solution-analyst + devils-advocate) built the
LSD file incrementally in HMBC batches:
- Iter 1: MULT(15) + HSQC(10) + 5 HMBC + COOH BONDs + gem-dimethyl BONDs + cross-ring COSY
  equivalence pairs + ring-exclusion DEFF F → 57 solutions.
- Iter 2: +5 HMBC (ring↔sidechain linkage) → 17.
- Iter 3: +3 HMBC (sidechain geometry); one zero-solution recovery (HMBC 8 13 deferred as a
  4J/conflict) → 5 solutions. Converged; ranking performed.

Three correlations were deferred as suspected 4J (`11 8`, `3 13`, `8 13`) — the para-aromatic
4J failure mode that broke v8.0/Phase 76 was handled by deferral, not by forcing the ring.

---

## Criterion 1 — Solve correctness: **PASS**

**Final solutions file:** `…/CASE1/analysis/iteration_03/solutions.smi` (5 solutions, highest iteration).

**Command:**
```
python scripts/verify_case_solution.py …/CASE1/analysis/iteration_03/solutions.smi C13H18O2
```
**Exit code:** 0 — **`"pass": true`**, formula C13H18O2.
Top-3 checked: #1 aromatic+formula-match (passes), #2 aromatic+formula-match (passes),
#3 aromatic_atoms=0 (non-aromatic isomer, fails — acceptable, harness pass = ≥1 valid).

**Independent RDKit re-parse (do not trust the script alone — D-78-03):** all 5 finals
canonicalised and compared against the bookkeeper reference `CC(C)Cc1ccc(C(C)C(=O)O)cc1`:

| # | formula | aromatic atoms | canonical SMILES | match |
|---|---------|----------------|------------------|-------|
| 1 | C13H18O2 | 6 | `CC(C)Cc1ccccc1C(C)C(=O)O` | ortho isomer |
| 2 | C13H18O2 | 6 | `CC(C)Cc1ccc(C(C)C(=O)O)cc1` | **EXACT MATCH (ibuprofen)** |
| 3 | C13H18O2 | 0 | `CC(C)C1=CC=C(C(C)C(=O)O)C=CC1` | non-aromatic 7-ring |
| 4 | C13H18O2 | 0 | `CC(C)C1=CC=CC=C(C(C)C(=O)O)C1` | non-aromatic 7-ring |
| 5 | C13H18O2 | 0 | `CC(C)C1=C(C(C)C(=O)O)C=CC=CC1` | non-aromatic 7-ring |

The correct para-disubstituted structure (ibuprofen) is present as solution **#2**, not merely
"some aromatic formula match". Independent verification confirms the harness result.

---

## Criterion 2 — Native-only emission / mechanism: **PASS — EMERGENT tier (clean pass)**

**Final emitted LSD file:** `…/CASE1/analysis/iteration_03/compound.lsd` (comments stripped for greps).

| grep | count | required |
|------|-------|----------|
| `SYME` | **0** | 0 |
| `DEFF NOT` | **0** | 0 |
| `^SKEL` | **0** | 0 |
| `^BOND` / `^COSY` | **6** | ≥1 |
| `^DEFF F` / `^FEXP` | **3** | ≥1 |

Sanity across **all** iterations: SKEL=0, SYME=0, DEFF NOT=0 in iter 01, 02 and 03 — the
mechanism was native-only from the start, never reverted.

**Aromatic-ring tier (D-77-06):** all `BOND` lines are
```
BOND 1 14   ; C1=O14 carbonyl
BOND 1 15   ; C1-O15 hydroxyl
BOND 10 11  ; gem-dimethyl (sidechain isopropyl)
BOND 10 12  ; gem-dimethyl (sidechain isopropyl)
```
Ring atoms are the aromatic carbons C2–C7. **No BOND line connects any ring atom (2–7).** The
benzene ring is **fully EMERGENT** — formed from MULT sp2 definitions + HMBC + the two
cross-ring COSY equivalence pairs (`COSY 6 5`, `COSY 7 4`, emitted via `lucy detect
aromatic-cosy`), with zero ring-BONDs and zero SKEL. This is the D-77-06 **CLEAN PASS** tier
and the exact failure Phase 76 could not avoid (it needed 6 forced ring BONDs).

---

## Criterion 3 — Solver path: **PASS**

CASE-PROGRESS.md and final_results.md contain **no** direct-binary bypass reference
(`outlsd`/`./lsd`/`/usr/local/bin/lsd`/`pylsd` → 0 matches).

**On-disk fingerprint of the fixed `lucy lsd run`** (D-78-03 — measured from disk, not
self-report): every iteration dir (01/02/03) contains `ring3` + `ring4` filter files **and** an
auto-produced `solutions.smi` alongside `compound.sol` + `solncounter`. Per
`src/lucy_ng/lsd/runner.py::_execute_lsd`, only `lucy lsd run` copies the bundled ring3/ring4
filter files (line ~290) and auto-invokes outlsd → solutions.smi (lines ~317–318). A direct
`lsd` binary call would neither copy those filter files (DEFF F1 "ring3" would fail to resolve)
nor auto-produce solutions.smi. The fingerprint is present in all three iterations → `lucy lsd
run` was the path end-to-end. Corroborated by the human observer (no manual path switch).

---

## Criterion 4 — Interventions: **PASS (0 path-changing)**

**Bookkeeper → blind-instance message log:** **EMPTY.** The tainted bookkeeper sent zero
messages to the blind instance during the run. The human observer confirmed (AskUserQuestion,
2026-06-03) the run was **completely autonomous** — no structural hint, no atom indices, no
COSY pairs, no "it's aromatic", no path switch. The internal `/lucy-ng:case` coordinator
interventions logged in CASE-PROGRESS.md are part of the system under test, not bookkeeper
interventions, and do not count under D-78-04.

| classification | count |
|----------------|-------|
| ADVISORY (non-disqualifying) | 0 |
| PATH-CHANGING (disqualifying) | **0** |

---

## Overall verdict: **UAT-03 PASS**

| Criterion | Verdict |
|-----------|---------|
| C1 — solve correctness (verify exits 0, pass:true, ibuprofen present @#2) | PASS |
| C2 — native-only emission, EMERGENT ring (SYME/DEFF NOT/SKEL = 0, no ring-BONDs) | PASS |
| C3 — `lucy lsd run` path, no direct-binary bypass | PASS |
| C4 — 0 path-changing bookkeeper interventions | PASS |

All four gate criteria pass on on-disk evidence. The aromatic ring emerged cleanly via the
Phase 77 cross-ring COSY mechanism with no forced ring-BONDs and no SKEL — the exact spirit
failure of Phase 76 is **not** repeated. The gate is satisfied for CASE1.
