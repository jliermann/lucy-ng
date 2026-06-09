# Phase 80: Long-Range (4J) HMBC Connectivity Defect - Context

**Gathered:** 2026-06-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve the v9.0 ship-blocker exposed by the Phase-79 blind CASE9 UAT: false-positive
long-range (4J) HMBC correlations are currently enforced as hard 2-3J bonds, which forces
wrong carbonyl connectivity and **excludes the correct structure**.

Concrete CASE9 trigger: `HMBC 1 8` = 166.1 (ester C=O) ↔ 70.2 (benzylic CH) is enforced
as a 2-3J bond, geometrically impossible in the true para-benzoate
`CC(C)OC(=O)c1ccc(C(C)O)cc1`, so CASE9 converges on a wrong benzylic carbonate
(meta, MAE 9.09, plausible-but-wrong).

This phase changes **HOW** suspect long-range correlations are handled so the correct
structure is no longer excluded. It is NOT a new capability — it is a fix to the existing
HMBC-constraint / solver / ranking pipeline. Must fix CASE9 blind **without regressing
CASE1** (ibuprofen).

</domain>

<decisions>
## Implementation Decisions

### 4J Mechanism (Bereich 1)
- **D-01:** Use LSD's native **global `ELIM N` tolerance** as the base mechanism. All HMBC
  are written as normal 2-3J; `ELIM N` lets the solver internally drop up to N HMBC/COSY
  correlations. This is the combinatorial "consider all ≤N-drop subsets" behaviour, native,
  in a single run — **no pre-classification of which correlation is 4J**, no permutation files.
  (LSD `ELIM I J`: "at most I HMBC/COSY correlations can be eliminated" — see MANUAL_ENG.html.)
- **D-02:** The ELIM budget N is determined by **iterative escalation**: start at `ELIM 0`
  (all constraints hard); only if no chemically plausible solution emerges, raise N stepwise
  (0→1→2…) until solutions appear. Keeps constraints as tight as possible and bounds the
  solution explosion. This cleanly encodes the manual agent reflex.

### Detection Strategy (Bereich 2)
- **D-03:** **No AI/agent classification of which correlations are 4J.** The historical
  per-correlation 4J detection (v7.0 statistical, 100% FP; the existing lsd-engineer
  aromatic↔aliphatic heuristic, which *missed* the CASE9 carbonyl↔oxygenated-CH case) is
  abandoned as a constraint driver. The solver (via ELIM) decides which correlations to drop.
- **D-04:** 4J detection survives **only as post-hoc explanation / plausibility check**: when
  ELIM drops a correlation, the solution-analyst / devils-advocate stage identifies *which*
  correlation was dropped and reports whether the drop is geometrically sane (e.g. "ELIM
  dropped 166↔70, plausible as a 4J in a para-benzoate"). Explanation, not a hard filter.

### Solver Path (Bereich 3)
- **D-05:** **Native ELIM single-path.** One LSD run with `ELIM N` (iteratively escalated).
  The buggy, UAT-bypassed **pyLSD permutation system is stood down / removed** for the 4J
  case. This resolves the open DESIGN-02 single-vs-dual-path tension toward single-path.
  Rationale: pyLSD permutation, to make "no assumptions", would have to permute over *all*
  HMBC (2^N runs, infeasible) or rely on a suspect pool (= the classification we are
  rejecting) — which is exactly why it was fragile. ELIM gives the same combinatorial
  behaviour natively without that ballast.
- **D-06:** Accepted trade-off: `ELIM` **discards** dropped correlations entirely (their info
  is lost), whereas pyLSD's extended-range `HMBC a b 2 4` *kept* them as weak 4J constraints.
  Reviving extended-range / pyLSD to retain that info is **deferred to backlog** — only
  revisit if ELIM's info-loss proves to cause real failures.

### Solution-Explosion Guardrail & Ranking (Bereich 4)
- **D-07:** **Remove the "minimise solution count / >10 → add more constraints / defer"
  reflex** from the skill (currently in lsd-engineer 4J-batch logic). It directly contradicts
  ELIM, which deliberately widens the solution set. "Few solutions" is no longer the goal.
- **D-08:** New stopping rule: stop at the **smallest ELIM N that yields ≥1 chemically
  plausible (aromatic / DBE-consistent) solution**, then **rank ALL solutions of that run**.
  Success target is "correct structure ranked at/near the top", not "small solution set".
- **D-09:** Discrimination moves to the **ranking stage**. Keep the existing 13C-HOSE
  prediction ranking (signal-match-count desc, then MAE asc — `src/lucy_ng/ranking/ranker.py`),
  but add a **chemical plausibility pre-filter** ahead of MAE ranking: DBE consistency,
  aromatic-ring check, HSQC-multiplicity consistency. This filters grossly-wrong solutions
  before MAE ranking and reuses the post-hoc signal from D-04.

### Claude's Discretion
- Exact LSD `ELIM` syntax/semantics (the `I J` two-argument form), the precise escalation
  ceiling for N, and where in the pipeline the plausibility pre-filter is implemented —
  research + planning decide. The strategic shape (single-path ELIM, iterative N, rank-all,
  pre-filter) is locked above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition & requirements
- `.planning/ROADMAP.md` — Phase 80 entry (the 4J-HMBC connectivity defect, the CASE9 trigger,
  and the v4.0/v7.0/v8.0 history of failed approaches)
- `.planning/REQUIREMENTS.md` — v9.0 requirements

### The defect & its forensics
- `.planning/phases/79-peak-picking-symmetry-fix/79-HUMAN-UAT.md` — blind CASE9 UAT that
  exposed the 4J trap once carbonyl-masking was removed
- `.planning/phases/79-peak-picking-symmetry-fix/79-VERIFICATION.md` — verification of the
  Phase-79 fixes (carbonyl picked, symmetry detected, ring emergent) that surfaced this blocker
- `.planning/v8.0-UAT-POSTMORTEM.md` — why the pyLSD permutation system was buggy/bypassed
  (constraint loss, empty merge) — the basis for standing it down (D-05)

### Prior design decisions
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — DESIGN-01 (where constraint
  translation lives) and DESIGN-02 (single vs dual solver path) — D-05 resolves DESIGN-02
  toward single-path for the 4J case

### LSD mechanism (authoritative)
- `~/Dropbox/develop/LSD/MANUAL_ENG.html` — native HMBC range (`HMBC a b 2 4`, line ~526/545)
  and `ELIM I J` semantics ("at most I HMBC/COSY correlations can be eliminated", line ~802/810).
  This is the ground truth for the ELIM mechanism.

### Skill to modify
- `~/.claude/agents/lucy-lsd-engineer.md` — holds the existing "4J Deferral Rule",
  `pylsd_mode`, `deferred_4j` machinery, and the ">10 solutions" minimisation reflex —
  the primary target for D-03/D-05/D-07
- `~/.claude/agents/lucy-diagnostic.md` — HMBC 2-3J semantics, 1J-leak vs long-range
  diagnosis (HMBC section ~line 109)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/lucy_ng/ranking/ranker.py` + `ranking/models.py` — existing 13C-HOSE ranking
  (signal-match-count then MAE). Reused as the primary discriminator (D-09); the plausibility
  pre-filter sits in front of it.
- `src/lucy_ng/lsd/generator.py`, `cli/lsd.py` — already emit `ELIM`; the native mechanism
  exists in the codebase. Phase 80 changes *how/when* it is used, not whether it exists.
- `src/lucy_ng/data/schemas/constraint_inventory_v2.json` — `deferred_4j` schema; will be
  affected by D-03 (no classification) — likely simplified/retired for the 4J case.

### Established Patterns
- LSD `ELIM I J` is native (unlike SYME/DEFF NOT which are lucy-ng abstractions). ELIM passes
  straight to the binary — no translation-layer constraint-loss risk on this path.
- Ranking algorithm contract (CLAUDE.md): signal-match-count desc, then MAE asc. Pre-filter
  must not break this ordering for surviving candidates.

### Integration Points
- `src/lucy_ng/cli/pylsd.py` — the pyLSD orchestration entry point being stood down (D-05).
- The agent skills (lsd-engineer, devils-advocate, solution-analyst, case.md) carry the 4J
  deferral / minimisation logic that D-03/D-07 remove and D-04/D-08/D-09 rewrite.

</code_context>

<specifics>
## Specific Ideas

- User's framing (verbatim intent): the AI should make **no assumptions** about which
  couplings are 4J; let combinatorics handle it. ELIM is the cleaner realisation of the
  pyLSD "try predefined 4J subsets across runs" idea the user originally had in mind.
- User's guardrail concern (verbatim intent): the skill must stop trying to *minimise* the
  number of solutions at all costs, because ELIM will explode the solution count — instead
  ensure a large solution set can be reduced to the most plausible one, which makes
  NMR-prediction + ranking relevant again. (Drives D-07/D-08/D-09.)
- Validation anchor: CASE9 = 4-(1-hydroxyethyl)benzoic acid isopropyl ester (C12H16O3),
  para-disubstituted benzene + ester carbonyl. Correct SMILES `CC(C)OC(=O)c1ccc(C(C)O)cc1`
  (or an RDKit-verified aromatic C12H16O3 isomer) must land top-3. CASE1 must not regress.

</specifics>

<deferred>
## Deferred Ideas

- **Revive pyLSD permutation / extended-range `HMBC a b 2 4`** to retain dropped-correlation
  info as weak 4J constraints instead of discarding it (vs ELIM's info-loss). Backlog —
  revisit only if ELIM's info-loss causes real failures (D-06).
- **Deeper ranking overhaul** (weighted multi-criteria, confidence scores, prediction-model
  change). Out of Phase-80 scope; existing ranking + plausibility pre-filter is the bet (D-09).
- **devils-advocate ELIM gates** (e.g. block runaway N escalation, flag implausible drops) —
  in scope conceptually via D-04/D-08 but exact gate wording is a planning detail, not a
  separate capability.

</deferred>

---

*Phase: 80-long-range-4j-hmbc-connectivity-defect*
*Context gathered: 2026-06-09*
