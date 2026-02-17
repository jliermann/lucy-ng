---
phase: 43
status: researched
researched: 2026-02-17
---

# Phase 43: Constraint Inventory System - Research

**Researched:** 2026-02-17
**Domain:** LSD file format, JSON schema design, constraint tracking, agent workflow protocol
**Confidence:** HIGH

## Summary

Phase 43 designs and implements a JSON-based constraint inventory embedded as a comment block in LSD file headers. The inventory is maintained by the LSD-Engineer agent across iterations and validated by the Devils-Advocate agent before each solver run. The system's purpose is to prevent the v3.0 constraint-loss bugs by making the full constraint state explicit and machine-checkable rather than relying on agent memory.

The core mechanism is simple: the LSD-Engineer reads the previous iteration's LSD file (including its inventory comment), updates the inventory with the new batch of HMBC correlations, and writes both the inventory and the LSD commands. The Devils-Advocate then parses the inventory and diffs it against the actual LSD commands to catch discrepancies before the solver runs.

This is NOT a complex system. There is no external database, no new CLI command, no new file format. It is a structured comment block at the top of an existing LSD file, read and written by the agents that already handle that file. The primary research question is: what exactly goes in the JSON schema, and how do the agents interact with it?

**Primary recommendation:** Implement inventory as a JSON comment block in the LSD file header. The LSD-Engineer maintains it; the Devils-Advocate validates it. No new tooling required — agents use Read/Grep/Bash to interact with the inventory.

---

## Empirical Analysis: v3.0 UAT Bug Evidence

The four actual CASE1 iteration LSD files from the v3.0 UAT (ibuprofen, C13H18O2) confirm the MEMORY.md bug reports precisely:

### What was actually lost between iterations

Examining the four iteration files at:
`/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_0{1,2,3,4}/compound.lsd`

**DEFF NOT patterns:** Zero DEFF NOT lines in ALL four iterations. The MEMORY.md reports "agent wrote 6 DEFF NOT patterns in iteration 1" — this is incorrect for CASE1. In CASE1, DEFF NOT was never written at all. This is worse than described: the bug is "never writes DEFF NOT" not "drops after iteration 1". The Devils-Advocate's iteration-1 baseline check is therefore insufficient — the inventory must also enforce that DEFF NOT is written FROM iteration 1.

**SYME constraints:** Never written despite the agent noting signal groups (C4/C5 at 129.38, C6/C7 at 127.26, C11/C12 at 22.37). Grouped atom notation was used in HMBC (pairs were created: MULT 4+5, MULT 6+7, MULT 11+12) but SYME was not written.

**Grouped HMBC notation:** Not used. All HMBC correlations use simple `HMBC N M` syntax, even for equivalent atom pairs. The comment in iteration 1 says "C6 is one of the equivalent pair at 127.26 ppm" but writes `HMBC 2 6` not `HMBC 2 (6 7)`.

**Detection results not applied:** The agent correctly identified equivalent pairs but never translated them to LSD constraints. This is the most important category — detection runs, finds results, but results die in the agent's context without becoming BOND/SYME/PROP/ELIM.

**Root cause:** The agent reconstructs the LSD file for each iteration (copy of all prior HMBC plus new batch) but omits any constraints it didn't explicitly add in the CURRENT reasoning chain. Without a persistent inventory telling it "you had 8 DEFF NOT patterns last time," the agent has no mechanism to preserve what it didn't explicitly decide to add this iteration.

---

## Architecture Patterns

### Pattern 1: JSON Inventory as LSD Comment Block

**What:** A JSON object embedded in the LSD file header as LSD comment lines (`;`). The entire inventory is delimited by special markers and parseable by Grep + Bash.

**When to use:** This is the only viable pattern. It keeps the inventory co-located with the constraints it tracks, making the dependency explicit. A separate sidecar file (e.g., `inventory.json`) would be simpler to parse but creates a file that can get out of sync with the LSD file — the very failure mode we're trying to prevent.

**Example structure:**
```
; === CONSTRAINT INVENTORY v1 ===
; {
;   "version": 1,
;   "iteration": 2,
;   "formula": "C13H18O2",
;   "mult_count": 15,
;   "hsqc_count": 10,
;   "hmbc_batches": [
;     {"batch": 1, "count": 5, "correlations": ["1 13", "2 6", "3 4", "10 11", "4 8"]},
;     {"batch": 2, "count": 5, "correlations": ["1 9", "3 13", "3 9", "5 9", "11 10"]}
;   ],
;   "hmbc_total": 10,
;   "bond_constraints": ["1 14"],
;   "deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1", "C1SC1", "C1SCC1", "C1OC1", "C1OCC1"],
;   "syme_pairs": [],
;   "list_prop_elim": [],
;   "grouped_hmbc": [],
;   "detection_results": {
;     "hybridisation_queries": ["132.5 sp2"],
;     "neighbours_queries": ["180.56 O mandatory 95.8%"],
;     "hhb_result": "no HHB detected",
;     "grouping_detected": ["[44.90, 45.03] span 0.13 ppm"]
;   },
;   "applied_from_detection": ["BOND 1 14 from neighbours 180.56 O mandatory"],
;   "pending_from_detection": ["SYME for grouped [44.90, 45.03] -- NOT YET APPLIED"]
; }
; === END CONSTRAINT INVENTORY ===
```

**Key design decisions:**
- Comments use `;` prefix (LSD comment syntax) so the LSD parser ignores them
- Delimiter lines (`; ===`) allow reliable extraction with `sed` or `grep -A`
- JSON is compact but multi-line (one JSON line per LSD comment line) for readability
- Inventory comes BEFORE all LSD commands in the file

### Pattern 2: Agent Read-Update-Write Protocol

**What:** The LSD-Engineer reads the previous iteration's inventory section, updates it with new constraints, and writes the complete new file (inventory + all LSD commands).

**Critical rule:** The LSD-Engineer NEVER reconstructs the inventory from memory. It reads the previous file's inventory, copies it, and appends new items. This mirrors the existing "read previous file, never reconstruct" rule and extends it to the structured inventory.

**Steps:**
1. Read `analysis/iteration_NN-1/compound.lsd`
2. Extract inventory JSON from comment block using grep/sed
3. Parse JSON: get current counts, existing constraints
4. Copy ALL existing constraints from previous LSD file (this already exists as rule)
5. Update inventory: increment iteration number, add new HMBC batch to `hmbc_batches`, increment `hmbc_total`
6. Write new `analysis/iteration_NN/compound.lsd`: inventory block first, then ALL LSD commands

**For iteration 1 specifically:** LSD-Engineer initializes inventory from scratch using detection results from nmr-chemist. The `deff_not_patterns` array is populated at initialization (not when agent remembers to add them).

### Pattern 3: Devils-Advocate Inventory Diff

**What:** The Devils-Advocate parses both the current inventory and the previous iteration's inventory (or reconstructs expected values from the previous LSD file), then diffs them.

**Diff algorithm:**

```
For each tracked constraint type:
  expected_count = previous_inventory[type]_count
  actual_count = count_occurrences(current_lsd_file, type)
  inventory_count = current_inventory[type]_count

  Check 1: inventory_count == actual_count   (inventory accurate?)
  Check 2: actual_count >= expected_count    (no regression?)
  Check 3: every item in previous_list exists in current_list (content preserved?)
```

**Bash-based extraction** (no Python required, consistent with agent toolset):
```bash
# Extract inventory block
sed -n '/=== CONSTRAINT INVENTORY/,/=== END CONSTRAINT INVENTORY/p' compound.lsd | grep "^; " | sed 's/^; //' | tr -d '\n' > /tmp/inventory.json

# Count actual DEFF NOT lines in file
grep -c "^DEFF NOT" compound.lsd

# Extract specific values from inventory
grep '"deff_not_patterns"' /tmp/inventory.json  # not needed -- parse JSON
```

**The Devils-Advocate does NOT need Python JSON parsing.** It can use `grep` to extract inventory counts and compare to `grep -c` counts on the actual LSD file. The inventory is a source of truth for expected values; the LSD file is ground truth for actual values. Discrepancy = bug.

---

## JSON Schema Design

### Complete Schema (v1)

```json
{
  "version": 1,
  "iteration": <integer, 1-based>,
  "formula": "<molecular formula string>",
  "timestamp": "<ISO timestamp>",

  "mult_count": <integer>,
  "hsqc_count": <integer>,

  "hmbc_batches": [
    {
      "batch": <integer, 1-based>,
      "count": <integer>,
      "correlations": ["<C atom> <H atom>", ...]
    }
  ],
  "hmbc_total": <integer>,
  "grouped_hmbc": ["(<C1> <C2>) <H>", ...],

  "bond_constraints": ["<C1> <C2>", ...],
  "syme_pairs": ["<A1> <A2>", ...],
  "list_prop_constraints": ["<description>", ...],
  "elim_value": <integer or null>,

  "deff_not_patterns": ["C1CC1", "C1CCC1", ...],

  "detection_results": {
    "hybridisation_queries": ["<shift> <state>", ...],
    "neighbours_queries": ["<shift> <element> <type> <frequency>", ...],
    "hhb_result": "<text>",
    "grouping_detected": ["[<ppm1>, <ppm2>] span <X> ppm", ...]
  },

  "applied_from_detection": ["<constraint> from <detection source>", ...],
  "pending_from_detection": ["<constraint> for <detection result> -- NOT YET APPLIED", ...]
}
```

### Schema Design Decisions

**`hmbc_batches` as array of objects:** Each batch is tracked separately so the Devils-Advocate can verify batch N is still fully present in iteration N+k. This prevents the case where a batch is partially dropped.

**`grouped_hmbc` as separate array:** Parenthesized HMBC syntax `(C1 C2) H` is tracked separately from regular HMBC correlations. The Devils-Advocate checks that `len(grouped_hmbc) >= previous_grouped_hmbc_count` to catch Bug 3 (notation dropped).

**`deff_not_patterns` as array of SMARTS strings:** These are the actual SMARTS patterns used in `DEFF NOT` commands, not atom numbers. They are constant across iterations (natural product set). The Devils-Advocate checks `len(deff_not_patterns) == grep_count("^DEFF NOT", lsd_file)` on every iteration, not just iteration > 1.

**`pending_from_detection`:** Explicitly tracks detection results that have NOT been translated to constraints. This addresses Bug 2 and Bug 5 — the inventory makes the gap visible rather than silently dropping the information. The LSD-Engineer must either apply the pending constraint or document why it was not applied (move to a "not_applicable" field).

**`detection_results`:** The raw detection output from `lucy detect` commands is stored here with source annotation. This makes the source of each constraint auditable.

**No versioning complexity:** `"version": 1` is a future-proofing field only. No migration code needed for v4.0 — all files will be version 1.

**`elim_value`:** Single integer or null (not an array). ELIM takes a single count argument. Tracking as a scalar simplifies the check (previous = null, new = 1 means first ELIM added; previous = 1, new = 2 means escalation).

---

## Implementation Details

### Where the Inventory Lives in the LSD File

The inventory block goes at the TOP of the file, before any MULT definitions. LSD reads the file sequentially; comment lines are ignored. This means:
- The file opens with the inventory (machine-readable metadata)
- Followed by human-readable description comments (existing practice)
- Followed by MULT definitions
- Followed by HSQC, HMBC, BOND, etc.

### How LSD-Engineer Writes the Inventory

The LSD-Engineer already uses the Write tool to create LSD files. The inventory is just additional content at the top. No new tools or processes needed.

The Write operation for iteration N:
1. Build inventory JSON object in memory
2. Serialize to multi-line JSON (each line prefixed with `; `)
3. Write: `; === CONSTRAINT INVENTORY v1 ===\n; {line1}\n; {line2}\n...\n; === END CONSTRAINT INVENTORY ===`
4. Append all existing LSD commands (copied from iteration N-1)
5. Append new HMBC batch

### How Devils-Advocate Reads the Inventory

The Devils-Advocate already has Read, Bash, Grep tools. The extraction is:

```bash
# Extract inventory from iteration_02/compound.lsd
grep "^; " analysis/iteration_02/compound.lsd | grep -A1000 "CONSTRAINT INVENTORY v1" | grep -B1000 "END CONSTRAINT INVENTORY" | sed 's/^; //' > /tmp/current_inv.json

# Extract inventory from iteration_01/compound.lsd
grep "^; " analysis/iteration_01/compound.lsd | grep -A1000 "CONSTRAINT INVENTORY v1" | grep -B1000 "END CONSTRAINT INVENTORY" | sed 's/^; //' > /tmp/prev_inv.json
```

Then compare using `grep` pattern matching (not Python JSON parsing) for critical checks:
- DEFF NOT count: `grep -c '"C1CC1"' /tmp/current_inv.json` vs `grep -c "^DEFF NOT C1CC1" compound.lsd`
- HMBC total: `grep '"hmbc_total"' /tmp/current_inv.json | grep -o '[0-9]*'` vs `grep -c "^HMBC" compound.lsd`

The Devils-Advocate workflow already described in Phase 42 (42-04-PLAN.md) covers most of the validation logic. Phase 43 adds the structured inventory that makes that validation reliable.

### Inventory Initialization (Iteration 1)

For iteration 1, the LSD-Engineer must initialize a complete inventory including:
- All MULT, HSQC counts (counted after writing them)
- First HMBC batch (added to `hmbc_batches` array as batch 1)
- All DEFF NOT patterns (the standard set for natural products, from its inlined knowledge)
- Detection results from nmr-chemist's message
- `applied_from_detection`: which detection results became constraints
- `pending_from_detection`: which detection results were NOT applied yet

**Critical:** The DEFF NOT patterns must go into the inventory at iteration 1, even if they go into the LSD file at iteration 1. The inventory is initialized from the SAME write operation that creates the LSD file, so they cannot get out of sync at initialization.

### Inventory Update (Iteration N > 1)

For iteration N:
1. Read iteration N-1 inventory
2. Increment `iteration`
3. Add new HMBC batch to `hmbc_batches`, update `hmbc_total`
4. Copy `deff_not_patterns`, `bond_constraints`, `syme_pairs`, `grouped_hmbc` verbatim from N-1 (unless advisory says change)
5. Update `pending_from_detection` if any pending constraints were applied this iteration
6. Update timestamp

**The copy-verbatim rule for structural constraints is the key mechanism.** By explicitly copying these fields from N-1, the LSD-Engineer cannot accidentally omit them — it has to actively delete them to drop them.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON parsing in Bash | Custom parser | `grep` + string extraction | Agents use Grep/Bash; no Python JSON library needed for validation |
| Separate sidecar file | `inventory.json` alongside `compound.lsd` | Embedded comment block in LSD file | Prevents inventory/LSD divergence |
| External inventory database | SQLite or file-per-iteration store | Comment block in LSD file | Unnecessary complexity; co-location is the feature |
| Automated constraint extraction | Script to parse LSD and build inventory | LSD-Engineer writes inventory while writing constraints | Agent already knows what constraints it added |

**Key insight:** The inventory works because the LSD-Engineer writes it as part of the same action as writing the constraints. If inventory maintenance were a separate step or tool, it would be vulnerable to the same forgetting failure mode it's meant to prevent.

---

## Common Pitfalls

### Pitfall 1: Inventory Gets Out of Sync with LSD File
**What goes wrong:** LSD-Engineer adds a DEFF NOT to the file but forgets to add it to `deff_not_patterns`. Or vice versa. Inventory becomes inaccurate.
**Why it happens:** Writing inventory and writing commands are two separate mental operations. Agent forgets one.
**How to avoid:** In the workflow specification, the inventory update and the LSD command write must be described as a SINGLE atomic operation. The inventory block is written first, then the LSD commands are written to match. Devils-Advocate validates alignment on every iteration.
**Warning signs:** `grep -c "^DEFF NOT" compound.lsd` does not match `len(deff_not_patterns)` in inventory.

### Pitfall 2: Inventory Rebuilt From Scratch Instead of Copied
**What goes wrong:** LSD-Engineer ignores the previous inventory and writes a fresh one. Previous batch history is lost.
**Why it happens:** This is the same "reconstruct from memory" failure mode the inventory is supposed to prevent. Agent writes "HMBC batch 3 (total 5 correlations)" because it forgets it already had 10 from batches 1-2.
**How to avoid:** The LSD-Engineer's workflow MUST specify: "Step 1: Read previous inventory. Step 2: Copy previous inventory as starting point. Step 3: Update fields." The "read previous file, never reconstruct" rule applies equally to the inventory.
**Warning signs:** `hmbc_total` in iteration N is less than `hmbc_total` in iteration N-1. `hmbc_batches` array has fewer entries than expected.

### Pitfall 3: `pending_from_detection` Never Gets Applied
**What goes wrong:** The detection result stays in `pending_from_detection` across all iterations without ever becoming a constraint.
**Why it happens:** The LSD-Engineer copies `pending_from_detection` verbatim from N-1 without reviewing whether any pending items should now be applied.
**How to avoid:** The LSD-Engineer workflow must include: "Review `pending_from_detection`. For each item: decide whether to apply now (move to `applied_from_detection` and write the constraint) or leave pending (with documented reason)." The Devils-Advocate should flag items that have been pending for 3+ iterations.
**Warning signs:** Same items in `pending_from_detection` across iterations 1, 2, 3, 4.

### Pitfall 4: Inventory Block Breaks LSD Parsing
**What goes wrong:** LSD parser rejects the file because inventory comment lines contain special characters (e.g., `{`, `}`, `"`, `(`, `)` in JSON) that the LSD parser misinterprets.
**Why it happens:** LSD comment syntax is `; text` but the parser may have edge cases.
**How to avoid:** Test with a minimal inventory block using `lucy lsd run` before finalizing the format. If the LSD parser chokes on JSON characters in comments, the fallback is to escape or use a simpler key=value format instead of JSON.
**Warning signs:** LSD solver reports parse error on a file that was valid before adding the inventory block.
**Mitigation:** If JSON in comments fails, switch to a simplified line-based format:
```
; INVENTORY_DEFF_NOT_COUNT: 8
; INVENTORY_HMBC_TOTAL: 10
; INVENTORY_SYME_COUNT: 0
```
This is less expressive but fully safe.

### Pitfall 5: Inventory Adds Significant Line Overhead
**What goes wrong:** A 30-atom molecule with 4 batches of HMBC has a 60-line inventory block, making the LSD file harder to read.
**Why it happens:** JSON is verbose when line-prefixed with `; `.
**How to avoid:** The inventory is metadata, not the primary content. LSD files are already organized with comment sections (they start with several header comment lines). Adding 30-60 lines of structured comments is acceptable. The alternative (compact single-line JSON) sacrifices readability.
**Mitigation:** Keep arrays compact on single lines where possible: `"deff_not_patterns": ["C1CC1", "C1CCC1", "C1NC1", "C1NCC1"]`

---

## What This Phase Changes in the Agent Files

Phase 43 modifies:

**`~/.claude/agents/lucy-lsd-engineer.md`:**
- Add JSON inventory schema definition to `<domain_knowledge>`
- Add inventory initialization procedure (iteration 1)
- Add inventory update procedure (iteration N)
- Update workflow steps 5-6 to explicitly include inventory writing
- Add rule: "inventory is written as part of the SAME operation as writing LSD commands"

**`~/.claude/agents/lucy-devils-advocate.md`:**
- Add inventory parsing procedure to `<domain_knowledge>`
- Add inventory-vs-actual reconciliation checks
- Update diff protocol: Check 1 = inventory accurate? (inventory counts match grep counts). Check 2 = no regression? (counts ≥ previous). Check 3 = content preserved?
- Update Bug 1 check: DEFF NOT dropped not just "after iteration 1" but "ever" — check vs inventory `deff_not_patterns` not just previous LSD file

**No changes to:**
- `~/.claude/agents/lucy-nmr-chemist.md` (NMR-Chemist doesn't write LSD files)
- `~/.claude/agents/lucy-solution-analyst.md` (Solution-Analyst doesn't handle LSD files)
- `~/.claude/commands/lucy-ng/case.md` (Orchestrator doesn't parse inventory directly)

---

## Phase Scope and Boundaries

### In Scope (Phase 43)
- JSON inventory schema design
- LSD-Engineer inventory initialization and update procedures
- Devils-Advocate inventory parsing and reconciliation checks
- Update to the two agent definition files (lsd-engineer.md, devils-advocate.md)
- Verification that the updated workflow prevents the v3.0 bugs

### Out of Scope (Phase 43)
- CASE-PROGRESS.md format (Phase 44) — the inventory is in the LSD file, not the progress log
- Team coordination protocol (Phase 45) — who assigns tasks and when
- New CLI commands — no new lucy-ng CLI functionality required
- Python tooling — all inventory interaction uses Bash/grep

### Boundary with Phase 44
Phase 44 (CASE-PROGRESS.md Format) defines how agents report iteration results in the progress log. The constraint inventory (Phase 43) lives in the LSD file header, not in CASE-PROGRESS.md. However, Phase 44 may reference the inventory for reporting: e.g., "Constraints: 8 DEFF NOT, 10 HMBC (2 batches), SYME: none" in the progress log. The constraint inventory is the source of truth for those numbers.

---

## Plan Structure Recommendation

### Wave 1: Schema and Protocol Design (1 plan)

**Plan 43-01: Constraint Inventory Schema and Protocol**
- Define the JSON schema (this research provides the draft)
- Write the detailed initialization and update procedures as agent knowledge
- Write the inventory parsing and validation procedures as agent knowledge
- No file changes yet — this plan produces the schema specification that plans 43-02 and 43-03 use

### Wave 2: Agent Definition Updates (2 plans, parallel)

**Plan 43-02: Update LSD-Engineer with Inventory Protocol**
- Add inventory schema knowledge to `~/.claude/agents/lucy-lsd-engineer.md`
- Add initialization procedure (iteration 1 creates inventory)
- Add update procedure (iteration N reads previous, updates)
- Update workflow steps to integrate inventory writing

**Plan 43-03: Update Devils-Advocate with Inventory Validation**
- Add inventory parsing knowledge to `~/.claude/agents/lucy-devils-advocate.md`
- Add inventory-vs-actual reconciliation checks
- Update diff protocol to use structured inventory instead of line counting

Plans 43-02 and 43-03 are INDEPENDENT (different files, same schema). They can run in parallel.

### Wave 3: Verification (1 plan)

**Plan 43-04: Verify Constraint Inventory System**
- Verify LSD-Engineer writes correct inventory for a test case (Ibuprofen iteration 1)
- Verify inventory is parseable by the Devils-Advocate procedure
- Verify all 5 v3.0 bugs are now caught by the Devils-Advocate inventory validation
- Verify no LSD parser errors from inventory comment block

**Dependency:** 43-04 depends on 43-02 and 43-03.

**Total: 4 plans across 3 waves.**

---

## Open Questions

### 1. LSD Parser Compatibility with JSON Characters in Comments
- **What we know:** LSD comments start with `;`. JSON contains `{`, `}`, `"`, `[`, `]`.
- **What's unclear:** Whether any of these characters cause the LSD parser to error or behave unexpectedly.
- **Recommendation:** Plan 43-01 includes testing with a minimal file. If JSON characters cause issues, use the simplified `; INVENTORY_KEY: VALUE` format instead of JSON. This is lower risk and the validation logic simplifies accordingly.
- **Confidence:** LOW (not tested)

### 2. Whether `pending_from_detection` Needs Explicit "Not Applicable" Category
- **What we know:** Some detection results (e.g., grouping) may not always produce constraints (e.g., grouping at extreme edges of spectrum may not warrant SYME).
- **What's unclear:** Should the LSD-Engineer be required to explicitly mark items as "not_applicable" rather than leave them in "pending"? Or does the current two-state model (applied/pending) cause the Devils-Advocate to flag too many false WARNINGs?
- **Recommendation:** Start with two-state model (applied/pending). If false WARNINGs are excessive in Phase 47 UAT, add a "not_applicable" field with required justification. This is a Phase 47 tuning concern, not a Phase 43 design blocker.
- **Confidence:** MEDIUM

### 3. Whether Inventory Needs to Track HMBC Correlation Content or Just Counts
- **What we know:** The roadmap success criterion says "Grouped notation (HMBC (5 6) 10) preserved in inventory." The schema draft stores full correlation strings in `hmbc_batches[n].correlations`.
- **What's unclear:** Is storing full content (`"1 13"`, `"2 6"`) necessary for the diff, or is counting sufficient?
- **Recommendation:** Store full content. Counts alone cannot detect the "notation degraded" case (where `HMBC (6 7) 2` becomes `HMBC 6 2` — still the same count, but grouped notation dropped). Content tracking catches this; count tracking does not.
- **Confidence:** HIGH

---

## Sources

### Primary (HIGH confidence)
- `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/iteration_0{1,2,3,4}/compound.lsd` — actual LSD files from v3.0 UAT, empirical confirmation of all bugs
- `~/.claude/agents/lucy-lsd-engineer.md` (306 lines, Phase 42 output) — current LSD-Engineer definition
- `~/.claude/agents/lucy-devils-advocate.md` (221 lines, Phase 42 output) — current Devils-Advocate definition
- `.planning/phases/42-agent-definitions/42-CONTEXT.md` — locked decisions for Phase 42
- `.planning/phases/42-agent-definitions/42-VERIFICATION.md` — what Phase 42 delivered
- `.planning/ROADMAP.md` — Phase 43 success criteria and scope boundaries
- `MEMORY.md` — v3.0 Post-UAT Findings (5 confirmed agent behavior bugs)

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY-v4.0.md` — v4.0 architecture research (constraint inventory concept)
- `.planning/research/ARCHITECTURE.md` — agent team architecture patterns
- `/Users/steinbeck/Dropbox/develop/lucy-ng/ibuprofen.lsd`, `ibuprofen_v3.lsd` — reference LSD files showing current format conventions

---

## Metadata

**Confidence breakdown:**
- JSON schema design: HIGH — schema derived from actual LSD files and enumerated constraint types
- Agent protocol (LSD-Engineer): HIGH — extends existing "read previous file" rule, same Write workflow
- Agent protocol (Devils-Advocate): HIGH — extends existing diff protocol with structured source
- LSD parser compatibility: LOW — not tested; fallback format ready
- Plan structure: HIGH — 4 plans, clear wave dependencies

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (schema is stable; recheck if LSD parser compatibility issue found)

---

*Phase: 43-constraint-inventory-system*
*Research completed: 2026-02-17*
