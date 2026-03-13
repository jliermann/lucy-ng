# Architecture Research: pyLSD Integration

**Domain:** pyLSD integration into existing lucy-ng CASE pipeline (v8.0)
**Researched:** 2026-03-13
**Confidence:** HIGH (existing codebase examined in full, real pyLSD file from project email archive examined, pyLSD official docs fetched, LSD tutorial PDF located)

---

## Executive Summary

pyLSD is not a replacement for LSD — it is a Python driver that calls LSD multiple times. Lucy-ng already calls LSD once per iteration via `LSDRunner`. The v8.0 integration replaces that single call with a pyLSD-style multi-run: one call per HMBC correlation permutation where suspect 4J correlations are toggled on/off. The result is a merged SMILES pool ranked by the existing `SolutionRanker`.

The key architectural finding from examining a real pyLSD file (`C13H6O8_pyLSD_Michael.lsd`) is that pyLSD is not a separate solver — it is a file format extension plus a Python orchestrator. The LSD binary does the actual solving. Lucy-ng already uses the LSD binary directly and already has `LSDRunner`. The v8.0 work therefore splits into three clean layers:

1. **File format extension** — add `FORM`, `ELIM`, `SHIX` support to `LSDInputGenerator` and the constraint inventory (agent-side changes are minimal — lsd-engineer adds `ELIM N N` when flagging 4J correlations).

2. **Multi-run orchestration in Python** — new `PyLSDOrchestrator` class in `src/lucy_ng/lsd/` that takes a base LSD file, a list of suspect HMBC lines, and runs LSD once per permutation, collecting all solutions.

3. **Solution deduplication** — new `SolutionMerger` that deduplicates SMILES across runs before passing to the existing `SolutionRanker`.

The agent team changes are contained: lsd-engineer learns to annotate suspect HMBC correlations with `; ELIM` comments (already practiced informally in iteration_07 file) and optionally writes `ELIM N N`. The orchestrator skill learns to call `lucy pylsd run` instead of `lucy lsd run`. No other agent changes are needed.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CASE Agent Workflow (unchanged)                     │
│  ┌──────────────┐   ┌────────────────┐   ┌──────────────────────────┐   │
│  │ nmr-chemist  │   │  lsd-engineer  │   │    solution-analyst       │   │
│  │ flags 4J     │   │ writes .lsd    │   │   ranks+verifies          │   │
│  │ correlations │   │ adds ELIM N N  │   │   aromatic ring check     │   │
│  └──────┬───────┘   └───────┬────────┘   └───────────┬──────────────┘   │
│         │  4J flag[]        │  compound.lsd           │ ranked SMILES     │
└─────────┼───────────────────┼─────────────────────────┼──────────────────┘
          │                   │                         │
┌─────────┼───────────────────┼─────────────────────────┼──────────────────┐
│         │      CLI Layer    │                         │                   │
│         │   lucy pylsd run  ▼                         │                   │
│         │   ┌──────────────────────────────────────┐  │                   │
│         │   │        PyLSDOrchestrator              │  │                   │
│         │   │  - parse ELIM lines from .lsd        │  │                   │
│         │   │  - generate N permutation files      │  │                   │
│         │   │  - call LSDRunner N times            │  │                   │
│         │   │  - collect .sol files                │  │                   │
│         │   │  - call outlsd N times               │  │                   │
│         │   └───────────┬──────────────────────────┘  │                   │
│         │               │  N * .sol files              │                   │
│         │   ┌───────────▼──────────────────────────┐  │                   │
│         │   │        SolutionMerger                 │  │                   │
│         │   │  - deduplicate SMILES (InChI key)    │  │                   │
│         │   │  - write merged.smi                  │  │                   │
│         │   └───────────┬──────────────────────────┘  │                   │
│         │               │  merged.smi                  │                   │
│         │   ┌───────────▼──────────────────────────┐  │                   │
│         └───►  lucy lsd rank merged.smi --shifts    ├──┘                   │
│               │        (unchanged)                  │                      │
│               └────────────────────────────────────┘                      │
├────────────────────────────────────────────────────────────────────────────┤
│                     Solver Layer (unchanged)                               │
│  ┌───────────────┐   ┌────────────┐   ┌────────────┐                      │
│  │  LSDRunner    │   │  LSD binary│   │   outlsd   │                      │
│  │  (subprocess) │──►│  (solver)  │──►│  (SMILES)  │                      │
│  └───────────────┘   └────────────┘   └────────────┘                      │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

### Existing Components (unchanged or minimally extended)

| Component | Location | What changes in v8.0 |
|-----------|----------|----------------------|
| `LSDRunner` | `src/lucy_ng/lsd/runner.py` | None — called by `PyLSDOrchestrator` |
| `LSDInputGenerator` | `src/lucy_ng/lsd/generator.py` | Add `FORM`, `ELIM N N`, `SHIX` emission; parse `; ELIM` annotation |
| `LSDOutputParser` | `src/lucy_ng/lsd/parser.py` | None |
| `SolutionRanker` | `src/lucy_ng/ranking/` | None — accepts merged SMILES file |
| `lsd_run` CLI | `src/lucy_ng/cli/lsd.py` | None — preserved for single-run use |
| `lsd_rank` CLI | `src/lucy_ng/cli/lsd.py` | None |
| `LSDSolutionAnalyzer` | `src/lucy_ng/lsd/analyzer.py` | None |

### New Components (v8.0 adds)

| Component | Location | Responsibility |
|-----------|----------|----------------|
| `PyLSDOrchestrator` | `src/lucy_ng/lsd/pylsd_orchestrator.py` | Parse ELIM-annotated .lsd file, generate permutations, run LSD N times, collect solutions |
| `SolutionMerger` | `src/lucy_ng/lsd/solution_merger.py` | Deduplicate SMILES from multiple runs using InChI keys; write merged.smi |
| `pylsd run` CLI | `src/lucy_ng/cli/lsd.py` (new subcommand) | Thin CLI wrapper over `PyLSDOrchestrator` |

### Agent Files (partial changes only)

| File | Location | What changes |
|------|----------|--------------|
| lsd-engineer agent | `~/.claude/agents/lsd-engineer.md` | Add `ELIM N N` writing rule; annotate suspect HMBC lines with `; ELIM` |
| case.md orchestrator skill | `~/.claude/commands/lucy-ng/case.md` | Replace `lucy lsd run` with `lucy pylsd run` when 4J correlations flagged |
| CLAUDE.md / SKILL.md | project root | Update `lucy lsd run` → `lucy pylsd run` in CLI reference |

---

## Key Design Decisions

### Decision 1: pyLSD as File Format + Orchestration, Not Replacement

**What:** pyLSD is not a separate binary or library to install — it is a Python script (`lsd.py`) that reads an extended LSD file and calls the LSD binary multiple times. Lucy-ng already has `LSDRunner` calling the LSD binary. The v8.0 work replicates what pyLSD does: generate permutation files, run LSD on each, merge results.

**Why not just call `python lsd.py`:** The pyLSD distribution is not a pip-installable package. It ships as a compressed archive with hardcoded paths and an nmrshiftdb2 dependency for its own ranking. Lucy-ng already has superior HOSE-based ranking. Wrapping the pyLSD Python script as a subprocess would create a fragile dependency on an unmaintained distribution. Building the equivalent multi-run logic inside lucy-ng is cleaner, testable, and gives full control over the permutation strategy.

**Confidence:** HIGH — confirmed by examining pyLSD GitHub repo (archived distribution, no pip package, version a8 based on LSD-3.5.2) and the real pyLSD file in the project email archive.

### Decision 2: ELIM Annotation as the Agent-File-Format Contract

**What:** The agent (lsd-engineer) annotates suspect HMBC lines with `; ELIM` comment and writes `ELIM N N` at the file header. The `PyLSDOrchestrator` parses this annotation to identify which correlations to permute.

**Evidence from real file (`C13H6O8_pyLSD_Michael.lsd`):**
```
ELIM 4 4          ; global: allow up to 4 correlations to be treated as 4J, up to 4 bonds
...
HMBC 11 10 3 4; ELIM   ; this specific HMBC allows 3-4 bonds (not default 2-3)
HMBC 9 11 3 4; ELIM    ; same
```

**What `ELIM N N` means:** `ELIM x y` = allow LSD to eliminate up to `x` HMBC correlations that may arise from couplings through up to `y` bonds. This is the core mechanism: LSD will try excluding each marked correlation to see if removing it yields solutions.

**Why this is better than generating multiple .lsd files manually:** The `; ELIM` annotation is already natural for the lsd-engineer agent (iteration_07 uses it as a comment already). Making it the trigger for multi-run keeps the LSD file as the single source of truth and the constraint inventory already tracks these annotations.

### Decision 3: Coexist, Not Replace

**What:** `lucy lsd run` is preserved unchanged. A new `lucy pylsd run` command wraps `PyLSDOrchestrator`. The orchestrator skill uses `lucy pylsd run` only when `nmr-chemist` has flagged 4J correlations. For compounds with no 4J risk, the workflow uses the original `lucy lsd run`.

**Why:** Backwards compatibility. The existing CASE workflow is validated and working. Forcing all runs through multi-run when there are no 4J correlations adds complexity with no benefit. The orchestrator skill detects 4J flag presence and routes accordingly.

### Decision 4: Deduplication by InChI Key, Not SMILES

**What:** `SolutionMerger` converts each SMILES to InChI (via RDKit) and uses InChI keys as the deduplication key. Multiple permutation runs will generate the same structure via different constraint paths.

**Why not SMILES comparison:** SMILES strings for the same structure differ by atom ordering, ring notation, and aromaticity representation. InChI is canonical and handles tautomers, stereochemistry flags, and ring notation uniformly. RDKit is already a dependency.

**Risk:** InChI generation can fail for unusual valence atoms. `SolutionMerger` falls back to SMILES string comparison when InChI fails (with a warning).

---

## Data Flow: 4J HMBC Exploration

```
1. nmr-chemist
   → detects aromatic pattern (127-141 ppm, sp2 carbons)
   → flags specific HMBC correlations as suspect 4J
   → posts flags to coordinator

2. lsd-engineer (receives 4J flags)
   → writes compound.lsd with:
       ELIM 2 4             ; allow up to 2 correlations excluded, up to 4 bonds
       ...
       HMBC 4 8 2 4 ; ELIM  ; suspect 4J: bond range extended to 2-4
       HMBC 6 9 2 4 ; ELIM  ; suspect 4J: bond range extended to 2-4
   → updates constraint inventory: "elim_value": "2 4", "elim_annotated": ["4 8", "6 9"]

3. orchestrator skill (detects ELIM in constraint inventory)
   → calls: lucy pylsd run compound.lsd --shifts "180.56,140.84,..."
   → NOT: lucy lsd run compound.lsd

4. PyLSDOrchestrator (Python)
   → parses compound.lsd, finds 2 ; ELIM lines
   → generates permutations: [(include 4 8, include 6 9), (exclude 4 8, include 6 9),
                               (include 4 8, exclude 6 9), (exclude 4 8, exclude 6 9)]
   → for each permutation:
       - write permutation_NN.lsd (copy of compound.lsd with that HMBC line removed or kept)
       - run LSDRunner on permutation_NN.lsd
       - if solutions: run outlsd, collect SMILES
   → hands collected SMILES to SolutionMerger

5. SolutionMerger
   → deduplicates by InChI key
   → writes merged.smi
   → writes run_report.json: {"total_raw": 45, "unique": 12, "permutations": 4, "yielded": [0,1,2,3]}

6. lucy lsd rank merged.smi --shifts "180.56,..." (unchanged)
   → returns ranked solutions as before

7. solution-analyst (unchanged)
   → reviews ranked solutions
   → checks aromatic ring presence
   → uses run_report.json to note which permutations contributed solutions
```

---

## File Format Extensions

### What lsd-engineer writes (v8.0 additions to existing format)

```
; === CONSTRAINT INVENTORY v2 ===
; {
;   ...existing fields...
;   "elim_value": "2 4",
;   "elim_annotated": ["4 8", "6 9"],
;   "pylsd_mode": true
; }
; === END CONSTRAINT INVENTORY ===

FORM C 13 H 18 O 2   ; pyLSD extension: molecular formula (pyLSD reads this)
ELIM 2 4             ; pyLSD extension: allow up to 2 correlations as 4J through 4 bonds

MULT 1 C 2 0 ...
...

HMBC 4 8 2 4 ; ELIM  ; bond range 2-4 (not default 2-3): suspect 4J aromatic-to-benzylic
HMBC 6 9 2 4 ; ELIM  ; bond range 2-4: suspect 4J aromatic-to-benzylic
HMBC 3 9             ; normal 3J, no ELIM
```

**Key additions:**
- `FORM C 13 H 18 O 2` — pyLSD FORM command. Not used by LSD binary, but harmless (LSD ignores unknown commands). Useful for documentation and future pyLSD compatibility.
- `ELIM x y` — LSD does understand this. It allows the solver to try excluding up to `x` marked correlations that span up to `y` bonds.
- `HMBC C H min_bonds max_bonds ; ELIM` — extended HMBC with explicit bond range. The `; ELIM` comment is parsed by `PyLSDOrchestrator` to identify permutable correlations.
- `SHIX` — already partially supported in `LSDInputGenerator` (lines 74-77 of generator.py). No new work needed.

**Note on LSD vs pyLSD for ELIM:** The LSD binary itself has an `ELIM` command — this was confirmed in the WebSearch result ("ELIM x y" allows LSD to eliminate up to x HMBC correlations). pyLSD adds the `FORM` command and the variable-status atom syntax `MULT N O (2 3) 0`. The ELIM command is a base LSD feature, not pyLSD-specific. This means lucy-ng can use `ELIM` with the existing LSD binary without needing to call pyLSD at all.

**Revised understanding:** The multi-run permutation approach is one strategy. LSD's own `ELIM N N` may already handle this internally in a single run. The `PyLSDOrchestrator` is still useful for explicit control over which correlations to test, producing per-permutation solution reports that the solution-analyst can inspect.

---

## Build Order and Phase Dependencies

### Phase Structure Recommendation

The work naturally splits into three waves with clear dependencies:

**Wave 1 — Foundation (no dependencies between phases, run in parallel)**

| Phase | What | Why First |
|-------|------|-----------|
| PYLSD-01 | `LSDInputGenerator` extensions: emit `FORM`, `ELIM N N`, extended HMBC bond ranges, parse `; ELIM` annotation | Everything else depends on the file format being correct |
| PYLSD-02 | `PyLSDOrchestrator` + `SolutionMerger` Python classes | Core new machinery; no CLI until this is tested |
| PYLSD-03 | Constraint inventory v2 schema: add `elim_value`, `elim_annotated`, `pylsd_mode` fields | Agent team needs the schema before writing updated LSD files |

**Wave 2 — CLI and Agent (depend on Wave 1)**

| Phase | What | Depends On |
|-------|------|-----------|
| PYLSD-04 | `lucy pylsd run` CLI command | PYLSD-01, PYLSD-02 |
| PYLSD-05 | lsd-engineer agent update: `ELIM N N` writing rule, `; ELIM` annotation rule, constraint inventory v2 | PYLSD-03 |
| PYLSD-06 | case.md orchestrator skill update: `lucy pylsd run` routing when `pylsd_mode: true` in inventory | PYLSD-04, PYLSD-05 |

**Wave 3 — Validation (depend on Wave 2)**

| Phase | What | Depends On |
|-------|------|-----------|
| PYLSD-07 | Ibuprofen CASE smoke test with pyLSD mode: verify correct structure found with 4J correlations included | All Wave 2 |
| PYLSD-08 | `lucy lsd check` extension: report pyLSD mode availability | PYLSD-04 |

### Build Order Rationale

- PYLSD-01 before PYLSD-02: the orchestrator needs the annotation parsing logic from the generator.
- PYLSD-03 is independent of PYLSD-01/02: schema is agent-facing metadata, not Python runtime.
- PYLSD-04 before PYLSD-06: the CLI command must exist before the orchestrator skill references it.
- PYLSD-05 before PYLSD-06: the skill cannot route to pyLSD mode until the agent knows how to set `pylsd_mode: true` in the inventory.
- PYLSD-07 last: the smoke test exercises the full stack.

---

## Architectural Patterns

### Pattern 1: Permutation File Generation

**What:** Given a base .lsd file with N `; ELIM`-annotated HMBC lines, generate 2^N permutation files by including/excluding each annotated line. For N <= 4 (typical for 4J aromatic systems) this is 16 files maximum.

**When to use:** Whenever `pylsd_mode: true` in constraint inventory.

**Trade-off:** Exponential in N. For N > 4, prune by only generating permutations where exactly 0, 1, or 2 correlations are excluded (not all 2^N combinations). This is `O(N^2)` permutations, sufficient for practical cases.

**Example:**
```python
from itertools import combinations

def generate_permutations(elim_lines: list[int], max_exclude: int = 2) -> list[set[int]]:
    """Generate sets of line indices to EXCLUDE (not include) from base file."""
    result: list[set[int]] = [set()]  # always include the all-included case
    for n in range(1, min(max_exclude + 1, len(elim_lines) + 1)):
        for excluded in combinations(elim_lines, n):
            result.append(set(excluded))
    return result
```

### Pattern 2: Run Report for Solution Traceability

**What:** `PyLSDOrchestrator` writes `run_report.json` alongside `merged.smi` recording which permutation each SMILES came from, how many raw solutions per run, and which HMBC lines were excluded in each permutation.

**Why:** The solution-analyst needs to know whether the correct structure was found with all correlations included (good) or only after excluding suspect 4J ones (signals 4J confirmation). This is directly relevant to the CASE-PROGRESS.md narrative.

**Format:**
```json
{
  "total_raw_solutions": 47,
  "unique_solutions": 12,
  "permutations": [
    {"id": 0, "excluded_hmbc": [], "solutions": 0},
    {"id": 1, "excluded_hmbc": ["4 8"], "solutions": 7},
    {"id": 2, "excluded_hmbc": ["6 9"], "solutions": 0},
    {"id": 3, "excluded_hmbc": ["4 8", "6 9"], "solutions": 40}
  ]
}
```

### Pattern 3: Constraint Inventory v2 Guards

**What:** The `pylsd_mode: true` flag in the constraint inventory is the single routing signal. The orchestrator skill checks this field. If absent or false, `lucy lsd run` is used. If true, `lucy pylsd run` is used.

**Why:** Avoids any ambiguity about which path is taken. The lsd-engineer agent sets this flag explicitly when it detects 4J correlations and writes `ELIM N N`. The devils-advocate agent can verify this field exists when `; ELIM` annotations are present in the file.

---

## Anti-Patterns

### Anti-Pattern 1: Installing pyLSD as an External Dependency

**What people do:** Try to pip install pyLSD or call the `python lsd.py` script as a subprocess from lucy-ng.

**Why wrong:** pyLSD is not pip-installable. It is a research distribution shipped as a compressed archive with hardcoded paths. It has its own nmrshiftdb2-based ranking that duplicates and conflicts with lucy-ng's HOSE-based ranking. It requires Java for structure diagram generation that lucy-ng does not use.

**Do this instead:** Implement the multi-run orchestration directly in `PyLSDOrchestrator`. This is 150-200 lines of Python and is fully testable. The LSD binary is already available on the system.

### Anti-Pattern 2: Agent Generates Permutation Files Manually

**What people do:** Have lsd-engineer write multiple .lsd variants manually, each with a different HMBC line removed.

**Why wrong:** N correlations = 2^N manual files. The agent has no reliable way to track which permutations were run, and the constraint inventory cannot represent the state cleanly. The agent will lose track after 2-3 iterations.

**Do this instead:** Agent writes one file with `; ELIM` annotations, Python handles permutation generation. This is the division of labour that matches the architecture: agent encodes chemical reasoning, Python handles combinatorial execution.

### Anti-Pattern 3: Deduplicating by SMILES String

**What people do:** Use Python `set()` on SMILES strings to deduplicate across runs.

**Why wrong:** LSD generates structures with arbitrary atom ordering. The same ibuprofen molecule may be `CC(C)Cc1ccc(cc1)C(C)C(=O)O` in one run and `OC(=O)C(C)Cc1ccc(cc1)CC(C)C` in another. String comparison gives false duplicates.

**Do this instead:** Convert each SMILES to InChI key via RDKit and use that as the deduplication key.

### Anti-Pattern 4: Running pyLSD Mode on Every Iteration

**What people do:** Always use `lucy pylsd run` regardless of whether 4J correlations are suspected.

**Why wrong:** Multi-run with N=0 ELIM annotations degenerates to a single LSD run with overhead. More importantly, running permutations when no 4J risk exists obscures the distinction between "correct structure found directly" vs "found only after 4J exclusion". The run report loses meaning.

**Do this instead:** Preserve `lucy lsd run` for the normal case. Route to `lucy pylsd run` only when `pylsd_mode: true` in the constraint inventory.

---

## Integration Points

### Python Layer Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `PyLSDOrchestrator` → `LSDRunner` | Direct instantiation and `run_file()` call | One `LSDRunner` instance, called N times in a loop |
| `PyLSDOrchestrator` → `SolutionMerger` | Direct: passes list of SMILES strings | No file I/O between these two classes |
| `SolutionMerger` → `SolutionRanker` | Via CLI: `lucy lsd rank merged.smi` | Ranking is unchanged; merger produces a .smi file |
| `LSDInputGenerator` → `PyLSDOrchestrator` | `PyLSDOrchestrator` calls `LSDInputGenerator.remove_elim_line(content, line_idx)` | Generator provides the file manipulation helpers |

### CLI Boundary

| Command | Input | Output | Notes |
|---------|-------|--------|-------|
| `lucy pylsd run <lsd_file> --shifts <shifts>` | .lsd file with `; ELIM` annotations | `merged.smi`, `run_report.json` | Replaces `lucy lsd run` in 4J case |
| `lucy lsd run` | .lsd file | .sol, outlsd.out | Preserved unchanged |
| `lucy lsd rank merged.smi --shifts <shifts>` | merged.smi | ranked solutions | Unchanged; accepts merged.smi directly |

### Agent Skill Boundary

| Agent | Input trigger | New output | Preserved output |
|-------|--------------|------------|-----------------|
| nmr-chemist | aromatic sp2 pattern + benzylic HMBC | `4j_suspects: ["4 8", "6 9"]` in message | All existing NMR analysis |
| lsd-engineer | `4j_suspects` in coordinator message | `ELIM N N`, `; ELIM` annotations, `pylsd_mode: true` in inventory | All existing LSD writing rules |
| case.md (orchestrator) | `pylsd_mode: true` in constraint inventory | calls `lucy pylsd run` instead of `lucy lsd run` | All existing loop detection, intervention |
| solution-analyst | `run_report.json` exists | notes which permutation yielded solution | All existing ranking, aromatic ring check |
| devils-advocate | `elim_annotated` in inventory | verifies `; ELIM` count matches `elim_annotated` list | All existing pre-run validation |

---

## Existing Code Reuse Map

| New Component | Reuses |
|---------------|--------|
| `PyLSDOrchestrator.run()` | `LSDRunner.run_file()` — no changes needed |
| `SolutionMerger.deduplicate()` | `LSDOutputParser.parse_smiles_file()` to read SMILES; RDKit (already a dep) for InChI |
| `pylsd run` CLI | `lsd_run()` pattern in `cli/lsd.py` — copy structure, add permutation loop |
| `LSDInputGenerator` extensions | Adds `emit_form()`, `emit_elim()`, `parse_elim_annotations()` static methods |

The only genuinely new code is `PyLSDOrchestrator` (~150 lines) and `SolutionMerger` (~80 lines). Everything else is additive to existing classes.

---

## Confidence Assessment

| Area | Confidence | Evidence |
|------|------------|---------|
| ELIM command syntax | HIGH | Real pyLSD file examined (`ELIM 4 4`, `HMBC 11 10 3 4; ELIM`) |
| pyLSD as multi-run driver | HIGH | pyLSD documentation fetched, GitHub examined |
| Multi-run not needing pyLSD binary | HIGH | pyLSD is not pip-installable; LSD binary supports ELIM natively |
| InChI deduplication approach | HIGH | RDKit InChI confirmed canonical across atom orderings |
| FORM command behavior | MEDIUM | Documented in pyLSD docs; untested whether LSD binary ignores it harmlessly |
| Permutation count in practice | MEDIUM | Ibuprofen has 4 suspect 4J correlations → 16 permutations max, likely practical |
| Agent workflow changes | HIGH | Iteration_07 file shows agents already annotating `; ELIM` informally |

---

## Sources

- pyLSD official documentation: [https://nuzillard.github.io/PyLSD/](https://nuzillard.github.io/PyLSD/)
- pyLSD GitHub repository: [https://github.com/nuzillard/PyLSD](https://github.com/nuzillard/PyLSD)
- Real pyLSD example file: `/Users/steinbeck/Dropbox/Private/Mail/.../C13H6O8_pyLSD_Michael.lsd` (from project email archive)
- LSD tutorial (Nuzillard 2017, MRC): ELIM command described — "ELIM x y allows LSD to eliminate up to x HMBC correlations that may arise from VLRCs through up to y bonds"
- Existing LSD file with informal ELIM annotations: `data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_07/compound.lsd`
- `src/lucy_ng/lsd/runner.py` — current `LSDRunner` implementation examined
- `src/lucy_ng/lsd/generator.py` — current `LSDInputGenerator` examined (SHIX partially supported at lines 73-77)
- `src/lucy_ng/lsd/models.py` — `LSDProblem`, `LSDCorrelation` models examined

---
*Architecture research for: pyLSD integration into lucy-ng CASE pipeline (v8.0)*
*Researched: 2026-03-13*
