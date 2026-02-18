# Architecture Research: 5-Agent CASE Team Integration

**Domain:** Multi-agent CASE workflow for NMR structure elucidation
**Researched:** 2026-02-16
**Confidence:** HIGH (based on Claude Opus 4.6 Team documentation and multi-agent architecture patterns)

## Executive Summary

The v4.0 architecture replaces the single autonomous CASE agent with a 5-agent collaborative team using Claude Opus 4.6's TeamCreate API. The orchestrator skill transitions from Task()-based spawning to TeamCreate-based coordination, with agents communicating in real-time through a shared task list and direct messaging.

**Key architectural changes:**

1. **Orchestrator skill** (`~/.claude/commands/lucy-ng/case.md`): Replace `Task(lucy-case-agent)` with `TeamCreate(team_definition)`, manage team lifecycle
2. **Agent definitions**: 5 specialized agent files in `~/.claude/agents/lucy-ng/case-team/` (new directory structure)
3. **Domain knowledge distribution**: NMR/LSD knowledge split by specialization vs current monolithic inlining
4. **Shared state**: CASE-PROGRESS.md becomes multi-agent journal with per-agent sections
5. **Diagnostic integration**: Specialist remains spawned by orchestrator (not team member)

**Integration complexity:** MEDIUM — TeamCreate API is new but straightforward; knowledge distribution requires careful design; constraint tracking is the critical success factor.

## 1. Orchestrator Architecture: From Task to TeamCreate

### Current Architecture (v3.0)

**File:** `~/.claude/commands/lucy-ng/case.md` (672+ lines)

**Pattern:**
```markdown
<step name="spawn_case_agent">
Task(
  agent_type="lucy-case-agent",
  model="opus",
  instructions="Perform CASE workflow for compound at <path> with formula <formula>.

  [Task-specific instructions only, agent has inlined knowledge]
  "
)
</step>
```

**Characteristics:**
- Single agent runs 3-10 LSD iterations autonomously
- Returns control to orchestrator when stuck or complete
- Orchestrator monitors CASE-PROGRESS.md, detects loops, spawns diagnostic specialist

### New Architecture (v4.0)

**File:** `~/.claude/commands/lucy-ng/case.md` (estimated 800+ lines)

**Pattern:**
```markdown
<step name="spawn_case_team">
TeamCreate(
  team_definition={
    "team_lead": "case-coordinator",
    "teammates": [
      "nmr-chemist",
      "lsd-engineer",
      "solution-analyst",
      "devils-advocate"
    ],
    "shared_context": {
      "compound_path": "<path>",
      "formula": "<formula>",
      "iteration": 0
    }
  },
  instructions="Coordinate CASE workflow with specialized team.

  Team lead (case-coordinator) manages workflow and iteration cycles.
  Teammates collaborate on peak picking, constraint building, validation, analysis.

  [Team-level coordination instructions]
  "
)
</step>
```

**Characteristics:**
- Team runs iteratively with real-time peer review
- Team lead coordinates workflow, teammates specialize
- Orchestrator monitors team task list and CASE-PROGRESS.md
- Diagnostic specialist remains orchestrator-spawned (not team member)

### Integration Points for Orchestrator

| Component | v3.0 (Task) | v4.0 (TeamCreate) | Changes Required |
|-----------|-------------|-------------------|------------------|
| **Spawning** | `Task(agent_type="lucy-case-agent")` | `TeamCreate(team_definition={...})` | Replace spawn logic |
| **Progress monitoring** | Read CASE-PROGRESS.md after Task returns | Read CASE-PROGRESS.md after team iteration batch | Parse multi-agent entries |
| **Loop detection** | Parse single-agent iteration history | Parse team iteration history with multi-agent contributions | Update parsers for team format |
| **Advisory intervention** | Re-spawn Task with advisory text | Send message to team lead with advisory | Use TeamMessage API |
| **Diagnostic delegation** | Spawn Task(lucy-diagnostic) separately | Spawn Task(lucy-diagnostic) separately (unchanged) | No change |
| **Results presentation** | Read final_results.md after Task complete | Read final_results.md after team complete | No change |

**Key architectural shift:** Orchestrator becomes **team manager** rather than **supervisor**. Instead of detecting loops and intervening, it provides resources and resolves escalations.

**Confidence:** HIGH — TeamCreate API is documented, mapping from Task to TeamCreate is straightforward.

## 2. Agent Definitions: File Structure and Location

### Current Structure (v3.0)

```
~/.claude/agents/
├── lucy-case-agent.md          (666 lines — monolithic autonomous agent)
└── lucy-diagnostic.md           (diagnostic specialist, orchestrator-spawned)
```

### Proposed Structure (v4.0)

```
~/.claude/agents/lucy-ng/
└── case-team/                   (NEW directory for team agents)
    ├── coordinator.md           (team lead — workflow coordination)
    ├── nmr-chemist.md           (peak picking, multiplicity assignment)
    ├── lsd-engineer.md          (LSD file construction, constraint inventory)
    ├── solution-analyst.md      (solution ranking, chemical plausibility)
    └── devils-advocate.md       (pre-run validation, constraint checking)

~/.claude/agents/
└── lucy-diagnostic.md           (unchanged — orchestrator-spawned specialist)
```

**Rationale for directory structure:**
- **Scoped namespace**: `lucy-ng/case-team/` prevents name collision with other projects
- **Team cohesion**: All team agents in one directory signals they work together
- **Discovery**: Easier to find and update related agents
- **Version control**: Team agents can be versioned together

**Alternative considered:** Flat structure with prefixes (`lucy-ng-case-coordinator.md`). Rejected because directory structure is cleaner and matches Claude SDK conventions.

**Confidence:** MEDIUM — Directory structure is logical, but needs validation that Claude Code discovers agents in subdirectories correctly.

## 3. Domain Knowledge Distribution Strategy

### Current Distribution (v3.0)

**lucy-case-agent.md (666 lines):**
- NMR background (50 lines)
- LSD command reference (200 lines)
- Statistical detection protocol (150 lines)
- Incremental HMBC strategy (100 lines)
- Chemistry-first hierarchy (80 lines)
- CASE-PROGRESS.md format (86 lines)

**All knowledge inlined in single agent.**

### Proposed Distribution (v4.0)

#### Coordinator (team lead)
**File:** `~/.claude/agents/lucy-ng/case-team/coordinator.md` (~300 lines)

**Knowledge:**
- Workflow orchestration (iteration lifecycle)
- Team coordination patterns (assign tasks, synthesize results)
- Progress documentation (CASE-PROGRESS.md format)
- Stopping conditions (convergence, safety cap)

**NOT included:**
- Detailed NMR experiment knowledge (delegates to nmr-chemist)
- LSD command syntax (delegates to lsd-engineer)
- Solution chemistry validation (delegates to solution-analyst)

#### NMR Chemist
**File:** `~/.claude/agents/lucy-ng/case-team/nmr-chemist.md` (~400 lines)

**Knowledge:**
- NMR experiment types and information content (13C, DEPT, HSQC, HMBC, COSY)
- Chemical shift regions and typical assignments
- Peak picking strategies (DEPT-guided, HMBC-guided)
- Multiplicity determination (DEPT-135 sign, DEPT-90 presence)
- Statistical detection protocol (hybridisation, neighbours, hhb, grouping)
- Chemistry-first hierarchy (DEPT > HSQC > detection > shift heuristics)
- Spectral quality assessment (SNR, resolution, artifacts)

**NOT included:**
- LSD file syntax (knows what constraints are needed, not how to write them)
- Ranking algorithms (knows expected shifts, not prediction mechanics)

#### LSD Engineer
**File:** `~/.claude/agents/lucy-ng/case-team/lsd-engineer.md` (~350 lines)

**Knowledge:**
- LSD command reference (MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM)
- Constraint translation (NMR evidence → LSD syntax)
- Constraint inventory management (read previous file, track all constraints)
- Hybridization rules (even sp2 count)
- Hydrogen budget matching
- Correlation order (HSQC before HMBC)
- Badlist filters (DEFF NOT patterns for strained rings)
- Incremental HMBC strategy (3-5 correlations per batch)

**NOT included:**
- NMR experiment details (receives constraints from nmr-chemist, doesn't interpret spectra)
- Solution ranking (builds inputs, doesn't evaluate outputs)

#### Solution Analyst
**File:** `~/.claude/agents/lucy-ng/case-team/solution-analyst.md` (~250 lines)

**Knowledge:**
- 13C shift prediction with HOSE codes
- Two-tier ranking (match count primary, MAE secondary)
- Solution quality assessment (MAE thresholds, match coverage)
- Chemical plausibility checks (strained rings, unusual connectivity)
- Confidence scoring (per-atom and overall)
- Ambiguity detection (close shifts, overlapping predictions)

**NOT included:**
- NMR data interpretation (receives experimental shifts from nmr-chemist)
- LSD file construction (analyzes solutions, doesn't build constraints)

#### Devils Advocate
**File:** `~/.claude/agents/lucy-ng/case-team/devils-advocate.md` (~200 lines)

**Knowledge:**
- Pre-run validation checklist (sp2 count, H budget, correlation order)
- Constraint diff protocol (compare current vs previous LSD file)
- Constraint persistence checks (DEFF NOT, SYME, grouped notation, detection results)
- Common failure modes (odd sp2, 1J artifacts, close carbons)
- Validation criteria (what makes an LSD file ready to run)

**NOT included:**
- How to fix issues (flags problems, lsd-engineer fixes them)
- Post-run analysis (validates inputs, solution-analyst validates outputs)

### Knowledge Distribution Principles

**1. Single Responsibility:** Each agent owns one aspect of the workflow
**2. Interface not Implementation:** Agents know WHAT to ask for, not HOW it's computed
**3. Shared Core:** Common NMR concepts (shift ranges, experiment types) duplicated minimally
**4. Explicit Handoffs:** Coordinator defines task boundaries and data contracts

**Example workflow with distributed knowledge:**

```
Coordinator: "nmr-chemist, pick peaks and determine multiplicities for iteration 1"
  ↓
NMR-Chemist: Runs `lucy pick 1d`, `lucy pick hsqc`, applies DEPT-guided strategy
NMR-Chemist: Runs `lucy detect hybridisation` for ambiguous shifts
NMR-Chemist: Posts to team: "13 carbons assigned, 3 quaternary, 10 protonated, 2 ambiguous (sp2/sp3)"
  ↓
Coordinator: "lsd-engineer, build LSD file from nmr-chemist assignments"
  ↓
LSD-Engineer: Reads previous iteration_NN/compound.lsd (if exists)
LSD-Engineer: Translates assignments to MULT commands (preserving constraints)
LSD-Engineer: Adds new HMBC batch (3-5 high-confidence correlations)
LSD-Engineer: Writes analysis/iteration_NN/compound.lsd
LSD-Engineer: Posts to team: "LSD file ready at iteration_NN/compound.lsd, 16 MULT, 10 HSQC, 8 HMBC, 6 DEFF NOT"
  ↓
Coordinator: "devils-advocate, validate LSD file before running"
  ↓
Devils-Advocate: Diffs iteration_NN vs iteration_{NN-1} (if exists)
Devils-Advocate: Checks sp2 count (even), H budget (matches formula), correlation order
Devils-Advocate: Verifies DEFF NOT present, SYME preserved (if applicable)
Devils-Advocate: Posts to team: "✓ Validation passed — sp2=14 (even), H=18 (matches), DEFF NOT=6 (preserved)"
  ↓
Coordinator: Runs `lucy lsd run`, observes solution count
Coordinator: "solution-analyst, evaluate 13 solutions from LSD"
  ↓
Solution-Analyst: Converts `outlsd 5 < compound.sol > solutions.smi`
Solution-Analyst: Ranks `lucy lsd rank solutions.smi --shifts "..."`
Solution-Analyst: Checks top solutions for strained rings, chemical plausibility
Solution-Analyst: Posts to team: "Rank #1: MAE=2.23, 13/13 matched, no strained rings, high confidence"
```

**Confidence:** MEDIUM — Distribution is logical but requires validation through UAT. Risk: coordination overhead may slow workflow vs monolithic agent.

## 4. CASE-PROGRESS.md: Multi-Agent Journal Format

### Current Format (v3.0)

```markdown
# CASE Progress Log

**Compound:** data/compound/ibuprofen
**Formula:** C13H18O2
**Started:** 2026-02-16 10:23:45
**CASE Agent:** lucy-case-agent

---

## Setup

**DBE:** 4 (calculation: (2×13 + 2 - 18) / 2)
**Spectra found:** 1H (exp 1), 13C (exp 2), DEPT-135 (exp 3), HSQC (exp 6), HMBC (exp 7)
...

---

## Iteration 1: Baseline with first HMBC batch

**Time:** 2026-02-16 10:24:12
**LSD file:** analysis/iteration_01/compound.lsd
**Solution count:** 47

**Constraints added:**
- HMBC C180.56-H2.45 (isolated carbon, unique proton)
...

**Why:** Starting with 5 high-confidence HMBC correlations...
```

**Characteristics:**
- Single agent writes all entries
- Linear narrative
- Clear iteration boundaries

### Proposed Format (v4.0)

```markdown
# CASE Progress Log

**Compound:** data/compound/ibuprofen
**Formula:** C13H18O2
**Started:** 2026-02-16 10:23:45
**Team:** case-team (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate)

---

## Setup

### Coordinator
**DBE:** 4 (calculation: (2×13 + 2 - 18) / 2)
**Team plan:** 5-phase workflow (symmetry → peaks → constraints → solve → analyze)

### NMR-Chemist
**Spectra found:** 1H (exp 1), 13C (exp 2), DEPT-135 (exp 3), HSQC (exp 6), HMBC (exp 7)
**Quality assessment:** 13C SNR=85 (good), HSQC SNR=62 (good), HMBC SNR=38 (moderate)
**Peak counts:** 13C: 10 peaks, DEPT-135: 10 peaks (7 positive, 3 negative), HSQC: 10, HMBC: 47 (raw)
**Symmetry:** 13 carbons expected (formula), 10 observed (13C spectrum) → 3 equivalent carbons
**Multiplicities:** 3 CH3, 5 CH2, 2 CH, 3 Cq (from DEPT-135 sign and HSQC)
**Statistical detection:**
  - 180.56 ppm: sp2=99%, O mandatory (98%) → carbonyl
  - 132.1 ppm: sp2=91%, C neighbors only → aromatic
  - 44.90/45.03 ppm: grouped (span 0.13 ppm) → equivalent CH2
**Key observations:** Carboxylic acid suspected (180.56 ppm + molecular formula C13H18O2)

### LSD-Engineer
**Constraint inventory (iteration 0):**
  - MULT: 0 atoms defined
  - HSQC: 0 correlations
  - HMBC: 0 correlations
  - DEFF NOT: 0 filters
  - SYME: 0 constraints
**Plan:** Build from NMR-Chemist assignments, start with 5 HMBC correlations

---

## Iteration 1: Baseline with first HMBC batch

### Coordinator
**Time:** 2026-02-16 10:24:12
**Phase:** Constraint building → LSD run → solution analysis
**Iteration goal:** Establish baseline solution count with initial constraints

### LSD-Engineer
**LSD file:** analysis/iteration_01/compound.lsd
**Constraints added:**
  - MULT: 13 C atoms (3 sp2 Cq, 7 sp3, 3 sp2 CH) + 2 O atoms (1 sp2, 1 sp3)
  - HSQC: 10 correlations (all protonated carbons)
  - HMBC: 5 correlations (high-confidence batch)
    - C180.56-H2.45 (isolated carbon, unique proton, quaternary carbonyl)
    - C132.1-H7.12 (aromatic, strong intensity)
    - C44.90-H1.45 (CH2, top quartile intensity)
    - C27.3-H1.05 (aliphatic, unique proton)
    - C18.2-H0.89 (CH3, terminal methyl)
  - DEFF NOT: 6 filters (cyclopropane, cyclobutane, aziridine, azetidine, thiirane, thietane)
  - BOND: C1-O13 (carbonyl C=O from detection)
  - SYME: None (symmetric atoms not yet encoded)
**Constraints removed:** None
**Why:** Starting with high-confidence correlations from isolated carbons, avoiding 1J artifacts
**Constraint inventory delta:** +15 MULT, +10 HSQC, +5 HMBC, +6 DEFF NOT, +1 BOND

### Devils-Advocate
**Validation:** ✓ sp2 count=6 (even), H budget=18 (matches), correlation order correct
**Pre-run checks:** ✓ All HSQC before HMBC, no 1J artifacts detected, DEFF NOT present
**Concerns:** Symmetric carbons (44.90/45.03 ppm) not encoded as SYME yet — may inflate solution count

### Coordinator
**LSD run:** `cd analysis/iteration_01 && lucy lsd run compound.lsd`
**Solution count:** 47
**Effectiveness:** Baseline established
**Next steps:** Convert solutions, rank, evaluate quality

### Solution-Analyst
**Conversion:** `outlsd 5 < compound.sol > solutions.smi` (47 solutions)
**Ranking:** `lucy lsd rank solutions.smi --shifts "180.56,132.1,..."`
**Top solution:** Rank #1: Ibuprofen (SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O)
  - MAE: 2.23 ppm
  - Matched: 13/13 signals
  - Quality: HIGH
**Strained rings:** None detected in top 10
**Chemical plausibility:** ✓ Carboxylic acid (180.56 ppm matches), para-substituted benzene, branched aliphatic
**Concerns:** Solution count still high (47) — need more HMBC constraints or SYME encoding

---

## Iteration 2: Add SYME for symmetric carbons and second HMBC batch

[Team continues in same format...]
```

**Characteristics:**
- Multi-agent sections per iteration
- Each agent documents their contribution
- Explicit handoffs between agents
- Constraint inventory tracking (lsd-engineer maintains delta)
- Validation results visible (devils-advocate)

**Coordinator responsibilities:**
- Writes iteration header (time, phase, goal)
- Writes LSD run results (solution count, effectiveness)
- Writes next steps (coordination)
- **Does NOT write** agent-specific details (agents write their own sections)

**File management:**
- Coordinator creates file headers and iteration boundaries
- Agents append their sections via direct file write
- Append-only pattern preserved (no overwrites)

**Confidence:** MEDIUM — Format is logical but may require iteration based on team dynamics. Risk: verbose logs if agents over-document.

## 5. Diagnostic Specialist Integration

### Current Integration (v3.0)

**Spawning:** Orchestrator detects loop pattern, spawns `Task(lucy-diagnostic)`

**Pattern:**
```markdown
<step name="delegate_specialist">
Task(
  agent_type="lucy-diagnostic",
  model="opus",
  instructions="Analyze LSD failure for compound at <path>.

  Read:
  - <path>/analysis/CASE-PROGRESS.md
  - <path>/<latest_lsd_file>

  Failure type: <failure_type>

  Write structured report to <path>/DIAGNOSTIC-REPORT.md.
  "
)
</step>
```

**Report consumption:** Orchestrator reads DIAGNOSTIC-REPORT.md, extracts root cause and primary fix, re-spawns CASE agent with advisory

### Proposed Integration (v4.0)

**Spawning:** UNCHANGED — orchestrator still detects loops and spawns specialist

**Why not a team member?**
1. **Diagnostic is reactive, not proactive:** Only needed when team is stuck
2. **Different lifecycle:** Spawned mid-workflow, not at start
3. **Independent analysis:** Should review team's work objectively, not participate
4. **Maintains existing pattern:** No changes to lucy-diagnostic.md needed

**Team interaction:**
```markdown
<step name="delegate_specialist">
Task(
  agent_type="lucy-diagnostic",
  model="opus",
  instructions="Analyze LSD failure for compound at <path>.

  Read:
  - <path>/analysis/CASE-PROGRESS.md (multi-agent iteration history)
  - <path>/<latest_lsd_file> (built by lsd-engineer)

  Failure type: <failure_type>
  Pattern: <pattern_name> (detected from team workflow)

  Write structured report to <path>/DIAGNOSTIC-REPORT.md.
  Include team-specific context in findings.
  "
)
</step>

<step name="apply_diagnostic">
# After specialist completes:
# 1. Read DIAGNOSTIC-REPORT.md
# 2. Extract root cause and primary fix
# 3. Send TeamMessage to case-coordinator with advisory
# 4. Team lead distributes fix tasks to appropriate agents

TeamMessage(
  team_id=<team_id>,
  recipient="case-coordinator",
  message="Diagnostic specialist identified: <root_cause>

  Primary fix: <fix_action>

  Suggested delegation:
  - lsd-engineer: <constraint fix>
  - devils-advocate: <validation check>
  "
)
</step>
```

**CASE-PROGRESS.md entry:**
```markdown
## Diagnostic Intervention (After Iteration 5)

### Orchestrator
**Pattern detected:** ELIM_THRASHING (2 occurrences)
**Specialist spawned:** lucy-diagnostic at 2026-02-16 10:45:23
**Report:** DIAGNOSTIC-REPORT.md

### Diagnostic Specialist (External)
**Root cause:** Odd sp2 count (15 atoms) — ether oxygen (O14) marked sp2 instead of sp3
**Primary fix:** Change `MULT 14 O 2 0` to `MULT 14 O 3 0`
**Confidence:** HIGH
**Evidence:** sp2 atoms = {C1, C2, ..., C13, O13, O14} = 15 (ODD)

### Coordinator
**Advisory received:** Fix sp2 count via O14 hybridization change
**Delegation:** lsd-engineer to update MULT 14, devils-advocate to verify sp2 count even

### LSD-Engineer
**Action:** Read iteration_05/compound.lsd, change line 27: `MULT 14 O 3 0`
**Verification:** sp2 count = 14 (even) ✓

### Devils-Advocate
**Validation:** ✓ sp2=14 (even), H budget=18 (matches), fix applied correctly

[Iteration 6 continues...]
```

**Confidence:** HIGH — Pattern is well-established, minimal changes needed.

## 6. Team Lifecycle and Coordination Flow

### Initialization

```
Orchestrator:
  1. Parse user input (compound path, formula)
  2. Validate prerequisites (lucy-ng, LSD, database)
  3. TeamCreate(team_definition)
  4. Wait for team initialization

Team Lead (coordinator):
  1. Receive compound path and formula
  2. Create analysis/ directory structure
  3. Create CASE-PROGRESS.md with team header
  4. Assign setup tasks to teammates:
     - nmr-chemist: Assess spectra, check symmetry
     - lsd-engineer: Initialize constraint inventory
     - solution-analyst: Verify database connection
     - devils-advocate: No action yet (validates later)
  5. Wait for setup completion

Teammates:
  1. Execute assigned setup tasks
  2. Post results to team
  3. Write sections to CASE-PROGRESS.md

Team Lead:
  4. Synthesize setup results
  5. Proceed to iteration 1
```

### Iteration Loop

```
Team Lead (coordinator):
  1. Start iteration N
  2. Assign peak picking (if N=1) or HMBC selection (if N>1) to nmr-chemist
  3. Wait for nmr-chemist completion

NMR-Chemist:
  1. Pick peaks OR select next HMBC batch
  2. Run statistical detection if ambiguous
  3. Post assignments to team
  4. Write to CASE-PROGRESS.md

Team Lead:
  5. Assign LSD file construction to lsd-engineer

LSD-Engineer:
  1. Read previous iteration_NN/compound.lsd (if exists)
  2. Update MULT commands from nmr-chemist assignments
  3. Add new HMBC batch (preserving all previous constraints)
  4. Update constraint inventory
  5. Write iteration_{N}/compound.lsd
  6. Post to team
  7. Write to CASE-PROGRESS.md

Team Lead:
  6. Assign pre-run validation to devils-advocate

Devils-Advocate:
  1. Diff iteration_{N} vs iteration_{N-1} (if exists)
  2. Check sp2 count, H budget, correlation order
  3. Verify DEFF NOT preserved, SYME preserved (if applicable)
  4. Post validation results to team
  5. Write to CASE-PROGRESS.md
  6. If validation fails: Flag to team, lsd-engineer fixes, re-validate

Team Lead:
  7. Run LSD: `cd analysis/iteration_{N} && lucy lsd run compound.lsd`
  8. Observe solution count
  9. Post to team
  10. Write to CASE-PROGRESS.md

Team Lead:
  11. If solution_count <= 10: Assign solution analysis to solution-analyst
  12. If solution_count > 10: Proceed to iteration N+1
  13. If solution_count = 0: Escalate to orchestrator

Solution-Analyst (if solution_count <= 10):
  1. Convert: `outlsd 5 < compound.sol > solutions.smi`
  2. Rank: `lucy lsd rank solutions.smi --shifts "..."`
  3. Check top solutions for strained rings, chemical plausibility
  4. Post quality assessment to team
  5. Write to CASE-PROGRESS.md

Team Lead:
  14. If quality HIGH: Write final_results.md, signal completion
  15. If quality MEDIUM/LOW: Continue iterations or flag concerns
```

### Termination

```
Team Lead:
  If solution_count <= 10 AND quality >= MEDIUM:
    1. solution-analyst writes final_results.md
    2. Team lead signals completion to orchestrator
    3. Orchestrator reads final_results.md, presents to user

  If iterations >= 10 (safety cap):
    1. Team lead writes incomplete convergence report
    2. Orchestrator presents with caveats

  If zero-solution loop OR ELIM thrashing:
    1. Team lead flags to orchestrator
    2. Orchestrator spawns diagnostic specialist
    3. Specialist writes DIAGNOSTIC-REPORT.md
    4. Orchestrator sends TeamMessage with advisory
    5. Team lead delegates fixes, continues
```

**Confidence:** MEDIUM — Flow is logical but needs validation through live testing. Risk: coordination overhead may slow iterations.

## 7. Build Order and Dependencies

### Phase 1: Orchestrator Skill Modification (Week 1)

**Files:**
- `~/.claude/commands/lucy-ng/case.md` — Replace Task() with TeamCreate()

**Changes:**
1. Replace `<step name="spawn_case_agent">` with `<step name="spawn_case_team">`
2. Define team_definition structure
3. Update progress monitoring to parse multi-agent CASE-PROGRESS.md
4. Replace advisory re-spawn with TeamMessage
5. Keep diagnostic specialist spawning (unchanged)

**Validation:**
- Team spawns successfully
- Team lead receives compound path and formula
- Orchestrator can send TeamMessage
- Diagnostic specialist still spawns on loop detection

**Dependencies:** None (extends existing orchestrator)

### Phase 2: Agent Definitions (Week 1-2)

**Files:**
- `~/.claude/agents/lucy-ng/case-team/coordinator.md` — NEW
- `~/.claude/agents/lucy-ng/case-team/nmr-chemist.md` — NEW
- `~/.claude/agents/lucy-ng/case-team/lsd-engineer.md` — NEW
- `~/.claude/agents/lucy-ng/case-team/solution-analyst.md` — NEW
- `~/.claude/agents/lucy-ng/case-team/devils-advocate.md` — NEW

**Knowledge distribution:**
1. Extract relevant sections from lucy-case-agent.md
2. Split by responsibility (see Section 3)
3. Define inter-agent interfaces (what each agent posts to team)
4. Write agent-specific workflow sections

**Validation:**
- Each agent can read CASE-PROGRESS.md
- Each agent can append to CASE-PROGRESS.md
- Each agent can post to team task list
- Coordinator can assign tasks to teammates

**Dependencies:** Phase 1 (orchestrator must support TeamCreate)

### Phase 3: Constraint Inventory System (Week 2)

**Files:**
- `~/.claude/agents/lucy-ng/case-team/lsd-engineer.md` — Constraint tracking protocol

**Changes:**
1. Define constraint inventory format (JSON or structured comment)
2. Implement "read previous LSD file" protocol
3. Implement "diff current vs previous" logic for devils-advocate
4. Document constraint delta in CASE-PROGRESS.md

**Example constraint inventory (LSD file header comment):**
```
; Constraint Inventory (Iteration 5)
; MULT: 15 atoms (13 C, 2 O)
; HSQC: 10 correlations
; HMBC: 23 correlations (5+5+5+5+3 batches)
; DEFF NOT: 6 patterns (cyclopropane, cyclobutane, ...)
; SYME: 2 constraints (C5-C6, C7-C8)
; BOND: 1 (C1-O13 carbonyl)
; LIST/PROP: 0
; ELIM: 0
```

**Validation:**
- lsd-engineer reads previous file correctly
- All constraints preserved when adding new batch
- devils-advocate detects dropped constraints (DEFF NOT, SYME)
- Constraint delta appears in CASE-PROGRESS.md

**Dependencies:** Phase 2 (lsd-engineer and devils-advocate must exist)

### Phase 4: CASE-PROGRESS.md Format (Week 2)

**Files:**
- `~/.claude/agents/lucy-ng/case-team/coordinator.md` — Update format definition

**Changes:**
1. Define multi-agent section structure
2. Define iteration header format (coordinator writes)
3. Define agent section format (agents write)
4. Define append-only protocol (no overwrites)

**Validation:**
- Coordinator creates iteration headers
- Agents append their sections
- File remains parseable by orchestrator monitoring
- No section overwrites or corruption

**Dependencies:** Phase 2 (all agents must write sections)

### Phase 5: Team Coordination Protocol (Week 3)

**Files:**
- `~/.claude/agents/lucy-ng/case-team/coordinator.md` — Task assignment and result synthesis

**Changes:**
1. Define task list structure (shared team state)
2. Define teammate assignment protocol
3. Define result collection and synthesis
4. Define stopping conditions (same as v3.0)

**Validation:**
- Coordinator assigns tasks correctly
- Teammates claim and complete tasks
- Coordinator synthesizes results
- Team converges to solution

**Dependencies:** Phases 1-4 (full stack must exist)

### Phase 6: Diagnostic Integration (Week 3)

**Files:**
- `~/.claude/commands/lucy-ng/case.md` — Update diagnostic delegation for teams

**Changes:**
1. Update DIAGNOSTIC-REPORT.md consumption for multi-agent context
2. Implement TeamMessage advisory delivery
3. Update coordinator to distribute fixes

**Validation:**
- Specialist reads multi-agent CASE-PROGRESS.md
- Orchestrator sends advisory via TeamMessage
- Coordinator delegates fixes appropriately
- Team resumes after diagnostic intervention

**Dependencies:** Phase 5 (team must be fully functional)

### Phase 7: UAT with Live Compounds (Week 4)

**Test cases:**
- Ibuprofen (C13H18O2) — baseline validation (v3.0 SUCCESS)
- Pulegone (C10H16O) — additional test case
- Virgiline (complex alkaloid) — stress test

**Success criteria:**
1. Team completes CASE workflow end-to-end
2. All v3.0 constraint-loss bugs fixed (DEFF NOT, SYME, grouped notation)
3. devils-advocate catches dropped constraints before LSD runs
4. solution-analyst provides quality assessment
5. CASE-PROGRESS.md is coherent and informative

**Dependencies:** Phases 1-6 (full stack complete)

### Dependency Chain Rationale

1. **Orchestrator first:** Team cannot spawn without orchestrator support
2. **Agents second:** Orchestrator needs agents to delegate to
3. **Constraint inventory third:** Critical for fixing v3.0 bugs
4. **Format fourth:** Communication protocol must be stable
5. **Coordination fifth:** All pieces assembled, now integrate workflow
6. **Diagnostic sixth:** Edge case handling after core workflow works
7. **UAT last:** Validate full system with real data

**Critical path:** Orchestrator → Agents → Constraint inventory → Coordination → UAT

**Estimated timeline:** 4 weeks for full implementation and validation

**Confidence:** HIGH — Build order is logical and incremental, each phase is independently testable.

## 8. Integration Patterns and Examples

### Pattern 1: TeamCreate in Orchestrator

**Before (v3.0):**
```markdown
<step name="spawn_case_agent">
Task(
  agent_type="lucy-case-agent",
  model="opus",
  instructions="Perform CASE workflow for compound at <compound_path> with formula <formula>.

  Write analysis/CASE-PROGRESS.md after EVERY LSD iteration.
  ..."
)
</step>
```

**After (v4.0):**
```markdown
<step name="spawn_case_team">
TeamCreate(
  team_definition={
    "team_lead": "case-coordinator",
    "teammates": [
      {"agent_type": "nmr-chemist", "model": "opus"},
      {"agent_type": "lsd-engineer", "model": "opus"},
      {"agent_type": "solution-analyst", "model": "opus"},
      {"agent_type": "devils-advocate", "model": "opus"}
    ],
    "shared_context": {
      "compound_path": "<compound_path>",
      "formula": "<formula>",
      "database_path": "data/reference/lucy-ng-derep.db",
      "iteration": 0,
      "safety_cap": 10
    }
  },
  instructions="Coordinate CASE workflow with specialized team.

  Team lead (case-coordinator): Manage iteration lifecycle, assign tasks, synthesize results.

  NMR-Chemist: Peak picking, multiplicity assignment, statistical detection.

  LSD-Engineer: Constraint building, LSD file construction, inventory management.

  Solution-Analyst: Solution ranking, chemical plausibility, quality assessment.

  Devils-Advocate: Pre-run validation, constraint checking, diff analysis.

  All agents: Append to analysis/CASE-PROGRESS.md after completing assigned tasks.

  Stopping conditions: solution_count <= 10 OR iterations >= 10 OR team consensus on escalation.
  "
)
</step>
```

**Key changes:**
- Explicit team structure (lead + teammates)
- Shared context (all agents see same data)
- Role-specific instructions (but detailed knowledge in agent definitions)

### Pattern 2: Knowledge Distribution Example

**v3.0 monolithic (lucy-case-agent.md):**
```markdown
## 3. LSD Command Reference

### MULT - Atom Definitions
**Syntax:** `MULT atom_index element hybridization hydrogen_count`
...

### HSQC - Direct C-H Attachment
**Syntax:** `HSQC carbon_index proton_position`
...

### Statistical Detection Protocol
**Timing:** Run detection AFTER peak picking, BEFORE LSD file writing
**Commands:** `lucy detect hybridisation <shift>`, ...
...

### Incremental HMBC Strategy
**Core principle:** NEVER add all HMBC at once, use 3-5 batches
...
```

**v4.0 distributed:**

**nmr-chemist.md:**
```markdown
## Statistical Detection Protocol

Run detection for ambiguous assignments:
- Hybridisation: `lucy detect hybridisation <db> <shift> --format json`
- Neighbours: `lucy detect neighbours <db> <shift> --format json`
- Signal grouping: `lucy analyze grouping "<shifts>" --format json`

Post results to team:
"Carbon at <shift> ppm: sp2=<fraction> (detection), sp3=<fraction> → recommend MULT hybridization=<2 or 3>"

DO NOT write LSD commands directly — report findings to lsd-engineer.
```

**lsd-engineer.md:**
```markdown
## LSD Command Reference

### MULT - Atom Definitions
**Syntax:** `MULT atom_index element hybridization hydrogen_count`
**Example:** `MULT 1 C 2 0  ; sp2 quaternary carbon`

Receive hybridization assignments from nmr-chemist:
- "sp2=0.92" → hybridization=2
- "sp3=0.88" → hybridization=3

### Incremental HMBC Strategy

Receive HMBC batch from nmr-chemist (3-5 correlations per iteration).

**CRITICAL:** Read previous iteration LSD file BEFORE writing new one.
Preserve ALL existing constraints (MULT, HSQC, DEFF NOT, SYME, BOND, LIST/PROP).

**Workflow:**
1. Read analysis/iteration_{N-1}/compound.lsd (if exists)
2. Extract constraint inventory
3. Add new HMBC batch from nmr-chemist
4. Write analysis/iteration_N/compound.lsd with full inventory
5. Update constraint inventory comment header
```

**devils-advocate.md:**
```markdown
## Pre-Run Validation Protocol

Before LSD runs, validate file:

1. **Constraint preservation check:**
   - Diff iteration_N vs iteration_{N-1}
   - Verify DEFF NOT count unchanged (should be 6 patterns)
   - Verify SYME constraints preserved (if symmetric carbons detected)
   - Verify grouped notation preserved (if signal grouping detected)

2. **Structural checks:**
   - sp2 count EVEN
   - H budget matches formula
   - HSQC before HMBC (correlation order)

Post to team:
"✓ Validation passed: sp2=<count> (even), H=<count> (matches), DEFF NOT=<count> (preserved), SYME=<count> (preserved)"

OR

"✗ Validation FAILED: <issue> detected — lsd-engineer please fix before running"
```

**Handoff clarity:**
- nmr-chemist provides WHAT (assignments), not HOW (LSD syntax)
- lsd-engineer translates WHAT to HOW (LSD commands)
- devils-advocate validates HOW (file structure), not WHAT (chemistry)

### Pattern 3: Constraint Inventory Tracking

**LSD file header comment (iteration 3):**
```
; lucy-ng LSD Input File
; Compound: data/compound/ibuprofen
; Formula: C13H18O2
; Iteration: 3
; Generated: 2026-02-16 10:30:15
;
; === CONSTRAINT INVENTORY ===
; MULT: 15 atoms (13 C, 2 O)
;   - sp2: 6 (C1, C5, C6, C7, C8, O13)
;   - sp3: 9 (C2, C3, C4, C9, C10, C11, C12, C13, O14)
; HSQC: 10 correlations (all protonated carbons)
; HMBC: 15 correlations (5+5+5 batches from iterations 1-3)
; DEFF NOT: 6 patterns (strained rings)
;   - C1CC1 (cyclopropane)
;   - C1CCC1 (cyclobutane)
;   - C1NC1 (aziridine)
;   - C1NCC1 (azetidine)
;   - C1SC1 (thiirane)
;   - C1SCC1 (thietane)
; SYME: 2 constraints (equivalent carbons)
;   - C9-C10 (para-benzene pair)
;   - C11-C12 (para-benzene pair)
; BOND: 1 (C1-O13 carbonyl from detection)
; LIST/PROP: 0
; ELIM: 0 (not used)
; === END INVENTORY ===

MULT 1 C 2 0    ; C1: sp2 quaternary (carbonyl) at 180.56 ppm
MULT 2 C 3 2    ; C2: sp3 CH2 at 44.90 ppm (grouped with C3)
...
```

**devils-advocate diff check:**
```bash
# Compare iteration 3 vs iteration 2
diff analysis/iteration_02/compound.lsd analysis/iteration_03/compound.lsd

# Expected: 5 new HMBC lines, inventory updated, all other constraints preserved
# If DEFF NOT count changed: FLAG to team
# If SYME constraints removed: FLAG to team
```

**CASE-PROGRESS.md entry (lsd-engineer section):**
```markdown
### LSD-Engineer
**LSD file:** analysis/iteration_03/compound.lsd
**Constraints added:**
  - HMBC: 5 correlations (third batch)
    - C5-H12 (aromatic, strong intensity)
    - ...
**Constraints removed:** None
**Constraint inventory delta:**
  - HMBC: +5 (10 → 15)
  - All other constraints: unchanged (MULT=15, HSQC=10, DEFF NOT=6, SYME=2, BOND=1)
**Why:** Continuing incremental HMBC strategy, preserving all baseline constraints
```

**This fixes v3.0 bugs:**
- DEFF NOT dropped after iteration 1: Inventory tracks count, devils-advocate flags if missing
- SYME forgotten: Inventory tracks constraints, devils-advocate flags if removed
- Grouped notation lost: Inventory includes grouped signals, devils-advocate checks preservation

## 9. Risk Assessment and Mitigations

### Risk 1: Team Coordination Overhead

**Issue:** 5 agents coordinating may be slower than 1 monolithic agent

**Impact:** MEDIUM — Slower workflow acceptable if quality improves, but not if 5x slower

**Mitigation:**
- Benchmark v3.0 vs v4.0 on same compounds (time to solution)
- Optimize task assignment (parallel where possible)
- If overhead > 2x, consider reducing team size (3 agents instead of 5)

**Fallback:** Revert to enhanced monolithic agent with constraint inventory (hybrid approach)

### Risk 2: Knowledge Distribution Gaps

**Issue:** Splitting knowledge may create gaps where no agent knows the full context

**Impact:** HIGH — Could cause workflow failures or incorrect chemistry

**Mitigation:**
- Define clear interfaces between agents (WHAT each agent posts to team)
- Validate knowledge coverage during Phase 2 (ensure no NMR/LSD concepts missing)
- Include cross-references in agent definitions ("For X, see agent Y")
- UAT with diverse compounds to expose gaps

**Fallback:** Re-inline shared knowledge (duplicated across agents) if gaps emerge

### Risk 3: CASE-PROGRESS.md Corruption

**Issue:** Multiple agents appending concurrently may corrupt file

**Impact:** LOW — File corruption breaks orchestrator monitoring

**Mitigation:**
- Define append-only protocol (agents never overwrite)
- Use structured sections (agent name headers) for safe parsing
- Test concurrent writes during Phase 4
- Consider file locking if corruption observed

**Fallback:** Coordinator as sole writer, agents post to team only (coordinator writes to file)

### Risk 4: Constraint Inventory Maintenance Burden

**Issue:** lsd-engineer must maintain accurate inventory across iterations

**Impact:** MEDIUM — Inventory errors cause constraint loss (same bugs as v3.0)

**Mitigation:**
- Structured inventory format (JSON in LSD comment)
- devils-advocate validates inventory on every run
- Automated diff checking (not manual inspection)
- Fail-safe: If inventory corrupt, rebuild from full LSD file parse

**Fallback:** Simplified inventory (count-only, no detail), stricter diff validation

### Risk 5: TeamCreate API Limitations

**Issue:** Claude SDK TeamCreate may have undocumented limitations or bugs

**Impact:** HIGH — Could block entire v4.0 milestone

**Mitigation:**
- Early prototype during Phase 1 (validate TeamCreate works as expected)
- Test team size limits (5 agents may be near max)
- Test message passing (TeamMessage latency, reliability)
- Engage with Anthropic support if blockers encountered

**Fallback:** Revert to Task-based architecture with enhanced monolithic agent (v3.5 instead of v4.0)

## 10. Alternative Architectures Considered

### Alternative 1: Enhanced Monolithic Agent with Constraint Inventory

**Idea:** Keep single agent, add constraint inventory tracking and pre-run validation to existing lucy-case-agent.md

**Rejected because:**
- Doesn't address fundamental issue: agent reconstructs LSD from memory, loses constraints
- Single agent still prone to same bugs (forgetting DEFF NOT, SYME)
- No peer review → constraint loss invisible until results are wrong
- Misses opportunity for specialization (nmr-chemist, lsd-engineer have different expertise)

**Could be fallback if TeamCreate doesn't work.**

### Alternative 2: 3-Agent Simplified Team

**Idea:** Reduce team size to coordinator, scientist (nmr+lsd), validator (devils-advocate+solution-analyst)

**Rejected because:**
- Scientist role too broad (combines peak picking and constraint building, both complex)
- Loses specialization benefits (deep NMR knowledge vs deep LSD syntax knowledge)
- Constraint inventory still managed by scientist (same risk as monolithic)

**Could be optimization if 5-agent overhead is excessive.**

### Alternative 3: Blackboard Pattern with Shared State

**Idea:** Agents post to shared blackboard (JSON file), no direct communication

**Rejected because:**
- TeamCreate provides native messaging, blackboard is reinventing the wheel
- Blackboard requires coordination protocol design (who reads, who writes, when)
- No real-time peer review (agents don't see each other's posts immediately)
- Harder to debug (no conversation history, just state changes)

### Alternative 4: Sequential Pipeline (No Team Coordination)

**Idea:** Task chain: nmr-chemist → lsd-engineer → devils-advocate → solution-analyst (no team lead)

**Rejected because:**
- No feedback loops (solution-analyst can't request more HMBC from nmr-chemist)
- No iterative workflow (constraint building is inherently iterative)
- No peer review (agents can't flag each other's issues)
- Sequential = slow (can't parallelize independent tasks)

## 11. Success Criteria

### Functional Criteria

1. **Team spawns successfully:** Orchestrator TeamCreate produces 5 agents with correct roles
2. **Workflow completes end-to-end:** Team solves test compound (Ibuprofen) without manual intervention
3. **Constraint persistence:** DEFF NOT, SYME, grouped notation preserved across all iterations
4. **Pre-run validation:** devils-advocate detects and flags constraint loss BEFORE LSD runs
5. **Solution quality assessment:** solution-analyst provides chemical plausibility review
6. **CASE-PROGRESS.md coherence:** Multi-agent journal is readable and informative

### Performance Criteria

1. **Time to solution:** v4.0 completes in < 2x v3.0 time (acceptable overhead for quality gain)
2. **Iteration count:** Similar or fewer iterations than v3.0 (better constraint building)
3. **Solution rank:** Correct structure in top 3 (same as v3.0)
4. **Constraint coverage:** >= 95% of relevant constraints captured (HMBC, SYME, DEFF NOT)

### Quality Criteria

1. **Bug fixes verified:** All v3.0 UAT bugs fixed (DEFF NOT persistence, SYME encoding, grouped notation)
2. **Peer review effectiveness:** devils-advocate catches >= 90% of constraint errors before LSD runs
3. **Knowledge coverage:** No NMR/LSD concepts missing from distributed knowledge
4. **Coordination clarity:** Task assignments and results are unambiguous in CASE-PROGRESS.md

### UAT Validation

**Test 1: Ibuprofen (C13H18O2)**
- Baseline validation (v3.0 SUCCESS, rank #1, MAE=2.23)
- v4.0 should match or exceed (rank #1, MAE < 3.0, 3-5 iterations)
- All constraints preserved across iterations
- devils-advocate flags any dropped constraints

**Test 2: Pulegone (C10H16O)**
- Additional validation (different functional groups)
- Ketone vs carboxylic acid differentiation
- SYME for equivalent methyl groups
- v4.0 should solve in < 8 iterations

**Test 3: Virgiline (complex alkaloid)**
- Stress test (multiple nitrogen atoms, complex connectivity)
- Team should handle complexity better than monolithic agent
- If team escalates to orchestrator: acceptable (diagnostic specialist should help)

## 12. Integration Checklist

### Orchestrator Modifications
- [ ] Replace Task() with TeamCreate() in spawn step
- [ ] Define team_definition structure
- [ ] Update CASE-PROGRESS.md parser for multi-agent format
- [ ] Implement TeamMessage for advisory delivery
- [ ] Test diagnostic specialist integration with team context

### Agent Definitions
- [ ] Create ~/.claude/agents/lucy-ng/case-team/ directory
- [ ] Write coordinator.md (team lead workflow)
- [ ] Write nmr-chemist.md (peak picking, detection)
- [ ] Write lsd-engineer.md (constraint building, inventory)
- [ ] Write solution-analyst.md (ranking, quality)
- [ ] Write devils-advocate.md (pre-run validation)
- [ ] Verify agent discovery in subdirectory

### Knowledge Distribution
- [ ] Extract NMR knowledge from lucy-case-agent.md → nmr-chemist.md
- [ ] Extract LSD knowledge from lucy-case-agent.md → lsd-engineer.md
- [ ] Extract ranking knowledge → solution-analyst.md
- [ ] Define inter-agent interfaces (WHAT to post)
- [ ] Cross-reference agents for shared concepts
- [ ] Validate no knowledge gaps

### Constraint Inventory System
- [ ] Define inventory format (JSON in LSD comment)
- [ ] Implement "read previous LSD file" in lsd-engineer
- [ ] Implement diff protocol in devils-advocate
- [ ] Test constraint preservation across iterations
- [ ] Validate DEFF NOT, SYME, grouped notation tracking

### CASE-PROGRESS.md Format
- [ ] Define multi-agent section structure
- [ ] Implement coordinator iteration headers
- [ ] Implement agent section append protocol
- [ ] Test concurrent writes (no corruption)
- [ ] Validate orchestrator can parse team format

### Team Coordination
- [ ] Define task list structure (shared state)
- [ ] Implement coordinator task assignment
- [ ] Implement teammate task claiming
- [ ] Implement result synthesis
- [ ] Test iteration loop (full cycle)

### UAT Execution
- [ ] Run v4.0 on Ibuprofen (baseline)
- [ ] Run v4.0 on Pulegone (additional)
- [ ] Run v4.0 on Virgiline (stress test)
- [ ] Compare performance vs v3.0 (time, iterations, quality)
- [ ] Verify all v3.0 bugs fixed

## Conclusion

The 5-agent CASE team architecture is a substantial but achievable evolution of the v3.0 single-agent system. Key integration points:

1. **Orchestrator:** Replace Task() with TeamCreate(), update monitoring for multi-agent format
2. **Agents:** 5 specialized agents in `~/.claude/agents/lucy-ng/case-team/` with distributed knowledge
3. **Constraint inventory:** lsd-engineer reads previous file, devils-advocate validates, inventory tracked in LSD comments
4. **CASE-PROGRESS.md:** Multi-agent journal with per-agent sections, coordinator writes headers
5. **Diagnostic specialist:** Remains orchestrator-spawned (not team member), sends advisory via TeamMessage

**Critical success factors:**
- Constraint inventory must be reliable (prevents v3.0 bugs)
- Knowledge distribution must be complete (no gaps)
- Team coordination must be efficient (< 2x overhead)
- Pre-run validation must catch errors (devils-advocate effectiveness)

**Recommended build order:**
1. Orchestrator skill modification (Week 1)
2. Agent definitions with knowledge distribution (Weeks 1-2)
3. Constraint inventory system (Week 2)
4. CASE-PROGRESS.md format (Week 2)
5. Team coordination protocol (Week 3)
6. Diagnostic integration (Week 3)
7. UAT with live compounds (Week 4)

**Estimated effort:** 4 weeks for full implementation and validation.

**Confidence:** HIGH for integration points, MEDIUM for team dynamics and coordination efficiency (requires empirical validation through UAT).

## Sources

Research based on:

**Claude Agent Teams:**
- [Orchestrate teams of Claude Code sessions - Claude Code Docs](https://code.claude.com/docs/en/agent-teams)
- [Agent Teams with Claude Code and Claude Agent SDK | Medium](https://kargarisaac.medium.com/agent-teams-with-claude-code-and-claude-agent-sdk-e7de4e0cb03e)
- [Claude Code Agent Teams: Multi-Session Orchestration](https://claudefa.st/blog/guide/agents/agent-teams)
- [Anthropic releases Opus 4.6 with new 'agent teams' | TechCrunch](https://techcrunch.com/2026/02/05/anthropic-releases-opus-4-6-with-new-agent-teams/)
- [Introducing Claude Opus 4.6 | Anthropic](https://www.anthropic.com/news/claude-opus-4-6)

**Multi-Agent Architecture Patterns:**
- [AI Agent Orchestration Patterns - Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Four Design Patterns for Event-Driven, Multi-Agent Systems](https://www.confluent.io/blog/event-driven-multi-agent-systems/)
- [Choose a design pattern for your agentic AI system | Google Cloud](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)
- [Choosing the Right Multi-Agent Architecture | LangChain](https://blog.langchain.com/choosing-the-right-multi-agent-architecture/)

**Project Context:**
- lucy-ng CLAUDE.md, PROJECT.md, STATE.md (local project files)
- Existing ARCHITECTURE.md (statistical detection features, v3.0)
- lucy-case-agent.md, lucy-diagnostic.md, case.md (current agent/skill architecture)

---
*Architecture research for: lucy-ng v4.0 Team-Based CASE*
*Researched: 2026-02-16*
