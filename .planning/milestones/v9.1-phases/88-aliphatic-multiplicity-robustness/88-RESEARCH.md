# Phase 88: Aliphatic Multiplicity Robustness - Research

**Researched:** 2026-06-25
**Domain:** CASE skill-level workflow hardening (NMR structure elucidation team agents) + one minimal CLI detector
**Confidence:** HIGH (all findings verified against the in-repo source and skill files this session)

## Summary

Phase 88 fixes a **search-space-coverage** defect, not an algorithm. When aliphatic CH/CH₂/CH₃ multiplicity is not hard-determinable (non-multiplicity-edited HSQC and/or phase-unreliable APT/DEPT), the lsd-engineer currently hard-codes one multiplicity model (CASE4: the iPr model `3×CH₃+CH`), so the correct constitution (CASE4 truth: `2×CH₃+ethyl`) is never in the solution set and no downstream net (rank override, MAE>4 guardrail, identity gate) can recover it. The fix runs **each viable whole-molecule multiplicity family as a separate, fully-constrained LSD run**, **unions** the per-family `solutions.smi`, ranks across the union, and **gates acceptance on family coverage** independent of MAE. It also makes the nmr-chemist emit a deterministic `[MULTIPLICITY-AMBIGUOUS]` signal and makes a devils-advocate "evidence FOR model X" flag a binding mandatory-search item.

The work is **almost entirely prompt edits** to five skill files (`lucy-nmr-chemist.md`, `lucy-lsd-engineer.md`, `lucy-devils-advocate.md`, `case.md`, plus the two references `loop-patterns.md` / `advisory-templates.md`) — they are repo `.claude/` files symlinked into `~/.claude`, so editing them changes the live skill but a **fresh Claude Code session is required to reload**, and functional validation is the blind CASE4 re-run (UAT-01 / Phase 89), NOT unit tests in this session.

The **one piece of real Python** worth adding is a deterministic "is this HSQC multiplicity-edited?" detector. The 1D picker already computes exactly the signal needed (`np.min(data) < -threshold*max_abs`, surfaced as `negative_detected` in `lucy pick 1d --format json`), but `lucy pick hsqc` does NOT compute or report it (it calls `PeakPicker2D.pick_peaks` with the default `detect_negative=False` and never inspects negatives). Porting that one check into `pick hsqc` as a `multiplicity_edited` JSON field gives the nmr-chemist a deterministic trigger and is unit-testable with the existing `CliRunner` + in-repo HSQC fixture — that is the single testable seam.

**Primary recommendation:** Edit the five skill files to implement D-01…D-06, and add ONE small CLI enhancement (`multiplicity_edited` flag on `lucy pick hsqc`) as the deterministic D-05 trigger. Union ranking = concatenate per-family `solutions.smi` (with explicit SMILES dedup — the parser does NOT dedup) and run a single `lucy lsd rank`. Cap families at 3 (planner discretion ≤3–4). Validate by blind CASE4 re-run, not unit tests, except for the new CLI flag and an optional family-enumeration helper.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01 (MULT-01):** When aliphatic multiplicity is not hard-determinable, the lsd-engineer runs **each viable multiplicity family as a SEPARATE, fully-constrained LSD run in its own iteration sub-directory** (e.g. `analysis/iteration_NN_iPr/`, `analysis/iteration_NN_ethyl/`), then **unions the per-family solution sets and ranks across the union**. NOT a single relaxed-MULT run; NOT sequential-with-fallback (the CASE4 failure mode). Each family is searched with its own correct MULT constraints.
- **D-02 (MULT-01):** "Viable family" = a **chemically sensible whole-molecule aliphatic partition** of the ambiguous aliphatic carbons + their attached protons that is **consistent with the molecular formula / H-count / DBE** (e.g. `3×CH₃+CH` vs `2×CH₃+CH₂+CH₂`). Enumerate at the **whole-molecule** level (not per-center cross-product).
- **D-03 (MULT-01):** **Hard cap** on the number of families searched (planner's discretion, target ≤ 3–4). If more than the cap are formally valid, rank by prior chemical plausibility, search the top-capped set, and **document the truncation explicitly** in CASE-PROGRESS.md (no silent drop).
- **D-04 (MULT-02):** A **deterministic coverage gate runs before the run may accept** — independent of MAE. The nmr-chemist's enumerated "viable families" list MUST be **fully covered** by the families actually searched. **If ≥2 viable families were identified but not all were searched, the run does NOT accept** — it reopens and searches the missing family(ies). This is a checklist/coverage check, NOT an MAE or plausibility threshold.
- **D-05 (MULT-04 + MULT-03):** The nmr-chemist flags **"multiplicity-ambiguous" deterministically/programmatically**: when HSQC is **non-multiplicity-edited** (no negative cross-peaks — reuse the existing negative-intensity / DEPT-negative detection path) **AND/OR** APT/DEPT is **phase-unreliable/inconsistent**. On that condition it emits an explicit **`[MULTIPLICITY-AMBIGUOUS]` signal listing the viable families** (MULT-04), which the lsd-engineer acts on deterministically (→ D-01).
- **D-06 (MULT-03):** A devils-advocate **"evidence FOR model X"** multiplicity flag becomes a **MANDATORY search item**: model X MUST enter the search space. It **cannot be dismissed by the convergence narrative**. The flag is closeable ONLY by showing model X was actually searched — not by argument.

### Claude's Discretion
- Exact family cap number (≤ 3–4 target); the precise naming of iteration sub-directories.
- The exact token/format of the `[MULTIPLICITY-AMBIGUOUS]` message and the coverage-gate checklist representation in CASE-PROGRESS.md.
- Whether the union ranking concatenates per-family `solutions.smi` files and runs one `lucy lsd rank`, or ranks per-family then merges — as long as ranking is across the union (D-01).
- How exactly per-family MULT constraints are derived (lsd-engineer construction detail), provided each family is fully constrained.

### Deferred Ideas (OUT OF SCOPE)
- Broadening parallel-family search to **non-aliphatic** multiplicity ambiguities (exchangeable/heteroatom multiplicity).
- A 13C-prediction model that separates iPr-methine from ethyl-CH₂ strongly enough to penalize the wrong class by MAE (improving the predictor is a separate concern; this phase fixes coverage, not ranking discrimination).
- Do NOT propose changes to the LSD solver, ranking algorithm, or 13C predictor.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MULT-01 | Search ALL viable multiplicity families rather than hard-coding one (iPr-path AND ethyl-path) | RQ2 (per-family runs + union via concatenated `solutions.smi` → single `lucy lsd rank`), RQ3 (two MULT blocks in lsd-engineer), RQ4 (whole-molecule partition enumeration). Edits: `lucy-lsd-engineer.md` §1 MULT + §3 File Org + workflow step 11. |
| MULT-02 | MAE-independent guardrail: ≥2 viable families exist but only one searched → do not accept; reopen | RQ5 (new pre-accept coverage gate in `case.md`, sits beside Pattern 5 / identity_gate; tracked via CASE-PROGRESS.md searched-families set). New loop pattern in `loop-patterns.md` + reopen advisory in `advisory-templates.md`. |
| MULT-03 | A DA "evidence FOR model X" flag forces model X into the search; cannot be narrated away | RQ6 (new binding DA multiplicity gate modeled on G-IDENT; flag recorded as mandatory-search item the coverage gate enforces). Edit `lucy-devils-advocate.md`. |
| MULT-04 | nmr-chemist emits explicit "multiplicity-ambiguous → enumerate families" signal when HSQC not multiplicity-edited | RQ1 (deterministic detector: port `negative_detected` logic into `lucy pick hsqc` as `multiplicity_edited`; nmr-chemist emits `[MULTIPLICITY-AMBIGUOUS]`). Edit `lucy-nmr-chemist.md` + `pick.py`. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Detect "HSQC is multiplicity-edited?" | CLI / Python (`lucy pick hsqc`) | nmr-chemist agent | Deterministic numeric check (negative cross-peaks) belongs in code, not LLM judgment (D-05 = "programmatically, not by judgment"). The agent consumes the boolean. |
| Emit `[MULTIPLICITY-AMBIGUOUS]` + viable families | nmr-chemist agent (skill) | — | Chemical reasoning (which partitions are valid for this formula/DBE) is the chemist's domain; enumeration uses data it already holds. |
| Per-family MULT construction + separate LSD runs + union | lsd-engineer agent (skill) | LSD runner (`lucy lsd run`, unchanged) | Constraint-file authoring is lsd-engineer's exclusive job; runner/ranker code is reused unchanged. |
| "evidence FOR model X" binding flag | devils-advocate agent (skill) | — | DA owns pre-run gates and post-solution review; this is a new binding gate. |
| Pre-accept coverage gate + reopen orchestration | orchestrator (`case.md` + references) | CASE-PROGRESS.md (state ledger) | Accept/reopen decisions and cross-agent state tracking are the coordinator's role; mirrors the existing Pattern-5 reopen and identity_gate. |

## Standard Stack

This phase writes **no new runtime libraries**. It edits Markdown skill prompts and (optionally) one Python CLI command using libraries already vendored in the project.

### Core (already in the repo — reused, not added)
| Library / Module | Purpose | Why used here |
|---|---|---|
| `click` | CLI framework for `lucy pick hsqc` | The `multiplicity_edited` flag is a small addition to existing `pick_hsqc`. [VERIFIED: src/lucy_ng/cli/pick.py] |
| `nmrglue` (`ng.peakpick.pick`) | 2D peak picking incl. negative peaks | `PeakPicker2D.pick_peaks(detect_negative=True)` already supports negative cross-peak detection. [VERIFIED: src/lucy_ng/processing/peak_picker_2d.py:160-187] |
| `numpy` | `np.min(data) < -threshold*max_abs` negative-presence test | The exact detector pattern already lives in `pick_1d`. [VERIFIED: src/lucy_ng/cli/pick.py:59-60] |
| `lucy lsd run` (`LSDRunner.run_file`) | Produces `compound.sol` + `solutions.smi` per run | Reused unchanged; running it in two sub-dirs yields two independent `solutions.smi`. [VERIFIED: src/lucy_ng/lsd/runner.py:228-256, 31] |
| `lucy lsd rank` (`_perform_ranking` → `LSDOutputParser.parse_smiles_file`) | Ranks a single `solutions.smi` (one SMILES/line) | Union input = concatenated per-family `.smi`. [VERIFIED: src/lucy_ng/cli/lsd.py:578-707, parser.py:37-68] |

**Installation:** None. No `npm`/`pip` install. (Package legitimacy audit therefore N/A — no external packages added.)

## Package Legitimacy Audit

**N/A — this phase installs no external packages.** All changes are prompt edits to repo `.claude/` skill files plus an optional enhancement to an existing in-repo CLI command using already-vendored libraries (`click`, `nmrglue`, `numpy`). No registry lookups or slopcheck required.

## Architecture Patterns

### System Architecture Diagram (the multiplicity-ambiguous branch)

```
  NMR data (13C, DEPT/APT, HSQC, HMBC, COSY)
        │
        ▼
  ┌───────────────────────────────────────────────┐
  │ nmr-chemist: peak pick + multiplicity assess    │
  │  • lucy pick hsqc → multiplicity_edited? (NEW)  │◄── deterministic detector
  │  • APT/DEPT phase reliable?                      │    (negative cross-peaks)
  └───────────────┬───────────────────────────────┘
                  │
        ┌─────────┴──────────┐
   edited &              non-edited HSQC
   reliable APT           AND/OR phase-unreliable APT
        │                      │
        │                      ▼
        │            [MULTIPLICITY-AMBIGUOUS] + viable families list
        │            (whole-molecule CH3/CH2/CH partitions, ≤cap)
        │                      │
        ▼                      ▼
  single LSD run      lsd-engineer: ONE LSD run PER FAMILY
  (existing flow)      iteration_NN_<family>/  (own MULT block each)
        │                      │
        │              ┌───────┴────────┐
        │         solutions.smi    solutions.smi   ... (per family)
        │              └───────┬────────┘
        │                      ▼
        │            UNION = concat + dedup SMILES → one file
        │                      │
        └──────────┬───────────┘
                   ▼
         lucy lsd rank  (across the union)
                   │
                   ▼
   ┌──────────────────────────────────────────────────┐
   │ orchestrator PRE-ACCEPT COVERAGE GATE (NEW, D-04)  │
   │  viable_families ⊆ searched_families ?             │
   │   • DA "evidence FOR model X" ∈ searched ? (D-06)  │
   └───────┬────────────────────────────┬─────────────┘
       all covered                  missing family
           │                            │
           ▼                            ▼
     identity_gate (G-IDENT)      REOPEN → search missing family
           │                      (back to lsd-engineer)
           ▼
     present_results
```

### Established workflow patterns this phase extends

1. **Per-iteration sub-directory convention** (`analysis/iteration_NN/compound.lsd|.sol|solutions.smi`). D-01's per-family dirs (`iteration_NN_iPr/`, `iteration_NN_ethyl/`) are a small extension. [VERIFIED: lucy-lsd-engineer.md §3 File Organization]

2. **PUSH message protocol** — the orchestrator wakes on each structured teammate reply and pushes the next `[BEGIN]`. A new `[MULTIPLICITY-AMBIGUOUS]` signal slots into `monitor_progress` exactly like `[SETUP-COMPLETE]`. [VERIFIED: case.md:265-310]

3. **Reopen-the-run gate precedent** — Pattern 5 "Quality Convergence Failure" already reopens a converged run (`solution_count ≤ 20` looks like success but is wrong); the coverage gate is the analogous "looks converged but a family was never searched" reopen, but **coverage-triggered, not MAE-triggered**. [VERIFIED: loop-patterns.md:60-89, case.md:449-454]

4. **Post-solution binding/advisory gate precedent** — `G-IDENT` (devils-advocate, post-solution, modeled in case.md `identity_gate` step) is the structural template for the new DA multiplicity gate. The multiplicity gate differs: it is **PRE-accept and BINDING** (cannot be narrated away), whereas G-IDENT is advisory. [VERIFIED: lucy-devils-advocate.md:416-455, case.md:632-655]

### Anti-Patterns to Avoid
- **Single relaxed-MULT run** (e.g. leaving CH/CH₂/CH₃ unconstrained and hoping LSD enumerates families): D-01 explicitly rejects this — explosion risk and LSD may not enumerate the intended families cleanly.
- **Sequential-with-fallback** ("search iPr; if it looks good, stop"): this IS the CASE4 failure mode. The leading family scored MAE 1.75 "PLAUSIBLE" and silently excluded the truth.
- **Per-center cross-product enumeration:** D-02 requires whole-molecule partitions, not the Cartesian product of per-carbon multiplicity guesses (explodes faster, harder to justify chemically).
- **Closing a DA multiplicity flag by argument:** D-06 forbids it. Only "model X was actually searched" closes it.
- **Hand-coding the negative-detection threshold in the prompt:** put the deterministic check in `lucy pick hsqc` (code), per D-05 "programmatically, not by judgment."

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| "Is HSQC multiplicity-edited?" | A new bespoke 2D-negative detector or an LLM eyeball judgment | Port the existing `pick_1d` pattern (`np.min(data) < -threshold*max_abs`; `PeakPicker2D.pick_peaks(detect_negative=True)`) into `pick hsqc` as `multiplicity_edited` | The exact logic already exists and is tested for 1D DEPT (`negative_detected`); 2D negative picking already supported. [VERIFIED: cli/pick.py:59-60, peak_picker_2d.py:160-187] |
| Union of per-family solutions | A new merge/rank module | Concatenate per-family `solutions.smi` (dedup SMILES) → one `lucy lsd rank` | `lsd rank` already ranks any one-SMILES-per-line file; the parser ignores blanks/comments. [VERIFIED: parser.py:53-67] |
| Running each family | A new multi-run orchestrator in Python | Reuse `lucy lsd run` once per sub-dir | Runner already writes `solutions.smi` to the output dir (defaults to input file's parent). [VERIFIED: runner.py:228-256] |
| Two MULT blocks for two families | A code generator | The lsd-engineer already authors MULT lines by hand from peak assignments | The CASE workflow writes native LSD files in the skill, not via the Python `LSDInputGenerator` (which builds MULT from a `dept_result`). [VERIFIED: lucy-lsd-engineer.md §1, generator.py:303-329] |

**Key insight:** The defect is a *coverage* gap, not a missing capability. Every mechanism needed (per-run dirs, `lsd run`, `lsd rank`, negative detection) already exists. The work is wiring the agents to *use* them across multiple families and adding ONE deterministic boolean so the chemist's "ambiguous" decision is not a judgment call.

## Runtime State Inventory

> This is a skill-prompt + CLI-flag phase, not a rename/migration. No stored data, live-service config, OS-registered state, secrets, or build artifacts carry a renamed string. The only "state" touched at runtime is per-run analysis files under the (out-of-repo) compound data directory.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no DB keys/collections/IDs change. The reference SQLite DB (HOSE/dereplication) is read-only and untouched. | None |
| Live service config | None — CASE runs are local; no external service config. | None |
| OS-registered state | None. | None |
| Secrets / env vars | None — `CLAUDE_CODE_SUBAGENT_MODEL` must remain `inherit` (per MEMORY); not changed by this phase. | None (verify it is still `inherit`) |
| Build artifacts / installed packages | The `lucy` CLI is an editable install; if `pick.py` changes, no rebuild needed for editable installs, but a `hatch build` would be required before any wheel ships. Skill files are symlinks → **a fresh Claude Code session is required to reload edited agents.** | Fresh session before blind UAT; reinstall only if shipping a wheel |

**Nothing found in categories stored-data / live-config / OS-state / secrets — verified by inspecting the change surface (5 Markdown skill files + 1 CLI command).**

## Common Pitfalls

### Pitfall 1: Union `solutions.smi` contains duplicate SMILES (no dedup in parser)
**What goes wrong:** Two families can independently yield the same SMILES; the same structure then appears twice in the ranking, distorting counts and rank positions.
**Why it happens:** `LSDOutputParser.parse_smiles_file` appends every valid line as a distinct `LSDSolution` with no de-duplication. [VERIFIED: parser.py:53-67]
**How to avoid:** When building the union file, dedup by **canonicalized** SMILES (or at minimum exact-string dedup) before `lucy lsd rank`. Document this in the lsd-engineer skill as a required step.
**Warning signs:** `total_solutions` in the rank JSON exceeds the sum of unique structures; identical SMILES at adjacent ranks.

### Pitfall 2: lsd-engineer's existing "≤20 → convert; >50 → skip conversion" rule can suppress a family's `solutions.smi`
**What goes wrong:** The anti-stall rule says don't convert large solution sets to `solutions.smi`. If one family explodes, its `.smi` may never be produced, silently dropping it from the union — re-introducing a coverage gap.
**Why it happens:** Conversion is decoupled from the completion signal for performance. [VERIFIED: lucy-lsd-engineer.md role block, lines 28-45]
**How to avoid:** In the multiplicity-ambiguous branch, each viable family must yield a `solutions.smi` (or be explicitly recorded as "searched, N solutions, not converted because over-constrained/exploded" so the coverage gate still counts it as *searched*). Coverage is about *searched*, not *ranked*.
**Warning signs:** A family in the viable list has no `solutions.smi` and no documented reason.

### Pitfall 3: `multiplicity_edited=false` is necessary but not sufficient for ambiguity
**What goes wrong:** Treating "HSQC not edited" as the only trigger misses the case where HSQC *is* edited but APT/DEPT phase is unreliable; and conversely a non-edited HSQC where DEPT-135 is clean is NOT ambiguous.
**Why it happens:** D-05 is an AND/OR: ambiguity = non-edited HSQC **AND/OR** phase-unreliable APT/DEPT. The boolean is one input.
**How to avoid:** nmr-chemist combines the `multiplicity_edited` boolean with its existing DEPT/APT reliability assessment (Section 7 "Multiplicity Conflicts") before emitting `[MULTIPLICITY-AMBIGUOUS]`. The CLI flag removes judgment from the HSQC half only.
**Warning signs:** Ambiguity declared on every compound (over-firing) or never (under-firing).

### Pitfall 4: Coverage gate fires before ranking exists, or never fires because state isn't tracked
**What goes wrong:** The gate can't tell "all families searched" without a tracked `searched_families` set; or it fires at the wrong lifecycle point.
**Why it happens:** CASE-PROGRESS.md is coordinator-written; the searched-families set and the viable-families list must both be recorded there as the run proceeds.
**How to avoid:** Mirror the identity_gate lifecycle — the coverage gate runs **after** the union is ranked (`final_results.md` / pre-`identity_gate`), reading `viable_families` (from `[MULTIPLICITY-AMBIGUOUS]`) and `searched_families` (from each family's `[ITERATION-COMPLETE]`) from CASE-PROGRESS.md. Guard: only fires when a `[MULTIPLICITY-AMBIGUOUS]` record exists.
**Warning signs:** Gate output references families that were never enumerated; or accept happens with `viable ⊄ searched`.

### Pitfall 5: A DA "evidence FOR model X" flag is recorded but not made binding
**What goes wrong:** Exactly the CASE4 defeat — DA flagged HMBC 11→13 as "evidence for ethyl," but the engineer/analyst re-explained it as gem-dimethyl coupling and never searched ethyl.
**Why it happens:** Today there is **no DA multiplicity gate at all** and no place that records a flag as a mandatory-search item.
**How to avoid:** Add a DA gate that emits a structured `[MULT-EVIDENCE-FOR] model=<X>` message; the coordinator writes it into the `searched_families` *requirement* set, and the coverage gate treats `model X ∈ searched_families` as mandatory (closeable only by an actual `iteration_NN_X/` run, not by narrative).
**Warning signs:** `final_results.md` contains a sentence rationalizing away a multiplicity correlation; no `iteration_NN_<flagged-model>/` directory exists.

## Code Examples

### Deterministic HSQC multiplicity-edited detector (the ONE code change, D-05/MULT-04)
The pattern already proven in `pick_1d` — port it into `pick_hsqc`:
```python
# Source: src/lucy_ng/cli/pick.py:58-60 (existing pick_1d logic, to be mirrored in pick_hsqc)
effective_threshold = 0.05
max_abs = float(np.max(np.abs(spectrum.data)))
multiplicity_edited = bool(np.min(spectrum.data) < -effective_threshold * max_abs)
# A multiplicity-edited HSQC has phased CH2 cross-peaks of OPPOSITE sign → genuine
# negative intensity well below the noise floor. No negatives ⇒ NOT edited ⇒ sign-ambiguous.
```
Surface it in the `pick hsqc --format json` output as a new field, e.g. `"multiplicity_edited": false`, alongside the existing `count`/`peaks`. The nmr-chemist reads this boolean instead of eyeballing the spectrum. [VERIFIED: cli/pick.py:97-112 shows where the JSON dict is built for pick_1d; pick_hsqc JSON dict at cli/pick.py:195-208]

### Union ranking (D-01 discretion — concatenate + dedup + single rank)
```bash
# Each family already produced its own solutions.smi via `lucy lsd run`:
#   analysis/iteration_03_iPr/solutions.smi
#   analysis/iteration_03_ethyl/solutions.smi
# Build a deduped union (exact-string dedup shown; prefer canonical-SMILES dedup):
sort -u analysis/iteration_03_iPr/solutions.smi analysis/iteration_03_ethyl/solutions.smi \
  > analysis/union_solutions.smi
# Rank across the union with ONE call (reuses the shared DB-first predictor):
lucy lsd rank analysis/union_solutions.smi --shifts "<13C shift list>" --format json
```
`lucy lsd rank` accepts any one-SMILES-per-line file; the parser skips blanks/comments and indexes 1..N. [VERIFIED: cli/lsd.py:578-707, parser.py:53-67]

### Two MULT blocks for the same skeleton (D-01/D-03, illustrative — lsd-engineer authors by hand)
```
; --- Family A: isopropyl model (3×CH3 + CH) ---
MULT 11 C 3 3    ; CH3
MULT 12 C 3 3    ; CH3
MULT 13 C 3 3    ; CH3
MULT 14 C 3 1    ; CH  (methine)

; --- Family B: ethyl + gem-dimethyl model (2×CH3 + CH2 + CH2 / per the valid partition) ---
MULT 11 C 3 3    ; CH3
MULT 12 C 3 3    ; CH3
MULT 13 C 3 2    ; CH2
MULT 14 C 3 2    ; CH2
```
Each family is a **separate, fully-constrained** `compound.lsd` in its own `iteration_NN_<family>/` dir; all other constraints (HSQC, HMBC, ring exclusion DEFF F1/F2/FEXP, BOND C=O) are identical and copied forward per the existing "read previous, never reconstruct" rule. [VERIFIED: lucy-lsd-engineer.md §1 MULT table lines 64-71, file-org §3]

## State of the Art

| Old Approach (current behavior) | New Approach (this phase) | Impact |
|---|---|---|
| lsd-engineer hard-codes ONE multiplicity model when ambiguous | Search EVERY viable family in parallel; union + rank | Truth stays reachable (CASE4 fix) |
| Multiplicity ambiguity judged by the chemist's eye | Deterministic `multiplicity_edited` boolean from `lucy pick hsqc` | Removes the human-judgment failure (D-05) |
| Accept gated only on MAE/plausibility (Pattern 5) | Additional MAE-INDEPENDENT coverage gate | Catches "wrong class scored MAE 1.75 PLAUSIBLE" (the silent-guardrail failure) |
| DA "evidence FOR X" is an advisory note that can be rationalized away | DA flag becomes a binding mandatory-search item | Closes the CASE4 HMBC-11→13 defeat |

**Deprecated/outdated:** Nothing removed. All edits are additive (new branch, new gate, new boolean) and must not regress the existing single-family flow when multiplicity IS hard-determinable.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A multiplicity-edited HSQC reliably produces negative (opposite-sign) CH₂ cross-peaks detectable by `np.min(data) < -0.05*max_abs`, the same way DEPT-135 does in `pick_1d`. | Code Examples, RQ1 | If a particular edited HSQC has very weak CH₂ negatives below 5% of max, the detector could mis-report "not edited" → over-firing ambiguity (safe direction: searches more families). False-negative-edited is the conservative error. Threshold may need tuning on real HSQC data. |
| A2 | Concatenating per-family `solutions.smi` and running one `lucy lsd rank` is an acceptable union-ranking implementation (vs. rank-per-family-then-merge). | RQ2 | Low — D-01 explicitly permits either, as long as ranking is across the union. Dedup (Pitfall 1) is the real requirement. |
| A3 | The whole-molecule family enumeration can be performed by the nmr-chemist agent from data it already has (carbon count, per-carbon H from HSQC, formula, DBE) without new Python. | RQ4 | Low–medium — if enumeration proves error-prone for the agent, a small `lucy` helper (see Validation Architecture) becomes the safer seam; planner may choose to add it. |
| A4 | A family cap of 3 (≤3–4 target) is sufficient for realistic aliphatic ambiguities (iPr vs ethyl vs n-propyl-type partitions). | RQ4/D-03 | Low — if >3 are genuinely valid, D-03 requires ranking by plausibility + documenting truncation, which is the designed behavior. |
| A5 | The blind CASE4 re-run (Phase 89 / UAT-01) is the binding functional validation; this session's edits cannot be self-tested because a fresh session is required to reload agents. | Validation Architecture | Low — explicitly stated in CONTEXT/CLAUDE.md. |

## Open Questions

1. **Exact `multiplicity_edited` threshold and where it lives.**
   - What we know: `pick_1d` uses `0.05*max_abs`; 2D negative picking exists.
   - What's unclear: whether 0.05 is the right fraction for HSQC CH₂ negatives across spectrometers, and whether to also expose a count of negative cross-peaks (more informative than a bare boolean).
   - Recommendation: implement the boolean with the proven 0.05 fraction AND include `negative_crosspeak_count` in the JSON so the chemist (and tests) can sanity-check; tune only if a real edited HSQC mis-reports.

2. **Where the family-enumeration logic should live (agent prompt vs. small CLI helper).**
   - What we know: the agent has all inputs; D-02 wants whole-molecule partitions consistent with formula/H/DBE.
   - What's unclear: whether the agent can reliably enumerate integer partitions of the ambiguous aliphatic H-budget under a cap.
   - Recommendation: start with agent-prompt enumeration (cheaper, fewer moving parts); if the planner wants determinism, add a tiny pure-function helper (`enumerate_aliphatic_families`) — it is unit-testable in isolation (see Validation Architecture) and is the strongest testable seam in the phase.

3. **Coverage-gate state representation in CASE-PROGRESS.md.**
   - What we know: CASE-PROGRESS.md is coordinator-written; identity_gate already adds a `### Devils-Advocate (G-IDENT post-solution)` entry.
   - What's unclear: exact section/field names for `viable_families`, `searched_families`, and DA mandatory-search items.
   - Recommendation: add a `## Multiplicity Coverage` section (viable list, searched list, DA-mandated models, gate verdict). Defer exact wording to the planner (Claude's Discretion per D-03/D-05).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| LSD + outlsd on PATH | Any per-family `lucy lsd run` (and the blind CASE4 UAT) | Required for runtime; not needed to author skill edits | per `lucy lsd check` | None — UAT cannot run without it (Phase 89 concern, not this phase) |
| Reference SQLite DB (`data/reference/lucy-ng-derep.db`) | `lucy lsd rank` 13C prediction | Required for runtime ranking | ~2.8 GB | None for ranking; not needed to author edits |
| `pytest` / `click.testing.CliRunner` | Unit-testing the new `pick hsqc` flag + optional enumeration helper | ✓ (dev env) | per pyproject | None needed |
| `data/Ibuprofen/6` (in-repo HSQC) | Fixture for the `pick hsqc` CLI test | ✓ (in repo) | — | `sample_spectrum_2d` conftest fixture |

**Missing dependencies with no fallback:** LSD/outlsd + reference DB are required for the **blind CASE4 UAT (Phase 89)**, not for authoring/unit-testing this phase's changes.
**Missing dependencies with fallback:** None block this phase's deliverables.

## Validation Architecture

> nyquist_validation is not disabled in `.planning/config.json` (key absent → treated as enabled). The CASE-skill behavior changes are validated by a **blind CASE4 re-run (UAT-01, Phase 89)**, NOT by unit tests. However, two **testable code seams** exist and SHOULD be unit-tested in this phase.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (with `click.testing.CliRunner` for CLI) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `addopts="-v --tb=short"`) [VERIFIED] |
| Quick run command | `pytest tests/test_cli_pick.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MULT-04 | `lucy pick hsqc --format json` reports `multiplicity_edited: true` on an edited HSQC and `false` on a non-edited one | unit (CLI) | `pytest tests/test_cli_pick.py -k multiplicity_edited -x` | ❌ Wave 0 (add to existing `tests/test_cli_pick.py`) |
| MULT-01 | (optional) `enumerate_aliphatic_families(formula, h_on_carbon, cap)` returns the valid whole-molecule partitions (iPr & ethyl present for the CASE4-shaped input) under the cap | unit (pure fn) | `pytest tests/test_multiplicity_families.py -x` | ❌ Wave 0 (only if helper is added per Open Q2) |
| MULT-01/02/03 | Per-family search + union + coverage gate + binding DA flag | **blind UAT** (skill behavior — NOT unit-testable this session) | Phase 89 blind CASE4 re-run; truth `2×CH₃+ethyl` constitution appears in the solution set | N/A (agent prompts) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_cli_pick.py -x` (only when `pick.py` changed); skill-only commits run no new tests.
- **Per wave merge:** `pytest` (full suite green — current baseline ~1054 passing).
- **Phase gate:** Full suite green; skill edits reviewed for D-01…D-06 coverage. Functional acceptance deferred to Phase 89 blind UAT.

### Wave 0 Gaps
- [ ] `tests/test_cli_pick.py` — add `test_pick_hsqc_multiplicity_edited_true` (edited HSQC fixture → `multiplicity_edited: True`) and `test_pick_hsqc_not_multiplicity_edited` (non-edited → `False`). Mirror existing `test_pick_1d_dept135_json_negative` / `test_pick_1d_c13_no_negative` (which assert `negative_detected`). Needs one in-repo HSQC dir with negatives and one without; if none exists, synthesize a `Spectrum2D` fixture (extend `sample_spectrum_2d`) with/without negative cross-peaks.
- [ ] (Conditional, Open Q2) `tests/test_multiplicity_families.py` — if the enumeration helper is added: assert the CASE4-shaped input yields both the iPr and ethyl partitions and respects the cap.
- [ ] No new framework install — pytest + CliRunner already present.

## Security Domain

> `security_enforcement` is not configured in `.planning/config.json`. This phase performs no network I/O, no auth, no untrusted input parsing beyond NMR spectra already handled by the existing readers, and adds no external packages. The only new code is a numeric `np.min`/`np.max` check on already-loaded spectrum data.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | minimal | Spectrum data is read by existing `BrukerReader`/`PeakPicker2D`; no new untrusted-input surface. The new `multiplicity_edited` computation is a pure numeric reduction over an already-validated `Spectrum2D.data` ndarray. |
| V6 Cryptography | no | — |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed/empty 2D spectrum → `np.min` on empty array | Denial of Service (local) | Guard against empty `data` (mirror `_compute_2d_noise_sigma`'s `data.size == 0` guard already present in peak_picker_2d.py). |

No security-sensitive surface is introduced; ASVS controls are inherited from existing readers.

## Sources

### Primary (HIGH confidence — in-repo source inspected this session)
- `src/lucy_ng/cli/pick.py` — `pick_1d` `negative_detected` logic (the detector to port); `pick_hsqc`/`pick_2d` lack it (`detect_negative=False`).
- `src/lucy_ng/processing/peak_picker_2d.py` — `PeakPicker2D.pick_peaks(detect_negative=...)`, `_compute_2d_noise_sigma` empty-guard.
- `src/lucy_ng/cli/lsd.py` — `lsd run` (`solution_count`, `solutions.smi`), `lsd rank` / `_perform_ranking` (single SMILES file input, shared `resolve_c13_predictor`).
- `src/lucy_ng/lsd/runner.py` — `run_file`/`_execute_lsd`/`_run_outlsd`: `solutions.smi` written to output dir (defaults to input parent).
- `src/lucy_ng/lsd/parser.py` — `parse_smiles_file`: NO dedup (Pitfall 1).
- `src/lucy_ng/lsd/generator.py` — MULT built from `dept_result` (confirms CASE flow authors MULT in the skill, not via this generator).
- `.claude/agents/lucy-nmr-chemist.md` — multiplicity assessment, `[SETUP-COMPLETE]` "Multiplicities:" field, no ambiguity signal.
- `.claude/agents/lucy-lsd-engineer.md` — MULT reference, iteration-dir convention, conversion-skip rule, ELIM escalation.
- `.claude/agents/lucy-devils-advocate.md` — gate structure + `G-IDENT` post-solution template; no multiplicity gate yet.
- `.claude/commands/lucy-ng/case.md` — `monitor_progress`, completion signals, `detect_loops` (Pattern 5), `identity_gate` (gate-lifecycle template).
- `.claude/commands/lucy-ng/references/loop-patterns.md`, `advisory-templates.md` — Pattern 5 reopen + advisory wiring.
- `tests/test_cli_pick.py`, `tests/conftest.py`, `pyproject.toml` — test seam (`CliRunner`, `negative_detected` assertions, `sample_spectrum_2d`, `data/Ibuprofen/6`).

### Secondary
- `.planning/REQUIREMENTS.md` (MULT-01..04), `.planning/STATE.md`, `.planning/todos/pending/2026-06-23-multiplicity-model-hardcoding-defect.md` (defect spec + CASE4 worked example).

### Tertiary
- None — no WebSearch needed; the phase is fully internal to this codebase.

## Metadata

**Confidence breakdown:**
- Standard stack (no new packages; reuse existing CLI/runner/ranker): HIGH — every reused mechanism verified in source.
- Architecture (per-family runs, union, coverage gate, binding DA flag): HIGH — modeled on existing Pattern-5 reopen + G-IDENT gate, both inspected.
- Detector (D-05 `multiplicity_edited`): HIGH on mechanism (1D pattern + 2D negative picking both exist); MEDIUM on the exact 0.05 threshold for HSQC (A1 — may need real-data tuning).
- Family enumeration location (agent vs helper): MEDIUM — works either way; helper is the stronger testable seam (Open Q2).
- Pitfalls (dedup, conversion-skip suppression): HIGH — both verified against source.

**Research date:** 2026-06-25
**Valid until:** ~2026-07-25 (stable — internal codebase; revalidate if `cli/pick.py`, `lsd/runner.py`, or the five skill files change before planning).
