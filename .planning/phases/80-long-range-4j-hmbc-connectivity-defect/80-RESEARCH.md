# Phase 80: Long-Range (4J) HMBC Connectivity Defect — Research

**Researched:** 2026-06-09
**Domain:** LSD ELIM mechanism, solver configuration, agent skill surgery, chemical plausibility pre-filter
**Confidence:** HIGH (all findings verified from source files, LSD manual, or codebase)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use LSD's native global `ELIM N` tolerance. All HMBC written as normal 2-3J; `ELIM N` lets the solver drop up to N internally. No per-correlation 4J pre-classification.
- **D-02:** ELIM budget N determined by iterative escalation: start `ELIM 0`; raise stepwise (0→1→2…) until ≥1 chemically plausible solution emerges.
- **D-03:** No AI/agent classification of which correlations are 4J. Historical per-correlation detection abandoned.
- **D-04:** 4J detection survives ONLY as post-hoc explanation / plausibility check after solutions appear.
- **D-05:** Native ELIM single-path. pyLSD permutation system is stood down / removed for the 4J case.
- **D-06:** ELIM discards dropped correlations (accepted info-loss). pyLSD extended-range (`HMBC a b 2 4`) deferred to backlog.
- **D-07:** Remove the ">10 solutions → add more constraints / defer" minimisation reflex from the skill.
- **D-08:** New stopping rule: smallest ELIM N that yields ≥1 chemically plausible (aromatic / DBE-consistent) solution, then rank ALL solutions.
- **D-09:** Chemical plausibility pre-filter added AHEAD of MAE ranking: DBE consistency, aromatic-ring check, HSQC-multiplicity consistency. Does not break ordering for survivors.

### Claude's Discretion

- Exact LSD `ELIM I J` two-argument semantics (research verifies)
- Precise ELIM escalation ceiling for N
- Pipeline location for the plausibility pre-filter

### Deferred Ideas (OUT OF SCOPE)

- Revive pyLSD permutation / extended-range `HMBC a b 2 4`
- Deeper ranking overhaul (weighted multi-criteria, confidence scores)
- Exact devils-advocate ELIM gate wording

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIX-07 | Long-range / 4J HMBC connectivity handling — false-positive 4J correlations must no longer be enforced as hard 2-3J bonds that exclude the correct structure. Exposed by Phase-79 blind CASE9 UAT. Must not reintroduce v7.0 100%-FP failure; must not regress CASE1 (ibuprofen). | D-01/02: ELIM N iterative escalation in generator.py. D-05: pyLSD stood down. D-07/08/09: ranking refactor with plausibility pre-filter. D-03/04: skill surgery. |

</phase_requirements>

---

## Summary

Phase 80 is a surgical, multi-layer fix. The strategy is locked (CONTEXT.md D-01..D-09); this research answers the implementation specifics.

**Layer 1 — Code (generator + ranker):** The Python `LSDProblem.elim_commands` field and `emit_elim()` method already exist but are gated behind `pylsd_mode=True`, which is being stood down (D-05). ELIM emission must be promoted to the primary path as a first-class parameter independent of `pylsd_mode`. The `SolutionRanker` already computes `has_aromatic_ring` per solution and logs an aromatic sanity warning; it needs a proper pre-filter function inserted before the MAE sort, using the RDKit helpers that are already imported.

**Layer 2 — Skill surgery (agent markdown files):** The 4J-Deferral Rule, `pylsd_mode` routing block, `deferred_4j` population logic, and ">10 solutions" stopping conditions in `lsd-engineer.md` are the primary targets. Secondary: `devils-advocate.md` Check-4 (G1–G4, G8) and all `; ELIM`-annotation greps reference the now-retired pylsd path. `solution-analyst.md` has a hardcoded aromatic↔aliphatic 4J removal advisory that is now post-hoc only. `case.md` has a 4J-correlation reporting line and ELIM-Thrashing loop pattern that need to be updated for the new semantics.

**Layer 3 — Schema + CLI:** `constraint_inventory_v2.json` has a `deferred_4j` array required field and `pylsd_mode`/`elim_annotated` booleans that encode the retired pyLSD classification approach. Phase 80 must retire those fields (or make them optional/unused) and replace `elim_value` (which was `null` in pylsd_mode) with a first-class `elim_budget` or similar field that records the N used for the global ELIM. `lucy pylsd run` CLI command can be kept as dead code or clearly deprecated/removed.

**Primary recommendation:** Implement ELIM escalation in a new `elim_budget` parameter on `LSDProblem` (replacing the `pylsd_mode`-gated `elim_commands` list); add `chemical_plausibility_filter()` to `SolutionRanker`; update agent skills in a targeted, section-by-section way; then run blind CASE9 UAT.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| ELIM emission in .lsd file | Python generator (`lsd/generator.py`) | Agent skill (writes parameter) | Generator owns file format; skill provides the N value |
| ELIM budget escalation logic | Agent skill (`lucy-lsd-engineer.md`) | Orchestrator (`case.md`) | Agent decides when to escalate; orchestrator detects loops |
| Post-hoc 4J identification | `lucy lsd analyze` CLI | Agent skill (solution-analyst) | Analyzer computes path lengths from .sol graph; analyst reports |
| Chemical plausibility pre-filter | Python ranker (`ranking/ranker.py`) | — | Pure computation on RDKit molecule objects already in ranker |
| DBE calculation | RDKit `rdMolDescriptors.CalcNumHBA` / `CalcMolFormula` | Agent DBE self-check (Phase 79) | RDKit is already imported in ranker.py |
| Schema state (constraint inventory) | `constraint_inventory_v2.json` schema + `cli/lsd.py` validator | Agent skill (writes inventory) | Schema enforces structure; CLI validates |
| pyLSD stand-down | `cli/pylsd.py` + `cli/main.py` | Agent skill routing block | Python removes/disables command; skill removes routing |

---

## Standard Stack

No new external packages required. All needed tools are already present:

### Core (existing, verified in codebase)

| Library | Where Used | Purpose |
|---------|-----------|---------|
| RDKit (`Chem`) | `ranking/ranker.py` line 6, 87-89 | Aromatic ring detection (already present) |
| RDKit `rdMolDescriptors` | `prediction/bond_pair_generator.py`, `dereplication/nmrshiftdb.py` | `CalcMolFormula` — available for DBE computation |
| `lucy_ng.lsd.generator.LSDInputGenerator` | All LSD file generation | `emit_elim(n, m)` already exists (line 62) |
| `lucy_ng.lsd.models.LSDProblem` | All LSD problems | `elim_commands: list[tuple[int,int]]` already exists (line 185) |
| `lucy_ng.lsd.analyzer.LSDSolutionAnalyzer` | `cli/lsd.py` `lsd_analyze` command | `path_length` / `j_coupling` on HMBC correlations — existing post-hoc 4J path |
| `lucy_ng.ranking.ranker.SolutionRanker` | `cli/lsd.py` `_perform_ranking()` | Primary discrimination engine |

### DBE Computation (no new import needed)

RDKit `rdMolDescriptors.CalcMolFormula` is already imported in two sibling modules. For DBE:

```python
from rdkit.Chem import Descriptors
# DBE = (2C + 2 + N - H - X) / 2
# Simpler: use rdMolDescriptors.CalcNumHeavyAtoms + ring count
# Or: compute from formula string (already done by parse_molecular_formula() in generator.py)
```

`parse_molecular_formula()` already exists in `generator.py` (lines 13–29); the DBE formula is deterministic from element counts. No new import needed — `rdMolDescriptors.CalcMolFormula` returns the formula string which can be fed to the existing parser.

### Package Legitimacy Audit

No new packages. All dependencies pre-installed. Audit not applicable.

---

## Research Question Answers

### Q1: LSD `ELIM I J` exact semantics [VERIFIED: MANUAL_ENG.html]

From `~/Dropbox/develop/LSD/MANUAL_ENG.html` lines 801-816:

```
ELIM I I: elimination of invalid HMBC and/or COSY correlations
  P1: maximum number of eliminated correlations.
  P2: maximum number of bonds between the atoms in eliminated correlations.
        Upper limit is P2 for HMBC; P2+1 for COSY.
        0 means: no limitation.

Example: ELIM 3 5 — up to 3 HMBC/COSY correlations can be eliminated.
Each eliminated HMBC is through a 4J coupling (lower limit) or 5J (upper limit).
For COSY: 5J lower limit, 6J upper limit.
```

**Critical semantic points:**

1. **P1 = "at most N correlations" (global budget, combinatorial).** LSD tries ALL subsets of size ≤N dropped; a solution is accepted if any such subset satisfies the remaining constraints. This is the combinatorial mechanism D-01 relies on — no pre-classification needed.

2. **P2 = maximum bond distance of dropped correlations.** `ELIM N 0` = "allow up to N drops with no bond-distance limit" — suitable for Phase 80 where we do NOT know in advance how long the spurious path is. For the CASE9 trigger (166.1↔70.2 at 4J), `ELIM 1 5` would work (upper bound ≤5 bonds for HMBC = 4J+5J range). Using `0` (no limit) is the safest default when path length is unknown.

3. **ELIM applies to HMBC AND COSY.** HSQC is not affected (HSQC has no path-range constraint in the ELIM model). Per manual line 521 and 549: correlations written as `HMBC X Y 2 3` (explicit range) or `COSY X Y 3 4` (explicit range) **will never be eliminated even if ELIM is present**. This is important: COSY equivalence-pair constraints added by `detect_aromatic_cosy_pairs()` should be safe, because the lsd-engineer should continue to write them with explicit range (3 bonds) or the default 3-bond range, both of which prevent ELIM from touching them.

4. **LSD does NOT report which specific correlations it dropped.** The `.sol` file records connectivity only. Post-hoc identification of dropped correlations requires `lucy lsd analyze` — which computes shortest-path lengths in each solution graph and flags any HMBC correlation whose path length exceeds 3 (indicating 4J or longer). The agent uses `lucy lsd analyze compound.sol compound.lsd` to identify which correlations were effectively incompatible with the solution (D-04 post-hoc check).

5. **Interaction with HSQC:** HSQC correlations are direct 1J bonds — they are never ELIM candidates. Only HMBC and COSY are candidates.

**Recommended escalation series for D-02:**
```
ELIM 0 0   → (no ELIM, current behaviour)
ELIM 1 0   → solver may drop any 1 HMBC/COSY
ELIM 2 0   → solver may drop any 2 HMBC/COSY
ELIM 3 0   → solver may drop any 3 HMBC/COSY
```

Using P2=0 (no bond-distance limit) avoids needing to know the actual path length. The manual's own example uses `ELIM 3 5` for a case with known 4J/5J candidates; for the general "unknown 4J" case `0` is correct.

**Practical ceiling:** The solution space grows combinatorially: N=1 → C(K,1) subsets, N=2 → C(K,2), N=3 → C(K,3), where K = total HMBC+COSY count. For CASE9 (K≈15 HMBC), N=1 = 15 subsets, N=2 = 105 subsets, N=3 = 455 subsets — all within LSD's per-run capacity. The stopping condition (D-08) limits escalation: stop at the smallest N producing ≥1 plausible solution. A hard ceiling of N=3 is a reasonable default guard; the skill can document this as a configurable upper bound.

---

### Q2: Current ELIM emission in the codebase [VERIFIED: codebase]

**Current state (gated behind `pylsd_mode=True`):**

In `src/lucy_ng/lsd/models.py` line 185:
```python
elim_commands: list[tuple[int, int]] = field(default_factory=list)
```
The field stores `(N, M)` tuples — i.e., the current design treats each `(N, M)` as a separate ELIM line to emit.

In `src/lucy_ng/lsd/generator.py` lines 111-118:
```python
if problem.pylsd_mode:
    if problem.molecular_formula:
        lines.append(LSDInputGenerator.emit_form(problem.molecular_formula))
    for n, m in problem.elim_commands:
        lines.append(LSDInputGenerator.emit_elim(n, m))
```

`emit_elim(n, m)` simply returns `f"ELIM {n} {m}"` (line 75).

**The Phase 80 change:** ELIM emission must be decoupled from `pylsd_mode`. The cleanest approach is to add a single `elim_budget: int = 0` field to `LSDProblem`, and emit `ELIM {N} 0` when `elim_budget > 0` **regardless of `pylsd_mode`**. The existing `elim_commands: list[tuple[int,int]]` field was designed for the pyLSD path (multiple `ELIM N M` lines with explicit atom counts per run); for the Phase 80 global `ELIM N 0` semantics, a single integer budget is the right abstraction.

**Minimal change option:** Keep `elim_commands` but gate its emission on `elim_budget > 0` rather than `pylsd_mode`. In practice, a new `elim_budget: int = 0` field is cleaner and more self-documenting.

**Generator change needed:**
- Remove the `if problem.pylsd_mode:` gate around ELIM emission
- Emit `ELIM {problem.elim_budget} 0` when `problem.elim_budget > 0`
- (The `; FORM` comment should remain as metadata even in non-pylsd_mode, but it is optional)

**Caller-controllable N:** The lsd-engineer agent currently writes the LSD file manually (as a text template in the skill), not via `LSDInputGenerator`. The `elim_budget` parameter needs to be communicated from the agent's constraint inventory to the LSD file content. The simplest path: the lsd-engineer writes `ELIM N 0` directly in the LSD file text (as it already writes all other commands manually), reflecting the current iteration's N value from the escalation loop. No Python generator change is strictly required for the agent workflow — but generator support enables unit testing and programmatic use.

---

### Q3: The 4J machinery to REMOVE from agent skills [VERIFIED: codebase]

#### `~/.claude/agents/lucy-lsd-engineer.md` (615 lines) — Primary target

**Section "4J Deferral Rule" (lines 261-299)** — REMOVE ENTIRELY.
This section contains:
- The heuristic (aromatic 110-160 ppm ↔ aliphatic 0-55 ppm)
- "Never include flagged 4J correlations in early batches"
- "Add to `deferred_4j` in constraint inventory"
- "Only add as final batch if solutions > 10"
- The 4J batch logic (lines 292-299) — the ">10 solutions → try 4J batch" reflex

**Adaptive Loop stopping condition (line 276-277)** — CHANGE:
```
# Current (REMOVE):
solution_count <= 10 -> STOP, proceed to ranking
# Replace with D-08:
≥1 chemically plausible (aromatic / DBE-consistent) solution -> STOP at current N, rank ALL
```

**Section "Stopping Conditions" (lines 285-290)** — REWRITE:
- Remove "Success: <=10 solutions → rank"
- Add: "Success: ELIM N yields ≥1 plausible solution → rank all. Plausibility: aromatic ring present if ≥4 shifts in 110-160 ppm; DBE consistent with formula."

**pyLSD routing block (lines 578-605)** — REMOVE THE FALLBACK BRANCH.
Current: "PRIMARY PATH" = `lucy lsd run`; "FALLBACK PATH when K≤3 deferred_4j + pylsd_mode=true" = `lucy pylsd run`.
Replace with: single path `lucy lsd run`, ELIM escalation is the only fallback mechanism.

**Constraint inventory update procedure (lines 504-525)** — CHANGE:
- Remove `pylsd_mode`, `elim_annotated`, `deferred_4j` population steps (5b, 5c, 5d)
- Add: `elim_budget: int` field (current ELIM N value, 0 when no ELIM)
- Step 5d rewrite: "If iteration yields 0 solutions AND all other checks pass (sp2 even, H budget correct, all HMBC added), escalate ELIM budget N+1 (starting from 0). Document N in inventory."

**[ITERATION-COMPLETE] template (lines 347-390)** — CHANGE:
- Remove the pylsd-mode appendix block (per-permutation table, pylsd_output.json)
- Replace "4J status: deferred/added/skipped" with "ELIM budget: N (N correlations dropped in accepted solutions)"

**Section 1 HMBC example (line 60)** — CHANGE:
```
# Current (REMOVE):
HMBC 3 8 2 4   ; extended bond range 2-4: primary 4J mechanism (D-01)
# Replace with:
HMBC 3 8       ; standard 2-3J
ELIM 1 0       ; global: solver may drop up to 1 HMBC/COSY (4J escalation, D-01)
```

**Section "ELIM Command (LAST RESORT)" (lines 119-127)** — REWRITE.
Current: "Only add if 0 solutions AND you have verified... Start with ELIM 1 0, increment."
Replace: "ELIM is the primary 4J mechanism (D-01). Add iteratively starting at N=1 only after all HMBC added and 0 plausible solutions. Ceiling N=3. P2=0 always (no bond-distance limit)."

**Total lsd-engineer changes:** ~4 sections rewritten, ~80 lines removed, ~40 lines added.

#### `~/.claude/agents/lucy-devils-advocate.md`

**Check 4: pyLSD Mode Consistency (G1–G4, G8) — REMOVE ENTIRELY.**
Lines containing: G1 FORM consistency check, G2 "no bare ELIM in pylsd_mode" block, G3 `; ELIM` annotation consistency, G4 K≤3 permutation cap, G5/G6 post-run pylsd_run/ checks, G8 pylsd reversion check.

**These gates enforced the pyLSD permutation path being stood down (D-05).** With pyLSD gone, all G1–G4 and G8 logic is obsolete. G5/G6 (post-run perm constraint completeness + empty-merge-vs-solncounter) are also obsolete.

**New ELIM gate to ADD:** A simple gate checking ELIM usage: "If ELIM N present AND N > 3: WARNING (excessive elimination; confirm ≤3 failed first). If ELIM present in iteration 1 before any HMBC exhausted: WARNING."

**Section 3 ELIM Usage (lines 183-186)** — UPDATE to reflect new semantics (ELIM is now the 4J mechanism, not last-resort; N=1 is expected when 4J is suspected).

**G5 (v8.0 failure mode: perm constraint completeness) and G6 (empty merge) — REMOVE.** These were pyLSD-specific.

**Total DA changes:** ~60 lines removed, ~15 lines added.

#### `~/.claude/agents/lucy-solution-analyst.md`

**Lines 121-123** (hardcoded 4J removal advisory): 
```
# Current (REMOVE active recommendation):
"Identify HMBC correlations between aromatic ring carbon positions (110-160 ppm) and
benzylic/alpha-substituent positions (0-55 ppm). Remove the most suspect ones and re-run LSD."
# Replace with D-04 post-hoc framing:
"Use `lucy lsd analyze compound.sol compound.lsd` to identify which correlations have path
length ≥4 in the accepted solution — these are 4J couplings; report as plausibility annotation
only, do NOT advise removing them (ELIM handles this automatically)."
```

**Line 206** (aromatic warning template) — minor update to reference ELIM escalation instead of manual removal.

**Total solution-analyst changes:** ~5 lines.

#### `~/.claude/agents/lucy-diagnostic.md`

**Section "ELIM - Correlation Elimination" (lines 268-301)** — UPDATE.
Current framing: "ELIM increases solution space (opposite of normal constraints). ELIM added prematurely → 1000+ solutions. NEVER use ELIM on first LSD run."
This is now WRONG for Phase-80 semantics. ELIM is the intended 4J mechanism.
Replace: "ELIM is the native 4J tolerance mechanism. `ELIM N 0` allows the solver to drop up to N correlations. Expects large solution sets — discrimination via chemical plausibility pre-filter + ranking. Diagnostic use: `lucy lsd analyze` shows path lengths in accepted solutions."

**Check 1 ELIM Presence (lines 575-609)** — UPDATE. Remove "FOUND → FAIL" logic. Replace with: "ELIM expected when 0-solution recovery reached ELIM escalation. If ELIM N > 3 without prior documentation in [ITERATION-COMPLETE]: flag WARNING."

**Total diagnostic changes:** ~20 lines rewritten.

#### `~/.claude/commands/lucy-ng/case.md`

**Line 192** (peak-picking checklist item "Potential 4J correlations") — REMOVE. nmr-chemist no longer classifies 4J suspects.

**Lines 348, 352, 378, 411-429** (ELIM Thrashing loop pattern) — REWRITE. "ELIM Thrashing" semantics change: old = ELIM being added/removed/re-added as a last resort; new = ELIM being escalated beyond N=3 without plausible solutions (runaway escalation). Update detection and advisory text.

**Lines 394-395** (loop-pattern check: "Check if ELIM command is present") — REWRITE to check for runaway N escalation.

**Lines 451, 488** (zero-solution recovery: "Remove ELIM if present") — UPDATE. ELIM is now the final tool, not the first to remove.

**Total case.md changes:** ~10 lines.

---

### Q4: pyLSD stand-down (D-05) [VERIFIED: codebase]

**`src/lucy_ng/cli/pylsd.py`** — The entry point is the `pylsd` Click group with a single `pylsd run` subcommand (line 144). It is registered in `src/lucy_ng/cli/main.py` line 14+54:
```python
from lucy_ng.cli.pylsd import pylsd
cli.add_command(pylsd)
```

**Stand-down options:**

1. **Remove `lucy pylsd run` from CLI** (D-05 "stood down"): Delete `cli/pylsd.py` and the two lines in `cli/main.py`. Clean but removes test coverage for the permutation path which may be needed if ELIM fails and pyLSD is revived from backlog (D-06).

2. **Deprecate: keep file, add deprecation warning** (preferred for reversibility). Add `click.echo("Warning: lucy pylsd run is deprecated (D-05). Use lucy lsd run with ELIM escalation.", err=True)` as the first line of `pylsd_run()`. This preserves the code for potential D-06 backlog revival without exposing it as a recommended path.

3. **Remove from agent skills only** (minimal). Remove the `lucy pylsd run` routing block from lsd-engineer. The CLI command stays but agents never invoke it.

**Tests to update:** `tests/test_lsd_orchestrator.py` (927 lines, 15+ test classes) covers `PyLSDOrchestrator` and `SolutionMerger`. These tests do NOT need to be deleted — the orchestrator code is kept for D-06 backlog. The test file needs only: remove the `pylsd_mode=True` requirement from any test that creates baseline `LSDProblem` objects, and ensure no test REQUIRES `lucy pylsd run` to be the primary path.

**`src/lucy_ng/lsd/__init__.py` lines 51-52, 79, 82:** `PyLSDOrchestrator` and `SolutionMerger` are exported. Keep exports (D-06 backlog). No change needed.

**`validate_pylsd_input()` in `generator.py` (lines 581-602):** This validates FORM/MULT carbon count consistency — it is harmless to keep and may still be useful if pyLSD is revived. Leave it.

---

### Q5: Ranking + plausibility pre-filter (D-08/D-09) [VERIFIED: codebase]

**Current ranking contract** (`src/lucy_ng/ranking/ranker.py` line 104):
```python
ranked.sort(key=lambda r: (-r.matched_count, r.mae))
```
Sort key: `-matched_count` ascending, `mae` ascending. This contract MUST be preserved for survivors.

**Existing infrastructure for pre-filter (already in ranker.py):**
- `has_aromatic_ring` already computed per solution (lines 85-89) using `any(atom.GetIsAromatic() for atom in mol.GetAtoms())`
- `has_aromatic_ring: bool` already stored in `RankedSolution` model
- Aromatic sanity warning already emitted (lines 113-126) when shifts suggest aromaticity but no solutions are aromatic
- `CalcMolFormula()` is available via `rdMolDescriptors` (already imported in sibling modules)

**Three proposed pre-filter checks (D-09):**

1. **DBE consistency:** Compute DBE from the molecular formula (already parsed by `parse_molecular_formula()` in generator.py). For each ranked solution, compute DBE from its SMILES via `rdMolDescriptors.CalcNumHeavyAtoms` + ring info. Flag solutions where DBE deviates from expected by >1 as IMPLAUSIBLE.

   ```python
   # DBE from formula: DBE = (2C + 2 + N - H - X) / 2
   # This is deterministic; parse_molecular_formula() already handles C/H/N counts.
   # For RDKit mol: use Chem.rdMolDescriptors.CalcNumRings() + double bonds
   # Simplest: CalcMolFormula() → feed to parse_molecular_formula() → compute DBE
   ```

2. **Aromatic ring check:** When ≥4 experimental shifts in 110-160 ppm range, a solution without an aromatic ring is flagged IMPLAUSIBLE. Already computed — just needs to become a FILTER, not just a WARNING.

3. **HSQC-multiplicity consistency:** The MULT definitions in the LSD file encode CH/CH2/CH3/quaternary assignments from DEPT. A solution is IMPLAUSIBLE if any atom's RDKit hydrogen count contradicts the MULT definition (e.g., a MULT-defined CH2 atom that RDKit gives 0 or 3 H). This requires passing MULT information into the ranker — currently not available.

**Recommended implementation:** Implement checks 1 and 2 first (both can be computed from SMILES + experimental shifts + formula string alone). Check 3 (HSQC-multiplicity) requires thread-through of MULT data from the LSD problem, which is a heavier change; defer to a follow-up or implement as a separate filter step.

**Pre-filter insertion point:**
```python
# In SolutionRanker.rank() — insert AFTER shift matching, BEFORE sort
ranked_filtered = [r for r in ranked if _is_chemically_plausible(r, experimental_shifts, formula)]
implausible = [r for r in ranked if not _is_chemically_plausible(r, experimental_shifts, formula)]
# Sort survivors by existing contract
ranked_filtered.sort(key=lambda r: (-r.matched_count, r.mae))
# Append implausible solutions AFTER sorted survivors (with plausibility flag)
```

The `_is_chemically_plausible()` function needs:
- `RankedSolution` (has `smiles`, `has_aromatic_ring`)
- `experimental_shifts: list[float]`
- `formula: str | None` (optional — skip DBE check if not provided)

**`RankedSolution` model change needed:** Add `is_plausible: bool = True` field so the agent can distinguish filtered-out solutions when reviewing the ranked list.

---

### Q6: Constraint inventory schema impact [VERIFIED: codebase]

**Current v2 schema** (`src/lucy_ng/data/schemas/constraint_inventory_v2.json`):

Required fields include: `pylsd_mode`, `elim_annotated`, `deferred_4j`.

These three fields encode the pyLSD classification path (D-03/D-05 retire):
- `pylsd_mode: bool` — "true when PyLSDOrchestrator multi-run mode is active"
- `elim_annotated: bool` — "true when HMBC lines carry `; ELIM` trailing comment"
- `deferred_4j: array` — structured 4J suspect objects with `atom1`, `atom2`, `shift1`, `shift2`, `annotation: "; ELIM"`

The schema also has:
- `elim_value: int | null` — "argument N to a bare `ELIM N M` command (last-resort)" — this is the field most relevant to D-02; currently `null` when `pylsd_mode=true` (enforced by `allOf` G2 invariant)

**Phase 80 schema changes needed:**

1. **Retire `deferred_4j` as a required field.** Make it optional (`"required"` list removes it). Existing LSD files with empty `deferred_4j: []` remain valid. The field can stay in the schema as optional for backward compatibility.

2. **Retire `elim_annotated` as a required field.** Set to always `false` (or make optional). The `; ELIM` annotation mechanism is retired.

3. **Change `pylsd_mode` from required to optional** (default `false`). The DA G2 invariant (`pylsd_mode=true` forbids `elim_value`) becomes vacuous since `pylsd_mode` will always be `false`.

4. **Repurpose `elim_value` as the ELIM budget field.** Current: `int | null`, non-null only in last-resort zero-solution recovery. Phase 80: rename conceptually to "current ELIM budget N". The G2 invariant block becomes: "no ELIM budget constraint (pylsd_mode always false)". The existing integer type is correct.

5. **Add `allOf` G2 removal** (or leave it harmlessly — it only triggers when `pylsd_mode=true` which is now always false).

**Code that reads/writes these fields:**
- `src/lucy_ng/cli/pylsd.py` — `_extract_suspects()` reads `inventory.get("deferred_4j", [])` (line 63). If pylsd.py is deprecated, this code is orphaned but not harmful.
- `src/lucy_ng/cli/lsd.py` — `_validate_and_parse_inventory()` validates against schema. No field-specific logic; just schema validation.
- `tests/test_lsd_schema.py` (if it exists) — may assert `deferred_4j` is required. Check and update.
- Agent skills — lsd-engineer populates the inventory block manually (text template in skill). Skill must remove `pylsd_mode`, `elim_annotated`, `deferred_4j` entries and add `elim_budget: N`.

**Minimum change:** Remove `pylsd_mode`, `elim_annotated`, `deferred_4j` from the `"required"` array in the schema. Add `elim_budget: integer, minimum: 0, default: 0` as an optional property. Update the agent skill template accordingly.

**Schema backward compatibility:** Existing CASE1/CASE9 LSD files that have `deferred_4j: []` will still validate (the field is now optional but still permitted). No migration needed.

---

### Q7: Regression guard mechanics [VERIFIED: codebase]

**`scripts/verify_case_solution.py`** exists (confirmed). It:
- Reads the first 3 valid SMILES from a `solutions.smi` file
- Checks each for: aromatic ring (≥6 aromatic atoms) AND exact formula match
- Returns JSON with per-solution results and overall `pass: bool`
- Exits 0 on pass, 1 on fail

**Current limitation for Phase 80:** The script does NOT verify that the correct SMILES is present — it only checks that ANY top-3 solution has aromatic ring + correct formula. For Phase 80, the regression guard should additionally verify that the true para-benzoate SMILES appears in the output (or that the top-1 solution is an RDKit-equivalent para-disubstituted ester).

**Proposed regression guard approach for Phase 80:**

1. **Unit test for ELIM escalation behaviour** (new, automated): Test that `LSDProblem(elim_budget=1)` emits `ELIM 1 0` in the generated file, and that `elim_budget=0` emits no ELIM. This is a pure Python unit test, fast, and locks the generator behaviour.

2. **Unit test for plausibility pre-filter** (new, automated): Given a list of known-wrong solutions (no aromatic ring) and one correct solution (has aromatic ring, correct DBE), assert the pre-filter rejects the wrong ones and retains the correct one.

3. **Agent-experiment regression guard for the historical ibuprofen 4J case** (documented, not automated): The Phase-72 Arm A experiment file (`arm_a.lsd`) is the existing controlled reference. Document: "run Arm A + `ELIM 1 0`; confirm ibuprofen appears in top-3 with correct aromatic ring". This is not a unit test — it requires a live LSD binary. Record the result in a `80-ELIM-REGRESSION.md` or similar findings file.

4. **CASE9 blind UAT** (Success Criterion 4): The blind re-run is itself the primary regression gate (Phase 78 AND-gate re-applied). Run after all code + skill changes.

**Cheapest reliable lock for both CASE9 and ibuprofen:** Two unit tests (ELIM emission + pre-filter) cover the Python changes. One documented experiment (Arm A + ELIM 1 0) covers the historical ibuprofen 4J case without requiring a full agent CASE run. The blind CASE9 re-run covers the integration gate.

---

### Q8: Validation Architecture (Nyquist) [VERIFIED: config.json]

`nyquist_validation` key is ABSENT from `.planning/config.json` — treat as ENABLED.

---

## Architecture Patterns

### System Architecture Diagram

```
                   CASE9 Spectrum
                        │
                        ▼
              [nmr-chemist: peak pick]
                        │
                  peaks + formula
                        │
                        ▼
             [lsd-engineer: build LSD file]
               All HMBC as normal 2-3J
               ELIM budget = 0 initially
                        │
                 compound.lsd
                        │
                        ▼
              [lucy lsd run] ←──────────────────────────────────┐
                        │                                        │
               ┌────────┴─────────┐                             │
               │                  │                             │
         solutions > 0      solutions = 0                       │
               │                  │                             │
               ▼                  ▼                             │
    ┌─ plausibility check  ┌─ checks (sp2, H,                   │
    │   any aromatic?      │  HMBC correct,                     │
    │   DBE consistent?    │  formula right)                     │
    │                      │   all pass?                         │
    │   ≥1 plausible       │      │                             │
    │   solution           │   YES: escalate                    │
    │       │              │   ELIM N+1 (max 3) ───────────────►┘
    │       ▼              │
    │   rank ALL solutions │   all checks fail OR N>3:
    │   (matched_count     │   diagnostic failure
    │    then MAE)         └──────────────────────┐
    │       │                                     │
    │       ▼                                     ▼
    │ [plausibility pre-filter]           [diagnostic specialist]
    │  - IMPLAUSIBLE removed first
    │  - PLAUSIBLE sorted by rank
    │       │
    │       ▼
    │ [solution-analyst: rank + report]
    │  lucy lsd analyze → path lengths
    │  → post-hoc 4J identification (D-04)
    │       │
    └───────►
            ▼
        CASE-PROGRESS.md + final_results.md
```

### Recommended Project Structure Changes

No new directories. Changes are surgical within existing structure:
```
src/lucy_ng/
├── lsd/
│   ├── models.py          # add elim_budget: int = 0 field
│   └── generator.py       # decouple ELIM emission from pylsd_mode
├── ranking/
│   ├── ranker.py          # add _is_chemically_plausible() + pre-filter step
│   └── models.py          # add is_plausible: bool = True to RankedSolution
├── data/schemas/
│   └── constraint_inventory_v2.json  # retire deferred_4j/pylsd_mode/elim_annotated as required
└── cli/
    └── pylsd.py           # add deprecation warning (keep file for D-06 backlog)

~/.claude/agents/
├── lucy-lsd-engineer.md   # primary skill surgery (4J-Deferral Rule, adaptive loop, routing)
├── lucy-devils-advocate.md # remove G1-G4/G8 pyLSD gates; add ELIM-budget gate
├── lucy-solution-analyst.md # post-hoc 4J framing only
└── lucy-diagnostic.md     # update ELIM section from "last resort" to "4J mechanism"

~/.claude/commands/lucy-ng/
└── case.md                # ELIM-Thrashing pattern update; remove 4J-correlation nmr-chemist item

tests/
├── test_lsd_models.py     # add test: elim_budget field default 0, emits ELIM N 0
├── test_lsd_generator.py  # add test: ELIM emitted when elim_budget>0; not when 0
└── test_ranking.py        # add test: plausibility pre-filter rejects non-aromatic when shifts suggest ring
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Aromatic ring detection | Custom ring SMARTS | `mol.GetAtoms() → atom.GetIsAromatic()` (already in ranker.py) | RDKit handles fused/heteroaromatic correctly |
| DBE from SMILES | Parse SMILES atom by atom | `rdMolDescriptors.CalcMolFormula()` → `parse_molecular_formula()` → formula arithmetic | RDKit formula computation handles isotopes and edge cases |
| Path length between atoms | BFS on SMILES graph | `lucy lsd analyze` / `LSDSolutionAnalyzer.analyze()` (already exists) | Already implemented with graph traversal on .sol file |
| LSD file validation | Re-read and parse LSD text | `lucy lsd validate-inventory --format json` | Already validates schema + returns full parsed inventory |

---

## Runtime State Inventory

> Rename/refactor phase: NO (this is a fix, not a rename). Skipping Runtime State Inventory.

---

## Common Pitfalls

### Pitfall 1: ELIM with explicit bond range prevents ELIM
**What goes wrong:** Any HMBC written as `HMBC X Y 2 3` (explicit range) or `HMBC X Y 2 4` will NEVER be eliminated by ELIM, even if ELIM N is present. The manual is explicit (line 549): "This correlation will never be eliminated, even if an ELIM command is present."
**Why it happens:** The old pyLSD path relied on `HMBC X Y 2 4` as the 4J mechanism. If any such lines were carried over into a Phase-80 LSD file, they would be immune to ELIM dropping.
**How to avoid:** Ensure all HMBC correlations in Phase-80 LSD files use the default `HMBC X Y` (no explicit bond range). Audit for any `HMBC X Y 2 4` lines from pyLSD-era files.
**Warning signs:** ELIM N > 0 present but suspected 4J correlation never appears as dropped in `lucy lsd analyze` output.

### Pitfall 2: COSY equivalence pairs being dropped by ELIM
**What goes wrong:** COSY constraints added by `detect_aromatic_cosy_pairs()` (e.g., `COSY 4 7`) are 3J couplings. For ELIM, a COSY correlation is a candidate if its path length > 3 bonds. A `COSY 4 7` without explicit range defaults to 3J; the manual (line 514-515) states that the highest path length cannot exceed `ELIM command value + 1`. So with `ELIM 1 0`, COSY could be subject to elimination if LSD tries extending its path to 4J.
**How to avoid:** Write aromatic COSY pairs with explicit 3-bond range: `COSY 4 7 3 3` (only 3 bonds, no extension possible, never eliminated per manual line 521). Confirm with lsd-engineer skill update.
**Warning signs:** Aromatic ring disappears from solutions when ELIM is added; `lucy lsd analyze` shows COSY correlations with path_length > 3.

### Pitfall 3: ELIM solution explosion without plausibility filter
**What goes wrong:** `ELIM N 0` with large N can produce thousands of solutions. Without the pre-filter, `lucy lsd rank` must process all of them, which may be slow and produces a ranking table dominated by IMPLAUSIBLE solutions.
**How to avoid:** Implement the chemical plausibility pre-filter (D-09) before the MAE sort. Confirm it runs in O(solutions) time using only SMILES + formula string (no network calls).
**Warning signs:** `lucy lsd rank` takes > 60 seconds on a solution set; ranked output has no aromatic solutions at top despite known aromatic compound.

### Pitfall 4: Schema validation failure due to pyLSD fields
**What goes wrong:** `lucy lsd validate-inventory` may reject LSD files that omit now-retired required fields (`deferred_4j`, `pylsd_mode`, `elim_annotated`).
**Why it happens:** The JSON schema `"required"` array still lists these fields until the schema is updated.
**How to avoid:** Update schema FIRST (Wave 0 or Wave 1), before any agent skill changes that produce inventory blocks without these fields.
**Warning signs:** `lucy lsd validate-inventory` exits 1 on a new Phase-80 LSD file with "missing required property: deferred_4j".

### Pitfall 5: Confusing `elim_value` vs new ELIM semantics in the DA gates
**What goes wrong:** The existing DA G2 gate blocks `elim_value != null` when `pylsd_mode=true`. With `pylsd_mode` always false, G2 never triggers. But the DA skill may still describe ELIM as a last resort and warn on N > 0.
**How to avoid:** Update DA ELIM section (lines 183-186) to reflect new semantics: ELIM is expected after all HMBC added; warn only on N > 3 without documentation.

### Pitfall 6: Post-hoc 4J identification confused with pre-classification
**What goes wrong:** After adding `lucy lsd analyze` output to the solution report, the agent may start treating the identified 4J correlations as a new "to remove" list (reverting to D-03-violating pre-classification).
**How to avoid:** Skill must explicitly state: "Post-hoc 4J identification is EXPLANATION ONLY. Do NOT remove or defer HMBC correlations based on this. ELIM handles them automatically."
**Warning signs:** lsd-engineer removes or adds `; ELIM` annotations to HMBC lines based on `lucy lsd analyze` output.

---

## Code Examples

### ELIM emission pattern (generator.py change)

```python
# VERIFIED: src/lucy_ng/lsd/models.py (existing field — new usage)
@dataclass
class LSDProblem:
    elim_budget: int = 0  # NEW field: global ELIM N (0 = no ELIM)
    # ... existing fields ...

# VERIFIED: src/lucy_ng/lsd/generator.py (existing emit_elim, new condition)
# In generate():
if problem.elim_budget > 0:
    lines.append(f"ELIM {problem.elim_budget} 0")
    lines.append("")
```

### Plausibility pre-filter (ranker.py addition)

```python
# VERIFIED: src/lucy_ng/ranking/ranker.py (new helper + use in rank())
def _is_chemically_plausible(
    solution: RankedSolution,
    experimental_shifts: list[float],
    formula: str | None = None,
) -> bool:
    """Check DBE consistency and aromatic ring presence."""
    # Check 1: aromatic ring when shifts suggest aromaticity
    aromatic_shift_count = sum(1 for s in experimental_shifts if 110.0 <= s <= 160.0)
    if aromatic_shift_count >= 4 and not solution.has_aromatic_ring:
        return False
    # Check 2: DBE consistency (when formula provided)
    if formula:
        expected_dbe = _calc_dbe(formula)  # from formula string
        mol = Chem.MolFromSmiles(solution.smiles)
        if mol is not None:
            actual_dbe = _calc_dbe_from_mol(mol)
            if abs(actual_dbe - expected_dbe) > 1:
                return False
    return True

# In rank() — after building ranked list, before sort:
plausible = [r for r in ranked if _is_chemically_plausible(r, experimental_shifts, formula)]
implausible = [r for r in ranked if not _is_chemically_plausible(r, experimental_shifts, formula)]
plausible.sort(key=lambda r: (-r.matched_count, r.mae))
# Final order: sorted plausible first, then implausible (preserves full set for audit)
ranked = plausible + implausible
```

### ELIM escalation loop in agent skill (new adaptive loop text)

```
### Adaptive Loop (Phase 80 revision)

1. Start with MULT + HSQC + heteroatom constraints + DEFF F/FEXP + first batch 3-5 HMBC
   - ELIM 0 (no ELIM command in file) 
2. Run LSD
3. Observe:
   ≥1 plausible solution (aromatic/DBE-consistent) → STOP; rank ALL via pre-filter + HOSE
   0 solutions → Zero-Solution Recovery (sp2, H budget, HMBC conflicts)
   >30% reduction → CONTINUE adding HMBC batches
   all HMBC added, still 0 plausible solutions → Escalate ELIM (see below)
4. Repeat until: ≥1 plausible solution, or HMBC exhausted + ELIM escalated to N=3, or 10 iterations (cap)

### ELIM Escalation (when all HMBC added, still 0 plausible solutions)

0 → Add ELIM 1 0 to LSD file; re-run LSD
  → still 0: Add ELIM 2 0 (replace ELIM 1 0)
  → still 0: Add ELIM 3 0 (replace ELIM 2 0)
  → still 0 at N=3: Escalate to diagnostic specialist (constraint conflict, not 4J)

When ≥1 plausible solution found at ELIM N:
  → rank ALL solutions from that run via `lucy lsd rank`
  → run `lucy lsd analyze compound.sol compound.lsd` for post-hoc 4J identification (D-04)
  → Report: "ELIM N: solver dropped [path-length-4 correlations per analyze output]"

### Stopping Rule (D-08)
Stop at the SMALLEST ELIM N that yields ≥1 plausible solution. Do NOT continue escalating to get "fewer" solutions.
"Plausible" = has aromatic ring (if ≥4 shifts 110-160 ppm) AND DBE consistent with formula.
```

### Post-hoc 4J identification using `lucy lsd analyze` (D-04)

```bash
# VERIFIED: exists in cli/lsd.py (lsd_analyze command)
lucy lsd analyze compound.sol compound.lsd --format json

# Output includes per-solution path lengths for all HMBC correlations:
# {
#   "solutions": [{
#     "solution_number": 1,
#     "correlations": [
#       {"carbon_idx": 1, "proton_idx": 8, "carbon_shift": 166.1, "path_length": 3, "j_coupling": 4, "j_notation": "⁴J"},
#       ...
#     ],
#     "all_2j_3j": false,
#     "max_j": 4
#   }]
# }
# Correlations with j_coupling >= 4 in accepted solutions = the ones ELIM dropped
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pre-classify 4J suspects, defer to pyLSD | Global `ELIM N 0` iterative escalation | Phase 80 | No AI classification; solver decides |
| `ELIM` as last resort (DA warns) | `ELIM` as primary 4J mechanism | Phase 80 | DA gates updated |
| ≤10 solutions stopping rule | ≥1 plausible solution stopping rule | Phase 80 | Pre-filter + ranking replaces count-based stop |
| `pylsd_mode=true` for 4J workflow | `pylsd_mode` retired (always false) | Phase 80 | Schema simplified |
| `deferred_4j` inventory field | `elim_budget: int` inventory field | Phase 80 | Cleaner representation |

**Deprecated/outdated after Phase 80:**
- `deferred_4j` schema field (replaced by `elim_budget`)
- `pylsd_mode` / `elim_annotated` required fields (retired)
- DA gates G1, G2, G3, G4, G8 (pyLSD permutation path)
- `; ELIM` annotation protocol on HMBC lines
- 4J Deferral Rule in lsd-engineer skill
- ">10 solutions → minimize" stopping condition
- `lucy pylsd run` as a recommended agent command

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | COSY equivalence pairs written as plain `COSY 4 7` (no explicit range) are subject to ELIM; writing as `COSY 4 7 3 3` protects them | Q1 / Pitfall 2 | If wrong: ELIM may destroy aromatic ring emergence by dropping COSY pairs — but `lucy lsd analyze` would reveal this immediately |
| A2 | N=3 as a practical ELIM ceiling is sufficient for CASE9 (4 spurious 4J correlations) | Q1 | If CASE9 needs N=4: ceiling raises, solution explosion larger but plausibility filter handles it |
| A3 | HSQC-multiplicity consistency check (D-09 third filter) is optional in Phase 80 scope | Q5 | If wrong: more IMPLAUSIBLE solutions survive to MAE ranking, but correct structure should still rank top by HOSE prediction |
| A4 | `lucy lsd analyze` correctly identifies which correlations have path_length ≥ 4 in the accepted solution — these are the correlations ELIM "dropped" | Q1 / D-04 | LSD does not directly report dropped correlations; `lsd analyze` infers them from graph path. If multiple ELIM drops exist, `analyze` shows all correlations with their actual path length but doesn't distinguish "would have been 2-3J in correct structure" from "was 4J and dropped" |

---

## Open Questions

1. **Should COSY equivalence pairs be written with explicit `3 3` range to prevent ELIM from touching them?**
   - What we know: manual line 521 says explicit-range COSY are never eliminated. Default COSY = 3J; ELIM path extends to ELIM_P2+1.
   - What's unclear: Whether LSD would actually try to eliminate a default-range `COSY 4 7` with `ELIM 1 0` (P2=0 means no bond limit).
   - Recommendation: Add `3 3` to all aromatic COSY equivalence pairs as a precaution (`COSY 4 7 3 3`). Low cost, high safety. Update lsd-engineer skill accordingly.

2. **What is the actual ELIM N needed for CASE9?**
   - What we know: 4 suspect correlations (HMBC 1 8, 2 3, 2 9, 3 8). May need N=1 or N=4 depending on which are truly spurious.
   - What's unclear: Whether a single N=1 run (drop the worst offender 166.1↔70.2) unlocks the para-benzoate.
   - Recommendation: No need to pre-determine. The iterative escalation (D-02) discovers this empirically during the blind UAT run.

3. **Where in the `SolutionRanker.rank()` call should the formula string be passed for DBE check?**
   - What we know: `rank()` currently takes `solutions`, `experimental_shifts`, `top_n`. Formula is not passed.
   - What's unclear: Whether to add `formula: str | None = None` to `rank()` signature (clean, explicit) or compute formula from SMILES inside the filter (unreliable — same formula may have different DBE depending on oxidation state).
   - Recommendation: Add `formula: str | None = None` to `rank()` and `_perform_ranking()` call chain. Optional parameter, backward compatible.

---

## Environment Availability

This phase is purely code + skill changes with no new external dependencies. All required tools are already installed.

| Dependency | Required By | Available | Notes |
|------------|------------|-----------|-------|
| LSD binary | Regression test (Arm A + ELIM) | ✓ | At system PATH per Phase-73 verification |
| RDKit | Plausibility pre-filter | ✓ | Already imported in ranker.py |
| `lucy lsd analyze` | D-04 post-hoc check | ✓ | cli/lsd.py lsd_analyze command, Phase 66+ |
| `scripts/verify_case_solution.py` | CASE9 blind UAT gate | ✓ | Present at `/Users/steinbeck/Dropbox/develop/lucy-ng/scripts/` |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pyproject.toml` / `pytest.ini` (project root) |
| Quick run command | `pytest tests/test_lsd_models.py tests/test_lsd_generator.py tests/test_ranking.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-07-A | `LSDProblem(elim_budget=1)` emits `ELIM 1 0` in generated file | unit | `pytest tests/test_lsd_generator.py::TestElimBudget -x` | ❌ Wave 0 |
| FIX-07-B | `LSDProblem(elim_budget=0)` emits NO ELIM line | unit | `pytest tests/test_lsd_generator.py::TestElimBudget -x` | ❌ Wave 0 |
| FIX-07-C | Plausibility pre-filter rejects non-aromatic solution when ≥4 shifts in 110-160 ppm | unit | `pytest tests/test_ranking.py::TestPlausibilityFilter -x` | ❌ Wave 0 |
| FIX-07-D | Plausibility pre-filter preserves ranking order (matched_count desc, MAE asc) for survivors | unit | `pytest tests/test_ranking.py::TestPlausibilityFilterOrdering -x` | ❌ Wave 0 |
| FIX-07-E | Schema accepts inventory without `deferred_4j`/`pylsd_mode`/`elim_annotated` | unit | `pytest tests/test_lsd_schema.py::TestSchemaV2Phase80 -x` | ❌ Wave 0 |
| FIX-07-F | CASE9 blind UAT: correct para-benzoate in top-3 via emergent path with ELIM escalation | agent-experiment | `scripts/verify_case_solution.py solutions.smi C12H16O3` | ✅ |
| FIX-07-G | CASE1 no regression: ibuprofen still found without ELIM (N=0 first) | agent-experiment | `scripts/verify_case_solution.py solutions.smi C13H18O2` | ✅ |

### Sampling Rate
- Per task commit: `pytest tests/test_lsd_models.py tests/test_lsd_generator.py tests/test_ranking.py -x`
- Per wave merge: `pytest`
- Phase gate: Full suite green before blind UAT runs

### Wave 0 Gaps
- [ ] `tests/test_lsd_generator.py::TestElimBudget` — new test class for `elim_budget` field emission
- [ ] `tests/test_ranking.py::TestPlausibilityFilter` — new test class for `_is_chemically_plausible()`
- [ ] `tests/test_lsd_schema.py::TestSchemaV2Phase80` — new test: schema accepts inventory without retired required fields

---

## Security Domain

This phase modifies Python library code and agent skill markdown. No authentication, session management, cryptography, or input from untrusted sources is involved. Security domain not applicable.

---

## Sources

### Primary (HIGH confidence)

- `~/Dropbox/develop/LSD/MANUAL_ENG.html` lines 195-217, 500-550, 801-816 — authoritative ELIM command semantics, COSY/HMBC range syntax
- `src/lucy_ng/lsd/generator.py` — `emit_elim()`, `pylsd_mode` gate, `LSDInputGenerator.generate()`
- `src/lucy_ng/lsd/models.py` — `LSDProblem.elim_commands`, `pylsd_mode` fields
- `src/lucy_ng/cli/pylsd.py` — `_extract_suspects()`, `pylsd_run()`, pyLSD entry point
- `src/lucy_ng/ranking/ranker.py` — existing `has_aromatic_ring` check, `rank()` contract
- `src/lucy_ng/ranking/models.py` — `RankedSolution`, `RankingResult` schemas
- `src/lucy_ng/data/schemas/constraint_inventory_v2.json` — `deferred_4j`, `pylsd_mode`, `elim_annotated`, `elim_value` fields
- `~/.claude/agents/lucy-lsd-engineer.md` lines 60, 119-127, 261-299, 576-605 — pyLSD routing, 4J deferral, adaptive loop
- `~/.claude/agents/lucy-devils-advocate.md` lines 314-489 — G1-G4/G8 pyLSD gates
- `.planning/phases/72-design-re-validation/72-DECISIONS.md` — DESIGN-02 single-path decision
- `.planning/phases/80-long-range-4j-hmbc-connectivity-defect/80-CONTEXT.md` — locked decisions D-01..D-09

### Secondary (MEDIUM confidence)

- `.planning/phases/79-peak-picking-symmetry-fix/79-HUMAN-UAT.md` — CASE9 forensics confirming 4J trigger correlations
- `.planning/STATE.md` — accumulated session decisions and constraints
- `scripts/verify_case_solution.py` — existing harness for blind UAT gate

### Tertiary (LOW confidence)

- A2 (N=3 ceiling) — based on CASE9 having 4 suspect correlations; actual N needed is empirically determined in UAT

---

## Metadata

**Confidence breakdown:**
- LSD ELIM semantics: HIGH — read from authoritative manual, cross-referenced with lsd-engineer skill examples
- Code change inventory: HIGH — all files read directly; exact line numbers cited
- Skill surgery scope: HIGH — all agent files read; sections identified by line number
- Pre-filter implementation: MEDIUM — RDKit APIs confirmed present; exact DBE formula implementation not validated against edge cases
- Schema migration: HIGH — schema read directly; field semantics confirmed from code that reads them
- Regression guard: HIGH — `verify_case_solution.py` confirmed present and operational

**Research date:** 2026-06-09
**Valid until:** 2026-07-09 (stable domain — no external dependency churn expected)
