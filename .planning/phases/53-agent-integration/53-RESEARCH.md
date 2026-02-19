# Phase 53: Agent Integration - Research

**Researched:** 2026-02-19
**Domain:** Agent instruction file modifications (markdown), CLI integration patterns, constraint inventory schema extension
**Confidence:** HIGH

## Summary

Phase 53 integrates the completed fragment search and DEFF formatting pipeline (Phases 49-52) into the CASE agent team by modifying three markdown agent definition files: `lucy-lsd-engineer.md`, `lucy-devils-advocate.md`, and the orchestrator skill `case.md`. No Python code changes are needed -- the CLI pipeline (`lucy fragment search --format json`, `lucy fragment to-lsd`) is complete and validated with LSD smoke tests.

The integration requires four coordinated changes: (1) add a fragment search step to lsd-engineer's per-iteration workflow, (2) extend the constraint inventory JSON schema with a `deff_fexp` section, (3) add fragment file existence checks to the devils-advocate validation protocol, and (4) add fragment result logging to the CASE-PROGRESS.md format in the orchestrator skill.

**Primary recommendation:** Modify three markdown files with surgical additions -- the existing agent architecture is well-structured with clear extension points (workflow steps, inventory schema, validation protocol, progress format). The changes are additive, not restructuring.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGNT-01 | lsd-engineer runs fragment search before each LSD iteration and applies best fragment as DEFF/FEXP | Workflow step 5 in lsd-engineer.md gets a new "5a. Fragment search" sub-step; LSD file ordering established by LINT-03 smoke test |
| AGNT-02 | Sequential injection protocol: one fragment at a time, discard if zero solutions, log conflict and continue | Zero-solution recovery pattern already exists in lsd-engineer (Section 2); fragment discard follows same pattern |
| AGNT-03 | Fragment constraints tracked in constraint inventory JSON (DEFF/FEXP section) | Inventory schema (Section 5A in lsd-engineer.md) has clear extension points; new `deff_fexp` field documented below |
| AGNT-04 | Devils-advocate verifies fragment file existence before LSD solver run | DA already checks file-level properties (inventory presence, DEFF NOT patterns); fragment file check is a new structural integrity item |
</phase_requirements>

## Standard Stack

### Core (Files to Modify)

| File | Location | Purpose | Lines |
|------|----------|---------|-------|
| `lucy-lsd-engineer.md` | `~/.claude/agents/lucy-lsd-engineer.md` | LSD constraint building and solver specialist | 367 |
| `lucy-devils-advocate.md` | `~/.claude/agents/lucy-devils-advocate.md` | Pre-run validation and quality gate | 349 |
| `case.md` | `~/.claude/commands/lucy-ng/case.md` | Orchestrator skill (CASE-PROGRESS.md writer) | ~1088 |

### Supporting (CLI Tools Available -- No Changes Needed)

| CLI Command | JSON Output Fields | Purpose |
|-------------|-------------------|---------|
| `lucy fragment search --shifts "..." --format json` | `fragments[].smiles`, `fragments[].atom_count`, `fragments[].avg_deviation`, `deff_commands[]`, `fexp_command`, `result_count` | Search fragment database for spectral matches |
| `lucy fragment to-lsd "SMILES" --format json` | `filename`, `path`, `deff_command`, `fexp_command`, `content`, `atom_count` | Generate fragment .lsd file from SMILES |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| One fragment per iteration | Multi-fragment injection (FRAG-05) | Deferred to v5.x -- over-constraining risk with multiple fragments |
| Agent-driven fragment search | Orchestrator-driven search | Agent has direct context of shifts and iteration state; orchestrator would add communication overhead |

## Architecture Patterns

### Current LSD File Layout (Before Phase 53)

```
; === CONSTRAINT INVENTORY v1 ===
; { ... JSON ... }
; === END CONSTRAINT INVENTORY ===
MULT 1 C 2 0     ; atom definitions
MULT 2 C 2 1
...
HSQC 2 2          ; correlations
HSQC 3 3
...
HMBC 1 2          ; HMBC correlations
HMBC 3 4
...
BOND 1 14         ; constraints
LIST L1 1 2
...
DEFF NOT C1CC1    ; badlist (strained ring exclusion)
DEFF NOT C1CCC1
...
```

### Required LSD File Layout (After Phase 53)

```
; === CONSTRAINT INVENTORY v1 ===
; { ... JSON with deff_fexp field ... }
; === END CONSTRAINT INVENTORY ===
DEFF F1 "fragment_abc123def456.lsd"    ; <-- NEW: goodlist fragment reference
FEXP "F1"                               ; <-- NEW: goodlist expression
MULT 1 C 2 0     ; atom definitions
MULT 2 C 2 1
...
HSQC 2 2
...
HMBC 1 2
...
BOND 1 14
...
DEFF NOT C1CC1    ; badlist (unchanged position)
DEFF NOT C1CCC1
...
```

**Critical ordering rule (confirmed by LINT-03 smoke test):** DEFF/FEXP goodlist commands MUST appear BEFORE MULT definitions. The constraint inventory comment block (`;`-prefixed) stays at the top since LSD ignores comment lines. So the order is: inventory comments -> DEFF/FEXP goodlist -> MULT -> HSQC -> HMBC -> BOND/LIST/PROP -> DEFF NOT badlist.

Note: DEFF NOT (badlist) commands go AFTER correlations (current position). DEFF Fn (goodlist file reference) goes BEFORE MULT. These are different LSD command types -- `DEFF NOT <SMARTS>` is inline badlist filtering while `DEFF F1 "file.lsd"` is a fragment file reference.

### Pattern 1: Fragment Search Integration in lsd-engineer Workflow

**What:** lsd-engineer runs `lucy fragment search` at the start of every iteration, before writing the LSD file.

**When to use:** Every iteration (not just iteration 1), because the shift list is constant but the fragment search should be documented per iteration.

**Workflow insertion point:** Between current step 4 (read previous LSD) and step 5 (build/update LSD file).

**New step 4a in lsd-engineer workflow:**
```
4a. Fragment search:
    a. Run: lucy fragment search --shifts "<comma_separated_13c_shifts>" --format json --top 1
    b. Parse JSON output: extract fragments[0].smiles, fragments[0].atom_count, fragments[0].avg_deviation
    c. If result_count == 0: skip fragment injection, document "no fragments found" in message
    d. If result_count > 0: Run: lucy fragment to-lsd "<best_fragment_smiles>" --output-dir analysis/iteration_NN/ --format json
    e. Parse: extract filename for DEFF command
    f. Add DEFF F1 "<filename>" and FEXP "F1" to LSD file BEFORE MULT (after inventory block)
    g. Update constraint inventory deff_fexp section
```

**Zero-solution recovery for fragments:**
```
If LSD returns 0 solutions AND fragment was injected:
    1. Remove DEFF F1 and FEXP lines from LSD file
    2. Re-run LSD without fragment
    3. If solutions return: fragment is conflicting, discard it
    4. Log in [ITERATION-COMPLETE] message: "Fragment discarded: <SMILES> (zero solutions with fragment)"
    5. Update inventory: deff_fexp.status = "discarded", deff_fexp.conflict_reason = "zero solutions"
    6. Continue normal iteration flow without fragment
```

### Pattern 2: Constraint Inventory Schema Extension

**What:** Add `deff_fexp` section to the constraint inventory JSON.

**New field in inventory JSON schema:**

```json
{
  "version": 1,
  "iteration": 2,
  "formula": "C13H18O2",
  "...existing fields...",
  "deff_fexp": {
    "status": "applied",
    "fragment_smiles": "Cc1ccccc1",
    "fragment_atoms": 7,
    "fragment_avgdev": 0.45,
    "fragment_filename": "fragment_abc123def456.lsd",
    "deff_command": "DEFF F1 \"fragment_abc123def456.lsd\"",
    "fexp_command": "FEXP \"F1\"",
    "search_result_count": 3,
    "conflict_reason": null
  }
}
```

**Status values:**
- `"applied"` -- fragment DEFF/FEXP is in the LSD file
- `"discarded"` -- fragment caused zero solutions, removed
- `"none"` -- no matching fragment found in search
- `null` -- fragment search not yet run (should not persist after iteration)

### Pattern 3: Devils-Advocate Fragment File Validation

**What:** DA checks that the fragment `.lsd` file referenced by DEFF actually exists on disk.

**New check in DA structural integrity section (Section 3):**

```
### Fragment File Existence

If the LSD file contains a DEFF F<N> "<filename>" command (goodlist reference):
1. Extract filename from the DEFF command (between double quotes)
2. Check that the file exists in the same directory as compound.lsd
3. If file missing: flag CRITICAL -- "DEFF references fragment file '<filename>' but file does not exist in <iteration_dir>/"
4. If file exists: verify it contains SSTR commands (basic sanity)

If no DEFF F<N> found: check inventory deff_fexp.status:
- If "applied": flag CRITICAL -- "Inventory claims fragment applied but no DEFF command found"
- If "discarded" or "none": OK (no fragment expected)
```

**New check in inventory validation (Section 5B):**

```
Check 1 addition: If deff_fexp.status == "applied":
- Verify grep -c "^DEFF F" compound.lsd == 1
- Verify grep -c "^FEXP" compound.lsd == 1

Check 2 addition: If previous inventory had deff_fexp.status == "applied"
  AND current has "discarded":
- This is NORMAL (zero-solution fallback) -- flag INFO, not CRITICAL
- Verify conflict_reason is populated
```

### Pattern 4: CASE-PROGRESS.md Fragment Logging

**What:** Orchestrator writes fragment search results per iteration.

**New fields in LSD-Engineer section of iteration entries:**

```markdown
### LSD-Engineer
**LSD file:** analysis/iteration_01/compound.lsd
**Solution count:** 42
**Fragment search:** Found 3 matches; applied rank #1: Cc1ccccc1 (7 atoms, AVGDEV 0.45 ppm)
**Fragment file:** fragment_abc123def456.lsd
...existing fields...
```

**Or when no fragment found:**
```markdown
**Fragment search:** No matching fragments found
**Fragment file:** N/A
```

**Or when fragment discarded:**
```markdown
**Fragment search:** Found 3 matches; applied rank #1: Cc1ccccc1 (7 atoms, AVGDEV 0.45 ppm) -- DISCARDED (zero solutions)
**Fragment file:** fragment_abc123def456.lsd (removed from LSD)
```

### Anti-Patterns to Avoid

- **Injecting multiple fragments at once:** Over-constraining risk. FRAG-05 is deferred. Always `--top 1` and inject only the best fragment.
- **Running fragment search from orchestrator:** The lsd-engineer has the shift context and iteration context. Don't add orchestrator complexity.
- **Skipping fragment search on iteration 1:** Fragment search should run on EVERY iteration. The shift list doesn't change, but logging it per iteration is required by success criteria 5.
- **Fragment file in wrong directory:** The `.lsd` fragment file MUST be in the same `iteration_NN/` directory as `compound.lsd`, because LSD resolves relative paths from the input file's location.
- **Using single quotes in DEFF command:** LSD 3.4.9 requires double quotes. The `DEFFFormatter.deff_command()` already handles this correctly.
- **Placing DEFF goodlist after MULT:** LSD requires fragment definitions BEFORE atom definitions. DEFF NOT (badlist SMARTS) goes after correlations, but DEFF Fn (goodlist file ref) goes before MULT.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fragment file generation | Manual SSTR/LINK writing in agent instructions | `lucy fragment to-lsd "SMILES" --output-dir <dir> --format json` | CLI handles RDKit conversion, hash filenames, double-quote syntax |
| Fragment search ranking | Agent parsing of database | `lucy fragment search --shifts "..." --format json --top 1` | CLI handles fingerprint screening, fine matching, ranking |
| DEFF/FEXP command syntax | String formatting in agent instructions | CLI JSON output includes `deff_command` and `fexp_command` fields | Already formatted with correct double-quote syntax |
| Fragment filename generation | Agent inventing names | CLI uses SHA-256 hash of canonical SMILES -> deterministic `fragment_<12hex>.lsd` | Reproducible, collision-free |

**Key insight:** The Phases 51-52 CLI pipeline was designed specifically for agent consumption. The `--format json` output includes ready-to-use LSD commands. The agent's job is orchestration (when to search, where to insert, how to handle zero solutions), not formatting.

## Common Pitfalls

### Pitfall 1: Inventory-File Desync After Fragment Discard

**What goes wrong:** lsd-engineer removes DEFF/FEXP from LSD file after zero solutions but forgets to update inventory `deff_fexp` section to `"discarded"`.
**Why it happens:** Fragment discard is a mid-iteration recovery action, not part of the normal write flow.
**How to avoid:** The zero-solution recovery protocol must explicitly include "update inventory deff_fexp.status to discarded" as a mandatory step.
**Warning signs:** DA inventory validation Check 1 catches this -- inventory claims "applied" but file has no DEFF command.

### Pitfall 2: Fragment File Path Resolution

**What goes wrong:** Fragment file written to compound root or analysis/ root, but DEFF command has just the filename. LSD can't find the file because it looks relative to compound.lsd location.
**Why it happens:** `lucy fragment to-lsd` defaults to cwd if no `--output-dir` specified.
**How to avoid:** Always pass `--output-dir analysis/iteration_NN/` explicitly. The fragment file MUST be co-located with compound.lsd.
**Warning signs:** LSD error about missing fragment file. DA file existence check catches this pre-run.

### Pitfall 3: Fragment Search on Every Iteration (Redundancy)

**What goes wrong:** Agent skips fragment search on iterations 2+ because "shifts haven't changed."
**Why it happens:** Optimization instinct -- shifts are constant, so search results are constant.
**How to avoid:** Success criteria 5 requires fragment search results per iteration in CASE-PROGRESS.md. The agent instruction must say "run fragment search at the start of EVERY iteration" with emphasis.
**Warning signs:** Missing "Fragment search:" field in [ITERATION-COMPLETE] message.

### Pitfall 4: DEFF NOT vs DEFF F Confusion

**What goes wrong:** Agent treats `DEFF NOT <SMARTS>` (badlist inline) and `DEFF F1 "file.lsd"` (goodlist file ref) as the same thing, placing them in the wrong order.
**Why it happens:** Both start with "DEFF" but have completely different semantics and ordering requirements.
**How to avoid:** Agent instructions must clearly distinguish: DEFF F1 (goodlist, BEFORE MULT) vs DEFF NOT (badlist, AFTER correlations). Different positions in the file.
**Warning signs:** DA ordering check catches DEFF F after MULT.

### Pitfall 5: Previous Fragment Not Carried Forward

**What goes wrong:** Iteration N applied a fragment successfully, but iteration N+1 doesn't include it (like the v3.0 DEFF NOT drop bug).
**Why it happens:** Same root cause as v3.0 Bug 1 -- reconstructing from memory instead of reading previous file.
**How to avoid:** The "read previous LSD file, never reconstruct" rule applies to DEFF/FEXP too. Copy fragment commands forward alongside all other constraints. Inventory tracks it.
**Warning signs:** DA Check 2 on `deff_fexp` -- if previous had "applied" and current has no deff_fexp or has "none", flag CRITICAL.

## Code Examples

### CLI Fragment Search Output (JSON)

Source: `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/cli/fragment.py` lines 199-208

```json
{
  "query_shifts": [155.08, 151.58, 130.2],
  "prescreening_count": 1240,
  "fine_match_count": 15,
  "result_count": 3,
  "fragments": [
    {
      "ssc_id": 42,
      "smiles": "Cc1ccccc1",
      "atom_count": 7,
      "avg_deviation": 0.45,
      "matched_shifts": [128.0, 130.5, 131.2],
      "fragment_shifts": [128.5, 130.1, 131.0],
      "rank": 1
    }
  ],
  "deff_commands": ["DEFF F1 \"fragment_1.lsd\""],
  "fexp_command": "FEXP \"F1\""
}
```

### CLI to-lsd Output (JSON)

Source: `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/cli/fragment.py` lines 375-386

```json
{
  "smiles": "Cc1ccccc1",
  "canonical": "Cc1ccccc1",
  "filename": "fragment_abc123def456.lsd",
  "path": "/abs/path/to/analysis/iteration_01/fragment_abc123def456.lsd",
  "deff_command": "DEFF F1 \"fragment_abc123def456.lsd\"",
  "fexp_command": "FEXP \"F1\"",
  "atom_count": 7,
  "content": "; Fragment: Cc1ccccc1\nSSTR S1 C 3 3\nSSTR S2 C 2 0\n..."
}
```

### Constraint Inventory with deff_fexp Section

```json
{
  "version": 1, "iteration": 2, "formula": "C13H18O2",
  "timestamp": "2026-02-19T10:00:00Z",
  "mult_count": 15, "hsqc_count": 10,
  "hmbc_batches": [
    {"batch": 1, "count": 5, "correlations": ["1 13", "2 6", "3 4", "10 11", "4 8"]},
    {"batch": 2, "count": 5, "correlations": ["1 9", "3 13", "3 9", "5 9", "11 10"]}
  ],
  "hmbc_total": 10, "grouped_hmbc": [],
  "bond_constraints": ["1 14"], "syme_pairs": [],
  "list_prop_constraints": [], "elim_value": null,
  "deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1", "C1SC1", "C1SCC1", "C1OC1", "C1OCC1"],
  "deff_fexp": {
    "status": "applied",
    "fragment_smiles": "Cc1ccccc1",
    "fragment_atoms": 7,
    "fragment_avgdev": 0.45,
    "fragment_filename": "fragment_abc123def456.lsd",
    "deff_command": "DEFF F1 \"fragment_abc123def456.lsd\"",
    "fexp_command": "FEXP \"F1\"",
    "search_result_count": 3,
    "conflict_reason": null
  },
  "detection_results": { "...existing..." },
  "applied_from_detection": ["BOND 1 14 from neighbours 180.56 O mandatory"],
  "pending_from_detection": []
}
```

### Example LSD File With Fragment (Complete)

```
; === CONSTRAINT INVENTORY v1 ===
; {
;   "version": 1, "iteration": 1, "formula": "C13H18O2",
;   "timestamp": "2026-02-19T10:00:00Z",
;   "mult_count": 15, "hsqc_count": 10,
;   "hmbc_batches": [{"batch": 1, "count": 5, "correlations": ["1 13", "2 6", "3 4", "10 11", "4 8"]}],
;   "hmbc_total": 5, "grouped_hmbc": [],
;   "bond_constraints": ["1 14"], "syme_pairs": [],
;   "list_prop_constraints": [], "elim_value": null,
;   "deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1", "C1SC1", "C1SCC1", "C1OC1", "C1OCC1"],
;   "deff_fexp": {
;     "status": "applied",
;     "fragment_smiles": "Cc1ccccc1",
;     "fragment_atoms": 7, "fragment_avgdev": 0.45,
;     "fragment_filename": "fragment_abc123def456.lsd",
;     "deff_command": "DEFF F1 \"fragment_abc123def456.lsd\"",
;     "fexp_command": "FEXP \"F1\"",
;     "search_result_count": 3, "conflict_reason": null
;   },
;   "detection_results": {},
;   "applied_from_detection": [],
;   "pending_from_detection": []
; }
; === END CONSTRAINT INVENTORY ===
DEFF F1 "fragment_abc123def456.lsd"
FEXP "F1"
MULT 1 C 2 0
MULT 2 C 2 1
; ...more MULTs...
HSQC 2 2
HSQC 3 3
; ...more HSQCs...
HMBC 1 13
HMBC 2 6
; ...more HMBCs...
BOND 1 14
; Exclude strained rings
DEFF NOT C1CC1
DEFF NOT C1CCC1
DEFF NOT C1NC1
DEFF NOT C1NCC1
DEFF NOT C1SC1
DEFF NOT C1SCC1
DEFF NOT C1OC1
DEFF NOT C1OCC1
```

### lsd-engineer Workflow Step (New Fragment Step)

```
4a. FRAGMENT SEARCH (run at start of EVERY iteration):
    a. Get 13C shift list from nmr-chemist's peak assignments (same shifts used for all iterations)
    b. Run: lucy fragment search --shifts "<shifts>" --format json --top 1
    c. Parse JSON: check result_count
    d. If result_count == 0:
       - Set deff_fexp = {"status": "none", ...null fields...}
       - Skip to step 5 (no fragment to inject)
    e. If result_count > 0:
       - Extract best fragment: fragments[0].smiles, atom_count, avg_deviation
       - Run: lucy fragment to-lsd "<smiles>" --output-dir analysis/iteration_NN/ --format json
       - Parse JSON: extract filename, deff_command, fexp_command
       - Set deff_fexp = {"status": "applied", ...populate all fields...}
       - DEFF/FEXP lines go in LSD file AFTER inventory block, BEFORE first MULT
```

### lsd-engineer [ITERATION-COMPLETE] Message (Updated Template)

```
[ITERATION-COMPLETE] Iteration N
LSD file: analysis/iteration_NN/compound.lsd
Solution count: <N>
Fragment search: <result_count> matches; applied rank #1: <SMILES> (<atoms> atoms, AVGDEV <dev> ppm)
  OR: No matching fragments found
  OR: Applied rank #1: <SMILES> -- DISCARDED (zero solutions with fragment)
Fragment file: <filename> OR N/A
Constraints added:
- <constraint with reasoning>
Constraints removed:
- <constraint with reasoning> (or "None")
Constraint inventory delta: MULT=N, HSQC=N, HMBC=+N (total N), DEFF NOT=N, SYME=N, BOND=N, DEFF_FEXP=applied/none/discarded
sp2 count: N (even/odd)
H budget: N (matches/mismatch)
HMBC correlations used: X/Y
Why: <natural language reasoning>
Constraint effectiveness: <% reduction | "baseline" | "over-constrained">
Confidence: <too many / converging / stuck>
```

### Devils-Advocate [VALIDATION-PASSED] Message (Updated Template)

```
[VALIDATION-PASSED] Iteration N
sp2 count: N (even)
H budget: N (matches <formula>)
DEFF NOT: N patterns (preserved from iteration N-1 / initialized)
DEFF FEXP: fragment_abc123def456.lsd exists in iteration_NN/ (verified)
  OR: No fragment applied (deff_fexp.status = "none")
  OR: Fragment discarded (deff_fexp.status = "discarded", conflict logged)
SYME: N constraints (preserved / N/A)
Grouped notation: N entries (preserved / N/A)
Correlation order: HSQC before HMBC (correct)
Fragment ordering: DEFF F1/FEXP before MULT (correct) OR N/A
Inventory accuracy: all counts match actual file
Concerns: <list or "None">
```

## Detailed File Modification Map

### File 1: `~/.claude/agents/lucy-lsd-engineer.md`

**Section 1 (Domain Knowledge) -- add after "### Badlist Filters (DEFF NOT)":**
- New subsection "### Fragment Goodlist (DEFF/FEXP)" documenting:
  - CLI commands: `lucy fragment search`, `lucy fragment to-lsd`
  - LSD file ordering: DEFF F1/FEXP BEFORE MULT (distinguish from DEFF NOT which goes after correlations)
  - Zero-solution fallback protocol
  - Fragment persistence rule: carry forward across iterations like DEFF NOT

**Section 5A (Inventory JSON Schema) -- extend table:**
- Add `deff_fexp` field to schema table: type = object, purpose = "Fragment goodlist tracking"

**Section 5B (LSD File Format) -- update example:**
- Add `deff_fexp` section to the inventory JSON example

**Section 5C (Initialization) -- update procedure:**
- Add: "Run fragment search. If match found, populate deff_fexp. Write DEFF F1/FEXP after inventory block, before MULT."

**Section 5D (Update Procedure) -- update:**
- Add: "Copy deff_fexp from previous inventory. Re-run fragment search. If previous was 'applied' and still matches, carry forward. If new search finds different best, update."

**Workflow (step 5) -- insert new step 4a:**
- Insert fragment search step between "read previous LSD" and "build/update LSD file"

**Manual Checklist -- add item 10:**
- "10. If fragment applied: DEFF F1/FEXP present before MULT, fragment .lsd file exists in iteration dir"

**[ITERATION-COMPLETE] Message Template -- add fields:**
- Add: Fragment search, Fragment file, DEFF_FEXP in inventory delta

### File 2: `~/.claude/agents/lucy-devils-advocate.md`

**Section 3 (Structural Integrity Checks) -- add new subsection:**
- "### Fragment File Existence" check (CRITICAL if missing)
- "### Fragment Ordering" check (DEFF F/FEXP before MULT)

**Section 5B (Three-Check Reconciliation) -- extend:**
- Check 1: Add deff_fexp.status vs actual DEFF F command count
- Check 2: Add deff_fexp regression check (applied -> missing = CRITICAL unless discarded)

**[VALIDATION-PASSED] template -- add field:**
- Add: DEFF FEXP line

**[VALIDATION-BLOCKED] template -- add field:**
- Add: Fragment file issues

### File 3: `~/.claude/commands/lucy-ng/case.md`

**write_progress step -- LSD-Engineer section format:**
- Add: `**Fragment search:** <from message>` field
- Add: `**Fragment file:** <from message>` field

**write_progress step -- Devils-Advocate section format:**
- Add: `**Fragment file:** <from message>` field

## Open Questions

1. **Fragment persistence across iterations with different best matches**
   - What we know: The same shift list always produces the same search results (deterministic). So re-running search on each iteration gives the same best fragment.
   - What's unclear: If the fragment database is updated between CASE runs, results could differ. Not relevant for a single CASE session.
   - Recommendation: Copy forward from previous iteration. Re-running search is for logging purposes and to detect if previous fragment was discarded.

2. **Multiple fragments in sequence (FRAG-05 future)**
   - What we know: Current scope is one fragment at a time (`--top 1`). FRAG-05 is explicitly deferred.
   - What's unclear: If one fragment yields >5 solutions, should a second be tried?
   - Recommendation: Out of scope for Phase 53. Document as future enhancement point in the agent instructions.

## Sources

### Primary (HIGH confidence)
- `~/.claude/agents/lucy-lsd-engineer.md` -- Full lsd-engineer agent definition (367 lines, read in full)
- `~/.claude/agents/lucy-devils-advocate.md` -- Full DA agent definition (349 lines, read in full)
- `~/.claude/commands/lucy-ng/case.md` -- Full orchestrator skill (1088 lines, read in full)
- `src/lucy_ng/fragments/lsd_formatter.py` -- DEFFFormatter API (179 lines, read in full)
- `src/lucy_ng/fragments/searcher.py` -- FragmentSearcher API (290 lines, read in full)
- `src/lucy_ng/cli/fragment.py` -- CLI commands (392 lines, read in full)
- `tests/test_lsd_formatter.py` -- LSD smoke test confirming DEFF/FEXP ordering before MULT
- `src/lucy_ng/fragments/models.py` -- SSCMatch model (69 lines, read in full)

### Secondary (HIGH confidence)
- `.planning/milestones/v5.0-ROADMAP.md` -- Phase 53 requirements and success criteria
- `.planning/REQUIREMENTS.md` -- AGNT-01 through AGNT-04 requirement text
- `~/.claude/agents/lucy-case-agent.md` -- Main CASE agent (1280 lines, read for workflow context)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all files read in full, no external dependencies
- Architecture: HIGH -- extension points are clear, LSD ordering confirmed by smoke test
- Pitfalls: HIGH -- based on v3.0/v4.0 UAT bug history (documented in project memory)

**Research date:** 2026-02-19
**Valid until:** indefinite (agent instruction files are project-internal, no external dependency versioning)
