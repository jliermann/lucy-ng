---
created: 2026-06-24
title: CASE run stalls ~5.5h — lsd-engineer goes idle after solver finishes without sending [ITERATION-COMPLETE]
area: skill
files:
  - .claude/commands/lucy-ng/case.md
  - .claude/commands/lucy-ng/references/loop-patterns.md
  - .claude/agents/lucy-lsd-engineer.md
---

## Problem

Blind CASE5 run (2026-06-24) "ran since the previous evening" and never surfaced a result;
only the user's poke revealed it was actually finished. Evidence in CASE-PROGRESS.md:

- iter 1 (line 75): "solutions.smi NOT generated — SMILES conversion ... stalled and the
  lsd-engineer went idle without sending [ITERATION-COMPLETE]. Coordinator recorded the
  count directly from analysis/iteration_01/solncounter."
- iter 2 (line 119): "solver finished ~09:25 Jun 24 but lsd-engineer went idle WITHOUT
  sending [ITERATION-COMPLETE] → workflow sat idle ~5.5 h until coordinator recovered it
  from the filesystem."

So the solver completed both times, but the lsd-engineer agent did not emit the completion
signal, and nothing polled/timed-out → the workflow hung until a human intervened. NO content
help was given (UAT remains valid); this is purely a coordination/completion-signal defect.

## Relationship to prior work

Sibling of the push-coordination fix (see memory `project_case_push_coordination`): idle
background agents don't poll, so case.md was rewritten push-based. That fix does NOT cover
this failure mode — here the worker FINISHED but never pushed [ITERATION-COMPLETE], and there
is no liveness/timeout watchdog on the coordinator side to detect "solver process gone +
solncounter present + no signal".

## Fix direction (to design)

- Coordinator-side liveness check: when an lsd-engineer task is outstanding, periodically
  check for solver completion on the filesystem (`solncounter` present + no LSD process via
  `ps`) and self-recover if no [ITERATION-COMPLETE] arrives within a threshold.
- And/or harden the lsd-engineer to ALWAYS send [ITERATION-COMPLETE] even when the
  (optional) SMILES conversion is skipped/stalled — decouple the signal from the conversion.
- Consider a max-idle timeout that escalates rather than hanging indefinitely.

Likely its own small reliability phase (not part of the Phase-87 IDENT scope).
