# Phase 88: Aliphatic Multiplicity Robustness - Context

**Gathered:** 2026-06-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden the CASE workflow so that when aliphatic CH/CH₂/CH₃ **multiplicity cannot be hard-determined from the spectra** (non-multiplicity-edited HSQC and/or unreliable/phase-distorted APT/DEPT), the search covers **every viable whole-molecule multiplicity family** — so the correct constitution stays reachable instead of being a-priori excluded. This is a **skill-level fix** to the CASE team agents (`lucy-nmr-chemist`, `lucy-lsd-engineer`, `lucy-devils-advocate`) and the orchestrator (`case.md` + its loop-patterns / advisory-templates references). It introduces **no new elucidation algorithm** and does not change how a single LSD run solves — only how many multiplicity hypotheses are searched and how the run guards against accepting before all viable families were tried.

Targets the **multiplicity-model-hardcoding** failure class, surfaced by the CASE4 (chamazulene) first VALID blind run (2026-06-23 → FAIL): truth = 7-ethyl-1,4-dimethylazulene (2×CH₃ + ethyl) was never in the solution set because the lsd-engineer hard-coded the iPr model (3×CH₃+CH) and never handed LSD the ethyl model.

This is independent of Phase 87 (naming) and the rank-scoring defect — it is a **search-space-coverage** problem: none of the existing nets (identity gate, rank analyst-override, MAE>4 quality loop) can recover a structure that is not in the searched set.

</domain>

<decisions>
## Implementation Decisions

### Parallel-family search mechanism (MULT-01)
- **D-01:** When aliphatic multiplicity is not hard-determinable, the lsd-engineer runs **each viable multiplicity family as a SEPARATE, fully-constrained LSD run in its own iteration sub-directory** (e.g. `analysis/iteration_NN_iPr/`, `analysis/iteration_NN_ethyl/`), then **unions the per-family solution sets and ranks across the union**. NOT a single relaxed-MULT run (LSD may not enumerate the intended families cleanly + explosion risk), and NOT sequential-with-fallback (that is the CASE4 failure mode — the leading family looking "good enough" silently excludes the truth). Each family is searched with its own correct MULT constraints so every family gets a fair, fully-constrained search.

### Family enumeration & bounding (MULT-01)
- **D-02:** "Viable family" = a **chemically sensible whole-molecule aliphatic partition** of the ambiguous aliphatic carbons + their attached protons that is **consistent with the molecular formula / H-count / DBE** (e.g. for an ambiguous aliphatic block: the valid CH₃/CH₂/CH integer partitions such as `3×CH₃+CH` vs `2×CH₃+CH₂+CH₂`). Enumerate at the **whole-molecule** level (not per-center cross-product — that explodes faster and is harder to justify chemically).
- **D-03:** **Hard cap** on the number of families searched (planner's discretion on the exact number, target ≤ 3–4). If more than the cap are formally valid, rank them by prior chemical plausibility, search the top-capped set, and **document the truncation explicitly** in CASE-PROGRESS.md (no silent drop).

### MAE-independent guardrail (MULT-02)
- **D-04:** A **deterministic coverage gate runs before the run may accept** — independent of MAE. The nmr-chemist's enumerated "viable families" list MUST be **fully covered** by the set of families actually searched. **If ≥2 viable families were identified but not all were searched, the run does NOT accept** — it reopens and searches the missing family(ies). This is a checklist/coverage check, NOT an MAE or plausibility threshold (the CASE4 wrong-class structure scored MAE 1.75 "PLAUSIBLE" and the existing MAE>4 guardrail stayed silent).

### Ambiguity detection signal + DA-flag hardening (MULT-04 + MULT-03)
- **D-05:** The nmr-chemist flags **"multiplicity-ambiguous" deterministically/programmatically**, not by judgment: when HSQC is **non-multiplicity-edited** (no negative cross-peaks — reuse the existing negative-intensity / DEPT-negative detection path) **AND/OR** APT/DEPT is **phase-unreliable/inconsistent**. On that condition it emits an explicit **`[MULTIPLICITY-AMBIGUOUS]` signal listing the viable families** (MULT-04), which the lsd-engineer acts on deterministically (→ D-01).
- **D-06:** A devils-advocate **"evidence FOR model X"** multiplicity flag becomes a **MANDATORY search item** (MULT-03): model X MUST enter the search space. It **cannot be dismissed by the convergence narrative / rationalized away** (the exact CASE4 defeat, where the diagnostic HMBC 11→13 "evidence for ethyl" was re-explained as gem-dimethyl coupling). The flag is closeable ONLY by showing model X was actually searched — not by argument.

### Claude's Discretion
- Exact family cap number (≤ 3–4 target); the precise naming of iteration sub-directories.
- The exact token/format of the `[MULTIPLICITY-AMBIGUOUS]` message and the coverage-gate checklist representation in CASE-PROGRESS.md (message-protocol detail).
- Whether the union ranking concatenates per-family `solutions.smi` files and runs one `lucy lsd rank`, or ranks per-family then merges — as long as ranking is across the union (D-01).
- How exactly per-family MULT constraints are derived (lsd-engineer construction detail), provided each family is fully constrained.

### Folded Todos
- **`.planning/todos/pending/2026-06-23-multiplicity-model-hardcoding-defect.md`** (score 0.9) — "Solver hard-codes one aliphatic multiplicity model under degraded 2D data (truth excluded from search space)." This is the phase's originating todo; its 3-point proposed fix maps directly onto D-01…D-06 (parallel families, MAE-independent guardrail, DA-flag binding) and its acceptance criteria are adopted below.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & roadmap
- `.planning/REQUIREMENTS.md` §MULT-01/02/03/04 — the four requirements this phase must satisfy.
- `.planning/ROADMAP.md` §"Phase 88: Aliphatic Multiplicity Robustness" — goal + 4 success criteria.

### Originating defect analysis (READ — it is the design spec)
- `.planning/todos/pending/2026-06-23-multiplicity-model-hardcoding-defect.md` — full root-cause, why this is the most dangerous of the three defect classes, the 3-point proposed fix, and acceptance criteria.
- `.planning/CASE-UAT-LOG.md` footnote ⁷ + the CASE4 2026-06-23 summary row — the blind-run evidence.

### CASE skill files to modify (in repo, symlinked into ~/.claude)
- `.claude/agents/lucy-nmr-chemist.md` — emit `[MULTIPLICITY-AMBIGUOUS]` + viable-families list; programmatic non-edited-HSQC / unreliable-APT detection (D-05, MULT-04).
- `.claude/agents/lucy-lsd-engineer.md` — run separate per-family LSD runs + union (D-01/D-02/D-03, MULT-01).
- `.claude/agents/lucy-devils-advocate.md` — make the "evidence FOR model X" flag a binding mandatory-search item (D-06, MULT-03).
- `.claude/commands/lucy-ng/case.md` — orchestrate the multiplicity-ambiguous branch + the pre-accept coverage gate (D-04, MULT-02); message-protocol for the new signal.
- `.claude/commands/lucy-ng/references/loop-patterns.md` — the coverage-gate / reopen pattern.
- `.claude/commands/lucy-ng/references/advisory-templates.md` — advisory wording for the multiplicity-coverage reopen.

### Reusable detection / ranking plumbing
- The existing **negative-intensity / DEPT-135 negative-peak detection** path used by `lucy pick 1d` (auto `detect_negative`) — the basis for "is HSQC multiplicity-edited?" (0 negative cross-peaks ⇒ not edited). Research must confirm the exact API/path for HSQC.
- `lucy lsd rank` — ranks a `solutions.smi`; the union-ranking input (D-01).

### Project rules
- `CLAUDE.md` — CASE skill edit/reload conventions (skill files in repo `.claude/`, symlinked into `~/.claude`; a fresh Claude Code session is required to reload edited agents).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Negative-peak detection** (`lucy pick 1d` `detect_negative` auto-detection, originally added for DEPT-135 CH₂ peaks): the same negative-intensity signal distinguishes a multiplicity-edited HSQC (CH₂ negative) from a non-edited one (no negatives). Reuse it for the D-05 programmatic ambiguity trigger rather than inventing a new detector.
- `lucy lsd rank` already consumes a `solutions.smi` and ranks by 13C MAE — the union of per-family solution files is the natural input for D-01's cross-family ranking; no new ranking code needed.
- The per-iteration `analysis/iteration_NN/` directory convention already exists; D-01's per-family sub-dirs are a small extension of it.

### Established Patterns
- CASE agents are Markdown skill files in `.claude/agents/` (repo-symlinked into `~/.claude`); behavior changes are prompt edits, and a **fresh Claude Code session is required to reload** edited agents. Functional validation is a blind CASE re-run (CASE4 = the acceptance test, UAT-01), NOT unit tests this session.
- The orchestrator is message-driven (PUSH protocol); a new `[MULTIPLICITY-AMBIGUOUS]` signal + a pre-accept coverage gate fit the existing structured-message + monitor_progress / detect_loops machinery in `case.md`.
- The existing MAE>4 "Quality Convergence Failure" loop (case.md detect_loops Pattern 5) is the precedent for a reopen-the-run gate — MULT-02's coverage gate sits alongside it but triggers on coverage, not MAE.

### Integration Points
- nmr-chemist `[SETUP-COMPLETE]` / multiplicity assessment → new `[MULTIPLICITY-AMBIGUOUS]` signal → lsd-engineer per-family runs → coordinator coverage gate before handing to ranking/accept.
- devils-advocate "evidence FOR model X" flag → coordinator records it as a mandatory-search item that the coverage gate enforces (cannot be closed by narrative).

</code_context>

<specifics>
## Specific Ideas

- **Acceptance (from ROADMAP success criteria + folded todo):**
  1. Re-run CASE4 blind → chamazulene's di-methyl-ethyl constitution (2×CH₃ + ethyl) **appears in the solution set** (truth reachable), regardless of which regioisomer ranks #1. This is UAT-01 / Phase 89.
  2. A **synthetic regression**: a compound with non-multiplicity-edited HSQC + an ambiguous iPr-vs-ethyl aliphatic pattern produces **BOTH families** in the searched space.
- The CASE4 worked example is the canonical illustration throughout the agent edits: HMBC 11→13 was genuine "evidence FOR ethyl" (two methyls in 1,4-dimethylazulene are far apart; a CH₃–CH₂ gives 2–3J) and must not be re-explained as gem-dimethyl coupling.

</specifics>

<deferred>
## Deferred Ideas

- Broadening parallel-family search to **non-aliphatic** multiplicity ambiguities (e.g. exchangeable/heteroatom multiplicity) — out of scope; this phase is aliphatic CH/CH₂/CH₃ only.
- A 13C-prediction model that separates iPr-methine from ethyl-CH₂ strongly enough to penalize the wrong class by MAE — the todo notes prediction does NOT currently do this; improving the predictor is a separate concern (this phase fixes coverage, not ranking discrimination).

### Reviewed Todos (not folded)
- None — the only matching todo (multiplicity-model-hardcoding) was folded.

</deferred>

---

*Phase: 88-aliphatic-multiplicity-robustness*
*Context gathered: 2026-06-25*
