---
created: 2026-06-30
title: hosegen-dependent ranking tests hard-fail instead of skipif(not HOSEGEN_AVAILABLE)
area: tests
files:
  - tests/test_ranking.py
---

## Problem

The hosegen-dependent tests in `tests/test_ranking.py` (TestRankCLIBackendWiring,
TestRankPredictParity, TestRankMAEAgreement, TestRankOrderingNonCircular,
TestRankRealDBOrderingFix, TestResolveC13Predictor.test_resolve_propagates_max_radius)
**hard-fail** when `hose-code-generator` is not installed — the CLI returns
`hosegen package not installed` (exit 1) and the assertions fail.

Surfaced during PR #1 review (2026-06-30): a fresh `uv sync` env (no hosegen — it is a
separate `--no-deps` install) produced 44 spurious failures that were purely the missing
hosegen, not a real regression. This is a confounder for CI / any clean env.

DB-dependent tests already use `skipif(... find_*_database() is None)`; the
hosegen-dependent ones should similarly `@pytest.mark.skipif(not HOSEGEN_AVAILABLE, ...)`
(import `HOSEGEN_AVAILABLE` from `lucy_ng.prediction`). Low priority, test-hygiene only —
no production code involved.

## Acceptance
- A clean env without hosegen runs `pytest tests/test_ranking.py` with the hosegen-dependent
  tests SKIPPED (not failed); they still run + pass when hosegen is present.
