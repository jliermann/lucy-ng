# Feature Landscape: Agent Team CASE Workflow

**Domain:** Multi-agent Computer-Assisted Structure Elucidation (CASE)
**Researched:** 2026-02-16
**Confidence:** HIGH (official Claude Code docs, established multi-agent patterns, existing v3.0 architecture)

## Table Stakes

Features users expect from a team-based CASE agent. Missing = workflow feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Task-based work distribution** | Standard agent team pattern — teammates claim tasks from shared list | Low | Built into Claude Code's TeammateTool (task creation, claim, complete) |
| **Inter-agent messaging** | Teammates must communicate findings mid-iteration, not just report to lead | Low | Built into Claude Code (message/broadcast) |
| **Shared CASE-PROGRESS.md** | All agents need access to the persistent state document | Low | Filesystem already shared across teammates |
| **Independent context windows** | Each agent needs full workspace without token interference | Low | Automatic in agent teams architecture |
| **File-based constraint persistence** | lsd-engineer must read previous LSD file, not reconstruct from memory | Medium | Agent discipline via spawn instructions — "read analysis/iteration_NN-1/compound.lsd FIRST" |
| **Iteration subfolder organization** | analysis/iteration_NN/ pattern already established in v3.0 | Low | Existing pattern, team must maintain |
| **Pre-run validation** | Diff previous vs current LSD file before `lucy lsd run` | Medium | devils-advocate task, requires file comparison logic |
| **Post-run quality review** | Solution-analyst checks chemical plausibility (strained rings, valency) after ranking | Medium | Requires chemistry knowledge in agent |
| **Coordinator role** | Lead manages iteration loop, task creation, result synthesis | Low | Standard team lead pattern |
| **Graceful team shutdown** | Clean termination after success/failure/user intervention | Low | Built into Claude Code (shutdown requests) |

## Differentiators

Features that set team-based CASE apart from v3.0 single-agent architecture. Not expected, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Real-time peer feedback** | Any agent can flag issues in another's work before it affects results | High | Requires inter-agent message protocol + detection rules |
| **Constraint inventory tracking** | lsd-engineer maintains explicit list of all constraints (MULT, HSQC, HMBC, BOND, DEFF NOT, SYME) | Medium | Prevents v3.0 bug where DEFF NOT dropped across iterations |
| **Detection→Constraint verification** | devils-advocate verifies statistical detection results are actually applied in LSD file | High | Requires mapping detection output to LSD commands |
| **Multi-agent CASE-PROGRESS.md** | Each agent contributes to progress log with attributed sections (who did what) | Medium | Structured markdown with agent attribution |
| **Chemistry adversarial review** | devils-advocate challenges every structural assumption before solver runs | Medium | Chemistry domain knowledge + critical reasoning |
| **Iterative refinement with self-feedback** | Team reviews previous iteration's mistakes, proposes fixes, validates fixes worked | High | PEER-like pattern (Plan/Execute/Express/Review) adapted to CASE |
| **Parallel hypothesis testing** | nmr-chemist and lsd-engineer explore competing interpretations of ambiguous spectra | High | Requires branching iteration paths, not linear |
| **Automated strained ring detection** | solution-analyst flags cyclopropane/cyclobutane rings in ranked solutions | Medium | RDKit SSSR query on SMILES |
| **H-budget verification** | devils-advocate checks sum of MULT H counts equals formula before each run | Low | Arithmetic check with clear error message |
| **sp²-count verification** | devils-advocate counts MULT type 2 atoms and compares to hybridisation detection | Medium | Cross-reference MULT commands with `lucy detect hybridisation` results |
| **Grouped notation persistence** | lsd-engineer preserves HMBC 2 (6 7) notation across iterations | Low | File reading discipline |
| **Escalation to diagnostic specialist** | After 2 failed iterations, coordinator spawns specialist for deep failure analysis | Low | Existing lucy-diagnostic.md agent, just needs team integration |

## Anti-Features

Features to explicitly NOT build in team workflow.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Nested teams** | Complexity explosion, Claude Code doesn't support it | Use 5-agent flat team, coordinator delegates tasks |
| **Agent voting on decisions** | Slows iteration, introduces bikeshedding | devils-advocate has veto power on invalid LSD files, otherwise coordinator decides |
| **Full LSD file regeneration** | Causes v3.0 bug where constraints are lost | lsd-engineer ALWAYS reads previous file, appends new HMBC lines |
| **Automated ELIM constraint writing** | Premature elimination causes valid structures to be excluded | ELIM only on user request or after 3+ iterations with thousands of solutions |
| **Split-pane display mode** | Requires tmux/iTerm2, adds setup friction for end users | Use in-process mode (default), Shift+Up/Down to view teammates |
| **Parallel LSD solving** | LSD is sequential — each iteration depends on previous results | Linear iteration loop, not parallel |
| **Dereplication in CASE workflow** | Already prohibited in v3.0, maintain absolute separation | Dereplication is /lucy-ng:dereplicate sub-command, never in CASE |
| **Agent-initiated model selection** | Coordinator already uses Opus, teammates inherit | All teammates use opus (model: inherit) |
| **Custom teammate permissions** | Complexity, not needed for CASE | All teammates inherit lead's permissions |

## Feature Dependencies

```
Coordinator spawning → Task creation
Task creation → Teammate claiming
Teammate claiming → File-based constraint persistence
File-based constraint persistence → Pre-run validation
Pre-run validation → Real-time peer feedback
Real-time peer feedback → Multi-agent CASE-PROGRESS.md
Multi-agent CASE-PROGRESS.md → Iterative refinement
Iterative refinement → Post-run quality review
```

Sequential dependencies:
- **Iteration N** → **lsd-engineer reads iteration N-1 LSD file** → **devils-advocate diffs and validates** → **coordinator spawns lucy lsd run task** → **solution-analyst reviews ranking** → **Iteration N+1**

Parallel opportunities:
- **nmr-chemist picks HMBC peaks** || **solution-analyst reviews previous iteration solutions** || **devils-advocate pre-checks detection results**

## MVP Recommendation

**Phase 1: Core team mechanics (table stakes)**
Prioritize:
1. 5-agent spawning (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate)
2. Task-based iteration loop via TeammateTool
3. File-based constraint persistence (read previous LSD file)
4. Shared CASE-PROGRESS.md with multi-agent attribution
5. Pre-run H-budget + sp² verification
6. Post-run strained ring detection

Defer:
- Parallel hypothesis testing (High complexity, needs branching iteration paths)
- Detection→Constraint verification (requires complex mapping logic, can do manual first)
- Real-time peer feedback protocol (need core workflow stable first)

**Phase 2: Self-correction (differentiators)**
Prioritize:
1. Constraint inventory tracking (explicit list in CASE-PROGRESS.md)
2. Real-time peer feedback with messaging protocol
3. Iterative refinement loop (team reviews mistakes, proposes fixes)
4. Chemistry adversarial review (devils-advocate challenges assumptions)

Defer:
- Parallel hypothesis testing (still deferred — linear iteration sufficient for most compounds)

## Team Roles Specification

Based on [Claude Code agent teams documentation](https://code.claude.com/docs/en/agent-teams), adapted to CASE domain:

### Coordinator (Team Lead)
- **Responsibility:** Manages iteration loop, creates tasks, synthesizes results, decides when to terminate
- **Does NOT:** Perform CASE work directly (delegate mode prevents this)
- **Tools:** TeammateTool (spawn, message, task management), lucy lsd run (via task delegation)
- **Spawns:** 4 teammates at start, diagnostic specialist on escalation

### nmr-chemist (Teammate)
- **Responsibility:** Peak picking (1D/2D), signal grouping detection, spectral interpretation
- **Key tasks:**
  - Run `lucy pick 1d`, `lucy pick hsqc`, `lucy pick hmbc`
  - Run `lucy analyze grouping` for close shifts
  - Identify symmetry discrepancies
- **Communicates with:** lsd-engineer (signals peaks detected), devils-advocate (defends assignments)

### lsd-engineer (Teammate)
- **Responsibility:** LSD file construction, constraint inventory management, incremental HMBC addition
- **Key tasks:**
  - Read previous iteration LSD file FIRST (analysis/iteration_NN-1/compound.lsd)
  - Append new HMBC correlations from nmr-chemist
  - Maintain constraint inventory in CASE-PROGRESS.md (MULT count, HSQC count, HMBC count, BOND count, DEFF NOT patterns, SYME groups)
- **Communicates with:** nmr-chemist (receives peaks), devils-advocate (receives validation feedback)
- **CRITICAL:** NEVER reconstruct LSD file from memory — always read + append

### solution-analyst (Teammate)
- **Responsibility:** Solution ranking quality review, strained ring detection, chemical plausibility checks
- **Key tasks:**
  - Run `lucy lsd rank` after outlsd
  - Detect 3/4-membered rings in top solutions (RDKit SSSR)
  - Flag solutions with valency violations or impossible bonding
  - Recommend which HMBC correlations to add next based on gaps
- **Communicates with:** coordinator (reports quality), lsd-engineer (suggests constraint additions)

### devils-advocate (Teammate)
- **Responsibility:** Pre-run validation, assumption challenging, constraint verification
- **Key tasks:**
  - Diff previous vs current LSD file (what changed?)
  - Verify H budget: sum of MULT H counts = formula H count
  - Verify sp² count: MULT type 2 count matches `lucy detect hybridisation` results
  - Check DEFF NOT patterns still present
  - Check SYME groups from `lucy analyze grouping` are applied
  - Challenge structural assumptions (why carboxylic acid vs ester?)
- **Communicates with:** All teammates (can flag issues in anyone's work)
- **Veto power:** Can block LSD run if validation fails

## Communication Patterns

Based on [multi-agent collaboration patterns research](https://aws.amazon.com/blogs/machine-learning/multi-agent-collaboration-patterns-with-strands-agents-and-amazon-nova/):

### Message Types

| Type | Pattern | When | Example |
|------|---------|------|---------|
| **Broadcast** | coordinator → all teammates | Start of iteration, end of iteration | "Starting iteration 3. nmr-chemist: pick 5 more HMBC peaks. lsd-engineer: add to LSD file. devils-advocate: validate before run." |
| **Direct** | teammate → teammate | Peer feedback, data handoff | nmr-chemist → lsd-engineer: "Found 5 new HMBC peaks: [[C12, H8], [C4, H15], ...]" |
| **Challenge** | devils-advocate → any | Validation failure, assumption questioning | devils-advocate → lsd-engineer: "H budget off by 2. Current MULT sums to 20H, formula is C13H18O2. Check CH2 vs CH assignments." |
| **Report** | teammate → coordinator | Task completion, findings | solution-analyst → coordinator: "Ranked 47 solutions. Top 3 all contain cyclopropane ring (DEFF NOT missing?)" |

### Feedback Loop Protocol

Adapted from [PEER pattern](https://www.marktechpost.com/2025/08/02/a-coding-guide-to-build-intelligent-multi-agent-systems-with-the-peer-pattern/) and [iterative refinement research](https://selfrefine.info/):

1. **Plan (coordinator):** Broadcast iteration N goals
2. **Execute (nmr-chemist, lsd-engineer):** Perform assigned tasks
3. **Express (devils-advocate):** Review outputs, provide critique
4. **Review (all):** If validation passes → coordinator spawns LSD task. If fails → return to Execute with feedback.

**Termination:** Loop continues until:
- Success: Top solution MAE < 3.0 ppm AND no strained rings AND H budget correct
- Escalation: 10 failed iterations with same pattern → diagnostic specialist
- User intervention: User stops the team

## Task Structure

Based on [Claude Code task assignment mechanisms](https://code.claude.com/docs/en/agent-teams#assign-and-claim-tasks):

Tasks sized to ~15-30 minutes of work (per [best practices](https://code.claude.com/docs/en/agent-teams#size-tasks-appropriately)):

### Iteration N Task Breakdown

```markdown
## Iteration N

- [ ] **nmr-chemist**: Pick 5 new HMBC correlations (depends: none)
- [ ] **nmr-chemist**: Check signal grouping for close shifts (depends: none)
- [ ] **lsd-engineer**: Read iteration N-1 LSD file and add new HMBC lines (depends: nmr-chemist HMBC picking)
- [ ] **devils-advocate**: Validate LSD file (H budget, sp² count, DEFF NOT present, SYME applied) (depends: lsd-engineer LSD update)
- [ ] **coordinator**: Run LSD solver (depends: devils-advocate validation PASS)
- [ ] **solution-analyst**: Rank solutions and review top 10 for plausibility (depends: coordinator LSD run)
- [ ] **coordinator**: Update CASE-PROGRESS.md with iteration N results (depends: solution-analyst review)
```

Task dependencies prevent race conditions (devils-advocate can't validate until lsd-engineer finishes).

## Token Cost Implications

Per [Claude Code agent teams token costs](https://code.claude.com/docs/en/costs#agent-team-token-costs):

**v3.0 single agent:** ~50K tokens/iteration × 4 iterations = 200K tokens
**v4.0 5-agent team:** ~50K tokens/iteration × 4 iterations × 5 agents = 1M tokens

**Mitigation strategies:**
1. Size tasks appropriately — avoid tiny tasks that just add coordination overhead
2. Use direct messages, not broadcasts (broadcasts cost 5× tokens)
3. Keep teammate context minimal — spawn with task-specific instructions only
4. Terminate teammates after iteration completes, respawn for next iteration (vs keeping all 5 alive entire workflow)

**Tradeoff justification:** 5× token cost acceptable because team prevents constraint loss bugs that cause failed elucidations (which waste ALL tokens).

## Quality Gates

From [verification-first AI peer review research](https://arxiv.org/pdf/2601.16909):

Automated quality checks before human review:

| Gate | Check | Enforcer | Trigger |
|------|-------|----------|---------|
| **H-budget** | Sum MULT H = formula H | devils-advocate | Before every LSD run |
| **sp²-count** | MULT type 2 count matches detection | devils-advocate | Before every LSD run |
| **DEFF NOT present** | Badlist patterns in current LSD file | devils-advocate | Before every LSD run |
| **SYME applied** | Signal groups from detection appear as SYME | devils-advocate | Before every LSD run |
| **Strained rings** | Top 10 solutions checked for 3/4-rings | solution-analyst | After every ranking |
| **Constraint inventory** | All constraint types counted in CASE-PROGRESS.md | lsd-engineer | After LSD file update |

**Enforcement via TeammateIdle hook:**

```bash
# .claude/hooks/TeammateIdle
# Exit code 2 → send feedback and keep teammate working

if [[ "$TEAMMATE_NAME" == "devils-advocate" ]]; then
  # Check if validation task completed
  if ! grep -q "VALIDATION PASSED" analysis/iteration_*/VALIDATION.md; then
    echo "Complete validation checks before going idle."
    exit 2
  fi
fi
```

## Gaps Requiring Phase-Specific Research

These areas need deeper investigation during roadmap execution:

1. **Detection→Constraint mapping logic:** How to programmatically verify that `lucy detect neighbours` results are translated to correct PROP/ELIM/LIST commands in LSD file? May need CLI output comparison tool.

2. **Parallel hypothesis testing branching:** If two teammates explore competing theories (e.g., "is 180 ppm an acid or ester?"), how to structure iteration tree? Need workflow for rejoining branches.

3. **Diagnostic specialist integration:** lucy-diagnostic.md is designed for single-agent spawn. How to integrate into team context? Does it replace one teammate or operate alongside?

4. **Hook-based validation enforcement:** TeammateIdle vs TaskCompleted — which hook is appropriate for each quality gate? Need testing.

5. **CASE-PROGRESS.md merge conflicts:** If multiple teammates try to append simultaneously, how to prevent race conditions? File locking? Sequential write protocol?

6. **Coordinator delegate mode reliability:** Does delegate mode fully prevent coordinator from doing CASE work itself, or can it still intervene? Need testing with actual spawn.

## Sources

**HIGH confidence sources:**
- [Claude Code Agent Teams Documentation](https://code.claude.com/docs/en/agent-teams) — Official specification
- [AddyOsmani: Claude Code Swarms](https://addyosmani.com/blog/claude-code-agent-teams/) — Practical patterns
- [Multi-Agent Collaboration Patterns with Strands Agents](https://aws.amazon.com/blogs/machine-learning/multi-agent-collaboration-patterns-with-strands-agents-and-amazon-nova/) — Architecture patterns
- [Self-Refine: Iterative Refinement with Self-Feedback](https://selfrefine.info/) — Feedback loop patterns
- [PEER Pattern for Multi-Agent Systems](https://www.marktechpost.com/2025/08/02/a-coding-guide-to-build-intelligent-multi-agent-systems-with-the-peer-pattern/) — Collaborative workflow

**MEDIUM confidence sources:**
- [Verification-First AI Peer Review](https://arxiv.org/pdf/2601.16909) — Quality gate principles
- [AI Scientist v2](https://pub.sakana.ai/ai-scientist-v2/paper/paper.pdf) — Automated scientific workflow
- [Multi-Agent Peer Review Research](https://github.com/HITsz-TMG/Multi-agent-peer-review) — Peer feedback mechanisms

**Project-specific (HIGH confidence):**
- lucy-ng v3.0 CLAUDE.md, PROJECT.md, STATE.md — Existing architecture
- ~/.claude/commands/lucy-ng/case.md — Current orchestrator (672 lines)
- ~/.claude/agents/lucy-case-agent.md — Current autonomous agent (666 lines)
