# Phase 32: End-to-End Validation - Research

**Researched:** 2026-02-08
**Domain:** System validation, integration testing, pre-flight checks, manual test documentation
**Confidence:** HIGH

## Summary

Phase 32 validates that the multi-agent CASE orchestration built in Phases 27-31 actually works when invoked. This is NOT a code-heavy phase — it's a "prepare and hand off" validation where we verify all components are in place, document what to test, and prepare clear instructions for the user to run the tests themselves in a fresh session.

The critical context: v2.0 shipped a "paper architecture" where agents were defined but never executed. Phase 32 is the validation gate that prevents repeating this mistake. All components exist (agent definitions, orchestrator skill, sub-command skills, domain knowledge) but have never been invoked via the Task tool spawning mechanism.

**Primary recommendation:** Create pre-flight verification script, comprehensive test documentation with expected outcomes, and structured handoff checklist. Focus on "what could go wrong" analysis based on known integration gaps.

## Standard Stack

This is a validation phase, not a build phase. The "stack" is the verification toolchain.

### Core
| Tool | Purpose | Why Standard |
|------|---------|--------------|
| Bash scripts | Pre-flight checks | Native, no dependencies, direct file/tool verification |
| lucy-ng CLI | System under test | The actual tool being validated |
| Manual invocation | Integration tests | Only way to test Task() spawning (can't automate agent spawning) |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `test -f` | File existence checks | All agent/skill file verification |
| `grep` | Content verification | Ensure files have required sections |
| `wc -l` | Substantive checks | Verify files aren't stubs |
| `ls -la` | Permission/ownership | Verify files are readable by Claude Desktop |

**No test frameworks:** Per user decision, no pytest scaffolding. Live manual runs ARE the validation.

## Architecture Patterns

### Pre-Flight Check Pattern

Validation phases should verify prerequisites BEFORE attempting execution.

**NASA V&V Pattern (aerospace validation):**
- Verify all components exist
- Verify interfaces are correct
- Verify configuration is valid
- THEN attempt integration testing

**Applied to Phase 32:**
1. File existence checks (all agents/skills present)
2. Content checks (no stubs, required sections present)
3. Environment checks (lucy-ng, LSD, database available)
4. THEN document test invocation

**Source:** NASA Verification and Validation Plan Outline — systems must be verified independently before integration testing.

### Handoff Documentation Pattern

When validation requires manual execution (can't be automated), clear handoff documentation is critical.

**Key components (from software handoff best practices):**
1. **What to run** — exact commands with no ambiguity
2. **Expected outcomes** — what success looks like (specific output, files created)
3. **How to verify** — step-by-step checks after each test
4. **Troubleshooting guide** — known failure modes and how to recognize them
5. **Reporting structure** — what information to provide if tests fail

**Applied to Phase 32:**
- Ibuprofen test script with exact invocation
- Expected CASE-PROGRESS.md structure and convergence criteria
- Known failure modes (Task spawning, agent context, LSD solver issues)
- Structured feedback template for user

**Source:** IT Project Handover Checklist — successful handoffs require clear documentation of test procedures and success criteria.

### Integration Gap Analysis Pattern

When paper architecture transitions to live execution, focus on integration points that haven't been tested.

**Known integration gaps (from Phase 28/29 summaries):**

| Gap | Risk | Detection Method |
|-----|------|------------------|
| Task() spawning | Agent never actually spawned | Invoke /lucy-ng:case, check agent thread created |
| model: inherit | Agent uses wrong model (Sonnet 4 vs Opus 4.6) | Check agent responses for capability level |
| CASE-PROGRESS.md writing | Agent might not write progress | Check file created after spawning |
| Agent file paths | Relative paths fail from different working dir | Agent should use absolute paths (verified in Phase 28) |
| skill/ file references | Agent can't find skill files if cwd wrong | Test agent reads skill/SKILL.md correctly |
| LSD file writing | Agent writes invalid LSD syntax | Run lucy lsd run on agent-written file |
| Advisory intervention parsing | Orchestrator re-spawns with constraints | Requires loop detection test (deferred per CONTEXT.md) |

**Validation approach:**
- Test the SIMPLEST path first (Ibuprofen happy path)
- If simple path fails, gaps surface immediately
- Document gaps for iterative fixing

### Anti-Patterns to Avoid

**Anti-pattern 1: Test theater**
Don't create elaborate test scaffolding that validates the scaffolding instead of the system. The system under test is "invoke /lucy-ng:case and observe outcome." Testing anything else is misdirection.

**Anti-pattern 2: Success bias**
Don't only document success criteria. Failure modes are equally important. "What does it look like when Task spawning fails?" is critical.

**Anti-pattern 3: Assuming prerequisites**
Don't assume user environment matches development environment. LSD might be missing, database might not be downloaded, permissions might differ. Check EVERYTHING.

## Don't Hand-Roll

Problems that look simple but need existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test framework | Custom test runner with result reporting | Manual invocation + structured docs | User decision: live runs only, no pytest (CONTEXT.md) |
| Pre-flight automation | Complex dependency checker with auto-fix | Simple bash script with clear error messages | Transparency over magic — user needs to understand failures |
| Agent spawning validation | Synthetic Task() test harness | Real CASE invocation on Ibuprofen | Only way to test is the real thing |

**Key insight:** This phase is about proving the REAL system works, not building test infrastructure. Minimize tooling, maximize real execution.

## Common Pitfalls

### Pitfall 1: Task Tool Model Inheritance Bug

**What goes wrong:** When using Task tool to spawn sub-agents, they default to Claude Sonnet 4 instead of inheriting the configured model (Claude Opus 4.6) from parent.

**Why it happens:** Known bug in Claude Desktop Task tool (GitHub issue #5456). Even with `model: inherit` in agent frontmatter, spawned agents may not get parent's model.

**How to avoid:**
- Verify lucy-case-agent.md has `model: inherit` in frontmatter (already verified in Phase 28)
- During testing, check agent responses for Opus 4.6 capabilities
- If agent seems "dumber" than expected, model inheritance likely failed

**Warning signs:**
- Agent makes basic mistakes that Opus 4.6 wouldn't make
- Agent can't handle complex multi-step reasoning
- Agent responses are shorter/less detailed than expected

**Source:** GitHub issue #5456 "Sub-agents Don't Inherit Model Configuration in Task Tool"

### Pitfall 2: Agent Working Directory Mismatch

**What goes wrong:** Agent spawned by Task tool has different working directory than orchestrator. Relative file paths (e.g., `data/Ibuprofen/`) fail with "file not found."

**Why it happens:** Task tool resets agent working directory to user home or project root (implementation-dependent). Agent can't find files specified with relative paths.

**How to avoid:**
- Phase 28 already implemented absolute path strategy
- Agent should use `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen/`
- NOT `data/Ibuprofen/`

**Warning signs:**
- Agent reports "directory not found" for paths that exist
- Agent writes files to unexpected locations
- `ls` commands in agent bash calls fail

**Detection:** Check first agent bash command. If it uses relative paths and fails, this is the issue.

### Pitfall 3: CASE-PROGRESS.md Not Created

**What goes wrong:** Orchestrator spawns agent, waits for CASE-PROGRESS.md, file never appears, orchestrator hangs or errors.

**Why it happens:**
- Agent doesn't have Write tool access (but Phase 28 verified tools list)
- Agent has wrong output directory path
- Agent workflow doesn't reach progress writing step (crashes earlier)

**How to avoid:**
- Pre-flight check: verify agent frontmatter has `tools: Read, Write, Bash, Glob, Grep`
- Test documentation: explicitly check for CASE-PROGRESS.md creation
- Timeout: if agent runs >10 min without progress file, something's wrong

**Warning signs:**
- Orchestrator waits indefinitely
- No CASE-PROGRESS.md in project root or compound directory
- Agent completes but no file written

**Detection:** After spawning agent, check for CASE-PROGRESS.md within 2-3 minutes. If absent, agent failed.

### Pitfall 4: LSD Solver Not Available

**What goes wrong:** Agent tries to run `lucy lsd run compound.lsd`, gets "LSD not found" error, CASE workflow fails.

**Why it happens:**
- LSD not installed on system
- LSD installed but not in PATH
- outlsd missing (needed for SMILES conversion)

**How to avoid:**
- Pre-flight check MUST verify: `lucy lsd check`
- Should report "LSD: available, outlsd: available"
- If either missing, STOP and instruct user to install

**Warning signs:**
- Agent reports "command not found: LSD"
- lucy lsd check fails in pre-flight

**Detection:** Pre-flight check catches this before spawning agent.

### Pitfall 5: Database Missing or Corrupt

**What goes wrong:** Agent tries to run `lucy lsd rank`, gets database error, ranking fails.

**Why it happens:**
- Database not downloaded (lucy database download never run)
- Database corrupted during download
- Database at wrong path

**How to avoid:**
- Pre-flight check MUST verify: `lucy database info data/reference/lucy-ng-derep.db`
- Should report "928,443 compounds"
- If fails, STOP and instruct user to run lucy database download

**Warning signs:**
- `lucy database info` reports file not found
- Reports different compound count
- SQLite errors during ranking

**Detection:** Pre-flight check catches this before spawning agent.

### Pitfall 6: Ibuprofen Data Path Wrong

**What goes wrong:** User invokes `/lucy-ng:case data/Ibuprofen C13H18O2`, but actual path is `data/compound/Ibuprofen`.

**Why it happens:** Confusion about project directory structure. Directory is actually named just "Ibuprofen" not "compound/Ibuprofen" (verified via bash: data/Ibuprofen/ exists).

**How to avoid:**
- Test documentation provides EXACT path to use
- Pre-flight check verifies Ibuprofen directory exists
- Clear error message if path doesn't exist

**Warning signs:**
- Orchestrator reports "compound directory not found"
- Path in test docs doesn't match actual filesystem

**Detection:** Pre-flight check: `ls /Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen/`

### Pitfall 7: Permissions Issues

**What goes wrong:** Agent can't write CASE-PROGRESS.md or LSD files due to permission denied errors.

**Why it happens:**
- Project directory not writable by Claude Desktop process
- Agent tries to write to protected system directory

**How to avoid:**
- Pre-flight check: verify project directory is writable
- Agent writes to project root or compound directory (both should be user-owned)

**Warning signs:**
- "Permission denied" errors in agent output
- Files created but empty

**Detection:** Pre-flight check: `touch /Users/steinbeck/Dropbox/develop/lucy-ng/.test-write && rm /Users/steinbeck/Dropbox/develop/lucy-ng/.test-write`

## Code Examples

### Pre-Flight Check Script

```bash
#!/bin/bash
# Phase 32 Pre-Flight Validation
# Verifies all components are ready for end-to-end testing

PROJECT_ROOT="/Users/steinbeck/Dropbox/develop/lucy-ng"
ERRORS=0

echo "=== Phase 32 Pre-Flight Checks ==="
echo ""

# 1. Agent definitions exist
echo "1. Checking agent definitions..."
if [ -f ~/.claude/agents/lucy-case-agent.md ]; then
    echo "   ✓ lucy-case-agent.md exists"
else
    echo "   ✗ lucy-case-agent.md MISSING"
    ERRORS=$((ERRORS + 1))
fi

if [ -f ~/.claude/agents/lucy-diagnostic.md ]; then
    echo "   ✓ lucy-diagnostic.md exists"
else
    echo "   ✗ lucy-diagnostic.md MISSING"
    ERRORS=$((ERRORS + 1))
fi

# 2. Sub-command skills exist
echo ""
echo "2. Checking sub-command skills..."
for skill in case dereplicate predict status sanitise lucy-ng; do
    if [ -f ~/.claude/commands/lucy-ng/${skill}.md ]; then
        echo "   ✓ ${skill}.md exists"
    else
        echo "   ✗ ${skill}.md MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# 3. Skill files exist
echo ""
echo "3. Checking skill files..."
for skill in skill/SKILL.md skill/CASE/SKILL.md skill/supervisor/SKILL.md skill/diagnostic/SKILL.md; do
    if [ -f "${PROJECT_ROOT}/${skill}" ]; then
        echo "   ✓ ${skill} exists"
    else
        echo "   ✗ ${skill} MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. lucy-ng CLI available
echo ""
echo "4. Checking lucy-ng CLI..."
if command -v lucy &> /dev/null; then
    VERSION=$(lucy --version 2>&1)
    echo "   ✓ lucy-ng installed: ${VERSION}"
else
    echo "   ✗ lucy-ng NOT FOUND (run: pip install lucy-ng)"
    ERRORS=$((ERRORS + 1))
fi

# 5. LSD solver available
echo ""
echo "5. Checking LSD solver..."
LSD_CHECK=$(lucy lsd check 2>&1)
if echo "$LSD_CHECK" | grep -q "LSD: available"; then
    echo "   ✓ LSD available"
else
    echo "   ✗ LSD NOT FOUND (download from http://eos.univ-reims.fr/LSD/)"
    ERRORS=$((ERRORS + 1))
fi

if echo "$LSD_CHECK" | grep -q "outlsd: available"; then
    echo "   ✓ outlsd available"
else
    echo "   ✗ outlsd NOT FOUND (download from http://eos.univ-reims.fr/LSD/)"
    ERRORS=$((ERRORS + 1))
fi

# 6. Database available
echo ""
echo "6. Checking compound database..."
DB_INFO=$(lucy database info data/reference/lucy-ng-derep.db 2>&1)
if echo "$DB_INFO" | grep -q "928,443"; then
    echo "   ✓ Database available (928,443 compounds)"
else
    echo "   ✗ Database MISSING or CORRUPT (run: lucy database download)"
    ERRORS=$((ERRORS + 1))
fi

# 7. Ibuprofen test data available
echo ""
echo "7. Checking Ibuprofen test data..."
if [ -d "${PROJECT_ROOT}/data/Ibuprofen" ]; then
    EXPT_COUNT=$(ls -d ${PROJECT_ROOT}/data/Ibuprofen/*/ 2>/dev/null | wc -l)
    echo "   ✓ Ibuprofen data exists (${EXPT_COUNT} experiments)"
else
    echo "   ✗ Ibuprofen data MISSING"
    ERRORS=$((ERRORS + 1))
fi

# 8. Project directory writable
echo ""
echo "8. Checking project directory permissions..."
if touch "${PROJECT_ROOT}/.test-write" 2>/dev/null; then
    rm "${PROJECT_ROOT}/.test-write"
    echo "   ✓ Project directory writable"
else
    echo "   ✗ Project directory NOT WRITABLE"
    ERRORS=$((ERRORS + 1))
fi

# 9. Agent frontmatter checks
echo ""
echo "9. Checking agent configuration..."
if grep -q "^model: inherit" ~/.claude/agents/lucy-case-agent.md; then
    echo "   ✓ lucy-case-agent has 'model: inherit'"
else
    echo "   ✗ lucy-case-agent MISSING 'model: inherit' (Task spawning may use wrong model)"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "^tools: Read, Write, Bash, Glob, Grep" ~/.claude/agents/lucy-case-agent.md; then
    echo "   ✓ lucy-case-agent has required tools"
else
    echo "   ✗ lucy-case-agent MISSING required tools"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "✓ All pre-flight checks passed. Ready for testing."
    exit 0
else
    echo "✗ ${ERRORS} check(s) failed. Fix issues before testing."
    exit 1
fi
```

### Test Invocation Template

```bash
# Ibuprofen CASE Test (reproduces Phase 26-05 via orchestration)

# Expected: Orchestrator spawns agent, agent performs CASE,
# correct structure appears in top 3 ranked solutions

/lucy-ng:case /Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen C13H18O2

# What to observe:
# 1. Task tool spawns lucy-case-agent (new thread created)
# 2. Agent writes CASE-PROGRESS.md to project root
# 3. Agent iterates through LSD cycles (observable in progress file)
# 4. Agent converges to ≤10 solutions
# 5. Orchestrator presents ranked results
# 6. Ibuprofen structure CC(C)Cc1ccc(cc1)C(C)C(=O)O in top 3

# Failure modes:
# - "Agent not found" → lucy-case-agent.md missing or invalid
# - "LSD not found" → Pre-flight check failed
# - Agent hangs → Check working directory / file paths
# - No CASE-PROGRESS.md → Agent crashed before writing
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Automated integration tests | Manual invocation + documentation | Phase 32 (user decision) | Tests the REAL system, not a test harness |
| pytest scaffolding | Live runs with structured reporting | Phase 32 (user decision) | Faster setup, real-world validation |
| Synthetic test data | Production dataset (Ibuprofen) | Phase 32 (from Phase 26-05) | Validates against known-good case |
| Test everything | Test happy path first | Phase 32 (prepare-and-hand-off) | Surfaces integration gaps quickly |

**Recent pattern shift (2026):**
Claude Desktop Task tool introduced native agent spawning (January 2026). Previous testing approaches assumed pytest-style automation, but Task() spawning can't be automated by spawned agents themselves (no recursive spawning). Manual invocation is now the standard validation approach for multi-agent systems.

**Deprecated approaches:**
- Building custom test harnesses for Task tool validation
- Attempting to automate agent spawning in test frameworks
- Using mock/stub agents instead of real definitions

## Open Questions

### Question 1: Should loop detection tests be included in Phase 32?

**What we know:**
- User decided "live run only" (no pytest)
- CONTEXT.md specifies "prepare and hand off"
- Requirements VALD-02 and VALD-03 mention loop detection and diagnostic delegation tests

**What's unclear:**
- Does "prepare and hand off" mean defer ALL tests including loop detection?
- Or does it mean document loop tests for user to run manually?

**Recommendation:**
Document loop detection test scenarios (force ELIM thrashing, force zero solutions) in the handoff documentation, but mark as "optional advanced tests." User can run after Ibuprofen happy path succeeds. Don't attempt during Phase 32 execution.

**Rationale:**
- Ibuprofen test validates basic orchestration (Task spawning, progress monitoring, convergence)
- Loop detection requires forcing failure states (more complex)
- User said "I will test various datasets if Ibuprofen works" — let user drive additional testing

### Question 2: How to verify model inheritance actually works?

**What we know:**
- Known bug: Task spawning may ignore `model: inherit`
- Agent has `model: inherit` in frontmatter (verified Phase 28)
- No programmatic way to query which model a spawned agent uses

**What's unclear:**
- How does user verify the agent is using Opus 4.6 vs Sonnet 4?
- What specific behaviors indicate wrong model?

**Recommendation:**
Include in test documentation: "Observe agent response quality. Opus 4.6 should demonstrate deep domain reasoning, detailed explanations, and complex multi-step analysis. If agent responses seem shallow or make basic mistakes, model inheritance may have failed."

**Validation approach:**
- Subjective quality assessment (no hard metric)
- Trust Phase 28 verification that frontmatter is correct
- If user suspects wrong model, check agent thread model indicator in Claude Desktop UI

### Question 3: What if Ibuprofen test reveals integration bugs?

**What we know:**
- User decision: "If issues found, decide based on severity whether to fix in Phase 32 or create follow-up"
- This is Claude's discretion area

**What's unclear:**
- Severity threshold for "fix now" vs "defer to follow-up phase"
- How many fix iterations are acceptable within Phase 32?

**Recommendation:**

**Fix immediately (within Phase 32):**
- File path bugs (wrong paths preventing agent from running)
- Missing frontmatter fields (agent definition errors)
- Pre-flight check failures (environment not ready)

**Defer to follow-up:**
- LSD logic bugs (agent writes invalid constraints → skill issue, not integration)
- Performance issues (agent takes too long but works correctly)
- Model inheritance bug (external Claude Desktop bug, not our code)

**Threshold:** If fix requires <30 min and unblocks testing, fix now. If fix requires investigating domain logic or external dependencies, defer and document.

## Sources

### Primary (HIGH confidence)

- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/28-case-agent-definition/28-01-SUMMARY.md` - Agent definition details, validation approach
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/29-case-orchestrator-skill/29-01-SUMMARY.md` - Orchestrator implementation, monitoring logic
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/26-thin-tools/26-05-PLAN.md` - Ibuprofen test specifics, expected outcomes
- `~/.claude/agents/lucy-case-agent.md` - Agent frontmatter, tools, model setting (verified exists, 613 lines)
- `~/.claude/commands/lucy-ng/case.md` - Orchestrator skill, 12-step process (verified exists, 698 lines)
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/REQUIREMENTS.md` - Phase 32 requirements (VALD-01 through VALD-05)
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/phases/32-end-to-end-validation/CONTEXT.md` - User decisions on test approach

### Secondary (MEDIUM confidence)

- [GitHub Issue #5456: Sub-agents Don't Inherit Model Configuration in Task Tool](https://github.com/anthropics/claude-code/issues/5456) - Known model inheritance bug
- [NASA Verification and Validation Plan Outline](https://www.nasa.gov/reference/appendix-i-verification-and-validation-plan-outline/) - Integration testing best practices
- [IT Project Handover Checklist](https://multishoring.com/blog/it-project-handover-checklist-steps-for-a-seamless-transition/) - Handoff documentation patterns
- [Software Testing QA Checklist](https://www.softwaretestinghelp.com/software-testing-qa-checklists/) - Manual testing validation approaches

### Tertiary (LOW confidence - informational only)

- [Manual Testing Checklist](https://www.professionalqa.com/manual-testing-checklist) - General testing guidance
- [Test Documentation Validation Checklist](https://www.knowledgeleader.com/tools/test-documentation-validation-checklist) - Documentation structure patterns

## Metadata

**Confidence breakdown:**
- Pre-flight checks: HIGH - standard validation pattern, all file paths verified
- Ibuprofen test specifics: HIGH - Phase 26-05 provides exact reference
- Known pitfalls: HIGH - extracted from Phase 28/29 summaries and known bugs
- Loop detection tests: MEDIUM - unclear if in scope for "prepare and hand off"
- Model inheritance verification: MEDIUM - no programmatic check available
- Fix strategy threshold: MEDIUM - Claude's discretion with limited guidance

**Research date:** 2026-02-08
**Valid until:** 30 days (stable components, but Task tool evolving rapidly)

**Critical findings:**
1. Task tool model inheritance bug (#18873/#5456) is a known issue — mitigation: verify `model: inherit` in frontmatter, trust Phase 28 verification
2. Agent definitions exist but never invoked — Phase 32 is the FIRST live execution test
3. Ibuprofen test data at `/Users/steinbeck/Dropbox/develop/lucy-ng/data/Ibuprofen/` (verified via filesystem check)
4. All prerequisites testable via bash pre-flight script (lucy-ng, LSD, database, files)
5. User decision: "prepare and hand off" not "execute during phase" — documentation is primary deliverable
