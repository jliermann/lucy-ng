# Pitfalls Research: Multi-Agent Team CASE Conversion

**Domain:** Converting single autonomous CASE agent to 5-agent collaborative team
**Researched:** 2026-02-16
**Confidence:** MEDIUM (web search + project context + architecture analysis)

---

## Critical Pitfalls

Mistakes that cause system failures, performance degradation, or require architectural rewrites.

### Pitfall 1: Knowledge Fragmentation When Splitting 666 Lines of Domain Expertise

**What goes wrong:**
When splitting the single lucy-case-agent's 666 lines of inlined NMR/LSD knowledge across 5 specialized agents (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate), each agent gets a subset of domain knowledge. Critical cross-domain knowledge becomes fragmented - for example, the nmr-chemist understands DEPT sign but not how it affects LSD MULT commands, while the lsd-engineer knows LSD syntax but not the NMR evidence hierarchy that determines when to override statistical detection. This fragmentation causes agents to make decisions without full context, leading to constraint conflicts that wouldn't occur with unified knowledge.

**Why it happens:**
The current agent definition uses hybrid context inlining - approximately 500-700 lines of critical knowledge embedded directly in the agent definition. When specialization requires splitting this knowledge, there's no clear boundary: NMR spectroscopy knowledge (Section 1-2), LSD command reference (Section 3), statistical detection protocol (Section 3.5), and incremental HMBC strategy (Section 4) all have interdependencies. Attempting to separate "NMR knowledge" from "LSD knowledge" creates artificial boundaries that don't match the actual workflow where every LSD decision requires NMR evidence and every NMR interpretation requires understanding LSD constraints.

Web search confirms "contextual information is often distributed across multiple agents, with no single agent having a complete picture, and this fragmentation can lead to inconsistent understanding and decision-making" and "different agents access different information naturally provide different solutions to identical issues."

**How to avoid:**
**Option A (Recommended):** Shared knowledge base approach. Create a centralized knowledge artifact (e.g., `~/.claude/agents/lucy-knowledge-base.md`) containing the full 666 lines of domain expertise, then use read-time references in specialized agent definitions rather than duplication. Each specialized agent's definition would be minimal (100-150 lines) with explicit references: "When making MULT decisions, read Section 3.6 Chemistry-First Hierarchy from knowledge-base.md." This maintains single source of truth while allowing specialization.

**Option B (Not recommended):** Duplicate core knowledge across all 5 agents. Increases total context from 666 lines to ~3000 lines (5x duplication), wastes tokens, and creates version drift when updating knowledge (must update 5 places).

**Option C (High risk):** Truly partition knowledge - nmr-chemist gets Sections 1-2, lsd-engineer gets Section 3, etc. Requires very high coordination overhead via message passing to reconstruct unified context for decisions.

**Warning signs:**
- Agents making contradictory recommendations (nmr-chemist says "sp2 from DEPT" while lsd-engineer says "sp3 from detection")
- Increased message volume as agents query each other for basic context ("what did DEPT show for carbon 5?")
- Decisions that would have been obvious to single agent now require 3-4 message exchanges
- Agent behavior changes when knowledge updates happen to only some agents

**Phase to address:**
Phase 1 (Architecture Design) - must decide knowledge architecture before implementing any agent specializations. If Option A chosen, Phase 2 creates the centralized knowledge base and rewrites agent definitions to reference it.

---

### Pitfall 2: Communication Overhead Degrades Latency and Increases Cost

**What goes wrong:**
Converting from single-agent (zero message passing) to 5-agent team introduces message passing as coordination mechanism. Each message incurs LLM call latency (hundreds of milliseconds to seconds), token costs for both sender and receiver, and potential for compounding errors across message chains. For example, if nmr-chemist detects CH2 from DEPT (iteration 1) → sends message to coordinator → coordinator delegates to lsd-engineer → lsd-engineer requests carbon shift value → nmr-chemist responds → lsd-engineer writes MULT → devils-advocate reviews → flags sp2 count issue → coordinator intervenes, this simple decision that took single agent 1 LLM call now requires 7 calls with total latency 5-10x higher.

Research shows "too much inter-agent messaging can slow down systems" and "messaging volume grows exponentially with system size." For the CASE workflow with ~10 iterations averaging 3-5 HMBC additions per iteration, message count could exceed 200-300 messages for a complete run versus ~50 LLM calls with single agent.

**Why it happens:**
Multi-agent frameworks optimize for task parallelism (multiple independent subtasks executing simultaneously), but CASE workflow is fundamentally sequential - each iteration depends on previous results. The workflow steps (peak picking → detection → LSD generation → solving → ranking) cannot run in parallel because later steps require earlier outputs. This means adding agents introduces coordination cost without parallelism benefit.

**How to avoid:**
**Minimize synchronous message passing:** Use asynchronous task claiming pattern. Instead of coordinator explicitly assigning "nmr-chemist, analyze DEPT," maintain a shared task list where agents autonomously claim next available task. This eliminates round-trip coordinator overhead.

**Batch communication:** Rather than message-per-decision, agents accumulate findings and send batch updates. For example, nmr-chemist completes all DEPT analysis, then sends single comprehensive report rather than 13 separate carbon-by-carbon messages.

**Read-over-ask protocol:** Before sending message to request information, agents check if answer exists in shared artifacts (CASE-PROGRESS.md, analysis files). If nmr-chemist already documented "carbon 5: DEPT-135 negative = CH2" in findings file, lsd-engineer reads file rather than asking.

**Latency budget:** Establish maximum acceptable delay. If single-agent baseline completes in 45 minutes, set team target at 60 minutes max (33% overhead acceptable). If team coordination pushes to 90+ minutes, coordination architecture failed.

**Warning signs:**
- Iteration time increases from ~3-5 minutes (single agent) to 10+ minutes (team) without quality improvement
- Message logs show request-response chains > 5 hops for simple information retrieval
- Total token cost 3x+ higher than single-agent baseline for same compound
- Agents waiting idle for responses rather than progressing (see Pitfall 5)

**Phase to address:**
Phase 2 (Team Coordination Protocol) - define communication patterns, batching rules, read-over-ask enforcement BEFORE implementing actual team workflow. Phase 5 (Performance Optimization) validates latency budget and optimizes slow paths.

---

### Pitfall 3: Coordination Deadlocks - Agents Waiting for Each Other

**What goes wrong:**
Coordination deadlocks occur when agent A waits for agent B who waits for agent C who waits for agent A, creating circular dependency that freezes workflow. For CASE team: devils-advocate cannot review LSD file until lsd-engineer writes it → lsd-engineer waits for nmr-chemist's multiplicity assignments → nmr-chemist waits for devils-advocate's validation of previous iteration constraints before proceeding → DEADLOCK. System appears active (agents are running, messages passing) but makes no progress (livelock pattern).

Research confirms "agents can duplicate work, wait for resources indefinitely (deadlock), or skip tasks" when coordination mechanisms fail, and "deadlocks where agents are stuck waiting for each other, or livelocks where agents are active but make no progress" are common multi-agent failure modes.

**Why it happens:**
The CASE workflow has natural dependencies (must pick peaks before building LSD file, must run solver before ranking), but team architecture introduces artificial synchronization points. If devils-advocate is defined as "reviews EVERY decision before it proceeds," this creates blocking dependency. If coordinator pattern is "wait for consensus from all agents before continuing," any agent delay blocks entire workflow.

**How to avoid:**
**Explicit dependency graph:** Document actual vs. artificial dependencies. Actual: cannot write LSD until peaks picked. Artificial: waiting for devils-advocate's approval to proceed (approval can happen in parallel with next step preparation).

**Non-blocking review:** Devils-advocate runs asynchronously, flagging issues that get addressed in NEXT iteration rather than blocking current iteration. Example: if devils-advocate detects "DEFF NOT patterns missing" during iteration 3 LSD generation, flag gets added to shared issue tracker, coordinator ensures lsd-engineer addresses it in iteration 4. Current iteration proceeds unblocked.

**Timeout mechanisms:** If agent doesn't respond within threshold (e.g., 30 seconds), coordinator proceeds with default assumption or escalates to user rather than infinite wait.

**Mediator pattern:** Research recommends "Mediator acts as the tie-breaker to prevent the system from freezing in a deadlock." Coordinator agent must have authority to break circular dependencies by making executive decisions when consensus fails.

**Warning signs:**
- Task list shows all tasks "in progress" but none completing
- Agent logs show waiting states > 60 seconds
- Iteration time spikes to 15+ minutes for steps that should take 2-3 minutes
- Message logs show circular request patterns (A→B→C→A)

**Phase to address:**
Phase 2 (Team Coordination Protocol) - define dependency graph, timeout policies, mediator escalation rules. Phase 4 (Error Handling) implements timeout detection and recovery.

---

### Pitfall 4: Context Window Pressure - Duplicating 666 Lines Across 5 Agents

**What goes wrong:**
If each specialized agent duplicates the full 666-line knowledge base to avoid fragmentation (Pitfall 1, Option B), total knowledge context expands to ~3300 lines (5 agents × 666 lines). Combined with agent-specific instructions (~100-150 lines per agent), task context (~200 lines), and conversation history (~500-1000 lines active context), each agent consumes 4000-5000 tokens of context before processing any work. At 200K token budget, this leaves ~195K for actual reasoning, but accumulated message history and iteration state can push total context to 50K+ tokens, degrading reasoning quality and increasing latency.

Research shows "large language models generally function within predetermined context windows, restricting their ability to sustain awareness during prolonged interactions" and multi-agent systems require "intelligent compression and memory mechanisms" to manage context.

**Why it happens:**
Knowledge duplication (to avoid fragmentation) + agent specialization (unique instructions per agent) + coordination overhead (message history) compounds context usage. Single agent has single context window with full knowledge, but team architecture multiplies context by number of agents.

**How to avoid:**
**Centralized knowledge base with read references** (Pitfall 1, Option A): Agents reference shared knowledge artifact rather than embedding full copy. Agent definition says "For DEPT interpretation rules, read Section 2.3 from lucy-knowledge-base.md" rather than inlining 50 lines. Agent loads only relevant sections on-demand rather than carrying full knowledge in permanent context.

**Stateless agents with file-based memory:** Agents store findings in structured files (analysis/nmr-findings.md, analysis/lsd-constraints.md) rather than accumulating in message history. Each new iteration, agents read current state from files rather than replaying entire conversation history.

**Context summarization:** After each iteration, coordinator compresses findings to essential state (solution count, constraints added, issues flagged) and archives detailed logs. Agents load compressed state rather than full iteration history.

**Selective knowledge loading:** nmr-chemist loads only NMR-specific sections (1-2) during peak picking phase, then loads statistical detection section (3.5) during detection phase. Knowledge loaded dynamically rather than permanently resident.

**Warning signs:**
- Agent responses become less detailed or miss obvious issues after 5+ iterations
- Token usage per iteration increases over time rather than staying constant
- Agents start "forgetting" earlier decisions or constraints
- Response latency increases significantly in later iterations

**Phase to address:**
Phase 1 (Architecture Design) - choose knowledge architecture that minimizes duplication. Phase 3 (Iteration State Management) implements file-based memory and summarization.

---

### Pitfall 5: Idle Agents - Paying for Unused Capacity

**What goes wrong:**
CASE workflow has distinct sequential phases with different skill requirements. During peak picking (Step 1), only nmr-chemist is active. During LSD file writing (Step 4), only lsd-engineer is active. During solution ranking (Step 6), only solution-analyst is active. If team architecture spawns all 5 agents at workflow start and keeps them running throughout, 3-4 agents sit idle during each phase, consuming context and orchestration overhead while providing zero value. Total cost = 5 agents × 10 iterations × token-per-iteration, but actual utilization = ~2 agents average = 60% waste.

Research on optimal team sizes concludes "for most development tasks, 2-3 teammates provide the best balance of parallelism and coordination overhead."

**Why it happens:**
Team architecture optimized for parallelism (multiple agents working simultaneously) mismatched to CASE workflow reality (sequential dependencies with occasional parallel opportunities). The workflow HAS some parallelism potential - nmr-chemist could pick HSQC peaks while simultaneously picking HMBC peaks, devils-advocate could review previous iteration while lsd-engineer builds next iteration - but these opportunities are limited and don't justify permanent 5-agent team.

**How to avoid:**
**Dynamic agent lifecycle:** Spawn agents on-demand rather than all upfront. Coordinator spawns nmr-chemist for peak picking phase, terminates after completion, spawns lsd-engineer for LSD generation phase. Agent count varies from 1-3 depending on current phase rather than fixed 5.

**Agent pooling:** Maintain 2-3 core agents (coordinator, nmr-chemist, lsd-engineer) permanently, spawn specialists (solution-analyst, devils-advocate) only when needed. For example, devils-advocate spawned only when constraint conflicts detected (not every iteration).

**Minimum viable team:** Research emphasizes "start with a single agent and good prompt engineering, and add tools before adding agents." Re-evaluate if true 5-agent team is necessary or if 2-3 agents + better tools achieves same goal with less overhead.

**Task-based spawning:** Use autonomous task claiming pattern - coordinator creates task list, spawns 2-3 agents, agents claim tasks as available. If 5 tasks available and only 2 agents, agents work through queue sequentially rather than spawning 5 agents for parallel execution when dependencies prevent true parallelism.

**Warning signs:**
- Agent logs show > 50% idle time (waiting for messages, no active tasks)
- Total workflow cost 3x+ single-agent baseline without proportional quality improvement
- Agents frequently report "nothing to do, waiting for X"
- Parallelism metrics show < 2 agents active simultaneously on average

**Phase to address:**
Phase 1 (Architecture Design) - determine minimum viable team size (2-3 agents likely sufficient). Phase 2 (Team Coordination Protocol) implements dynamic spawning if > 3 agents needed.

---

### Pitfall 6: Message Loss - Critical Flags Dropped in Queue

**What goes wrong:**
Devils-advocate detects critical issue ("DEFF NOT patterns missing from LSD file") and sends flag message to coordinator. Coordinator receives message while processing lsd-engineer's "LSD file ready" message and nmr-chemist's "iteration 5 complete" message. Under message queue pressure or priority conflicts, devils-advocate's flag gets queued behind lower-priority messages, delayed past iteration start, or lost entirely if message buffer overflows. LSD runs without badlist filters, generates strained-ring solutions that should have been excluded, wastes entire iteration. This is exactly the v3.0 UAT bug - agent dropped DEFF NOT between iterations - now amplified by multi-agent message passing.

Research identifies "messaging volume grows exponentially as more AI agents join multi-agent systems" and "messages between agents can grow exponentially with system size, overwhelming network resources." With 5 agents, potential message paths = 5×4 = 20 bidirectional channels, creating message queue management challenge.

**Why it happens:**
Multi-agent coordination frameworks typically use message queues with eventual delivery but no guaranteed ordering or priority. If devils-advocate sends high-priority issue flag simultaneously with coordinator sending task assignments to 3 other agents, all messages enter same queue. Without priority mechanism, critical flags can be delayed behind routine task assignments.

**How to avoid:**
**Priority message channels:** Separate high-priority (issue flags, validation failures) from routine (status updates, task assignments). Devils-advocate flags bypass normal queue and trigger immediate coordinator attention via priority channel.

**Acknowledgment protocol:** Critical messages require explicit ACK. Devils-advocate sends "CRITICAL: DEFF NOT missing" → waits for coordinator ACK within 5 seconds → if no ACK, retransmits up to 3 times → if still no ACK, escalates to user.

**Synchronous validation steps:** For critical pre-conditions (devils-advocate pre-run validation), use synchronous blocking call rather than async message. Coordinator calls devils-advocate.validate(lsd_file) and blocks until response received rather than sending async message and continuing.

**File-based issue tracking:** Instead of message-only flags, devils-advocate writes issues to persistent file (analysis/issues.md). Coordinator polls file before each iteration rather than depending on message delivery. Message serves as notification, but file is source of truth.

**Distributed tracing:** Implement OpenTelemetry or equivalent (research recommends "use OpenTelemetry for traces and metrics so observability is portable across tools"). Trace each message from sender → queue → receiver to detect lost messages and debug delivery failures.

**Warning signs:**
- Issues flagged by devils-advocate in logs but not addressed in subsequent iterations
- Coordinator reports "no issues found" while devils-advocate logs show issue flag sent
- LSD files missing constraints that devils-advocate validated
- Symptoms match v3.0 UAT bugs (DEFF NOT dropped, SYME unused) despite team architecture designed to prevent them

**Phase to address:**
Phase 2 (Team Coordination Protocol) - define message priorities, ACK requirements, file-based issue tracking. Phase 4 (Error Handling) implements retry logic and distributed tracing.

---

### Pitfall 7: Over-Engineering - 5-Agent Team for What Single Agent Could Fix

**What goes wrong:**
The v3.0 UAT bugs (DEFF NOT dropped, signal grouping detected but not applied, grouped notation lost, PROP/ELIM/LIST unused) all stem from single root cause: agent reconstructs LSD file from memory across iterations rather than reading previous file and incrementally modifying. This is fixable with better prompting and file management in single agent: "Read analysis/iteration_NN/compound.lsd, copy all MULT/BOND/DEFF NOT lines verbatim, append new HMBC batch." Creating 5-agent team introduces 100x implementation complexity for a problem solvable with 10 lines of better instructions.

Research strongly emphasizes this risk: "most AI failures in production (2024-2026) did not fail due to model quality but because of architectural issues" and "many agentic tasks are best handled by a single agent with well-designed tools, which are simpler to build, reason about, and debug." The industry consensus for 2026 is "start minimal, add complexity only when necessary."

**Why it happens:**
Multi-agent architecture is appealing solution when single agent exhibits bugs - "multiple agents can catch each other's errors" seems like robust design. But if root cause is simple (file reconstruction vs. incremental modification), adding architectural complexity treats symptom rather than disease. The 5-agent team design (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate) adds coordination overhead, message passing latency, knowledge fragmentation risk, and implementation complexity without addressing core issue: how to maintain constraint inventory across iterations.

**How to avoid:**
**Fix single-agent approach first:** Before committing to team architecture, validate whether enhanced single agent solves v3.0 UAT bugs. Modifications needed:

1. **Constraint inventory file:** Agent maintains analysis/constraint-inventory.md with authoritative list of all constraints (DEFF NOT, SYME groups, PROP rules). Each iteration reads inventory, applies constraints to new LSD file. Inventory is append-only (never loses constraints).

2. **Incremental LSD builder:** Agent reads previous iteration's compound.lsd as template, modifies in-place (add new HMBC lines) rather than reconstructing from scratch. This preserves all auxiliary constraints automatically.

3. **Pre-run validation checklist:** Agent self-validates before running LSD: "Read current compound.lsd, verify DEFF NOT count matches iteration 1, verify SYME groups present, verify sp2 count even, verify H budget matches." If validation fails, agent fixes before running solver.

4. **Structured logging:** CASE-PROGRESS.md already requires listing constraints added/removed - enhance to require "constraints preserved from previous iteration" section. Forces agent to explicitly account for constraint persistence.

If these 4 modifications fix the bugs, 5-agent team is over-engineering. Total implementation: ~200 lines of enhanced instructions vs. ~2000 lines for full team architecture.

**Minimum viable team test:** If team approach still preferred, start with 2-agent MVP (coordinator + lsd-engineer with constraint inventory responsibility). If 2-agent solves bugs, no need for 5-agent. Research recommends "2-3 teammates provide the best balance."

**Warning signs:**
- Team architecture taking > 2 weeks to implement
- Coordination code becoming larger than domain logic
- Debugging team interactions harder than debugging single-agent logic
- Performance metrics show team 3x+ slower than single agent without quality improvement
- Roadmap phases dominated by coordination infrastructure rather than CASE capabilities

**Phase to address:**
Phase 0 (Pre-Architecture Validation) - NOT in current v4.0 plan, but should be. Before committing to team architecture, validate enhanced single-agent approach. If single agent + constraint inventory + incremental LSD builder fixes UAT bugs, pivot away from team architecture. If bugs persist, proceed with minimal team (2-3 agents) rather than full 5-agent design.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Duplicate knowledge across agents | Avoid fragmentation, agents self-sufficient | 3-5x context bloat, version drift, update complexity | Never - use shared knowledge base with read references |
| Async message-only coordination | Simpler implementation, no blocking | Lost messages, no delivery guarantees, hard to debug | Only for non-critical notifications - use sync calls + file tracking for critical flags |
| Spawn all agents upfront | Simpler lifecycle, no dynamic spawning logic | 60%+ idle capacity waste, high cost | Only if workflow has true parallelism (CASE doesn't) |
| Skip distributed tracing | Faster initial implementation | Message loss undetectable, coordination bugs unfindable | Never in production - tracing is essential for multi-agent debugging |
| Global message queue (no priority) | Simpler queue implementation | Critical flags lost in routine traffic | Only for MVP with < 20 messages/run - production needs priority channels |
| Single-agent with better prompts instead of team | 10x simpler, faster to implement, easier to debug | No peer review, single point of failure | Acceptable if enhanced agent solves UAT bugs - validate first |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Agent-to-Agent messaging | Assume reliable delivery, no ACK needed | Critical messages require ACK, timeout, retry - routine messages can be fire-and-forget |
| Shared knowledge base | Inline full content in each agent (duplication) | Agents read sections on-demand, cite location (e.g., "per Section 3.6"), single source of truth |
| Task assignment | Coordinator explicitly assigns every task | Agents autonomously claim from shared task list (reduces round-trip latency) |
| Constraint persistence | Agent reconstructs LSD from memory each iteration | Agent reads previous LSD file, incrementally modifies (preserves all constraints) |
| Issue tracking | Devils-advocate sends message, assumes coordinator acts | Message + persistent file - message notifies, file is source of truth coordinator must check |
| Context management | Accumulate full history in agent context | Summarize after each iteration, store details in files, agents load compressed state |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Message passing overhead | Iteration time 3x+ single agent, token cost 3x+ | Batch communications, read-over-ask protocol, async task claiming | > 50 messages per iteration (5-agent team easily exceeds this) |
| Idle agent waste | 60%+ of agent capacity unused, cost without value | Dynamic spawning or minimal team size (2-3 agents max) | Spawning > 3 agents for sequential CASE workflow |
| Context window bloat | Later iterations slower/lower quality, responses generic | Centralized knowledge base, file-based state, context summarization | Knowledge duplication across 5 agents (3300 lines total) |
| Synchronous blocking deadlock | Workflow freezes, tasks stuck "in progress" indefinitely | Timeout mechanisms, non-blocking review, mediator pattern | Circular dependencies (A waits for B waits for C waits for A) |
| Exponential message growth | Queue overflow, delivery delays, lost messages | Priority channels, file-based tracking, distributed tracing | 5 agents × 4 possible targets = 20 message paths |
| Coordination complexity exceeds domain complexity | More code managing agents than doing CASE, harder to debug than single agent | Start with enhanced single agent, validate team needed, use minimal team (2-3) | Full 5-agent team for problem solvable with better prompting |

## Minimum Viable Team Decision Tree

Decision framework for determining actual team size needed:

```
Can enhanced single agent (constraint inventory + incremental LSD builder +
  pre-run validation + structured logging) fix v3.0 UAT bugs?

  ├─ YES → Use enhanced single agent
  │         Benefits: 10x simpler, faster, easier to debug, proven track record
  │         Skip team architecture entirely
  │
  └─ NO → Bugs persist despite enhancements
      │
      ├─ Do bugs stem from lack of peer review (agent doesn't catch own errors)?
      │
      │   ├─ YES → Try 2-agent team (primary + reviewer)
      │   │         Examples: (lsd-engineer + devils-advocate) or
      │   │                   (coordinator + lsd-engineer with self-review)
      │   │         Benefits: Minimal overhead, clear division
      │   │         Test: Does reviewer catch constraint loss? If yes, sufficient.
      │   │
      │   └─ NO → 2-agent insufficient
      │       │
      │       └─ Is parallelism actually achievable in workflow?
      │
      │           ├─ YES → Limited parallel opportunities exist
      │           │         (e.g., HSQC + HMBC picking simultaneously)
      │           │         Try 3-agent team with dynamic task claiming
      │           │         Examples: (coordinator + 2 workers) or
      │           │                   (nmr-chemist + lsd-engineer + reviewer)
      │           │         Test: Does parallelism reduce wall time? If no, overhead exceeds benefit.
      │           │
      │           └─ NO → Workflow is inherently sequential
      │               │
      │               └─ Reconsider if multi-agent solves actual problem
      │                   Full 5-agent team likely over-engineering
      │                   Focus on better tools/prompts for single/2-agent approach
```

**Key principle from research:** "Simple architectures often suffice: start with a single agent and good prompt engineering, and add tools before adding agents."

## "Looks Done But Isn't" Checklist

- [ ] **Team coordination:** Message passing implemented but no priority channels - critical flags can be lost in routine traffic. Verify priority mechanism exists.
- [ ] **Knowledge architecture:** Each agent has "access" to full knowledge but achieved via duplication - context bloat hidden. Verify centralized knowledge base with read references.
- [ ] **Constraint persistence:** Agents "remember" constraints via message history - fails when context expires. Verify file-based constraint inventory that persists across iterations.
- [ ] **Performance baseline:** Team "works" in tests but no latency comparison to single agent - 3x slowdown undiscovered. Verify team completes in ≤ 1.5x single-agent time.
- [ ] **Error detection:** Distributed tracing "planned" but not implemented - lost messages undetectable. Verify OpenTelemetry or equivalent active before production.
- [ ] **Idle capacity:** All 5 agents spawn at start but utilization metrics not tracked - 60% waste invisible. Verify avg agents active > 2.5 or use dynamic spawning.
- [ ] **Deadlock handling:** Timeout mechanisms exist but never tested - first deadlock in production. Verify timeout recovery tested in Phase 4 integration tests.
- [ ] **Cost tracking:** Token usage tracked per-run but not per-agent - cost attribution unclear. Verify can identify which agent consumed which tokens for optimization.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Knowledge fragmentation causing contradictory agent decisions | MEDIUM | 1. Create centralized knowledge base (lucy-knowledge-base.md), 2. Rewrite agent definitions to reference rather than duplicate, 3. Validate agents cite consistent sources, 4. Test cross-agent decision consistency |
| Message loss causing dropped constraints (v3.0 bugs resurface) | LOW | 1. Implement file-based issue tracking (analysis/issues.md), 2. Add coordinator file poll before iterations, 3. Message becomes notification only, 4. Test constraint persistence across 10 iterations |
| Coordination deadlock freezing workflow | HIGH | 1. Implement timeout mechanisms (30s agent response limit), 2. Add mediator escalation logic to coordinator, 3. Identify and break circular dependencies, 4. May require workflow redesign if dependencies inherent |
| Context bloat degrading quality in late iterations | MEDIUM | 1. Implement context summarization after each iteration, 2. Move detailed logs to files, 3. Agents load compressed state (solution count, constraints added, issues) instead of full history, 4. Test quality maintenance through iteration 10 |
| Idle agent waste inflating cost 3x+ | LOW | 1. Switch to dynamic agent spawning or 2. Reduce to minimal team (2-3 agents) or 3. Implement agent pooling (spawn specialists on-demand), 4. Validate cost within 1.5x single-agent baseline |
| Over-engineering - team slower/harder to maintain than single agent | HIGH | 1. Pivot to enhanced single agent (constraint inventory + incremental LSD builder), 2. Deprecate team architecture, 3. May require significant roadmap revision, 4. Sunken cost in team implementation |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Knowledge fragmentation | Phase 1: Architecture Design - choose shared knowledge base | Each agent definition < 200 lines, all cite lucy-knowledge-base.md, no duplication |
| Communication overhead | Phase 2: Team Coordination Protocol - batching, read-over-ask, async claiming | Iteration time ≤ 1.5x single-agent baseline, < 50 messages per iteration |
| Coordination deadlocks | Phase 2: Team Coordination Protocol - timeouts, non-blocking review, mediator | All iterations complete within 10 min, no stuck tasks, tested circular dependency recovery |
| Context window pressure | Phase 3: Iteration State Management - file-based state, summarization | Agent context < 10K tokens per iteration, quality maintained through iteration 10 |
| Idle agents | Phase 1: Architecture Design - minimal team size OR dynamic spawning | Avg agents active ≥ 60% OR dynamic spawning tested, cost ≤ 2x single-agent |
| Message loss | Phase 2: Team Coordination Protocol - priority channels, ACK protocol, file tracking | Critical flags delivered 100% in tests, distributed tracing shows all message paths |
| Over-engineering | Phase 0: Pre-Architecture Validation - test enhanced single agent first | Enhanced single agent UAT with ibuprofen - if bugs fixed, skip team architecture |

---

## Sources

### Multi-Agent Coordination Challenges
- [Why Your Multi-Agent System is Failing: Escaping the 17x Error Trap](https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/)
- [Multi-Agent Systems: Complete Guide | Medium](https://medium.com/@fraidoonomarzai99/multi-agent-systems-complete-guide-689f241b65c8)
- [Guide to Multi-Agent Systems in 2026 | K21Academy](https://k21academy.com/agentic-ai/guide-to-multi-agent-systems-in-2026/)
- [Designing Effective Multi-Agent Architectures | O'Reilly](https://www.oreilly.com/radar/designing-effective-multi-agent-architectures/)

### Communication and Deadlock Patterns
- [Coordination Mechanisms in Multi-Agent Systems](https://apxml.com/courses/agentic-llm-memory-architectures/chapter-5-multi-agent-systems/coordination-mechanisms-mas)
- [9 Key Challenges in Monitoring Multi-Agent Systems at Scale | Galileo](https://galileo.ai/blog/challenges-monitoring-multi-agent-systems)
- [Challenges in Scaling Multi-Agent Systems](https://apxml.com/courses/agentic-llm-memory-architectures/chapter-5-multi-agent-systems/challenges-scaling-mas)

### Minimum Viable Team and Over-Engineering
- [Google's Eight Essential Multi-Agent Design Patterns | InfoQ](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/)
- [Designing Effective Multi-Agent Architectures | O'Reilly](https://www.oreilly.com/radar/designing-effective-multi-agent-architectures/)
- [Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline](https://arxiv.org/html/2601.12307v1)

### Context Management and Knowledge Sharing
- [Architecting efficient context-aware multi-agent framework for production | Google](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [Advancing Multi-Agent Systems Through Model Context Protocol](https://arxiv.org/html/2504.21030v1)
- [Memory in LLM-based Multi-Agent Systems](https://www.techrxiv.org/users/1007269/articles/1367390/master/file/data/LLM_MAS_Memory_Survey_preprint_/LLM_MAS_Memory_Survey_preprint_.pdf?inline=true)

### Agent Team Coordination and Load Balancing
- [Claude 4.6 Agent Teams: The Complete Guide | LaoZhang AI](https://blog.laozhang.ai/en/posts/claude-4-6-agent-teams)
- [Decentralized adaptive task allocation for dynamic multi-agent systems | Nature](https://www.nature.com/articles/s41598-025-21709-9)
- [Multi-Agent Coordination Gone Wrong? Fix With 10 Strategies | Galileo](https://galileo.ai/blog/multi-agent-coordination-strategies)

### Debugging, Monitoring, and Observability
- [Agent Tracing for Debugging Multi-Agent AI Systems | Maxim](https://www.getmaxim.ai/articles/agent-tracing-for-debugging-multi-agent-ai-systems/)
- [AG2 OpenTelemetry Tracing: Full Observability for Multi-Agent Systems](https://docs.ag2.ai/latest/docs/blog/2026/02/08/AG2-OpenTelemetry-Tracing/)
- [AI Agent Monitoring: Best Practices, Tools, and Metrics for 2026 | UptimeRobot](https://uptimerobot.com/knowledge-hub/monitoring/ai-agent-monitoring-best-practices-tools-and-metrics/)

### Domain Knowledge and Workflow State
- [Building Domain-specific AI Agents for the Enterprise | Aisera](https://aisera.com/blog/domain-specific-ai-agents/)
- [What is fragmented knowledge and why it matters | Glean](https://www.glean.com/perspectives/what-is-fragmented-knowledge)
- [The 2026 Guide to Agentic Workflow Architectures | Stack AI](https://www.stack-ai.com/blog/the-2026-guide-to-agentic-workflow-architectures)

### Lucy-ng Project Context
- lucy-case-agent.md (666 lines inlined NMR/LSD knowledge)
- /lucy-ng:case orchestrator skill (672 lines)
- v3.0 UAT findings (constraint loss bugs)
- PROJECT.md (v4.0 milestone definition)

---

*Pitfalls research for: Multi-Agent Team CASE Conversion*
*Researched: 2026-02-16*
