# Phase 70: Agent Skill Updates — Research

**Researched:** 2026-05-19
**Domain:** Markdown skill-file editing — lsd-engineer.md, devils-advocate.md, case.md
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-17:** Routing (`lucy pylsd run` vs `lucy lsd run`) lives in **lsd-engineer.md**. Before every LSD invocation, lsd-engineer reads its own v2 inventory via `lucy lsd validate-inventory --format json`, checks `inventory.pylsd_mode`, and picks the CLI command. case.md is and remains CLI-agnostic.
- **D-17a (Encapsulation):** Domain logic (which solver mode for which inventory) stays with the agent that writes the inventory. case.md does NOT know the schema.
- **D-17b (Spawn protocol):** case.md does NOT change its spawn protocol. lsd-engineer gets the same context block; it decides internally via inventory read which CLI command to invoke via Bash.
- **D-18:** devils-advocate G4 = hard BLOCK when K > 3. Consistent with Phase 67 PyLSDOrchestrator.run() ValueError(K>3).
- **D-18a (No override):** Consistent with D-08 (Phase 68). No new override path.
- **D-18b (Severity):** CRITICAL, same level as G1/G2/G3. Block message must name: K=N, 2^N permutation count, K≤3 cap, and instruct nmr-chemist to prioritize top-3 4J suspects.
- **D-19:** ABSENT inventory → silent `lucy lsd run`. MALFORMED → hard error (Phase 69 WR-01). v1 legacy → WARNING + fallback (Phase 68 D-02).
- **D-19a/b:** Phase 68 and 69 behaviors remain unchanged.
- **D-20:** When `lucy pylsd run` was invoked, lsd-engineer writes two structured blocks in [ITERATION-COMPLETE]:
  1. Per-permutation table: `permutation_id`, `defer_set`, `solution_count`, `top_rank_quality`.
  2. Aggregated block: `merged_count`, `top_3_smiles`.
- **D-20a (Source):** Data from `run_report.json` + `lucy pylsd run --format json` stdout.
- **D-20b (Readability):** Markdown table in code-fence; parseable by case.md loop detection for "any permutation has aromatic ring in top rank".

### Claude's Discretion

- Exact wording of lsd-engineer §"Run LSD" routing block
- Exact wording of G4 block message in devils-advocate
- Whether lsd-engineer calls `lucy pylsd run` with or without `--working-dir` (default `<lsd_dir>/pylsd_run` per Phase 69 is sufficient)
- Exact ITERATION-COMPLETE markdown table format (column order, SMILES truncation)
- Whether case.md loop detection needs new patterns for pylsd_mode iterations

### Deferred Ideas (OUT OF SCOPE)

- case.md loop detection pattern for "K permutations all empty" — defer until Phase 71 UAT shows it's needed
- nmr-chemist 4J prioritization logic when K > 3
- Parallel iteration strategy for pylsd_mode
- Inventory version migration script for v1 → v2

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AGT-01 | lsd-engineer writes extended HMBC bond range (`HMBC X Y 2 4`) for suspect 4J correlations | Already in lsd-engineer.md §5C step 5d (line 413) and §5B example (lines 392-393). Phase 70 adds explicit command reference table so the agent's §1 domain knowledge is complete; §5C procedure already correct. |
| AGT-02 | lsd-engineer uses `lucy pylsd run` when `pylsd_mode: true` | Currently missing — lsd-engineer.md lines 268 and 481 both unconditionally invoke `lucy lsd run`. Phase 70 replaces these with a conditional branch reading the inventory. |
| AGT-03 | case.md orchestrator routes to multi-run path when nmr-chemist flags aromatic 4J risk | Per D-17, routing lives in lsd-engineer, not case.md. SC3 in ROADMAP is slightly mis-worded. case.md spawn protocol unchanged. AGT-03 is satisfied by lsd-engineer's internal routing. No case.md edit needed for this requirement. |
| AGT-04 | devils-advocate validates 4J deferral decisions (which correlations deferred, permutation count reasonable) | G1/G2/G3 already exist (Phase 68). Phase 70 adds G4: permutation count K≤3 hard block. Also needs VALIDATION-PASSED template to report G4 status. |

</phase_requirements>

---

## Summary

Phase 70 is purely markdown editing across three skill files. No Python changes. The Python infrastructure (PyLSDOrchestrator, SolutionMerger, `lucy pylsd run` CLI, constraint inventory v2 schema) is fully implemented and verified in Phases 66–69.

The two highest-value changes are: (1) adding the conditional routing block in lsd-engineer.md to replace two unconditional `lucy lsd run` invocations at lines 268 and 481 — this is the only thing blocking AGT-02; and (2) inserting G4 as a fourth sub-check in devils-advocate.md §5B Check 4 after the existing G3 block at line 331.

A confirmed Phase 68 advisory CR-02 has already been fixed: `lucy lsd validate-inventory --format json` now returns the full `inventory` object in its success response, so the `INVENTORY=$(echo "$RESULT" | python3 ...)` extraction in devils-advocate §5A actually works and exposes `pylsd_mode` / `deferred_4j` for G4's jq/python extraction. This was the main risk that could have broken the routing block — it is resolved.

**Primary recommendation:** Plan as three separate tasks (one per file), each with a concrete `grep`-based verification step. The lsd-engineer task is the largest (routing block + ITERATION-COMPLETE extension + pyLSD command vocabulary addition); the devils-advocate task is bounded (insert G4 + update VALIDATION-PASSED template); the case.md task is minimal or no-op depending on Discretion decision for loop-patterns.md.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Solver CLI routing (`lucy pylsd run` vs `lucy lsd run`) | lsd-engineer (agent) | — | Agent that writes the inventory owns the decision. D-17 locks this. |
| Permutation count validation (K≤3) | devils-advocate (agent) | — | Pre-run gate agent; mirrors Python-layer ValueError in PyLSDOrchestrator. |
| ITERATION-COMPLETE reporting | lsd-engineer (agent) | case.md (reads for loop detection) | lsd-engineer writes; orchestrator parses for loop detection patterns. |
| Loop pattern detection | case.md (orchestrator) | loop-patterns.md (reference) | Orchestrator reads patterns file; pylsd-mode patterns are OUT OF SCOPE per Deferred. |
| pyLSD command vocabulary | lsd-engineer §1 (skill knowledge) | — | Domain knowledge section must be authoritative; currently missing FORM/SHIX/SHIH. |

---

## Standard Stack

No new packages. Phase 70 is markdown-only. The relevant runtime dependencies were installed in earlier phases.

---

## Package Legitimacy Audit

Not applicable — no new packages installed in this phase.

---

## Architecture Patterns

### Files Being Edited

Three skill files. Their current state is:

```
~/.claude/agents/lucy-lsd-engineer.md       487 lines
~/.claude/agents/lucy-devils-advocate.md    439 lines
~/.claude/commands/lucy-ng/case.md          595 lines
```

### Existing Content That Phase 70 Builds On (Do Not Replicate)

lsd-engineer.md is already v2-aware with the following content in place:
- §1 ELIM command reference (lines 78–84) [VERIFIED: file read]
- §2 "4J Deferral Rule" (lines 195–233) [VERIFIED: file read]
- §4 ITERATION-COMPLETE template (lines 277–308) — `4J status:` field already present [VERIFIED: file read]
- §5A schema table with `pylsd_mode`, `elim_annotated`, `deferred_4j` (lines 315–344) [VERIFIED: file read]
- §5B LSD file format showing `HMBC 4 8 2 4 ; ELIM` example (lines 350–396) [VERIFIED: file read]
- §5C initialization procedure (lines 399–416) including step 5b/5c/5d for pylsd_mode and deferred_4j [VERIFIED: file read]

devils-advocate.md already has G1, G2, G3 under §5B Check 4 (lines 296–333) [VERIFIED: file read]:
- G1: FORM/MULT consistency (line 300–308)
- G2: No bare ELIM in pylsd_mode (lines 310–318)
- G3: Annotation-vs-Mode consistency (lines 320–331)
- All-gates summary line (line 333)

case.md loop detection (lines 345–368) reads from `~/.claude/commands/lucy-ng/references/loop-patterns.md` via `Read file:` step. case.md does NOT call `lucy lsd run` or `lucy pylsd run` directly anywhere [VERIFIED: grep returned no matches].

---

## What Phase 70 Actually Needs to Add

### Change 1: lsd-engineer.md — §"Run LSD" Routing Block

**Current state — TWO locations with unconditional invocation:**

Line 268 (inside §3 File Organization):
```
- Run LSD from within iteration dir: `cd analysis/iteration_NN && lucy lsd run compound.lsd`
```
[VERIFIED: file read, line 268]

Line 481 (workflow step 11):
```
11. Run LSD: `cd analysis/iteration_NN && lucy lsd run compound.lsd`
```
[VERIFIED: file read, line 481]

**What must replace them (D-17):** Both sites become a conditional block. The routing reads the inventory that lsd-engineer just wrote (it is always present because lsd-engineer writes it atomically per §5E Atomic Write Rule). Pseudocode for the routing block:

```bash
# Read inventory to determine solver mode
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
PYLSD_MODE=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")

if [ "$PYLSD_MODE" = "True" ]; then
  lucy pylsd run analysis/iteration_NN/compound.lsd --shifts "<13c_shifts>" --format json | tee pylsd_output.json
else
  cd analysis/iteration_NN && lucy lsd run compound.lsd
fi
```

**Exact JSON path confirmed:** `validate-inventory --format json` returns `{"valid": true, ..., "inventory": {"pylsd_mode": true/false, "deferred_4j": [...], ...}}` — the `inventory` key contains the parsed schema object. [VERIFIED: live CLI test — python3 invocation returned full inventory object with `pylsd_mode` key]

**Note on line 268:** Line 268 is inside a comment/rules block (file organization rules, not a workflow step). The wording there is a documentation example, not executable code. The planner must decide: either update the documentation string to say "run via routing block (see workflow step 11)" or leave it as a simplified example and update only step 11. The workflow step 11 is what the agent actually executes.

**D-19 routing behavior (ABSENT inventory):** lsd-engineer always writes the inventory before running LSD (§5E Atomic Write Rule). The ABSENT case only arises for files written before Phase 68 — not for lsd-engineer's own output. For the routing block, if validate-inventory returns `valid: false` with "No v2 inventory block found", fall through to `lucy lsd run` silently (matches D-19).

### Change 2: lsd-engineer.md — pyLSD Command Vocabulary (§1 Addition)

lsd-engineer §1 "LSD Command Reference" currently documents: MULT, HSQC, HMBC, BOND/LIST/ELEM/PROP/SYME, ELIM, outlsd, solution count table, DEFF NOT, Fragment Goodlist, Manual Checklist. [VERIFIED: file read]

**Missing from §1:** SHIX, SHIH, and the `; FORM` comment convention. These are used by LSDInputGenerator when lsd-engineer sets `pylsd_mode=true` in the inventory, but lsd-engineer has no reference for them in §1. The agent needs to know their syntax so it does not accidentally write them wrong if asked to inspect generated permutation files.

Current §1 ELIM section (lines 78–84) documents bare `ELIM N M`. It does NOT explicitly say "in pylsd_mode, ELIM must not appear as a bare command — use `HMBC X Y 2 4 ; ELIM` instead." The §5 inventory sections do say this, but §1 is the quick-reference domain knowledge. A one-line note linking ELIM to the pylsd-mode rule belongs in §1.

**FORM note:** LSDInputGenerator emits `; FORM C13H18O2` (comment form). lsd-engineer does NOT write FORM lines itself — PyLSDOrchestrator generates permutation files. lsd-engineer inspects the output. §1 should document what `; FORM` means and that the bare form is rejected by LSD-3.4.9 (so lsd-engineer doesn't add a bare FORM if trying to help).

**Exact syntax for §1 pyLSD vocabulary subsection:**

```
; FORM C13H18O2    ; molecular formula — LSD comment (not a real command; bare FORM rejected by LSD-3.4.9 error 102)
SHIX 3 125.5       ; assign 13C chemical shift 125.5 ppm to atom 3
SHIH 3 7.2         ; assign 1H chemical shift 7.2 ppm to atom 3
HMBC X Y 2 4       ; HMBC correlation with extended bond range 2-4 (correct 4J mechanism)
HMBC X Y 2 4 ; ELIM  ; same + ; ELIM trailing comment marks X-Y as PyLSDOrchestrator suspect
```

[ASSUMED for SHIX/SHIH syntax — derived from LSDInputGenerator source in Phase 66, confirmed by REQUIREMENTS.md INPUT-03. Not independently verified against LSD binary documentation.]

### Change 3: lsd-engineer.md — ITERATION-COMPLETE Extension for pylsd_mode (D-20)

**Current template** ends with (line 299):
```
4J status: <"N deferred" / "added as final batch" / "skipped — solutions converged" / "N/A — no potential 4J">
```
[VERIFIED: file read, lines 277-299]

**What D-20 adds BELOW the existing template** (pure addition, no replacement): When `lucy pylsd run` was invoked (i.e., `pylsd_mode=true`), lsd-engineer appends two additional blocks:

**Block 1 — Per-permutation table (in Markdown code-fence):**

| permutation_id | defer_set | solution_count | top_rank_quality |
|---------------|-----------|----------------|-----------------|
| perm_00 | none | 7 | excellent |
| perm_01 | atom4-atom8 | 12 | good |
| perm_02 | atom6-atom9 | 0 | — |
| perm_03 | atom4-atom8 + atom6-atom9 | 3 | excellent |

**Block 2 — Aggregated:**
```
Merged (unique InChI): 15
Top-3 SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O | <smiles2> | <smiles3>
```

**Data source — exact JSON paths from `lucy pylsd run --format json`:**

The CLI output (confirmed from `src/lucy_ng/cli/pylsd.py` lines 267–274) returns:
```json
{
  "permutations": 4,
  "merged_count": 15,
  "ranked_solutions": [
    {"smiles": "...", "matched_count": 10, "mae": 2.3, "quality": "excellent", ...},
    ...
  ],
  "run_report_path": "analysis/iteration_01/pylsd_run/run_report.json"
}
```
[VERIFIED: source code read, pylsd.py lines 268-274]

The per-permutation data does NOT appear in `--format json` stdout — it lives in `run_report.json`. The `run_report.json` structure (from orchestrator.py lines 385-400) is:
```json
{
  "total_permutations": 4,
  "total_raw_solutions": 20,
  "unique_solutions": 15,
  "solutions": [
    {
      "inchi_key": "XXXXX",
      "smiles": "CC(C)Cc1...",
      "provenance": [
        {
          "perm_index": 0,
          "include_flags": [true, false],
          "original_solution_index": 0,
          "active_correlations": [{"atom1": 4, "atom2": 8}]
        }
      ]
    }
  ]
}
```
[VERIFIED: source code read, orchestrator.py lines 385-400]

**What lsd-engineer actually needs to extract for the per-permutation table:**

The per-permutation `solution_count` is NOT in run_report.json directly. run_report.json records per-unique-solution provenance, not per-permutation solution counts. The per-permutation solution count must be derived by counting solutions in each `perm_NN/solutions.smi` file.

The `top_rank_quality` per permutation is also not in run_report.json. It must be inferred from the ranked output for the subset of solutions from that permutation (cross-referencing `perm_index` in provenance). For practical purposes, lsd-engineer can read `perm_NN/solutions.smi` to get count and derive `defer_set` from the `include_flags` field per permutation index.

**Practical jq one-liners for data extraction:**

```bash
# merged_count and top-3 SMILES from --format json stdout
PYLSD_JSON=$(cat pylsd_output.json)
MERGED_COUNT=$(echo "$PYLSD_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['merged_count'])")
TOP3=$(echo "$PYLSD_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(' | '.join(s['smiles'][:40] for s in d['ranked_solutions'][:3]))")

# per-permutation solution_count from individual solutions.smi files
for i in 00 01 02 03; do
  count=$(wc -l < "pylsd_run/perm_${i}/solutions.smi" 2>/dev/null || echo 0)
  echo "perm_${i}: ${count} solutions"
done

# defer_set (which suspects included in each permutation) from run_report.json
python3 -c "
import json
with open('pylsd_run/run_report.json') as f:
    r = json.load(f)
# derive per-perm data from provenance
perm_map = {}
for sol in r['solutions']:
    for prov in sol['provenance']:
        p = prov['perm_index']
        ac = prov['active_correlations']
        perm_map.setdefault(p, set()).add(
            '+'.join(f'atom{c[\"atom1\"]}-atom{c[\"atom2\"]}' for c in ac) or 'none'
        )
for p,labels in sorted(perm_map.items()):
    print(f'perm_{p:02d}: {list(labels)[0]}')
"
```
[ASSUMED — jq-less python approach; planner should decide whether to document as python one-liner or suggest jq. The data structure is VERIFIED from source code.]

**Simpler approach for the planner:** Given that the per-permutation data extraction is non-trivial (requires reading both JSON stdout and individual .smi files), the D-20 ITERATION-COMPLETE blocks can be documented with a NOTE: "Extract per-permutation counts from `pylsd_run/perm_NN/solutions.smi` (line count per file); extract defer_set from `run_report.json` provenance; extract top-3 SMILES from `lucy pylsd run --format json` output `ranked_solutions[0..2].smiles`." This is simpler to document than inlining a complex python one-liner.

### Change 4: devils-advocate.md — G4 Permutation Cap Check

**Insertion point:** After the G3 block summary line at line 333:
```
**All three gates G1/G2/G3 are CRITICAL severity and blocking.**
```
[VERIFIED: file read, line 333]

G4 inserts as a new sub-section after the "All three gates" closing summary sentence. The structure should follow G1/G2/G3 pattern: bold heading + when clause + bash/python command + if/else logic.

**Proposed G4 section:**

```
**G4: Permutation Count Cap**

When `pylsd_mode=true`:
```bash
K=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('inventory',{}).get('deferred_4j', [])))")
```
- If K > 3: **BLOCK** with message: "K={K} exceeds permutation cap (K≤3, max 2^3=8 permutations). PyLSDOrchestrator.run() will raise ValueError. Action: nmr-chemist must prioritize Top-3 most likely 4J suspects (highest probability aromatic-to-aliphatic at >4Å distance); demote remaining entries from deferred_4j or remove '; ELIM' annotation on lower-priority HMBC lines."
- If K <= 3: G4 passes.
```

Note: `$RESULT` is already set from the `lucy lsd validate-inventory --format json` call in §5A (line 227). G4 reuses the same `$RESULT` variable — no additional CLI call needed. [VERIFIED: §5A extraction pipeline in devils-advocate lines 225-253 sets `$RESULT`]

**The "All gates" summary line must be updated** from "All three gates G1/G2/G3" to "All four gates G1/G2/G3/G4 are CRITICAL severity and blocking."

**VALIDATION-PASSED template update:** The template at lines 363-380 does not currently include a `pylsd_mode` / permutation check field. For completeness, a one-line field should be added:
```
pyLSD mode: N/A (pylsd_mode=false) / PASS (K=N, N<=3) / BLOCKED (K=N>3)
```

### Change 5: case.md — Assessment and Recommendation

case.md currently:
- Does NOT call `lucy lsd run` or `lucy pylsd run` anywhere [VERIFIED: grep returned no matches]
- Spawns lsd-engineer with the same prompt regardless of pylsd_mode (D-17b)
- Reads loop-patterns.md via `Read file:` at line 347 [VERIFIED: file read, line 347]
- Loop detection in detect_loops step (lines 345-368) parses CASE-PROGRESS.md solution_count per iteration — it does not inspect solver-mode fields

**What case.md needs for Phase 70 (minimal):** Nothing mandatory for AGT-03 (routing is lsd-engineer's job). The Discretion question is whether pylsd_mode-specific loop patterns go into loop-patterns.md.

**Recommendation (DEFER per Deferred decisions):** The "K permutations all empty" pattern is deferred to Phase 71. No case.md or loop-patterns.md edit in Phase 70. The planner should include this as an explicit no-op task: "Verify case.md needs no changes; confirm loop-patterns.md unchanged."

The only potential case.md addition would be: if loop detection parses ITERATION-COMPLETE messages and those now include pylsd_mode output blocks, the parser needs to not break. Since loop detection only reads CASE-PROGRESS.md for `solution_count` per iteration (lines 238-239 of case.md), and CASE-PROGRESS.md is written by the orchestrator from the structured ITERATION-COMPLETE message, the aggregated solution count is still present. The additional pylsd_mode blocks are extra text that the orchestrator can include without breaking the existing `solution_count` parsing. No change required.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| K count extraction | Custom parser | `lucy lsd validate-inventory --format json <file>` — returns `inventory.deferred_4j` array; len() it |
| Permutation solution counts | Custom orchestrator replay | Read `pylsd_run/perm_NN/solutions.smi` line count per directory |
| ITERATION-COMPLETE JSON parsing | Regex on text output | `lucy pylsd run --format json` → parse `merged_count`, `ranked_solutions` |
| pylsd_mode detection | Grep on LSD file | `lucy lsd validate-inventory --format json` → `inventory.pylsd_mode` |

---

## Common Pitfalls

### Pitfall 1: Stale `lucy lsd validate-inventory` Success Response

**What goes wrong:** The Phase 68 advisory CR-02 warned that `validate-inventory --format json` did not include the `inventory` object in its success response. If the planner reads the Phase 68 VERIFICATION.md and concludes CR-02 is still open, they will design a workaround.

**Why it matters:** It is NOT open. CR-02 was fixed before Phase 69 shipped. Live CLI test (run during this research session) confirms the response is:
```json
{"valid": true, "file": "...", "version": 2, "inventory": {"pylsd_mode": true, ...}}
```
[VERIFIED: live CLI invocation — see Execute step in research session]

**How to avoid:** The routing block in lsd-engineer and the K-counting step in devils-advocate both use `.inventory.pylsd_mode` and `.inventory.deferred_4j` paths. These work as-is.

### Pitfall 2: Updating Line 268 Without Updating Line 481

**What goes wrong:** lsd-engineer.md has `lucy lsd run` in two locations. Updating only the workflow step (line 481) leaves the documentation string at line 268 inconsistent. It creates a contradiction visible in any future reading of the file.

**How to avoid:** Plan must list BOTH locations explicitly. Line 268 is in §3 File Organization rules block; line 481 is in the workflow step. Both need to be addressed (either updated or annotated).

### Pitfall 3: G4 Placed BEFORE the "All three gates" Summary Line

**What goes wrong:** If G4 is inserted between G3 and the summary line, and the summary line is not updated, the file reads "All three gates G1/G2/G3 are CRITICAL" immediately after a G4 block, confusing future readers.

**How to avoid:** G4 insertion and "All three → four gates" summary update are a single atomic edit.

### Pitfall 4: ITERATION-COMPLETE Extension as Replacement

**What goes wrong:** The `4J status:` field at line 299 already exists and is correct for the non-pylsd_mode case. If a planner reads D-20 as "replace the 4J status line", they lose the existing working field.

**How to avoid:** D-20 says "two additional blocks" added below the existing template. The `4J status:` field persists. The pylsd_mode blocks are conditional extras ("When `lucy pylsd run` was invoked, append...").

### Pitfall 5: Using Bare FORM in §1 Documentation

**What goes wrong:** If the new §1 pyLSD vocabulary subsection writes `FORM C13H18O2` without the `;` prefix, lsd-engineer might copy it verbatim into a file it's editing.

**How to avoid:** The §1 entry MUST be `; FORM C13H18O2` with explicit note "LSD comment — not a real command". Reference `.planning/findings/form-tolerance.md`.

### Pitfall 6: lsd-engineer Calling validate-inventory a Second Time at Run Step

**What goes wrong:** lsd-engineer already sets `pylsd_mode` in the inventory during §5C/5D. At workflow step 11 (run LSD), reading the inventory again is a re-read of the same file lsd-engineer just wrote. This is correct and efficient. But if lsd-engineer reconstructs pylsd_mode from memory instead of reading the inventory, it re-introduces the "never reconstruct from memory" anti-pattern.

**How to avoid:** Routing block must explicitly call `lucy lsd validate-inventory --format json` on the iteration file lsd-engineer just wrote, not infer pylsd_mode from memory.

### Pitfall 7: G4 Block Message Omits nmr-chemist Action

**What goes wrong:** A G4 block that only says "K>3, too many suspects" without naming who should resolve it leaves the team confused.

**How to avoid:** G4 block message must name nmr-chemist as the agent responsible for deprioritizing suspects (D-18b). Template: "nmr-chemist must prioritize Top-3 most likely 4J suspects; demote remaining from deferred_4j or remove '; ELIM' annotation on lower-priority HMBC lines."

### Pitfall 8: Stale `deferred_4j` Schema Wording at Line 200

**What goes wrong:** lsd-engineer.md line 200 (§2 Incremental HMBC Strategy) still says:
```
- Add them to `deferred_4j` in the constraint inventory as structured objects per v2 schema (see Section 5C step 5d for the required fields...)
```
[VERIFIED: file read, line 200]

The Phase 68 VERIFICATION.md flagged this as a stale "string descriptions" reference that was not fully cleaned up (noted as "warning — not a debt marker" in that report). However, re-reading line 200 in the current file, it already says "structured objects per v2 schema" — the stale text was the previous wording "string descriptions" and it IS already updated in the current file. No edit needed here.

---

## Code Examples

### validate-inventory Response Shape (confirmed live)

```json
{
  "valid": true,
  "file": "/path/to/compound.lsd",
  "version": 2,
  "inventory": {
    "version": 2,
    "pylsd_mode": true,
    "elim_annotated": true,
    "deferred_4j": [
      {"atom1": 4, "atom2": 8, "shift1": 129.38, "shift2": 45.03, "correlation_type": "HMBC", "annotation": "; ELIM"},
      {"atom1": 6, "atom2": 9, "shift1": 127.26, "shift2": 44.90, "correlation_type": "HMBC", "annotation": "; ELIM"}
    ],
    "hmbc_total": 10,
    ...
  }
}
```
[VERIFIED: live CLI test during research]

### lucy pylsd run --format json Output Shape

Source: `src/lucy_ng/cli/pylsd.py` lines 268-274:
```json
{
  "permutations": 4,
  "merged_count": 15,
  "ranked_solutions": [
    {
      "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
      "matched_count": 10,
      "mae": 1.8,
      "quality": "excellent"
    },
    ...
  ],
  "run_report_path": "analysis/iteration_01/pylsd_run/run_report.json"
}
```
[VERIFIED: source code read]

Note: `ranked_solutions` items come from `_perform_ranking()`'s json output. The `quality` field is from `lucy lsd rank --format json` — the same ranking logic used for single-run mode.

### run_report.json Schema

Source: `src/lucy_ng/lsd/orchestrator.py` lines 385-400:
```json
{
  "total_permutations": 4,
  "total_raw_solutions": 20,
  "unique_solutions": 15,
  "solutions": [
    {
      "inchi_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
      "smiles": "CC(C)Cc1...",
      "provenance": [
        {
          "perm_index": 0,
          "include_flags": [true, false],
          "original_solution_index": 3,
          "active_correlations": [{"atom1": 4, "atom2": 8}]
        }
      ]
    }
  ]
}
```
[VERIFIED: source code read]

Per-permutation solution counts are NOT in run_report.json. Derive from `perm_NN/solutions.smi` line count.

### lsd-engineer Routing Block (for §"Run LSD")

Proposed replacement for lines 268 and 481:

```bash
# Determine solver mode from constraint inventory
RESULT=$(lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd)
PYLSD_MODE=$(echo "$RESULT" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('inventory',{}).get('pylsd_mode', False))")

if [ "$PYLSD_MODE" = "True" ]; then
  # Multi-run mode: use PyLSDOrchestrator via lucy pylsd run
  lucy pylsd run analysis/iteration_NN/compound.lsd \
    --shifts "<comma_separated_13C_shifts>" \
    --format json | tee analysis/iteration_NN/pylsd_output.json
else
  # Single-run mode: classic lucy lsd run
  cd analysis/iteration_NN && lucy lsd run compound.lsd
fi
```

Note: `--working-dir` is omitted; default `pylsd_run/` subdirectory under the LSD file's directory is sufficient per Phase 69 D-14 Discretion.
[ASSUMED — exact wording/formatting is Claude's Discretion; structure is VERIFIED against D-17 and CLI help]

### G4 Sub-Check Template (for §5B Check 4 in devils-advocate)

```
**G4: Permutation Count Cap**

When `pylsd_mode=true`, count deferred_4j entries and check against K≤3 cap:

K=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('inventory',{}).get('deferred_4j', [])))")

- If K > 3: **BLOCK** with message: "K={K} exceeds permutation cap (K≤3, max 2^3=8 permutations).
  PyLSDOrchestrator.run() will raise ValueError before creating any files (K-cap is the first check in run()).
  Action: nmr-chemist must prioritize the Top-3 most likely 4J suspects; demote the remaining
  entries from deferred_4j (remove their '; ELIM' annotation from HMBC lines) or reclassify
  them as non-suspect."
- If K <= 3: G4 passes.

**Note:** $RESULT is set in §5A extraction (lucy lsd validate-inventory --format json). No additional
CLI call needed for G4.
```
[ASSUMED — exact wording is Claude's Discretion; structure is VERIFIED against D-18/D-18a/D-18b]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SHIX/SHIH syntax in §1 new vocabulary subsection: `SHIX 3 125.5` assigns 13C shift to atom 3 | "Change 1: pyLSD Command Vocabulary" | Wrong syntax in skill docs; agent might write invalid SHIX lines in permutation files. Low impact: lsd-engineer doesn't write SHIX directly, PyLSDOrchestrator does. |
| A2 | lsd-engineer routing block uses python3 (not jq) for JSON extraction | Code Examples — Routing Block | If python3 is unavailable, the condition never fires. Low risk on any modern Unix. |
| A3 | `ranked_solutions[].quality` field exists in `_perform_ranking()` JSON output | Code Examples — pylsd run JSON | If field is named differently (e.g., `rank_quality`), the ITERATION-COMPLETE table source for `top_rank_quality` column is wrong. Planner should verify against `src/lucy_ng/cli/lsd.py::_perform_ranking`. |

---

## Open Questions

1. **ITERATION-COMPLETE per-permutation solution count source**
   - What we know: run_report.json has per-solution provenance with `perm_index`. The per-permutation solution count must be derived by counting `perm_NN/solutions.smi` lines.
   - What's unclear: should lsd-engineer inline a python script in the ITERATION-COMPLETE section of its skill, or just document the two-step procedure (count lines from .smi files, extract top-3 from JSON stdout)?
   - Recommendation: Document procedure prose + show the python extraction for top-3 from `--format json` output. Keep it simple; per-permutation counts from line counting are straightforward enough to describe without a code block.

2. **`quality` field name in `_perform_ranking()` JSON output**
   - What we know: `lucy pylsd run --format json` wraps `_perform_ranking()` output as `ranked_solutions` array. The `quality` field is referenced in CONTEXT.md D-20 as `top_rank_quality`.
   - What's unclear: The exact key name in the per-solution JSON object from `_perform_ranking()`.
   - Recommendation: Planner should run `grep -n "quality\|rank_quality" src/lucy_ng/cli/lsd.py` to confirm field name before writing the ITERATION-COMPLETE documentation.

3. **Line 268 vs line 481 — documentation vs executable**
   - What we know: Line 268 is in a documentation/rules block; line 481 is an executable workflow step.
   - What's unclear: Should line 268 be replaced with the routing block, or updated to say "see workflow step 11"?
   - Recommendation: Update line 268 to a prose note ("Run via solver-mode routing block — see workflow step 11 below"); replace line 481 with the full routing bash block. This keeps §3 as documentation-style and §workflow as executable-style, consistent with the file's existing structure.

---

## Environment Availability

Step 2.6: The relevant CLI commands already confirmed available per Phase 68/69 verification:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `lucy lsd validate-inventory` | lsd-engineer routing block, G4 extraction | Yes | Verified Phase 68 | — |
| `lucy pylsd run` | lsd-engineer routing block | Yes | Verified Phase 69 | `lucy lsd run` (D-19) |
| `python3` | JSON extraction in bash | Yes | System python3 | jq (if installed) |
| `jq` | Optional extraction | Not verified | — | python3 one-liner |

---

## Validation Architecture

Per `.planning/config.json` — nyquist_validation not explicitly set to false, so validation is enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pyproject.toml` (no separate pytest.ini) |
| Quick run command | `pytest tests/ -q` |
| Full suite command | `pytest --cov=lucy_ng` |

### Phase Requirements → Test Map

Phase 70 is markdown-only. No Python changes means no new pytest tests. Validation is via grep verification of skill files:

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGT-01 | `HMBC X Y 2 4` syntax documented in lsd-engineer §1 | grep | `grep "HMBC X Y 2 4" ~/.claude/agents/lucy-lsd-engineer.md` | After Phase 70 edit |
| AGT-02 | Routing block present in lsd-engineer workflow | grep | `grep "pylsd_mode\|lucy pylsd run" ~/.claude/agents/lucy-lsd-engineer.md` | After Phase 70 edit |
| AGT-03 | case.md spawn protocol unchanged (routing in lsd-engineer) | grep | `grep -c "lucy lsd run\|lucy pylsd run" ~/.claude/commands/lucy-ng/case.md` should be 0 | Confirm no-op |
| AGT-04 | G4 block present in devils-advocate | grep | `grep "G4\|Permutation Count Cap\|K > 3\|K>3" ~/.claude/agents/lucy-devils-advocate.md` | After Phase 70 edit |

### Wave 0 Gaps
None — existing test infrastructure covers Python code; skill file edits are verified by grep patterns in plan tasks.

---

## Security Domain

Not applicable to this phase. Skill file editing with no input handling, authentication, or data persistence.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single `lucy lsd run` unconditionally | Conditional routing based on `pylsd_mode` inventory field | Phase 70 (this phase) | Agent can now choose multi-run mode autonomously |
| G1/G2/G3 only | G1/G2/G3/G4 with permutation count cap | Phase 70 (this phase) | Hard block at K>3 before PyLSDOrchestrator raises ValueError |
| Bare `FORM C13H18O2` | `; FORM C13H18O2` (LSD comment) | Phase 69 backport of Phase 66 | LSD-3.4.9 rejects bare FORM (error 102) — comment form silently ignored |

**Deprecated/outdated:**
- `FORM` bare command: rejected by LSD-3.4.9. Always use `; FORM` comment form. Documented in `.planning/findings/form-tolerance.md`.
- Phase 68 advisory CR-02 (missing `inventory` in validate-inventory success response): FIXED. The `inventory` key is present in the success response as of Phase 69.

---

## Sources

### Primary (HIGH confidence)
- `~/.claude/agents/lucy-lsd-engineer.md` — full file read; line-by-line current state documented
- `~/.claude/agents/lucy-devils-advocate.md` — full file read; G1/G2/G3 structure confirmed
- `~/.claude/commands/lucy-ng/case.md` — full file read; confirmed no `lucy lsd run` calls
- `src/lucy_ng/cli/pylsd.py` — full source read; `--format json` output shape confirmed
- `src/lucy_ng/lsd/orchestrator.py` — full source read; run_report.json structure confirmed
- `.planning/phases/68-constraint-inventory-v2-schema/68-VERIFICATION.md` — CR-02 status confirmed
- `.planning/phases/69-cli-command-and-regression-suite/69-VERIFICATION.md` — CLI shape confirmed
- `.planning/phases/70-agent-skill-updates/70-CONTEXT.md` — locked decisions D-17 through D-20
- Live CLI test: `lucy lsd validate-inventory --format json` with test LSD file — confirmed `inventory` key present in success response

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` §Phase 70 — success criteria
- `.planning/REQUIREMENTS.md` §Agent Integration — AGT-01..AGT-04
- `.planning/phases/67-pylsdorchestrator-and-solutionmerger/67-01-SUMMARY.md` — run_report.json field names

---

## Metadata

**Confidence breakdown:**
- Current file state (what's already in place): HIGH — all three files read in full
- `--format json` output shapes: HIGH — source code read directly
- G4 insertion point and structure: HIGH — G1/G2/G3 pattern confirmed, insertion point line 333 confirmed
- SHIX/SHIH syntax: ASSUMED — derived from Phase 66 context, not verified against LSD binary docs
- Routing block bash syntax: ASSUMED — structure matches D-17 decisions and CLI, exact wording is Claude's Discretion

**Research date:** 2026-05-19
**Valid until:** 2026-06-19 (stable — skill files change only when phases edit them; code output shapes are pinned to Phases 67/69)
