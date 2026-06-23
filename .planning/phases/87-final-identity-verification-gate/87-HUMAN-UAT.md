---
status: partial
phase: 87-final-identity-verification-gate
source: [87-VERIFICATION.md]
started: 2026-06-23T00:00:00Z
updated: 2026-06-23T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Blind CASE re-run with reloaded agents (Phase-89 UAT-02)
expected: In a FRESH Claude Code session (required to reload the edited CASE agents), a blind CASE re-run (CASE5 sanitised = the IDENT acceptance test) shows: the solution-analyst calls `check-identity` on the top SMILES, renders the tool-derived identity (never a recalled name), and marks non-confirmed trivial names `(tentative, unverified)`; the devils-advocate runs the G-IDENT post-solution advisory gate and flags any name↔structure mismatch.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
