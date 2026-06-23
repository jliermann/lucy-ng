# Phase 87: Final Identity-Verification Gate - Context

**Gathered:** 2026-06-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a final identity-verification gate so the compound name reported by a CASE run is **derived from the solved structure by a deterministic tool and independently cross-checked** — a wrong trivial name recalled from model memory can no longer be asserted as fact. This is a **skill-level fix** to the CASE team agents (`lucy-solution-analyst`, `lucy-devils-advocate`) plus an extension of `scripts/verify_case_solution.py`. It introduces **no new CASE elucidation algorithm** and does not change how structures are solved — only how the resulting structure is *named, qualified, and checked* before reporting.

Targets the recurring **parametric naming-hallucination** failure class: CASE4 (chamazulene — wrong "literature" reference), CASE5 (indigo↔isoindigo mislabel; indirubin called "indigo").

</domain>

<decisions>
## Implementation Decisions

### Identity derivation (IDENT-01)
- **D-01:** The solution-analyst derives identity from the **solution SMILES**, not from memory: generate the RDKit **InChIKey** from the solved SMILES, then look that up in the bundled 928K-compound reference DB to obtain a canonical name.
- **D-02:** Lookup strategy is **InChIKey-first with canonical-SMILES fallback**. NOTE for research/planning: the DB importer currently skips InChI/InChIKey generation (`src/lucy_ng/database/importer.py:256-257` set `inchi=""`, `inchi_key=""`), so the `compounds.inchi_key` column may be empty in the shipped DB. The fallback must match on **RDKit-canonicalized SMILES** against `compounds.smiles` when the InChIKey column yields nothing. Research must confirm the actual state of these columns in `data/reference/lucy-ng-derep.db`.
- **D-03:** A **no-hit is a first-class outcome** — when the structure is not in the DB (the common case for genuinely novel natural products, the whole point of CASE), the identity result is "not in reference DB / novel", NOT a guessed name.

### Independent gate (IDENT-02)
- **D-04:** The gate lives in **both** places, with clear roles:
  - **Authoritative, deterministic:** extend `scripts/verify_case_solution.py` with a name↔structure check. It re-derives the InChIKey/identity from the reported structure and compares it against the name the analyst reported. This is the binding gate.
  - **Advisory, LLM:** `lucy-devils-advocate` additionally sanity-checks the name↔structure mapping as a second, independent reasoning layer.
- **D-05:** The InChIKey-generation + DB-name-lookup logic is **integrated into `verify_case_solution.py`** (no new `lucy` CLI subcommand). The same script/function is the analyst's derivation tool AND the gate's check. Independence is preserved because the gate verifies that the analyst's **reported** name matches the deterministic tool output — it catches the analyst overriding the tool with a recalled name (exactly the CASE4/CASE5 mode); the devils-advocate LLM layer provides the truly independent second opinion.

### Gate severity (mismatch handling)
- **D-06:** On a detected name↔structure discrepancy, the gate **downgrades the name to "tentative" and emits a prominent warning** rather than hard-failing the whole report. "Blocking" applies to *asserting the name as established fact* — that is blocked — while the structural result (SMILES/rank/MAE) still reports. Rationale: CASE targets are often novel, so a hard report-block on every unconfirmed name would be too brittle.

### Tentative presentation (IDENT-03)
- **D-07:** When identity is not tool-confirmed, the report uses the **structural identifier (InChIKey + canonical SMILES) as the primary identity**, and any model-suggested trivial name is rendered explicitly as **"(tentative, unverified)"** with a confidence qualifier. Confirmed names (DB hit) may be stated plainly.

### Claude's Discretion
- Exact wording/format of the confidence qualifier and the warning string (planner/analyst-template detail).
- Internal function/CLI-arg shape of the extended `verify_case_solution.py` (e.g., an `identify`/`check-identity` mode vs an importable function) — as long as D-05's "one shared deterministic path, integrated in the script" holds.
- Whether the analyst invokes the script as a subprocess or imports the function.

### Folded Todos
- **`.planning/todos/pending/2026-06-21-final-identity-verification-gate.md`** — "Add a tool-based final identity-verification gate (stop parametric naming hallucination)." This is the phase's originating todo; its intent (tool-derived identity + independent gate to stop recalled-name hallucination) is fully captured by D-01…D-07.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements & roadmap
- `.planning/REQUIREMENTS.md` §IDENT-01/02/03 — the three requirements this phase must satisfy.
- `.planning/ROADMAP.md` §"Phase 87: Final Identity-Verification Gate" — goal + 4 success criteria (incl. the CASE4/CASE5 catch criterion).

### CASE skill files to modify (in repo, symlinked into ~/.claude)
- `.claude/agents/lucy-solution-analyst.md` — derives identity + reports the name; must be changed to call the tool and apply tentative-marking (D-01, D-07). Current results template around its `# CASE Results:` / `Top solution:` section.
- `.claude/agents/lucy-devils-advocate.md` — gains the advisory name↔structure sanity gate (D-04).
- `scripts/verify_case_solution.py` — currently checks only aromatic-ring (≥6 aromatic atoms) + exact formula; extend with the deterministic InChIKey→DB-name derivation + name↔structure check (D-04, D-05).

### Reusable identity/DB plumbing
- `src/lucy_ng/database/manager.py` (~line 301) — `compounds` SELECT exposing `name, smiles, formula, inchi, inchi_key`; the name-lookup source.
- `src/lucy_ng/database/schema.py` — `compounds` table schema.
- `src/lucy_ng/database/importer.py:248-276` — shows InChI/InChIKey are skipped on import (the D-02 caveat).
- `src/lucy_ng/cli/dereplicate.py` (~lines 220, 243) — existing precedent for surfacing `entry.name` / `entry.inchi_key`.

### Project rules
- `CLAUDE.md` — HOSE no-explicit-H rule (not central here, but applies if any prediction is touched); CASE skill edit/reload conventions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/verify_case_solution.py`: already an argparse CLI producing JSON + exit 0/1; natural host for the new deterministic identity check (D-05). Uses RDKit (`Chem.MolFromSmiles`, `rdMolDescriptors`) — InChIKey via `Chem.MolToInchiKey` fits the existing import surface.
- `src/lucy_ng/database/manager.py`: read path to `compounds` (name/smiles/inchi_key) — the name-lookup backend.
- RDKit is already a hard dependency throughout — InChIKey + canonical-SMILES generation needs no new package.

### Established Patterns
- CASE agents are Markdown skill files in `.claude/agents/` (repo-symlinked into `~/.claude`); behavior changes are prompt edits, and a **fresh Claude Code session is required to reload** edited agents.
- Existing devils-advocate is structured as numbered gates (e.g., G5–G8 for prior failure modes) — the new advisory name↔structure check should be added as a new gate in that style.
- `verify_case_solution.py` returns structured JSON consumed downstream — extend the JSON contract rather than printing prose.

### Integration Points
- Analyst → calls the extended `verify_case_solution.py` (or its function) to derive identity from the solved SMILES.
- Final gate (script, blocking-on-assertion) + devils-advocate (advisory) run before the analyst's `CASE Results` report is emitted.
- The DB used is the same `data/reference/lucy-ng-derep.db` already required for dereplication/prediction.

</code_context>

<specifics>
## Specific Ideas

- The gate MUST be demonstrably effective on the historical failures: CASE4 (chamazulene — wrong substitution-isomer "literature" name) and CASE5 (indigo vs isoindigo; indirubin mislabeled "indigo"). Success criterion 4 requires the gate to catch these on those structures — these are the natural regression fixtures (IDENT/gate tests should pin them).
- Independence semantics (important, avoids a false sense of "independent"): the deterministic script and the analyst share the same derivation code, so the script's job is to confirm the analyst did not deviate from the tool output; the devils-advocate LLM layer is the genuinely independent cross-check.

</specifics>

<deferred>
## Deferred Ideas

- A standalone `lucy identify` CLI subcommand (SMILES → InChIKey + DB-name + confidence, `--format json`) was considered for reusability/testability but **deferred** in favor of integrating into `verify_case_solution.py` (D-05). Revisit only if a second consumer outside the CASE gate emerges.

### Reviewed Todos (not folded)
- **`.planning/todos/pending/2026-06-23-multiplicity-model-hardcoding-defect.md`** — "Solver hard-codes one aliphatic multiplicity model under degraded 2D data." Matched this phase (score 0.9) but belongs to **Phase 88: Aliphatic Multiplicity Robustness**, a different failure class (search-space exclusion, not naming). Left for Phase 88.

</deferred>

---

*Phase: 87-final-identity-verification-gate*
*Context gathered: 2026-06-23*
