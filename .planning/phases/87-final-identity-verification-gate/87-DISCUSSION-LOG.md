# Phase 87: Final Identity-Verification Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-23
**Phase:** 87-final-identity-verification-gate
**Areas discussed:** Identity-Tool, Gate-Ort, Gate-Severity, Tentative-Form, Lookup-Form

---

## Identity-Tool (IDENT-01)

| Option | Description | Selected |
|--------|-------------|----------|
| InChIKey + DB-Name-Lookup (Fallback canonical-SMILES) | RDKit InChIKey from solved SMILES → match against 928K reference DB (inchi_key, else canonical SMILES); no hit → "not in DB / novel" | ✓ |
| Struktureller Identifier primär | InChIKey + canonical SMILES as identity; trivial name only if DB-confirmed | |
| lucy dereplicate Cross-Check | Spectrum-based dereplicate result must agree with solved structure's InChIKey | |

**User's choice:** InChIKey + DB-Name-Lookup with canonical-SMILES fallback.
**Notes:** DB `inchi_key` column likely empty (importer skips InChI/InChIKey generation) — fallback to canonical-SMILES match required; novel-compound no-hit is a first-class outcome.

---

## Gate-Ort (IDENT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Beide: Skript (blockierend) + devils-advocate (advisory) | Deterministic name↔structure check in verify_case_solution.py (authoritative) + devils-advocate LLM plausibility check | ✓ |
| Nur verify_case_solution.py | Deterministic only, no LLM in the gate | |
| Nur devils-advocate | Agent-prompt only, no Python change | |

**User's choice:** Both — deterministic script (authoritative) + devils-advocate (advisory).

---

## Gate-Severity (mismatch handling)

| Option | Description | Selected |
|--------|-------------|----------|
| Name auf 'tentative' herabstufen + Warnung | Report proceeds; name flagged unverified, discrepancy surfaced | ✓ |
| Report blockieren (hard fail) | Mismatch blocks output until resolved | |

**User's choice:** Downgrade name to tentative + prominent warning.
**Notes:** "Blocking" means blocking the *assertion of the name as fact*, not the whole report — structural result still reports. Chosen because CASE targets are often novel.

---

## Tentative-Form (IDENT-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Strukturelle ID primär, Trivialname als '(tentative, unverified)' | InChIKey/SMILES as identity; model-suggested name explicitly qualified | ✓ |
| Trivialnamen ganz weglassen wenn unbestätigt | No unconfirmed names at all | |

**User's choice:** Structural ID primary; unconfirmed trivial name rendered "(tentative, unverified)" with confidence qualifier.

---

## Lookup-Form

| Option | Description | Selected |
|--------|-------------|----------|
| In verify_case_solution.py integrieren (kein neues CLI) | InChIKey gen + DB-name lookup live in the extended gate script; analyst calls the same script/function | ✓ |
| Neues `lucy identify` CLI-Subcommand | Dedicated reusable subcommand | |

**User's choice:** Integrate into verify_case_solution.py — no new CLI.

---

## Claude's Discretion

- Exact wording of the confidence qualifier and warning string.
- Internal shape of the extended verify_case_solution.py (subcommand vs importable function), as long as one shared deterministic path is integrated in the script.
- Subprocess vs import for the analyst's invocation.

## Deferred Ideas

- Standalone `lucy identify` CLI subcommand — deferred in favor of integrating into verify_case_solution.py; revisit if a second consumer emerges.
- Multiplicity-model-hardcoding todo (2026-06-23) — reviewed but belongs to Phase 88 (Aliphatic Multiplicity Robustness), not folded.
