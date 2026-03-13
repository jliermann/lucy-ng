# Pitfalls Research: pyLSD Integration and 4J HMBC Exploration

**Domain:** Adding pyLSD-based solving and systematic 4J HMBC exploration to existing LSD-based CASE system
**Researched:** 2026-03-13
**Confidence:** HIGH (v7.0 post-mortem + direct LSD/pyLSD documentation + WebCocon 4J research + existing codebase analysis)

---

## Critical Pitfalls

Mistakes that require rewrites, silently produce wrong structures, or break working ibuprofen-free test cases.

### Pitfall 1: ELIM Command Semantics Are Counterintuitive — `ELIM x y` Explores Elimination, Not Bonds

**What goes wrong:**
The ELIM command means "allow LSD to eliminate up to x HMBC correlations that may arise from VLRCs through up to y bonds." The second parameter `y` is NOT the maximum allowed bond count — it is the maximum bond count of correlations that may be ELIMINATED. The HMBC correlation is still interpreted as 2J then 3J; it is discarded entirely (not extended to 4J) if that fails and fewer than x correlations have been dropped.

Concretely:
- `ELIM 1 0` — LSD may ignore up to 1 HMBC correlation with no bond distance restriction. This is how the existing agent uses ELIM as a last resort for over-constrained problems.
- `ELIM 1 4` — LSD may ignore up to 1 correlation that passes through 4 bonds. This is NOT the same as "allow HMBC to be 4J."

The correct syntax for allowing 4J HMBC interpretation is NOT ELIM — it is using `HMBC C H 2 4` (the 4-argument form) which explicitly sets min/max bond range per correlation. ELIM causes correlations to be dropped entirely, not extended.

Using `ELIM 1 4` when you intend "allow this correlation to be 4J" causes the correlation to be silently discarded when it cannot be satisfied as 2J/3J, producing structures that ignore genuine 4J-only connections. Solutions found under ELIM may be valid subsets of the over-constrained problem, but the 4J connectivity is missing — not resolved.

**Why it happens:**
The ELIM command looks like it relaxes bond distance constraints ("through up to y bonds") but it actually controls correlation *elimination* not correlation *extension*. The distinction is invisible in the syntax. ELIM is the existing agent's emergency tool for zero solutions — the obvious next step when you know 4J correlations exist is to raise the ELIM distance parameter. That is the wrong approach.

**How to avoid:**
Use per-correlation explicit bond range syntax for known 4J correlations:
```
HMBC 4 8 2 4    ; C4 to H8, allow 2J-4J (explicit range)
HMBC 6 9 2 3    ; C6 to H9, strict 2J-3J (default range)
```
Reserve `ELIM x 0` for its intended use: when a small number of correlations are suspected to be spectral artifacts or data entry errors (not genuine 4J). The v8.0 design should use explicit per-correlation ranges for 4J candidates, NOT ELIM.

**Warning signs:**
- Agent writes `ELIM 1 4` to "allow 4J" and gets solutions, but solutions lack the expected aromatic ring pattern (4J connectivity was dropped rather than satisfied)
- lsd-engineer skill documentation conflates ELIM's "through y bonds" with explicit bond range syntax
- Solutions pass with ELIM but fail the aromatic ring sanity check (silent 4J correlation loss)

**Phase to address:**
pyLSD integration phase — lsd-engineer knowledge update must distinguish ELIM from per-correlation bond ranges. Add explicit tested examples to agent skill. Document: "ELIM drops correlations entirely. Use `HMBC C H min max` to allow 4J without dropping."

---

### Pitfall 2: FORM Command Specifies Formula Independently of MULT — Mismatch Causes Zero Solutions Without Diagnosis

**What goes wrong:**
pyLSD's FORM command defines the molecular formula of the problem. LSD's MULT commands implicitly define the formula by listing every atom. If FORM specifies `C13H18O2` but the MULT block defines 12 carbons (off-by-one from a typo), pyLSD filters out atom status combinations that don't match FORM — silently producing zero valid LSD input files to run. No LSD run occurs. The agent reports "0 solutions" but the real failure is that pyLSD generated 0 input files before LSD even started.

This is worse than a standard 0-solution outcome because:
- The existing agent diagnostic for 0 solutions (check sp2 parity, H budget, HMBC correctness) is designed for LSD failures, not pyLSD pre-filtering failures.
- Diagnostic iteration will not help: the problem is upstream of LSD in the pyLSD layer.
- LSD stderr will not contain informative output because LSD was never called.

**Why it happens:**
In the current workflow, MULT implicitly defines the formula and there is no FORM command. When migrating to pyLSD, a FORM command is added. If the FORM comes from peak picking (trusted) and MULT comes from agent knowledge (re-derived per iteration), they can diverge. Common divergence points: agent uses FORM formula but adds one extra heteroatom MULT for a hydroxyl oxygen that was already counted; agent updates MULT block in a later iteration but forgets to match FORM.

**How to avoid:**
1. Make FORM the single source of truth and derive MULT atom count validation from it at write time, not at LSD run time. The agent (or a pyLSD input generator) should verify: `sum(MULT carbon atoms) == FORM carbon count` before writing the file.
2. Write a `validate_pylsd_input(content: str) -> list[str]` function that checks FORM vs MULT consistency as part of the pre-run validation gate (currently handled by devils-advocate).
3. Treat pyLSD "0 input files generated" as a distinct error class from LSD "0 solutions" — they require different diagnostic paths.

**Warning signs:**
- pyLSD exits without printing any LSD run output (normally prints "Running LSD file 1/N...")
- 0 solutions with no stderr from LSD process (LSD was never invoked)
- Agent diagnostic focuses on HMBC correctness but FORM/MULT mismatch is the actual cause
- After adding FORM command, first pyLSD run produces 0 solutions on a previously-working LSD file

**Phase to address:**
pyLSD input file generator phase — FORM/MULT consistency check must be part of the LSD input validation function. Add to devils-advocate pre-run checklist: "FORM carbon count matches MULT carbon atom count."

---

### Pitfall 3: Combinatorial Explosion from Ambiguous MULT — pyLSD Can Generate Thousands of LSD Files

**What goes wrong:**
pyLSD's power is generating multiple LSD files for ambiguous atom states. But the number of LSD files grows combinatorially with the number of ambiguous atoms. The Wenk thesis shows this directly:

| Constraint added | LSD files created | Solutions |
|-----------------|-------------------|-----------|
| NMR correlations only | 56,829 LSD files | 1,607,593 |
| + HHB forbidden | still many | reduced |
| + hybridization states | 30 LSD files | 30 |
| + forbidden/mandatory neighbors | 10 LSD files | 10 |

Without hybridization constraints (MULT with explicit sp state), pyLSD generates ALL combinations of sp1/sp2/sp3 for each atom — `56,829 LSD files for Caripyrin`. At 1-2 seconds per LSD run, 56,829 runs = 15+ hours. This happens silently when the MULT block omits explicit hybridization.

For the v8.0 4J exploration approach (run pyLSD once per suspect-4J-excluded combination), even a 2-atom ELIM combination space generates `C(n,2)` combinations. With 5 suspect 4J correlations, that is `C(5,2) = 10` combinations plus individual and all-in runs — manageable. But if hybridization is also ambiguous in any atom, these multiply.

**Why it happens:**
The existing agent uses explicit hybridization in every MULT command (sp2/sp3 always specified). When migrating to pyLSD syntax, if any MULT line is written without explicit hybridization (using pyLSD's ambiguous MULT form), the combinatorial count explodes. The pyLSD documentation shows how to write ambiguous MULT commands — the developer may use them without understanding the scale consequence.

**How to avoid:**
1. Maintain the existing rule: always specify hybridization in MULT. Never use pyLSD's ambiguous MULT form unless you have confirmed the sp state is genuinely unknown AND that the hybridization detector (`lucy detect hybridisation`) was inconclusive.
2. Add a pre-run check: count the number of MULT lines with ambiguous hybridization. If > 0 for the initial run, reject and require explicit states.
3. Cap pyLSD's output: if the count of generated LSD files exceeds 50, abort and diagnose before proceeding.

**Warning signs:**
- pyLSD reports "Generating LSD file N..." where N exceeds 50 on first run
- Agent omits hybridization state from any MULT line "to let pyLSD figure it out"
- Run time exceeds 5 minutes on a molecule with < 25 atoms (normal run: < 60 seconds)
- pyLSD output directory fills with hundreds of `.lsd` intermediate files

**Phase to address:**
pyLSD integration phase — pyLSD wrapper must count generated LSD files and abort if > 50 without explicit user override. Pre-run validation gate must check: all MULT atoms have explicit hybridization.

---

### Pitfall 4: 4J Combination Space Grows Faster Than Expected — Systematic Exclusion Without a Cap Becomes Intractable

**What goes wrong:**
The v8.0 design uses multiple pyLSD runs with different subsets of suspect 4J correlations included/excluded. For `n` suspect 4J correlations, the naive "try all subsets" strategy generates `2^n` runs. For ibuprofen with 3 suspect 4J correlations (`n=3`): 8 combinations — acceptable. For a compound with 6 suspects: 64 combinations — borderline. For 10 suspects: 1024 combinations — each taking 30-60 seconds = hours of runtime.

More subtly, the WebCocon paper documents that allowing unlimited 4J interpretations caused a 1000x increase in calculation time. The pyLSD approach via multiple runs avoids this inside a single LSD call but the explosion reappears at the orchestration level if the combination count is uncapped.

**Why it happens:**
Aromatic natural products commonly have 4-8 HMBC correlations through 4 bonds (ortho, meta, para substitution patterns plus benzylic positions). The heuristic 4J flagging in v6.0 flags aromatic HMBC patterns broadly. If all flagged correlations are systematically explored, the combination count grows quickly. The agent has no cap on how many 4J suspects it creates.

**How to avoid:**
1. Implement a strict cap: maximum 3 suspect 4J correlations explored per run. If nmr-chemist flags more than 3, prioritize by aromatic pattern specificity (W-pathway para-substituted benzene > generic aromatic > borderline).
2. Use a sequential strategy (not exhaustive subset enumeration): first run all suspects excluded, then add back one at a time in order of suspicion. Stop when a run produces solutions that pass the aromatic ring sanity check.
3. Abort after 8 pyLSD runs without a valid solution and escalate to the diagnostic agent.

**Warning signs:**
- nmr-chemist flags > 5 correlations as "suspect 4J"
- Agent plans "try all combinations" without a cap
- CASE-PROGRESS.md shows pyLSD run count > 10 on a single compound
- 4J exploration phase of CASE takes > 15 minutes (wall time)

**Phase to address:**
4J exploration protocol phase — define the cap and strategy before agent integration. The cap must be in the lsd-engineer skill, not just the orchestrator, because lsd-engineer decides which correlations to defer.

---

### Pitfall 5: Migrating Working LSD Files to pyLSD Breaks the Existing CASE Pipeline

**What goes wrong:**
The existing `lucy lsd run` command takes an LSD file and invokes the LSD binary directly via stdin. pyLSD is a different program that wraps LSD. Migrating requires:
1. Writing pyLSD input format (with FORM, PIEC 1, DUPL 1, SHIX) not just LSD input format
2. Invoking pyLSD executable, not the LSD binary
3. Parsing pyLSD's output format (combined solutions from multiple LSD runs, ranked by chemical shift fit)

If the v8.0 migration replaces `lucy lsd run` wholesale with a pyLSD runner, ALL existing LSD functionality — including fragment injection (DEFF/FEXP), constraint inventory, SYME, BOND, LIST/ELEM/PROP — must be verified to work correctly through pyLSD. A single incompatible command in the existing constraint toolkit causes silent zero solutions or outright pyLSD parse errors.

The known migration risk from pyLSD documentation: pyLSD version a5 had a bug where two-letter atomic symbols (Cl, Br) were not accepted in MULT commands. If any test compound has chlorine or bromine atoms, this bug will surface.

**Why it happens:**
LSD and pyLSD share command syntax for the core MULT/HSQC/HMBC/BOND commands but differ in file-level structure (FORM/PIEC required, solution output format differs). The existing LSDRunner assumes stdin-based invocation and stdout/stderr for results. pyLSD outputs to a directory of files and its solution format may differ from the `.sol` format that `outlsd` expects.

**How to avoid:**
1. Run a regression suite on all existing test compounds through pyLSD before replacing `lucy lsd run`. Confirm: ibuprofen.lsd → pyLSD → same solution count as direct LSD.
2. Introduce pyLSD as a SEPARATE runner class (`PyLSDRunner`) that wraps `LSDRunner` and adds FORM/PIEC. Do NOT replace `LSDRunner` — keep the original working for non-4J cases.
3. Verify each constraint type through pyLSD independently: DEFF NOT, DEFF/FEXP, SYME, BOND, LIST/ELEM/PROP, ELIM.
4. Check pyLSD version — v8.0 should require pyLSD-a8 (Python 3 compatible). Earlier versions may have bugs with multi-character atom symbols.

**Warning signs:**
- First pyLSD run on `ibuprofen.lsd` produces a different solution count from direct LSD
- Any command in the existing constraint inventory produces "unknown command" in pyLSD output
- Fragment library DEFF/FEXP injection (validated in v5.0) stops working after pyLSD migration
- `outlsd` fails to parse pyLSD's combined solution output (format differs from single-run LSD `.sol`)

**Phase to address:**
pyLSD runner implementation phase — regression suite (existing LSD test cases run through pyLSD) must be a BLOCKING acceptance criterion before any agent integration.

---

### Pitfall 6: v7.0 Lesson — Calibrate the New Approach Before Building the Full Pipeline

**What goes wrong:**
The v7.0 failure spent multiple development phases (DB schema, generator, detection engine, agent updates) before discovering at calibration that the statistical approach was fundamentally non-viable (100% false positive rate). The failure mode was not a bug — the approach itself did not work. Five phases of work were abandoned.

The v8.0 pyLSD approach must not repeat this pattern. The core hypothesis is: "running pyLSD with 4J suspects excluded will produce solutions, and one of them will pass the aromatic ring sanity check." This hypothesis must be validated on ibuprofen BEFORE building pyLSD infrastructure.

**Why it happens:**
It is tempting to build the clean abstraction first (pyLSD runner, 4J combination explorer, result merger, agent integration) and validate the approach at the end. This is the wrong order. If the pyLSD-based approach also fails (e.g., excluding 4J correlations still produces zero solutions because the remaining 2J/3J correlations are still ambiguous), the entire infrastructure is wasted.

**How to avoid:**
Manual validation first, code second:
1. Run pyLSD manually on ibuprofen.lsd with the 3 suspected 4J correlations (HMBC 4 8, HMBC 6 9, HMBC 8 4) removed from the input.
2. Check: does this produce solutions? Do those solutions include an aromatic ring (verify with `lucy lsd rank` + aromatic ring check)?
3. If YES → hypothesis validated → build infrastructure.
4. If NO → diagnose before committing any code.

This is a 30-minute manual test. It must be Phase 1 of the v8.0 roadmap.

**Warning signs:**
- Roadmap starts with "implement PyLSDRunner" before manual validation test
- First phase is infrastructure, not hypothesis validation
- The approach is justified by "it worked in Sherlock" without direct ibuprofen confirmation

**Phase to address:**
Phase 1 of v8.0 must be: "Validate 4J-removal hypothesis on ibuprofen manually." This is a non-code phase (or a 1-day phase with a single test). Gate the entire roadmap on this result.

---

### Pitfall 7: pyLSD Solution Ranking Uses Its Own NMRShiftDB Algorithm — Conflicts with Existing HOSE-Based Ranker

**What goes wrong:**
pyLSD has a built-in solution ranking algorithm that uses nmrshiftdb2 predictions to rank solutions by chemical shift fit. This is activated via `SHIX` commands (experimental 13C shifts) in the input file. If SHIX is present, pyLSD's ranking overrides the order of solutions in its combined output.

The existing `lucy lsd rank` uses a HOSE-based ranker with:
- Two-tier ranking (match count primary, MAE secondary)
- Per-atom confidence from the 7.9M HOSE statistics database
- Aromatic ring sanity check post-ranking

If pyLSD's ranking is allowed to run, the combined solution file will be pre-sorted by pyLSD's nmrshiftdb ranking, which may differ from the HOSE-based ranking. Using pyLSD's ranking without understanding its algorithm risks the v4.0 failure mode returning: a wrong structure with coincidentally low MAE outranks the correct structure.

**Why it happens:**
SHIX commands are recommended by pyLSD documentation as required for solution ranking. A developer following pyLSD documentation will add SHIX commands and assume pyLSD ranking is correct. The project's existing two-tier ranking exists specifically because naive MAE ranking caused the v4.0 UAT failure (solution analyst hallucinated "rank #1 = ibuprofen" for a 7-membered ring isomer).

**How to avoid:**
Do NOT rely on pyLSD's built-in ranking. Include SHIX commands for documentation purposes (they also control SYME equivalence detection for identical-status atoms) but post-process all solutions from all pyLSD runs through the existing `lucy lsd rank` command with two-tier ranking. pyLSD's ranking output should be explicitly discarded or treated as advisory only.

**Warning signs:**
- Solution analyst references "pyLSD ranking" rather than "HOSE-based ranking" in CASE-PROGRESS.md
- Solutions are processed in pyLSD output order without re-ranking through `lucy lsd rank`
- Aromatic ring sanity check is not run on pyLSD solutions (it was added post-v4.0 specifically for this failure mode)

**Phase to address:**
pyLSD integration phase — specify explicitly in lsd-engineer and solution-analyst skills: "Use `lucy lsd rank` on combined pyLSD solutions. Do not use pyLSD's pre-sorting. Always run aromatic ring sanity check."

---

### Pitfall 8: 4J Heuristic Over-Flags — Agent Defers Too Many Correlations and Misses Correct Structure

**What goes wrong:**
The v6.0 heuristic flags aromatic HMBC correlations broadly as "suspect 4J." If lsd-engineer defers ALL flagged correlations (safe strategy), the problem becomes under-constrained: not enough HMBC correlations to uniquely determine the structure, producing hundreds of solutions. If the agent defers only "high confidence" flags but the 4J signals were genuinely 3J, the over-constrained problem persists.

The WebCocon paper documents the opposite failure: "if actual 4J correlations exist but the 4J-Flag is zero, the process will fail entirely." The danger here is setting 4J-Flag too high (deferring valid 3J correlations), not too low.

**Why it happens:**
W-pathway 4J correlations through aromatic rings are visually indistinguishable from 3J correlations in HMBC spectra. The heuristic (shift range + aromatic neighborhood) cannot distinguish them from genuine 3J correlations without structural knowledge. Without the correct structure, you cannot know which correlations are 4J.

**How to avoid:**
Use a conservative deferral strategy: defer only correlations that satisfy ALL of these criteria simultaneously:
1. Both carbons are in aromatic sp2 shift range (120-145 ppm)
2. The HMBC spectrum shows a well-defined aromatic region
3. The compound has a substituted benzene ring based on HSQC (2+ aromatic CH peaks with quaternary carbons)
4. Zero solutions are obtained when the correlation is included

Never pre-emptively defer correlations without first running with all correlations included. If you have 12 solutions with all correlations, there is no need to investigate 4J.

**Warning signs:**
- Agent defers 4+ correlations before any LSD run
- First LSD run is run with correlations missing (agent didn't run with full set first)
- Solution count explodes to > 100 after deferral (under-constrained)
- CASE-PROGRESS.md shows "4J deferred" but no zero-solution evidence justifying the deferral

**Phase to address:**
4J exploration protocol definition phase — lsd-engineer skill must mandate: "Run with all correlations first. Defer correlations only if zero solutions. Defer minimum number."

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Replace `LSDRunner` directly with `PyLSDRunner` | Single code path | Breaks regression on non-4J compounds; no fallback if pyLSD unavailable | Never — keep both runners |
| Use pyLSD's built-in ranking | No ranking code needed | Two-tier ranking lost; v4.0 MAE-hallucination failure mode returns | Never — always use `lucy lsd rank` |
| Add `FORM` to existing LSD files without validation | Minimal file change | FORM/MULT mismatch causes zero LSD files generated, no diagnostic | Never — validate consistency first |
| Try all 2^n 4J subsets | Complete coverage | Combinatorial explosion for n > 4 | Acceptable only for n ≤ 3 |
| Rely on ELIM for 4J handling | Simple change to existing workflow | Correlations dropped rather than satisfied as 4J; aromatic connectivity silently missing | Never — use per-correlation bond ranges |
| Run full pyLSD without checking generated file count | Simpler orchestration | 10,000+ LSD runs without notice | Never — abort if > 50 generated files |

---

## Integration Gotchas

Common mistakes when connecting pyLSD to the existing CASE system.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| pyLSD executable invocation | Run pyLSD like LSD (`lsd < input.lsd`) | pyLSD is a Python script, not a binary; invoke with `python pylsd.py input.pylsd` or equivalent wrapper |
| Solution file format | Assume pyLSD outputs single `.sol` file like LSD | pyLSD combines solutions from multiple LSD runs; the combined output format may differ from single-run `.sol` — verify `outlsd` compatibility |
| SHIX vs. HOSE ranking | Use pyLSD's SHIX-based ranking as final answer | Run all combined solutions through `lucy lsd rank` with two-tier ranking; treat pyLSD ordering as input, not output |
| DUPL command | Omit DUPL (default behavior) | Default DUPL 2 removes duplicates — may combine identical structures from different LSD runs. Use `DUPL 1` to preserve all solutions before ranking |
| PIEC command | Omit PIEC | Without `PIEC 1`, pyLSD may produce solutions with disconnected fragments. Always include `PIEC 1` |
| Fragment library DEFF/FEXP | Assume DEFF/FEXP works the same in pyLSD | Test DEFF/FEXP through pyLSD on a known compound before assuming it functions identically |
| Constraint inventory across iterations | Rebuild pyLSD-specific lines (FORM, PIEC) from memory each iteration | Treat FORM and PIEC as fixed constants; copy them from previous iteration file like other constraints |

---

## Performance Traps

Patterns that work at small scale but fail with pyLSD's multi-run approach.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Ambiguous MULT hybridization | pyLSD generates 1000+ LSD files silently | Require explicit hybridization in every MULT; abort if generated file count > 50 | Immediately with any ambiguous atom |
| Exhaustive 4J subset search | 2^n combinations for n suspect correlations | Cap at 3 suspects max; use sequential not exhaustive strategy | n > 4 suspects (16+ combinations × 30s = 8+ minutes) |
| Per-run timeout too short | LSD runs hit timeout before finding solutions | pyLSD runs individual LSD files sequentially; each may need up to 60s; total budget = files × 60s | Multi-file runs without cumulative timeout budget |
| No results-merger for combined outlsd parsing | `outlsd` called once on combined `.sol` fails | Merge solutions before calling `outlsd` or call `outlsd` per-run and aggregate SMILES | Always — pyLSD multi-run needs explicit merging |
| Diagnostic iteration continues after pyLSD structural failure | Agent escalates HMBC constraints when FORM/MULT mismatch is the real issue | Add pyLSD-specific pre-diagnostic (check generated file count before LSD run diagnostic) | Zero pyLSD-generated files (FORM/MULT mismatch) |

---

## "Looks Done But Isn't" Checklist

Critical checks that indicate pyLSD integration is genuinely functional vs. appearing to work.

- [ ] **Regression test passes:** `ibuprofen.lsd` through pyLSD produces same solution count as direct LSD (before 4J handling changes). If count differs, pyLSD is changing behavior on known-working files.
- [ ] **FORM/MULT consistency verified:** For every test compound, `sum(MULT carbons) == FORM carbon count`. Failures = FORM/MULT mismatch pitfall.
- [ ] **Aromatic ring check runs on combined output:** After pyLSD 4J exploration, `lucy lsd rank` is called on the combined SMILES, and the aromatic ring sanity check field is present in the JSON output. If missing, v4.0 failure mode is undetected.
- [ ] **Fragment library still works:** After pyLSD migration, DEFF/FEXP goodlist (v5.0 feature) reduces solution count on a test compound. If fragment injection has no effect, pyLSD broke DEFF/FEXP handling.
- [ ] **4J suspect deferral only after zero-solution evidence:** CASE-PROGRESS.md shows: first run included all correlations, zero solutions, THEN 4J deferral. If the first iteration already has deferred correlations, the protocol is inverted.
- [ ] **Generated file count is bounded:** pyLSD run log shows "Generating N LSD files" where N is < 50. If N > 50, combinatorial explosion is occurring.
- [ ] **ELIM is not used for 4J:** No `ELIM` command appears in pyLSD files for 4J handling. ELIM should only appear as a last-resort for suspected spectral artifacts. Per-correlation ranges (`HMBC C H 2 4`) are used for 4J.
- [ ] **Two-tier ranking applied to combined output:** `lucy lsd rank` output shows `matched_count` as the primary sort criterion (not MAE). If solutions are sorted by MAE only, the v4.0 ranking regression has occurred.

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| ELIM used for 4J (correlations silently dropped) | MEDIUM | 1. Identify all LSD files where ELIM was used with 4J intent, 2. Replace ELIM with per-correlation range syntax `HMBC C H 2 4`, 3. Re-run and compare solution count |
| FORM/MULT mismatch (0 pyLSD files) | LOW | 1. Count MULT atoms by element, 2. Compare to FORM string, 3. Fix discrepancy (usually heteroatom double-count), 4. Re-run pyLSD |
| Combinatorial explosion (1000+ LSD files) | LOW | 1. Kill pyLSD, 2. Identify which MULT atoms have ambiguous hybridization, 3. Specify explicit sp state for each, 4. Re-run |
| 4J combination space too large | MEDIUM | 1. Cut suspect list to top-3 by chemical evidence, 2. Switch from exhaustive subset search to sequential, 3. Re-run |
| pyLSD migration broke fragment library | HIGH | 1. Revert to `LSDRunner` for fragment injection, 2. Use pyLSD only for 4J exploration phase, 3. Merge solutions from both runs |
| Solution analyst uses pyLSD ranking instead of HOSE ranking | LOW | 1. Re-run `lucy lsd rank` on combined SMILES file, 2. Update solution-analyst skill with explicit instruction |
| Regression: pyLSD changes behavior on existing cases | HIGH | 1. Identify which commands differ in pyLSD vs. LSD, 2. Maintain `LSDRunner` as fallback, 3. Route non-4J cases through LSDRunner |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| ELIM semantics confusion | pyLSD input format phase — update lsd-engineer skill | Agent uses `HMBC C H 2 4` for 4J, never ELIM for bond extension |
| FORM/MULT mismatch | pyLSD input generator phase — add consistency validator | `validate_pylsd_input()` catches discrepancy before run |
| Combinatorial explosion from ambiguous MULT | pyLSD runner phase — add generated-file count abort | pyLSD wrapper aborts if N > 50 files |
| 4J combination space | 4J exploration protocol phase | Cap defined in lsd-engineer skill; sequential strategy |
| Migration regression | pyLSD runner phase — regression suite | `ibuprofen.lsd` through pyLSD matches direct LSD solution count |
| pyLSD ranking overrides HOSE ranking | Agent integration phase | All runs go through `lucy lsd rank`; aromatic ring check present in output |
| v7.0 recurrence — build before validate | Phase 1 gate | Manual ibuprofen test PASSES before any code is written |
| 4J over-deferral | 4J protocol phase | First iteration always includes all correlations |

---

## v7.0 Lessons Applied

These are directly extracted from the v7.0 post-mortem and mapped to v8.0 risks.

| v7.0 Lesson | v8.0 Risk | Prevention |
|-------------|-----------|------------|
| 100% false positive rate from aggregate statistics | pyLSD multi-run may also fail to find correct structure (different approach, same underlying problem) | Validate on ibuprofen manually before building infrastructure |
| Spent 5 phases building before calibrating | v8.0 could spend phases building pyLSD runner before knowing it works | Phase 1 = manual validation test; gate entire roadmap on result |
| j5_plus dominates regardless of environment — statistics cannot discriminate | Per-correlation HMBC ranges also risk false positives if 4J/3J discrimination is wrong | The 4J identification still relies on heuristics; wrong identification = wrong deferral |
| Schema migration was rolled back entirely | pyLSD integration risks requiring rollback if it breaks existing cases | `PyLSDRunner` is additive (new class), never replaces `LSDRunner` |
| Agent skill updates were written for a detection CLI that turned out non-viable | Agent updates for pyLSD 4J protocol may be written before confirming pyLSD produces correct structures | Agent skill updates come AFTER successful manual test AND regression suite |

---

## Sources

### Primary: Project Post-Mortem
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/milestones/v7.0-ROADMAP.md` — v7.0 failure analysis, 100% false positive rate, pyLSD as next approach
- `/Users/steinbeck/Dropbox/develop/lucy-ng/.planning/PROJECT.md` — v4.0 UAT findings (4J root cause), v3.0 constraint-loss bugs, architecture decisions

### Primary: Project Memory (MEMORY.md)
- v4.0 UAT: all 7 solutions wrong due to 4J HMBC through aromatic ring; solution analyst hallucinated correct answer
- v7.0 abandonment at calibration after full database generation

### Primary: Wenk Thesis
- `background/wenk-thesis.txt` lines 4666-4744 — Caripyrin example showing 56,829 LSD files → 30 files with hybridization constraints. Demonstrates combinatorial explosion risk without explicit sp states.

### Primary: LSD Manual
- [LSD MANUAL_ENG.html](https://nuzillard.github.io/LSD/MANUAL_ENG.html) — ELIM command semantics (HIGH confidence): `ELIM P1 P2` means eliminate up to P1 correlations through up to P2 bonds. DUPL 0/1/2 semantics. SHIX/SHIH documentation.

### Primary: pyLSD Documentation
- [PyLSD official site](https://nuzillard.github.io/PyLSD/) — FORM command, PIEC 1, MULT ambiguous forms, SHIX for ranking, migration path from LSD (MEDIUM confidence: documentation sparse on edge cases)
- [PyLSD HISTORY.html](https://nuzillard.github.io/PyLSD/HISTORY.html) — version history, a5 bug: two-letter atomic symbols (Cl, Br) not accepted in MULT

### Supporting: 4J HMBC Research
- [WebCocon paper: Incorporation of 4J-HMBC and NOE Data (PMC8398166)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398166/) — 4J-Flag semantics, 1000x explosion when unlimited 4J allowed, step-by-step addition strategy (MEDIUM confidence)

### Supporting: lucy-ng Codebase
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/lsd/runner.py` — LSDRunner implementation, outlsd invocation, solution counting
- `/Users/steinbeck/Dropbox/develop/lucy-ng/src/lucy_ng/lsd/cli/lsd.py` — `lucy lsd run` and `lucy lsd rank` CLI (existing pipeline to preserve)
- `/Users/steinbeck/.claude/agents/lucy-lsd-engineer.md` — current ELIM usage (last-resort, not 4J), constraint inventory rules

---
*Pitfalls research for: pyLSD integration and 4J HMBC exploration — v8.0 milestone*
*Researched: 2026-03-13*
