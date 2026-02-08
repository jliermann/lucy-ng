# Phase 32: End-to-End Validation - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate that the multi-agent CASE orchestration actually works end-to-end. Prepare everything needed for the user to run `/lucy-ng:case` on Ibuprofen data and verify the full pipeline (spawn agent, write progress, monitor, detect loops, intervene if needed, converge to correct structure). Also verify simple sub-commands work.

</domain>

<decisions>
## Implementation Decisions

### Test execution approach
- **Prepare and hand off** — Phase 32 gets everything ready and documents what to run; user tests in a fresh session afterward
- No live test execution during phase — user runs `/lucy-ng:case` themselves and reports back
- If the test reveals issues, user will report what failed and we iterate

### Test formality
- **Live run only** — No pytest scaffolding, no automated test scripts
- The real test is invoking `/lucy-ng:case` on Ibuprofen data and observing whether it works end-to-end
- No "minimum 10 integration tests" — the Ibuprofen CASE run IS the validation
- If Ibuprofen works, user tests more datasets manually

### Sub-command testing
- **Leave for manual** — /lucy-ng:dereplicate, /lucy-ng:predict, /lucy-ng:status also tested by user, not during phase execution

### Fix strategy
- **Claude's discretion** — If issues are found, decide based on severity whether to fix in Phase 32 or create follow-up

### What Phase 32 actually delivers
- Pre-flight checks: verify all files exist, agents are defined, skills are reachable
- Documentation: clear instructions for running the Ibuprofen CASE test
- Test dataset readiness: confirm Ibuprofen data is available and accessible
- Expected outcomes: document what success looks like (correct structure in top 3, CASE-PROGRESS.md created, etc.)

</decisions>

<specifics>
## Specific Ideas

- User said: "I will test the system on various datasets if the Ibuprofen case works (for me). Otherwise, I will let you know what failed."
- The Ibuprofen CASE test should reproduce Phase 26-05's success but through the full orchestration path (/lucy-ng:case → spawn agent → monitor → converge)
- Phase 26-05 already validated Ibuprofen de novo CASE with thin CLI + skill — this phase validates the orchestration wrapper works

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 32-end-to-end-validation*
*Context gathered: 2026-02-08*
