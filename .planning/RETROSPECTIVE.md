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

## Milestone: v9.0 — CASE Reliability & Skill Consolidation

**Shipped:** 2026-06-17
**Phases:** 14 (72–85) | **Plans:** 34

### What Was Built
- Solution plumbing: `lucy lsd run`/outlsd produces real ranked SMILES + fails loud; deterministic cross-ring COSY derivation (`lucy detect aromatic-cosy`).
- Native-only constraint translation (SYME→BOND/COSY, DEFF NOT→DEFF F/FEXP) across all paths + permutation constraint preservation; devils-advocate G5–G8 gates.
- Peak-picking integrity: SNR-floor for 13C (FIX-08) and HMBC (FIX-12) + overcount guard.
- Constraint-hardness guard (FIX-10); blind-UAT skill decontamination (FIX-09); Kekulé-aromatize-before-predict (FIX-11).
- Validation: CASE9 solved (UAT-04) + CASE1 clean emergent pass (UAT-03).

### What Worked
- **Goal-backward blind UAT as the gate**: repeatedly failing the blind UAT (Phases 76/78/79/80) surfaced the *real* upstream defects (peak-picking) instead of letting a green unit suite mask them.
- **Independent RDKit verification by a tainted bookkeeper**: kept "found ibuprofen" claims honest (caught the ortho-vs-para distinction and the rank-vs-predict MAE discrepancy).
- **Fix the model, not just the skill**: the single highest-leverage fix was `CLAUDE_CODE_SUBAGENT_MODEL=inherit` — many "skill" failures were Sonnet-4.6-driven.

### What Was Inefficient
- **Long chain of failed gates (76→78→79→80→81)**: each blind UAT exposed one more upstream layer (LSD mechanism → carbonyl masking → 4J trap → peak-picking flood). Earlier raw-spectrum inspection would have found the snr_floor=3 noise flood sooner.
- **Auto-memory contaminated the "blind" UAT**: per-data-dir auto-memory leaked the answer into supposedly-blind runs; required quarantine + `autoMemoryEnabled:false` + workspace-trust to make blind runs repeatable.

### Patterns Established
- **Blind-UAT hygiene**: quarantine per-data-dir memory + `autoMemoryEnabled:false` before each blind run; orchestrating instance is bookkeeper only.
- **SNR-floor over fraction-of-max**: noise-relative thresholds for both 1D and 2D pickers so weak-but-real signals survive.
- **Constraint-hardness discipline**: statistical/uncertain inferences stay advisory; never hard PROP/BOND that can exclude the truth.

### Key Lessons
1. A green unit suite is not validation — only the end-to-end blind UAT against real spectra caught the upstream peak-picking defects.
2. Confirm the runtime model before blaming the skill — a silent subagent-model override caused failures no skill edit could fix.
3. Auto-memory and repeatable blind testing conflict; isolate test fixtures from persistent memory.

### Cost Observations
- Model mix: Opus 4.8 for CASE runs + orchestration (the model upgrade was itself the decisive fix)
- Notable: the winning run needed 0 coordinator bypass interventions — the mechanism finally carried the result

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v9.0 | many | 14 | Blind UAT as the real gate; fix the runtime model, not just the skill; blind-UAT memory hygiene |
| v7.0 | ~4 | 6 | ABANDONED — calibrate statistical metrics early before building infrastructure |
| v6.0 | 3 | 4 | Auto-advance pipeline; pure .md editing; integration checker for wiring |

### Cumulative Quality

| Milestone | Tests | Coverage | Skill Lines |
|-----------|-------|----------|-------------|
| v9.0 | 1081 passing | — | 4-agent team + orchestrator (repo/.claude, symlinked) |
| v7.0 | 860 (7 skipped) | — | ~4,200 (unchanged — all code reverted) |
| v6.0 | 867 (unchanged) | — | ~4,200 (skills + agents, factored with references) |

### Top Lessons (Verified Across Milestones)

1. Integration wiring is the highest-risk area for multi-agent skill architectures — individual files pass verification but cross-file field relay is where gaps hide
2. Calibrate statistical approaches on small samples before building full infrastructure — the distribution problem in v7.0 was visible at any scale
3. A green unit suite ≠ validation — the end-to-end blind UAT against real data is the only gate that catches upstream (peak-picking) defects (v9.0)
4. Verify the runtime model/config before attributing failures to the skill — a silent subagent-model override drove much of the v9.0 failure chain
