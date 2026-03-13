# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v7.0 — Statistical 4J Detection (ABANDONED)

**Abandoned:** 2026-03-12
**Phases:** 6 planned, 5 executed | **Plans:** 9 executed, all reverted

### What Was Built
- Schema v7 migration with coupling_path_stats table (3.78M entries from 895K compounds)
- CouplingPathStatsGenerator with checkpoint/resume pattern
- StatisticalDetector.detect_4j_coupling with three-tier classification
- detect_4j_batch with HOSE code pre-loading optimization
- CLI commands: `lucy detect 4j` and `lucy detect 4j-batch`
- Agent skill updates for statistical 4J detection across 3 agents
- **All reverted** — net code change: 0 lines

### What Worked
- **Rapid prototyping**: 5 phases (9 plans) executed in 2 days — fast enough to fail cheaply
- **Calibration before UAT**: Phase 63 calibration caught the fundamental flaw before wasting time on agent integration testing
- **Clean revert**: Single `git revert` cleanly removed all v7.0 code, 860 tests pass

### What Was Inefficient
- **Late calibration**: Should have run calibration on a small sample (1K compounds) BEFORE building the full pipeline (phases 59-62). The fundamental distribution problem would have been visible with 10K entries, not 3.78M
- **Full generation run**: 3.78M entries generated over hours, only to discover the metric is useless. A proof-of-concept with 1% sample would have saved significant compute time

### Patterns Established
- **Calibrate early**: For statistical approaches, validate the metric on a small sample before building full infrastructure
- **Fail fast, fail cheap**: When an approach has a theoretical risk, test the theory before building the tooling

### Key Lessons
1. **Aggregate pair distance statistics don't discriminate 4J**: Most atom pairs in any molecule are 5+ bonds apart, making "long-range path probability" meaningless as a discriminator
2. **The 4J problem needs solver-level exploration**: Statistical pre-filtering can't work because the question isn't "are these atoms far apart in general" but "are they far apart in THIS molecule" — which requires the solver
3. **Abandoned milestones are still valuable**: The post-mortem and calibration data prevent re-attempting the same failed approach

### Cost Observations
- Model mix: ~40% opus (orchestration, calibration analysis), ~60% sonnet (execution)
- Sessions: ~4
- Notable: 3 days of work with zero net code change — but the learning was essential

---

## Milestone: v6.0 — Skill Quality Overhaul

**Shipped:** 2026-03-10
**Phases:** 4 | **Plans:** 7 | **Sessions:** 3

### What Was Built
- Factored case.md orchestrator with 3 extracted reference files (progress-format, loop-patterns, advisory-templates)
- 4J HMBC coupling awareness pipeline: nmr-chemist flags → lsd-engineer defers → solution-analyst verifies
- Orchestrator message validation with RESEND-REQUIRED protocol
- Natural-language trigger phrases in all 5 skill descriptions + routing decision tree
- Error recovery in predict (HOSE miss) and dereplicate (0-match), dry-run gate in sanitise
- Version compatibility check in status, smoke test mode (--smoke-test) in CASE orchestrator

### What Worked
- **Auto-advance pipeline**: /gsd:plan-phase --auto executed 4 phases (plan → verify → execute → verify → complete) in a single session with minimal human interaction
- **Parallel execution**: Plans 57-01 and 57-02 ran in parallel (Wave 1) with non-overlapping file sections, completing in ~6 minutes combined
- **No Python changes**: Pure .md skill editing meant zero test failures, zero regressions, zero build issues — fastest milestone to ship
- **Integration checker**: Caught 2 genuine wiring gaps (aromatic expectation relay, 4J status validation) that individual phase verifiers missed

### What Was Inefficient
- **gsd-tools init can't find milestone-scoped phases**: Phases 55-58 exist in v6.0-ROADMAP.md but init returns phase_found=false. Required manual directory creation and variable setup each time
- **SUMMARY frontmatter inconsistency**: No `requirements-completed` field in SUMMARYs, making 3-source cross-reference incomplete in audit. The verification + traceability table was sufficient but the third source was weak

### Patterns Established
- **"Use when:" trigger phrase pattern**: Skill frontmatter descriptions with explicit trigger phrases for intent routing
- **Dry-run gate pattern**: READ-ONLY scan → manifest report → exact "proceed" confirmation before writes
- **Reference extraction pattern**: Large static content in references/ subdirectory, loaded on-demand via "Read file:" directives
- **Smoke test mode**: --smoke-test flag for 1-iteration pipeline validation with structured checkpoint table

### Key Lessons
1. **Skill-only milestones are fast**: 4 phases in 1 day with auto-advance. No test suite to run, no build to break — focus on content quality and integration wiring
2. **Integration checking matters most for .md changes**: Individual file verification passes easily but cross-file wiring (who relays what field to whom) is where gaps hide
3. **Milestone-scoped roadmaps need better tool support**: The init tool's inability to find phases in milestone-specific roadmaps added friction to every phase

### Cost Observations
- Model mix: ~30% opus (orchestration), ~70% sonnet (planning, execution, verification)
- Sessions: 3 (phases 55-56, phases 57-58, audit + complete)
- Notable: Auto-advance eliminated context switches between plan/execute/verify — single session handled phases 57 and 58 end-to-end

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v7.0 | ~4 | 6 | ABANDONED — calibrate statistical metrics early before building infrastructure |
| v6.0 | 3 | 4 | Auto-advance pipeline; pure .md editing; integration checker for wiring |

### Cumulative Quality

| Milestone | Tests | Coverage | Skill Lines |
|-----------|-------|----------|-------------|
| v7.0 | 860 (7 skipped) | — | ~4,200 (unchanged — all code reverted) |
| v6.0 | 867 (unchanged) | — | ~4,200 (skills + agents, factored with references) |

### Top Lessons (Verified Across Milestones)

1. Integration wiring is the highest-risk area for multi-agent skill architectures — individual files pass verification but cross-file field relay is where gaps hide
2. Calibrate statistical approaches on small samples before building full infrastructure — the distribution problem in v7.0 was visible at any scale
