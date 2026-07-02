# Phase 88: Aliphatic Multiplicity Robustness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-25
**Phase:** 88-aliphatic-multiplicity-robustness
**Areas discussed:** Parallel-family mechanism, Family enumeration & bounding, MAE-independent guardrail (MULT-02), Ambiguity detection + DA-flag hardening (MULT-04/03)

---

## Parallel-family search mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Separate LSD runs + union | Per-family fully-constrained LSD run in its own iteration dir, union solution sets, rank across union | ✓ |
| Single run, relaxed MULT | One LSD run with under-specified MULT, LSD explores both | |
| Sequential (fallback) | Leading family first; alternative only on poor convergence | |

**User's choice:** Separate LSD runs + union (recommended).
**Notes:** Sequential is essentially the CASE4 failure mode (leading family looks "good enough" → truth excluded). Relaxed-MULT risks explosion + LSD not enumerating intended families cleanly.

---

## Family enumeration & bounding

| Option | Description | Selected |
|--------|-------------|----------|
| Whole-molecule partitions + cap | Chemically sensible whole-molecule aliphatic partitions consistent with formula/H-count/DBE; hard cap ≤3–4; document truncation | ✓ |
| Per-center + cross-product cap | Enumerate each ambiguous center, cap the cross-product | |
| Only on explicit DA flag | No enumeration logic; split only when DA names an alternative | |

**User's choice:** Whole-molecule partitions + cap (recommended).
**Notes:** Per-center explodes faster and is harder to justify chemically. DA-flag-only misses ambiguities the DA doesn't explicitly name.

---

## MAE-independent guardrail (MULT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Coverage gate before accept | nmr-chemist's viable-families list must be fully covered by searched set; ≥2 viable but not all searched → do not accept, reopen | ✓ |
| Reopen only on DA flag | Reopen strictly coupled to a DA-named alternative | |
| Advisory warning only | Warn but allow accept | |

**User's choice:** Coverage gate before accept (recommended).
**Notes:** Advisory-only is the CASE4 mode (guardrail silent at MAE 1.75). The gate must be MAE-independent and checklist-based.

---

## MULT-04 detection + MULT-03 DA-flag hardening

| Option | Description | Selected |
|--------|-------------|----------|
| Programmatic + DA-flag binding | Deterministic ambiguity detection (0 negative HSQC pixels / phase-distorted APT) → [MULTIPLICITY-AMBIGUOUS] + families; DA "evidence FOR model X" = mandatory search item, not rationalizable away | ✓ |
| Heuristic + advisory | Agent judges ambiguity; DA flag advisory | |
| Programmatic detection, advisory DA flag | Hard detection, but DA flag stays dismissible | |

**User's choice:** Programmatic + DA-flag binding (recommended).
**Notes:** Heuristic/advisory variants are vulnerable to exactly the CASE4 rationalization (the diagnostic HMBC "evidence for ethyl" was re-explained as gem-dimethyl coupling and dismissed).

## Claude's Discretion

- Exact family cap number (≤3–4 target); iteration sub-directory naming.
- Token/format of the `[MULTIPLICITY-AMBIGUOUS]` message + coverage-gate checklist representation.
- Union-ranking implementation (concatenate solutions.smi + one rank vs per-family then merge).
- Per-family MULT-constraint construction detail.

## Deferred Ideas

- Parallel-family search for non-aliphatic (heteroatom/exchangeable) multiplicity ambiguities.
- A 13C predictor that separates iPr-methine from ethyl-CH₂ strongly enough to penalize the wrong class by MAE (this phase fixes coverage, not ranking discrimination).
