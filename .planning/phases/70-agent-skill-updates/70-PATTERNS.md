# Phase 70: Agent Skill Updates — Pattern Map

**Mapped:** 2026-05-19
**Files analyzed:** 2 (modified skill markdown files)
**Analogs found:** 2 / 2

---

## File Classification

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `~/.claude/agents/lucy-lsd-engineer.md` | skill (domain-encoding for AI agent) | request-response (agent reads skill before every iteration) | Phase 68 Plan 03 task editing the same file (`68-03-PLAN.md`) | exact — same file, same task structure |
| `~/.claude/agents/lucy-devils-advocate.md` | skill (domain-encoding for AI agent) | request-response (agent reads skill before every validation) | Phase 68 Plan 04 task editing the same file (`68-04-PLAN.md`) | exact — same file, same task structure |

**Not modified (per D-17a/b, RESEARCH.md Key Finding 5):**
- `~/.claude/commands/lucy-ng/case.md` — explicitly no-op for Phase 70; no pattern needed

---

## Pattern Assignments

### `~/.claude/agents/lucy-lsd-engineer.md` — Three changes

**Analog:** `.planning/phases/68-constraint-inventory-v2-schema/68-03-PLAN.md` (Task 1)

---

#### Change A: §"Run LSD" Routing Block (AGT-02)

**Two target locations — both must be addressed (Pitfall 2 from RESEARCH.md):**

**Location 1 — §3 File Organization documentation string (line 268):**

Current text to REPLACE (line 268):
```
- Run LSD from within iteration dir: `cd analysis/iteration_NN && lucy lsd run compound.lsd`
```

Replace with prose note:
```
- Run LSD via solver-mode routing block (see workflow step 11 below for the conditional branch)
```

**Location 2 — Workflow step 11 (line 481):**

Current text to REPLACE (line 481):
```
11. Run LSD: `cd analysis/iteration_NN && lucy lsd run compound.lsd`
```

Replace with the full conditional routing block:

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

**D-19 fallback behavior to document inline:** If `validate-inventory` returns `valid: false` with "No v2 inventory block found" (ABSENT case), `pylsd_mode` defaults to `False` via the `.get('inventory',{}).get('pylsd_mode', False)` expression — fall-through to `lucy lsd run` is silent, no WARNING emitted. MALFORMED inventory (other validation errors) is a hard error already handled by G2/G3 gates.

**`--working-dir` flag:** Omit. Default `pylsd_run/` subdirectory under the LSD file's parent directory is sufficient (Phase 69 D-14 Discretion).

**Acceptance criteria pattern (from Phase 68 analog):**
```bash
grep "pylsd_mode\|lucy pylsd run" ~/.claude/agents/lucy-lsd-engineer.md
grep -c "cd analysis/iteration_NN && lucy lsd run compound.lsd" ~/.claude/agents/lucy-lsd-engineer.md
# second command should return 0 — both old occurrences removed
```

---

#### Change B: §1 pyLSD Command Vocabulary Subsection (AGT-01)

**Insertion point:** After the existing `### ELIM Command (LAST RESORT)` subsection (lines 78–84). Insert a new named subsection.

**Existing ELIM section to add cross-reference to (lines 78–84):**
```
### ELIM Command (LAST RESORT)

```
ELIM 1 0    ; eliminate at most 1 correlation (0 = no bond distance limit)
```

Do NOT include ELIM on first run. Only add if 0 solutions AND you have verified: sp2 even, H budget correct, HMBC correlations correct, formula correct. Start with `ELIM 1 0`, increment.
```

**New subsection to INSERT after line 84:**

```markdown
### pyLSD Commands (pylsd_mode only)

When `pylsd_mode=true`, LSDInputGenerator generates permutation files using these additional commands. lsd-engineer does NOT write these directly — PyLSDOrchestrator generates permutation files. Document for inspection/debugging purposes:

```
; FORM C13H18O2    ; molecular formula — LSD comment (not a real command)
                   ; bare FORM rejected by LSD-3.4.9 error 102; always use ; FORM comment form
                   ; reference: .planning/findings/form-tolerance.md
SHIX 3 125.5       ; assign 13C chemical shift 125.5 ppm to atom 3
SHIH 3 7.2         ; assign 1H chemical shift 7.2 ppm to atom 3
HMBC X Y 2 4       ; HMBC correlation with extended bond range 2-4 (correct 4J mechanism)
HMBC X Y 2 4 ; ELIM  ; same + trailing comment marks X-Y as PyLSDOrchestrator suspect
```

**ELIM in pylsd_mode:** Do NOT write bare `ELIM N M` when `pylsd_mode=true`. G2 gate blocks it. Use `HMBC X Y 2 4 ; ELIM` instead (extended bond range + annotation for PyLSDOrchestrator permutation parsing). See §2 4J Deferral Rule and §5 Constraint Inventory.
```

**Acceptance criteria pattern:**
```bash
grep "SHIX\|SHIH\|; FORM" ~/.claude/agents/lucy-lsd-engineer.md
grep "bare FORM rejected\|error 102" ~/.claude/agents/lucy-lsd-engineer.md
grep "HMBC X Y 2 4" ~/.claude/agents/lucy-lsd-engineer.md
```

---

#### Change C: §4 ITERATION-COMPLETE Template Extension (D-20)

**Existing template — current last field to PRESERVE (line 299, do NOT replace):**
```
4J status: <"N deferred" / "added as final batch" / "skipped — solutions converged" / "N/A — no potential 4J">
```

**Extension: append below line 299 as a conditional block.** These blocks are output ONLY when `lucy pylsd run` was invoked (i.e., `pylsd_mode=true`):

```markdown
When `lucy pylsd run` was invoked, append two additional blocks after the `4J status:` line:

**Block 1 — Per-permutation table** (derive from `pylsd_run/perm_NN/solutions.smi` line counts and `pylsd_run/run_report.json` provenance):

```
| permutation_id | defer_set                      | solution_count | top_rank_quality |
|----------------|-------------------------------|----------------|-----------------|
| perm_00        | none                           | 7              | excellent        |
| perm_01        | atom4-atom8                    | 12             | good             |
| perm_02        | atom6-atom9                    | 0              | —                |
| perm_03        | atom4-atom8 + atom6-atom9      | 3              | excellent        |
```

**Block 2 — Aggregated** (extract from `lucy pylsd run --format json` stdout saved in `pylsd_output.json`):

```
Merged (unique InChI): <merged_count from pylsd_output.json>
Top-3 SMILES: <ranked_solutions[0].smiles> | <ranked_solutions[1].smiles> | <ranked_solutions[2].smiles>
```

**Data extraction procedure:**
- `merged_count`: `python3 -c "import sys,json; print(json.load(open('analysis/iteration_NN/pylsd_output.json'))['merged_count'])"`
- Top-3 SMILES: `python3 -c "import json; d=json.load(open('analysis/iteration_NN/pylsd_output.json')); print(' | '.join(s['smiles'][:60] for s in d['ranked_solutions'][:3]))"`
- Per-permutation `solution_count`: count lines in each `pylsd_run/perm_NN/solutions.smi` (one SMILES per line)
- `defer_set`: derive from `run_report.json` provenance — for each `perm_index`, collect `active_correlations` from any solution's provenance; format as `atomN-atomM` pairs joined with ` + ` (or `none` if include_flags all false)
- `top_rank_quality`: read `quality` field from `ranked_solutions` in `pylsd_output.json` for solutions whose provenance includes that `perm_index`
```

**Pitfall 4 guard (from RESEARCH.md):** The `4J status:` line at line 299 MUST remain. D-20 adds blocks BELOW it; it does not replace the existing field.

**Acceptance criteria pattern:**
```bash
grep "Per-permutation\|permutation_id\|defer_set\|merged_count\|Top-3 SMILES" ~/.claude/agents/lucy-lsd-engineer.md
grep "pylsd_output.json" ~/.claude/agents/lucy-lsd-engineer.md
# existing field preserved:
grep "4J status:" ~/.claude/agents/lucy-lsd-engineer.md
```

---

### `~/.claude/agents/lucy-devils-advocate.md` — One change

**Analog:** `.planning/phases/68-constraint-inventory-v2-schema/68-04-PLAN.md` (Task 1, Check 4 insertion)

---

#### Change: G4 Permutation Count Cap (D-18, AGT-04)

**Exact insertion point — after line 333 (current last line of Check 4):**

```
**All three gates G1/G2/G3 are CRITICAL severity and blocking.** No new override mechanism exists beyond the existing APPROVED/BLOCKED/WARNING semantics (per design decision D-08). The user may intervene via the orchestrator advisory if a gate fires incorrectly.
```

**Insert G4 block BEFORE that summary sentence, then update the summary sentence itself.**

**Step 1 — Insert G4 between G3 and the summary line.** The G3 block currently ends at line 331:
```
- If any condition is false: **BLOCK** with message: "HMBC lines carry '; ELIM' annotations but constraint inventory is inconsistent..."
```

After G3's closing bullet, insert:

```markdown
**G4: Permutation Count Cap**

When `pylsd_mode=true`, count deferred_4j entries and check against the K≤3 cap:

```bash
K=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('inventory',{}).get('deferred_4j', [])))")
```

- If K > 3: **BLOCK** with message: "K={K} exceeds permutation cap (K≤3, max 2^3=8 permutations). PyLSDOrchestrator.run() will raise ValueError before creating any files. Action: nmr-chemist must prioritize the Top-3 most likely 4J suspects (highest probability aromatic-to-aliphatic); demote remaining entries from deferred_4j by removing their '; ELIM' annotation from the corresponding HMBC lines, or reclassify them as non-suspect."
- If K ≤ 3: G4 passes.

**Note:** `$RESULT` is already set from the `lucy lsd validate-inventory --format json` call in §5A. No additional CLI call needed for G4.
```

**Step 2 — Update the "All three gates" summary line (line 333) atomically with Step 1:**

Change from:
```
**All three gates G1/G2/G3 are CRITICAL severity and blocking.**
```
To:
```
**All four gates G1/G2/G3/G4 are CRITICAL severity and blocking.**
```

The rest of the sentence (about no new override mechanism) is unchanged.

**Step 3 — Update [VALIDATION-PASSED] template** to include a `pyLSD mode:` field (lines 363–380). After the `Aromatic ring check:` line, add:

```
pyLSD mode: N/A (pylsd_mode=false) / PASS (K=N, N≤3) / BLOCKED (K=N>3)
```

**Pitfall 3 guard (from RESEARCH.md):** G4 and the summary update are a single atomic edit. Do not insert G4 and leave "All three gates" as-is.

**`$RESULT` variable source (lines 225–253 in §5A):** `$RESULT` is set by `lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd` in §5A. G4 reuses it with `.inventory.deferred_4j` path — confirmed live (RESEARCH.md Verified).

**Acceptance criteria pattern (following Phase 68-04 analog):**
```bash
grep "G4\|Permutation Count Cap\|K > 3\|K>3" ~/.claude/agents/lucy-devils-advocate.md
grep "All four gates G1/G2/G3/G4" ~/.claude/agents/lucy-devils-advocate.md
grep "pyLSD mode:" ~/.claude/agents/lucy-devils-advocate.md
# confirm "All three gates" is gone:
grep -c "All three gates G1/G2/G3 are CRITICAL" ~/.claude/agents/lucy-devils-advocate.md
# ^ should return 0
```

---

## Shared Patterns

### Skill-File Edit Protocol (cross-cutting — apply to both tasks)

**Source:** Phase 68 Plan 03 and Plan 04 task structure (confirmed working approach for these exact files)

**Pattern:**
1. `read_first` block must name the EXACT section + line range to edit (not the whole file, but the agent must read the full file before writing to avoid overwriting non-targeted sections)
2. `action` block specifies which text to REPLACE vs which to INSERT AFTER/BEFORE
3. `verify` block uses `grep`-based acceptance criteria against the actual file on disk
4. Each change is described as REPLACE (existing text shown verbatim) or INSERT AFTER (anchor text shown verbatim), never as abstract "update section X"

**Grep verification template (from Phase 68-03 and 68-04):**
```bash
# Positive checks — new content present
grep "NEW_PATTERN" ~/.claude/agents/lucy-AGENTNAME.md

# Negative checks — old content absent
grep -c "OLD_PATTERN" ~/.claude/agents/lucy-AGENTNAME.md
# ^ should return 0
```

### Markdown Structure Convention (from lsd-engineer.md existing sections)

**Source:** `~/.claude/agents/lucy-lsd-engineer.md` §2 "4J Deferral Rule" (lines 195–233) and §1 subsections

**Pattern for new subsections:**
- `### Subsection Name` header
- Prose introduction sentence
- Numbered list for multi-step procedures OR bulleted list for rules
- Code fences for bash/LSD commands
- Bold key terms in prose (e.g., `**CRITICAL:**`, `**Note:**`)

**Pattern for G-gate subsections** (from existing G1/G2/G3 at lines 300–331):
- Bold header: `**GN: Gate Name**`
- When clause in prose
- Code fence for the bash command
- Bulleted if/else logic
- Explicit anchor explanation for grep patterns (to prevent false positives)

---

## No Analog Found

None. Both modified files have exact prior-phase analogs for the edit pattern (Phase 68 Plans 03 and 04 edited these exact files).

---

## JSON Field Confirmation

| Field | Location | Verified Value |
|-------|----------|----------------|
| `validate-inventory --format json` → `inventory.pylsd_mode` | `~/.claude/agents/lucy-devils-advocate.md` §5A routing, lsd-engineer routing block | `true`/`false` boolean — live CLI confirmed (RESEARCH.md) |
| `validate-inventory --format json` → `inventory.deferred_4j` | G4 K-count extraction | Array of objects — live CLI confirmed |
| `lucy pylsd run --format json` → `merged_count` | ITERATION-COMPLETE Block 2 | Integer — `src/lucy_ng/cli/pylsd.py` lines 268–274 confirmed |
| `lucy pylsd run --format json` → `ranked_solutions[].smiles` | ITERATION-COMPLETE Top-3 SMILES | String — confirmed |
| `lucy pylsd run --format json` → `ranked_solutions[].quality` | ITERATION-COMPLETE `top_rank_quality` column | String (`"quality_label"` serialized as `"quality"` at `lsd.py` line 295) — confirmed |
| `run_report.json` → `solutions[].provenance[].perm_index` | Per-permutation defer_set derivation | Integer — `orchestrator.py` lines 385–400 confirmed |
| `run_report.json` → `solutions[].provenance[].active_correlations` | defer_set column formatting | Array of `{atom1, atom2}` dicts — confirmed |

---

## Metadata

**Analog search scope:** `~/.claude/agents/`, `~/.claude/commands/lucy-ng/`, `.planning/phases/68-*/`, `.planning/phases/69-*/`
**Files scanned:** 6 skill files + 8 plan files (read 5 in full or targeted ranges)
**Pattern extraction date:** 2026-05-19
