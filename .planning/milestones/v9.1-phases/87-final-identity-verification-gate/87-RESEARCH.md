# Phase 87: Final Identity-Verification Gate - Research

**Researched:** 2026-06-23
**Domain:** CASE skill-level fix — deterministic structure→name identity derivation + name↔structure gate (RDKit + bundled SQLite reference DB), CASE team agent prompt edits
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** The solution-analyst derives identity from the **solution SMILES**, not from memory: generate the RDKit **InChIKey** from the solved SMILES, then look that up in the bundled 928K-compound reference DB to obtain a canonical name.
- **D-02:** Lookup strategy is **InChIKey-first with canonical-SMILES fallback**. The importer skips InChI/InChIKey generation (`importer.py:256-257` set `inchi=""`, `inchi_key=""`), so `compounds.inchi_key` may be empty in the shipped DB. The fallback must match on **RDKit-canonicalized SMILES** against `compounds.smiles` when the InChIKey column yields nothing. Research must confirm actual column state. **→ CONFIRMED below (Critical Finding 1).**
- **D-03:** A **no-hit is a first-class outcome** — when the structure is not in the DB (the common case for genuinely novel natural products), the identity result is "not in reference DB / novel", NOT a guessed name.
- **D-04:** The gate lives in **both** places:
  - **Authoritative, deterministic:** extend `scripts/verify_case_solution.py` with a name↔structure check that re-derives identity from the reported structure and compares against the name the analyst reported. Binding gate.
  - **Advisory, LLM:** `lucy-devils-advocate` additionally sanity-checks the name↔structure mapping as a second independent reasoning layer.
- **D-05:** The InChIKey-generation + DB-name-lookup logic is **integrated into `verify_case_solution.py`** (no new `lucy` CLI subcommand). The same script/function is the analyst's derivation tool AND the gate's check.
- **D-06:** On a detected name↔structure discrepancy, the gate **downgrades the name to "tentative" and emits a prominent warning** rather than hard-failing the whole report. The structural result (SMILES/rank/MAE) still reports.
- **D-07:** When identity is not tool-confirmed, the report uses the **structural identifier (InChIKey + canonical SMILES) as the primary identity**, and any model-suggested trivial name is rendered explicitly as **"(tentative, unverified)"** with a confidence qualifier. Confirmed names (DB hit) may be stated plainly.

### Claude's Discretion
- Exact wording/format of the confidence qualifier and the warning string.
- Internal function/CLI-arg shape of the extended `verify_case_solution.py` (an `identify`/`check-identity` mode vs an importable function) — as long as D-05's "one shared deterministic path, integrated in the script" holds.
- Whether the analyst invokes the script as a subprocess or imports the function.

### Deferred Ideas (OUT OF SCOPE)
- A standalone `lucy identify` CLI subcommand — deferred in favor of integrating into `verify_case_solution.py` (D-05). Revisit only if a second consumer outside the CASE gate emerges.
- Phase 88 multiplicity-model-hardcoding defect (different failure class — search-space exclusion, not naming).
- **No new elucidation/LSD/ranking algorithm.** Only how the solved structure is named, qualified, and checked.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| IDENT-01 | Solution-analyst derives identity from SMILES via a tool (InChIKey / structure lookup); never asserts a recalled trivial name as fact. | Verified working two-path lookup (Critical Findings 1–3); analyst template edit site identified (analyst §6, lines 162–193); RDKit `MolToInchiKey`/`MolToSmiles` already imported in `verify_case_solution.py`. |
| IDENT-02 | An independent final gate (devils-advocate and/or `verify_case_solution.py`) checks the analyst's name↔structure mapping before results are reported; a mismatch blocks/flags. | Two-layer design confirmed (D-04): deterministic check in the script (extend existing JSON+exit-code contract) + advisory DA gate (slots into Check-5 gate table, lines 411–416). Note lifecycle difference (Pitfall 4). |
| IDENT-03 | When identity cannot be tool-confirmed, the report marks the name tentative (with confidence) rather than asserting it. | `verify_case_solution.py` already emits structured JSON; extend with `identity` block carrying `confidence`/`tentative` fields. Analyst template gets a tentative-name rendering rule. |
</phase_requirements>

## Summary

This is a contained skill-level + small-script change. RDKit (already a hard dependency, v2025.09.4 verified installed) provides everything needed for structure→identity derivation: `Chem.MolToInchiKey(mol)` and `Chem.MolToSmiles(mol)`. The reference DB (`data/reference/lucy-ng-derep.db`, present locally, 928,443 compounds) is the name source, reached via the existing `DatabaseFinder.find_derep_database()` discovery helper (verified: returns the project DB).

**The single most important finding** (the D-02 caveat, now resolved with hard numbers) is that the two lookup columns are **disjoint by source**: COCONUT rows (895,099 / 96.4%) have canonical `smiles` but empty `inchi_key`; NMRShiftDB rows (33,344 / 3.6%) have `inchi_key` but empty `smiles`. Neither column alone covers the DB. Therefore the InChIKey-first + canonical-SMILES-fallback strategy (D-02) is **mandatory and complementary, not redundant** — InChIKey-first reaches the NMRShiftDB partition, SMILES-fallback reaches the COCONUT partition. A no-hit is genuinely common (verified: even ibuprofen is absent from this DB), validating D-03.

**Primary recommendation:** Add an importable `derive_identity(smiles, db_path=None) -> dict` function (plus a thin `check-identity`/`identify` argparse subcommand wrapping it) to `verify_case_solution.py`. It canonicalizes the SMILES with `Chem.MolToSmiles`, computes the InChIKey with `Chem.MolToInchiKey`, then queries the DB inchi_key column first and the canonical-smiles column second, returning `{matched, name, source, inchi_key, canonical_smiles, confidence}`. The analyst calls this (subprocess or import) and renders tentative names per D-07; the gate compares the analyst's reported name against this deterministic output (D-04 binding layer); the devils-advocate adds the advisory LLM cross-check.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Canonical SMILES + InChIKey generation | Python script / RDKit (`verify_case_solution.py`) | — | Deterministic chemistry computation; must be reproducible, never LLM. |
| DB name lookup (InChIKey-first, SMILES-fallback) | Python script (read-only SQLite via `DatabaseFinder`) | — | One shared deterministic path (D-05). |
| Deriving the reported identity from the solved SMILES | CASE analyst agent (calls the script) | Python script | Analyst orchestrates; script does the actual derivation. IDENT-01. |
| Binding name↔structure gate | Python script (`verify_case_solution.py`) | — | Authoritative, deterministic; catches analyst overriding the tool. IDENT-02. |
| Advisory name↔structure sanity gate | CASE devils-advocate agent (LLM) | — | Genuinely independent reasoning layer; second opinion. IDENT-02/D-04. |
| Tentative-name presentation | CASE analyst agent (report template) | — | Prompt-level rendering rule. IDENT-03/D-07. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| RDKit | 2025.09.4 (installed, VERIFIED) | `MolToInchiKey`, `MolToSmiles`, `MolFromSmiles` | Already a hard dependency; same library the importer used to write `compounds.smiles`. |
| sqlite3 (stdlib) | Python 3.12 | Read-only DB query | DB is plain SQLite; `manager.py` and `dereplicate.py` already use it. |

No new packages. No `npm`/`pip` install step required for this phase.

### Supporting (existing project assets — reuse, do not rebuild)
| Asset | Path | Purpose |
|-------|------|---------|
| `DatabaseFinder.find_derep_database()` | `src/lucy_ng/database/finder.py:26` | Locates `lucy-ng-derep.db` (env var → project → common → mdfind → Dropbox). VERIFIED returns project DB. |
| `verify_case_solution.py` | `scripts/verify_case_solution.py` | Existing argparse CLI → JSON + exit 0/1; already imports `Chem`, `rdMolDescriptors`. Host for D-05. |
| `tests/test_verify_case_solution.py` | — | Existing black-box subprocess test pattern; extend with identity + regression cases. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Two-path lookup (InChIKey + SMILES) | InChIKey-only | **Rejected by data:** misses all 895K COCONUT rows. |
| Two-path lookup | SMILES-only | **Rejected by data:** misses all 33K NMRShiftDB rows (incl. CASE5 indigo, which is reachable ONLY by inchi_key). |
| Importable function | Subprocess-only | Importable is cleaner for tests + analyst; subprocess still works (D-05 allows either). Recommend exposing BOTH (function + subcommand). |
| New `lucy identify` CLI | — | Explicitly deferred (D-05). Do not add. |

**Installation:** None. (RDKit + sqlite3 already present.)

## Package Legitimacy Audit

No external packages are installed by this phase. All dependencies (RDKit, sqlite3) are pre-existing and verified present. Audit not applicable.

## Critical Findings (the D-02 resolution — read first)

### Critical Finding 1 — DB column state (HIGHEST PRIORITY, CONFIRMED)
`data/reference/lucy-ng-derep.db` is present locally (3.97 GB uncompressed). `[VERIFIED: sqlite3 query]`

```
SELECT count(*), count(nullif(inchi_key,'')), count(nullif(smiles,'')), count(nullif(inchi,'')) FROM compounds;
→ total=928443  inchi_key_populated=33344  smiles_populated=895099  inchi_populated=33344
```

**The columns are disjoint by source** `[VERIFIED: sqlite3 GROUP BY source]`:

| source | rows | with inchi_key | with smiles |
|--------|------|----------------|-------------|
| coconut | 895,099 | 0 | 895,099 |
| nmrshiftdb | 33,344 | 33,344 | 0 |

Implication: **both lookup paths are required and complementary.** InChIKey-first finds NMRShiftDB compounds; canonical-SMILES fallback finds COCONUT compounds. This is the load-bearing fact for the plan.

### Critical Finding 2 — SMILES round-trips stably (fallback is apples-to-apples)
The importer stores `smiles = Chem.MolToSmiles(mol)` with **default flags** (`importer.py:250`). `[VERIFIED: scripts/verify_case_solution.py source + importer.py:248-252]` A stored COCONUT SMILES re-parsed and re-canonicalized with the same default `Chem.MolToSmiles` is **byte-identical** to the stored value `[VERIFIED: round-trip test, stored == recanon → True]`, and an exact-equality SQL match (`WHERE smiles = ?`) finds it. **The fallback must therefore canonicalize the analyst's SMILES with `Chem.MolToSmiles(Chem.MolFromSmiles(s))` (no extra flags) and do an exact string match** — same RDKit major version (2025.09) is used on both sides, so canonical output is stable.

### Critical Finding 3 — Regression fixtures verified against the real DB
`[VERIFIED: sqlite3 + RDKit lookup of CASE4/CASE5 truth structures]`

| Fixture | Canonical SMILES | InChIKey | DB hit |
|---------|------------------|----------|--------|
| Chamazulene (CASE4 truth) | `CCc1ccc2ccc(C)c-2c(C)c1` | `FVZVDQVUOAAMCG-UHFFFAOYSA-N` | **No hit (neither path)** → "not in reference DB" |
| Indigo (CASE5 truth) | `O=C1/C(=C2\Nc3ccccc3C2=O)Nc2ccccc21` | `COHYTHOBJLSHDF-BUHFOSPRSA-N` | **Hit via inchi_key only** → name "2,2'-Bis(2,3-dihydro-3-oxoindolyliden); Indigo" (nmrshiftdb). by_smiles empty. |
| Isoindigo | `O=C1Nc2ccccc2/C1=C1/C(=O)Nc2ccccc21` | `MLCPSWPIYHDOKG-YPKPFQOOSA-N` | No hit |
| Indirubin | `O=C1Nc2ccccc2/C1=C1\Nc2ccccc2C1=O` | `CRDNMYFJWFXOCH-BUHFOSPRSA-N` | No hit |
| Ibuprofen (CASE1) | `CC(Cc1ccc(C(C)C)cc1)C(=O)O` | `FLMVHZOJMRGXRO-UHFFFAOYSA-N` | **No hit** — even a common drug is absent |

**Two crucial consequences for the gate design:**
1. **Indigo proves the InChIKey-path is non-optional** — it is unreachable by SMILES (nmrshiftdb has empty smiles). A SMILES-only gate would falsely report indigo as "novel/no-hit."
2. **Chamazulene and ibuprofen prove no-hit is the common case** (D-03). The gate must NOT block or treat no-hit as failure; it falls back to InChIKey+SMILES as the primary identity (D-07).

**How the gate catches CASE4/CASE5 historically:** the gate compares the analyst's *reported name* against the deterministic tool output.
- CASE4: analyst reported a wrong "literature" isomer name for chamazulene → tool returns "no DB hit" → any asserted trivial name is downgraded to tentative + warning (D-06). The wrong name can no longer be stated as fact.
- CASE5: analyst mislabeled indigo as "isoindigo" / called indirubin "indigo" → tool's InChIKey lookup of the *solved* structure returns the DB's "Indigo" record (for the indigo structure) — mismatch between reported "isoindigo" and derived "Indigo" triggers the warning; for indirubin the tool returns no-hit, so "indigo" cannot be asserted.

### Critical Finding 4 — Lookup performance is acceptable without an index
There is **no index** on `smiles` or `inchi_key` (only `idx_compounds_formula_normalized`). `[VERIFIED: sqlite_master]` A full-scan equality lookup measured **~0.06 s** for both columns `[VERIFIED: timed query]`. No index needs to be added for a single per-run lookup. (If the planner wants belt-and-suspenders speed, an index could be added at gate-time, but it is unnecessary and would touch the shipped DB — recommend NOT doing so.)

## Architecture Patterns

### System Architecture Diagram

```
  Solved structure (merged.smi, top SMILES)
              │
              ▼
   ┌─────────────────────────────────────────────────────────┐
   │  verify_case_solution.py  (D-05: one shared deterministic │
   │                            path; RDKit + sqlite3)         │
   │                                                            │
   │  derive_identity(smiles):                                  │
   │    mol  = Chem.MolFromSmiles(smiles)                       │
   │    cano = Chem.MolToSmiles(mol)      # default flags       │
   │    ik   = Chem.MolToInchiKey(mol)                          │
   │    db   = DatabaseFinder.find_derep_database()             │
   │    ┌── path 1: SELECT name,source WHERE inchi_key = ik  ───┤  reaches NMRShiftDB (33K)
   │    └── path 2 (if path1 empty):                            │
   │           SELECT name,source WHERE smiles = cano        ───┤  reaches COCONUT (895K)
   │    → {matched, name, source, inchi_key, canonical_smiles,  │
   │       confidence: confirmed|tentative|novel}              │
   └─────────────────────────────────────────────────────────┘
              │                                   │
              ▼ (IDENT-01 derivation)             ▼ (IDENT-02 binding gate)
   ┌────────────────────────┐      ┌────────────────────────────────────┐
   │ lucy-solution-analyst   │      │ name↔structure check:                │
   │ renders report:         │      │  reported_name == derived_name ?     │
   │  - DB hit  → name plain │      │   match  → confirmed                 │
   │  - no hit  → InChIKey + │      │   mismatch / no-hit-but-name-asserted│
   │    canonical SMILES as  │      │     → DOWNGRADE to tentative + WARN  │
   │    primary identity,    │      │       (D-06: structural result still │
   │    trivial name marked  │      │        reports; name not blocked     │
   │    "(tentative,         │      │        from printing, only from being│
   │     unverified)" (D-07) │      │        asserted as fact)             │
   └────────────────────────┘      └────────────────────────────────────┘
              │
              ▼ (IDENT-02 advisory, independent)
   ┌────────────────────────────────────────────┐
   │ lucy-devils-advocate  (LLM second opinion)   │
   │  new gate: does the reported name plausibly  │
   │  match the drawn structure? flag if not.     │
   └────────────────────────────────────────────┘
```

File-to-implementation mapping is in Component Responsibilities below.

### Component Responsibilities
| File | Change | Notes |
|------|--------|-------|
| `scripts/verify_case_solution.py` | Add `derive_identity(smiles, db_path=None)` + a `check-identity`/`identify` argparse subcommand; extend JSON contract with an `identity` block. Keep existing aromatic+formula behavior unchanged (existing tests must stay green). | Imports already present: `Chem`, `rdMolDescriptors`, `json`, `sys`, `Path`. Add `from rdkit import Chem` already there; add `import sqlite3` and import `DatabaseFinder` (or replicate its project-path lookup to keep the script dependency-light — see Pitfall 5). |
| `.claude/agents/lucy-solution-analyst.md` | §6 "Final Results Report" template (lines 162–193) + `[RANKING-COMPLETE]` `Top solution:` line (line 206): derive identity via the tool; render tentative names per D-07. | Add a derivation step in the workflow list (lines 232–248, after step 7 "Write final_results.md" → make derivation precede the name in the header). |
| `.claude/agents/lucy-devils-advocate.md` | Add a new advisory gate in the Check-5 gate style (around lines 344–416 / the gate summary table 411–416). | **Lifecycle caveat — Pitfall 4.** Existing DA gates run pre-LSD-run on `compound.lsd`. The name↔structure gate runs post-solution on `final_results.md`. The plan must define when this gate fires. |

### Pattern 1: Importable function + thin CLI wrapper (D-05 compliant)
**What:** Core logic in `derive_identity()`; argparse subcommand calls it; analyst can subprocess OR import.
**When to use:** Always here — satisfies "one shared deterministic path."
```python
# Source: synthesized from scripts/verify_case_solution.py (existing imports) +
#         importer.py:250 (canonicalization) + finder.py:26 (DB discovery). [VERIFIED]
import sqlite3
from rdkit import Chem

def derive_identity(smiles: str, db_path=None) -> dict:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"matched": False, "error": "invalid smiles", "confidence": "novel"}
    canonical = Chem.MolToSmiles(mol)            # default flags — matches importer (Finding 2)
    inchi_key = Chem.MolToInchiKey(mol)
    # db_path: caller passes, or use DatabaseFinder.find_derep_database()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    # Path 1: InChIKey-first (reaches NMRShiftDB partition)
    row = conn.execute(
        "SELECT name, source FROM compounds WHERE inchi_key = ? AND inchi_key != '' LIMIT 1",
        (inchi_key,),
    ).fetchone()
    # Path 2: canonical-SMILES fallback (reaches COCONUT partition)
    if row is None:
        row = conn.execute(
            "SELECT name, source FROM compounds WHERE smiles = ? AND smiles != '' LIMIT 1",
            (canonical,),
        ).fetchone()
    conn.close()
    if row is None:
        return {"matched": False, "inchi_key": inchi_key,
                "canonical_smiles": canonical, "confidence": "novel"}
    return {"matched": True, "name": row["name"], "source": row["source"],
            "inchi_key": inchi_key, "canonical_smiles": canonical, "confidence": "confirmed"}
```

### Anti-Patterns to Avoid
- **InChIKey-only or SMILES-only lookup:** silently misses an entire DB partition (Findings 1, 3). Always run both paths.
- **Canonicalizing with non-default flags** (e.g. `isomericSmiles=False`, custom `canonical=`): breaks the byte-equality match against `compounds.smiles` (Finding 2). Use bare `Chem.MolToSmiles(mol)`.
- **Hard-failing the report on no-hit:** contradicts D-03/D-06; no-hit is normal for novel natural products.
- **Treating COCONUT `name` (e.g. `CNP0220816`) as a human trivial name:** COCONUT names are accession codes, not trivial names. A COCONUT hit confirms *presence in DB*, not a friendly name. The plan/analyst template should treat a COCONUT-code hit as "known structure (DB accession), no trivial name confirmed" rather than asserting a human name.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| InChIKey from structure | String hashing / manual InChI | `Chem.MolToInchiKey(mol)` | Standard, deterministic, already imported. |
| Canonical SMILES | Custom canonicalization | `Chem.MolToSmiles(mol)` (default flags) | Must byte-match importer output (Finding 2). |
| DB file discovery | Hard-coded `data/reference/...` path | `DatabaseFinder.find_derep_database()` | Handles env var / Spotlight / Dropbox dev locations; works from CASE data dirs outside the repo (CASE runs execute outside the repo). |
| DB read | New ORM/query layer | Direct `sqlite3` read-only connection | `manager.py`/`dereplicate.py` already do this; one-shot lookup. |

**Key insight:** Everything required already exists in the codebase. The phase is plumbing two known RDKit calls into two SQL equality lookups, plus prompt edits — no novel logic.

## Runtime State Inventory

> This is a refactor/skill-edit phase that adds a derivation step; the relevant "runtime state" is the shipped DB and the symlinked skill files.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Reference DB `data/reference/lucy-ng-derep.db` — read-only consumer; columns confirmed (Finding 1). NOT modified by this phase. | None (read-only). Do NOT add indexes to the shipped DB. |
| Live service config | None — no external service. | None. |
| OS-registered state | CASE agents are repo `.claude/agents/*.md` **symlinked into `~/.claude`**. Editing the repo copy edits the live skill. | A **fresh Claude Code session is required to reload edited agents** (per CLAUDE.md). The plan's verification cannot test the edited agent behavior in the same session that edited it. |
| Secrets/env vars | `LUCY_DATABASE` env var (read by `DatabaseFinder`) — used, not changed. | None. |
| Build artifacts | None — no package rename. `scripts/verify_case_solution.py` is a loose script, not a packaged entry point. | None. |

## Common Pitfalls

### Pitfall 1: SMILES-only (or InChIKey-only) lookup misses half the DB
**What goes wrong:** Indigo (CASE5) is reachable ONLY via inchi_key; all COCONUT compounds ONLY via smiles.
**Why it happens:** Importer split — Finding 1.
**How to avoid:** Always run both paths, InChIKey first then SMILES fallback.
**Warning signs:** Indigo regression fixture reports "novel" when it should report a DB hit.

### Pitfall 2: Non-canonical or non-default-flag SMILES comparison
**What goes wrong:** `WHERE smiles = ?` silently returns nothing because the analyst's SMILES, though chemically identical, differs in string form.
**Why it happens:** Different RDKit flags or skipping canonicalization.
**How to avoid:** `Chem.MolToSmiles(Chem.MolFromSmiles(s))` with default flags (Finding 2); same RDKit major version both sides.
**Warning signs:** Known COCONUT structures all report "novel."

### Pitfall 3: Treating no-hit as gate failure
**What goes wrong:** Novel natural products (the CASE target class) and even ibuprofen produce no-hit; a hard-fail would block almost every real run.
**Why it happens:** Misreading IDENT-02 "mismatch blocks/flags" as "no-hit blocks."
**How to avoid:** D-06 — downgrade asserted name to tentative + warn; structural result still reports. No-hit + no asserted name = clean "novel" outcome (no warning needed).
**Warning signs:** Gate exit-code 1 on a correct novel structure.

### Pitfall 4: Devils-advocate gate lifecycle mismatch (PLANNING-CRITICAL)
**What goes wrong:** All existing DA gates run **pre-solver** on the `compound.lsd` constraint file (before any structure exists). The name↔structure gate is inherently **post-solution** (operates on the solved SMILES + reported name in `final_results.md`).
**Why it happens:** The DA agent's current workflow is the constraint-validation stage of each iteration; there is no existing "post-solution review" hook.
**How to avoid:** The plan must explicitly define the firing point — e.g. a new DA invocation/section after the analyst produces `final_results.md`, OR fold the advisory check into the analyst's own final report step with the DA gate documented as a distinct reasoning pass. Do not bolt the new gate into the per-iteration pre-run gate table without specifying when it runs.
**Warning signs:** A gate that has no structure to inspect because it fires before solving.

### Pitfall 5: Script imports vs. running outside the repo
**What goes wrong:** CASE runs execute from NMR data directories **outside the lucy-ng repo**. `verify_case_solution.py` is invoked there; `from lucy_ng.database.finder import DatabaseFinder` works only if `lucy_ng` is importable (installed in the env — it is, since `lucy` CLI is on PATH).
**Why it happens:** The script currently imports only RDKit (always installed), not `lucy_ng`.
**How to avoid:** Confirm `lucy_ng` is importable in the CASE runtime (it is — `lucy` CLI requires it). Prefer importing `DatabaseFinder` for robust DB discovery. Fallback: replicate the `LUCY_DATABASE` env-var + `data/reference/` + Dropbox-dev path probe inline to keep the script self-contained (matches `finder.py:26-83`).
**Warning signs:** `ModuleNotFoundError: lucy_ng` when running the script from a CASE data dir, or "DB not found" when run outside the repo.

### Pitfall 6: Editing the skill and testing it in the same session
**What goes wrong:** Edited `.claude/agents/*.md` do not take effect until a fresh Claude Code session (CLAUDE.md / Runtime State Inventory).
**How to avoid:** Plan deterministic-side verification (the `verify_case_solution.py` tests + regression fixtures) as the binding automated check; agent-behavior validation is necessarily a separate blind run in a fresh session (the project's established blind-UAT discipline).

## Code Examples

### Deterministic identity derivation (the shared D-05 path)
See Pattern 1 above (verified component synthesis).

### Extending the existing JSON/exit-code contract (IDENT-02/IDENT-03)
```python
# Add an "identity" subcommand alongside the existing aromatic+formula default.
# Existing behavior (default invocation: merged_smi + formula) MUST remain unchanged
# so tests/test_verify_case_solution.py stays green.
#
# check-identity mode JSON:
# {
#   "mode": "identity",
#   "reported_name": "<analyst name or null>",
#   "derived": { "matched": true, "name": "...", "source": "nmrshiftdb",
#                "inchi_key": "...", "canonical_smiles": "...", "confidence": "confirmed" },
#   "name_match": true|false|null,        # null when no name reported / no DB hit
#   "verdict": "confirmed" | "tentative" | "novel",
#   "warning": "<string or null>"         # D-06 prominent warning on mismatch
# }
# exit 0 on confirmed/novel-without-asserted-name; exit nonzero only if the planner
# decides a hard signal is wanted on mismatch — but per D-06 default is downgrade+warn,
# so prefer exit 0 + verdict/warning fields (let the consumer decide).
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Analyst asserts recalled trivial name | Tool-derived InChIKey→DB name; tentative marking on no-confirm | This phase | Eliminates parametric naming hallucination (CASE4/CASE5 class). |

**Deprecated/outdated:** None relevant. (Note: a previously considered standalone `lucy identify` CLI is explicitly deferred — do not build it.)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The chamazulene truth SMILES `CCc1ccc2ccc(C)c-2c(C)c1` and indigo `O=C1/C(=C2\Nc3ccccc3C2=O)Nc2ccccc21` (from `.planning/CASE-DATASET-IDENTITIES.md`, orchestrator-only ground truth) are the correct regression fixtures. | Critical Finding 3 | If the fixture SMILES are wrong, the regression test pins the wrong behavior. Mitigated: both parse + canonicalize cleanly in RDKit and the indigo InChIKey matches a real DB record. |
| A2 | `lucy_ng` is importable in the CASE runtime (so `DatabaseFinder` import works from outside the repo). | Pitfall 5 | If not importable, must use the inline DB-path fallback. Low risk — `lucy` CLI on PATH implies the package is installed. |

## Open Questions

1. **When exactly does the devils-advocate advisory gate fire?**
   - What we know: existing DA gates are pre-solver on `compound.lsd`; the name↔structure check is post-solution.
   - What's unclear: whether to add a new post-solution DA pass, or document the advisory check inside the analyst's final-report step.
   - Recommendation: planner adds an explicit post-solution review hook (see Pitfall 4); simplest is a dedicated DA section triggered after `final_results.md` is written, mirroring the gate-table style but flagged as post-solution.

2. **COCONUT-accession hit semantics.**
   - What we know: a COCONUT SMILES hit yields a code like `CNP0220816`, not a trivial name.
   - What's unclear: should a COCONUT-code hit count as "confirmed name" or "known structure, no trivial name"?
   - Recommendation: treat it as "structure known in DB (COCONUT accession), trivial name not confirmed" — i.e. confidence "confirmed-structure" but any human name still tentative. Planner to decide the exact label.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| RDKit | InChIKey + canonical SMILES | ✓ | 2025.09.4 | — (hard dependency) |
| sqlite3 (stdlib) | DB read | ✓ | py3.12 | — |
| Reference DB `lucy-ng-derep.db` | name lookup | ✓ (3.97 GB) | schema with name/smiles/formula/inchi/inchi_key | `lucy database download` if absent; DB-absent path must degrade to InChIKey+SMILES-only identity (no name lookup) |
| `lucy_ng` package importable | optional `DatabaseFinder` import | ✓ (lucy CLI on PATH) | — | inline path probe (Pitfall 5) |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** If the DB is unavailable at gate time, the tool still returns InChIKey + canonical SMILES (the D-07 structural identity) and marks identity "novel/unverified" — the gate still functions, just without DB-name confirmation.

## Validation Architecture

> `workflow.nyquist_validation` is absent from `.planning/config.json` → treated as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=7.0 (pytest-cov >=4.0) `[VERIFIED: pyproject.toml]` |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=`tests`, addopts=`-v --tb=short`) |
| Quick run command | `pytest tests/test_verify_case_solution.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| IDENT-01 | `derive_identity` returns InChIKey + canonical SMILES from a SMILES | unit/black-box | `pytest tests/test_verify_case_solution.py -k identity -x` | ❌ Wave 0 (add cases to existing file) |
| IDENT-01 | InChIKey-path finds indigo (nmrshiftdb) | integration (needs DB) | `pytest tests/test_verify_case_solution.py -k indigo -x` | ❌ Wave 0 + DB-present guard |
| IDENT-01 | SMILES-fallback finds a known COCONUT structure | integration (needs DB) | `pytest tests/test_verify_case_solution.py -k coconut -x` | ❌ Wave 0 |
| IDENT-02 | Reported name ≠ derived → verdict "tentative" + warning | unit | `pytest tests/test_verify_case_solution.py -k mismatch -x` | ❌ Wave 0 |
| IDENT-02 | CASE4 chamazulene wrong-isomer name → caught (no-hit, name not asserted) | regression | `pytest tests/test_verify_case_solution.py -k chamazulene -x` | ❌ Wave 0 |
| IDENT-02 | CASE5 indigo↔isoindigo mislabel → caught | regression | `pytest tests/test_verify_case_solution.py -k indigo_mislabel -x` | ❌ Wave 0 |
| IDENT-03 | No DB hit → identity marked tentative/novel, not asserted | unit | `pytest tests/test_verify_case_solution.py -k novel -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_verify_case_solution.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] Extend `tests/test_verify_case_solution.py` — identity derivation, two-path lookup, mismatch/no-hit verdicts, CASE4/CASE5 regression fixtures.
- [ ] DB-dependent tests need a guard: `@pytest.mark.skipif(DatabaseFinder.find_derep_database() is None, reason="reference DB not present")` so CI without the 2.8 GB DB still passes. (Pure-RDKit derivation tests need no DB.)
- [ ] No framework install needed (pytest present).

*Note: the existing black-box subprocess test style (no `lucy_ng` imports) is preserved for the default mode; identity tests may import `derive_identity` directly OR subprocess the new subcommand — recommend at least one subprocess test to lock the CLI contract.*

## Security Domain

`security_enforcement` is absent from `.planning/config.json`. This phase performs only read-only local SQLite queries on a bundled DB and pure RDKit computation — no auth, no network, no untrusted input beyond SMILES strings the analyst already produced. ASVS V5 (Input Validation) is the only marginally relevant category: SMILES are validated by `Chem.MolFromSmiles` returning `None` (already handled). Parameterized SQL (`?` placeholders) prevents injection — confirmed in the Pattern 1 example. No further controls required.

## Sources

### Primary (HIGH confidence)
- `data/reference/lucy-ng-derep.db` — direct sqlite3 queries (column counts, source split, regression-fixture lookups, timing, indexes). `[VERIFIED]`
- `scripts/verify_case_solution.py` — full read (existing contract, imports). `[VERIFIED]`
- `src/lucy_ng/database/importer.py:230-281` — canonicalization + empty inchi/inchi_key. `[VERIFIED]`
- `src/lucy_ng/database/manager.py:285-346` — only `get_by_formula`; no SMILES/InChIKey lookup exists. `[VERIFIED]`
- `src/lucy_ng/database/models.py` — `CompoundRecord` fields. `[VERIFIED]`
- `src/lucy_ng/database/finder.py:26-95` — `DatabaseFinder.find_derep_database()`; verified returns project DB. `[VERIFIED]`
- `src/lucy_ng/cli/dereplicate.py:200-253` — `entry.name`/`entry.inchi_key` surfacing precedent. `[VERIFIED]`
- `.claude/agents/lucy-solution-analyst.md` (§6 lines 155–193; `[RANKING-COMPLETE]` line 206; workflow 232–248). `[VERIFIED]`
- `.claude/agents/lucy-devils-advocate.md` (gate structure, Check-5 table lines 411–416). `[VERIFIED]`
- `.planning/CASE-DATASET-IDENTITIES.md` + memory `reference_case_identities.md` — CASE4/CASE5 ground-truth SMILES. `[CITED]`
- RDKit 2025.09.4 — `MolToInchiKey`/`MolToSmiles` behavior verified by direct execution. `[VERIFIED]`
- `pyproject.toml` `[tool.pytest.ini_options]`, `.planning/config.json`. `[VERIFIED]`

### Secondary (MEDIUM confidence)
- None required — all findings verified by direct tool execution against the real DB and source.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — RDKit + sqlite3 verified installed/used; no new packages.
- DB column state / lookup strategy: HIGH — confirmed by direct queries with hard numbers (the D-02 caveat is fully resolved).
- Regression fixtures: HIGH — CASE4/CASE5 structures verified against the live DB.
- Architecture / edit sites: HIGH — exact files and line ranges read.
- DA gate lifecycle: MEDIUM — the firing point is a design decision left to the planner (Open Question 1 / Pitfall 4).

**Research date:** 2026-06-23
**Valid until:** 2026-07-23 (stable — local code + bundled DB; only RDKit minor version could drift, low impact since same-major canonicalization is what matters).
