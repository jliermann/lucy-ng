---
description: "Use when working on lucy-ng CASE structure elucidation, NMR spectra, LSD constraints, HMBC/HSQC peak picking, solution ranking, or the CASE agent workflow."
---

# lucy-ng CASE Workflow

## Purpose

Use these conventions when working on the lucy-ng structure elucidation workflow.

## Core invariants

- Use `lucy` CLI commands for project-specific operations.
- HOSE-code prediction must use molecules without explicit hydrogens.
- `lucy lsd check` should report both `LSD` and `outlsd` when the environment is ready.
- The reference database is `data/reference/lucy-ng-derep.db`.
- Prefer direct spectral evidence over statistical priors when making hard constraints.
- When the structure is uncertain, keep the constraint set open and let ranking or diagnostics decide.

## Common commands

- `lucy read ...`
- `lucy pick ...`
- `lucy analyze ...`
- `lucy detect ...`
- `lucy lsd check`
- `lucy lsd run ...`
- `lucy lsd rank ...`
- `lucy predict c13 ...`
- `lucy identify ...`

## Agent workflow

1. Analyze spectra and assign peaks.
2. Build LSD constraints from direct evidence.
3. Validate the LSD file before running the solver.
4. Run the solver and inspect solution counts.
5. Rank candidate structures with 13C prediction.
6. Derive identity with `lucy identify` before writing the final report.

## Output style

- Be explicit about blockers and assumptions.
- Prefer structured summaries with: findings, impact, next step, and confidence.
- Do not rely on Claude Code messaging primitives; Copilot agents should return the result directly.
