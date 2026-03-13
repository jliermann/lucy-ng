# Feature Landscape: pyLSD Integration and 4J Exploration

**Domain:** pyLSD-based structure generation with systematic 4J HMBC coupling exploration
**Researched:** 2026-03-13
**Confidence:** HIGH — Wenk thesis (Sherlock) provides full pyLSD specification with concrete ibuprofen example; existing codebase provides integration context

---

## Background: What pyLSD Changes and Why It Matters

The current lucy-ng pipeline calls LSD directly. LSD requires fully-specified, unambiguous atom states: one hybridisation state and one proton count per atom. If any ambiguity exists (unknown heteroatom hybridisation, possible 4J vs 3J HMBC coupling), the user must choose one option — and a wrong choice yields zero solutions or wrong structures.

pyLSD removes this limitation by accepting **ambiguous MULT declarations** and internally generating and running multiple LSD files — one per combination of ambiguous atom states. All solutions from all runs are collected into a unified result set. For 4J exploration specifically, this means marking a suspect HMBC correlation as having bond range `2 4` (instead of the default `2 3`) and using ELIM to permit the system to include or exclude it while exploring all valid configurations.

The critical insight from the ibuprofen failure (v4.0 UAT): three HMBC correlations through the aromatic ring are 4J, not 3J. When written as `HMBC X Y` (default 2–3 bonds), LSD enforces them as 2–3J constraints and produces wrong ring systems. The fix is `HMBC X Y 2 4` — but this only works if ELIM is enabled to allow that extended range.

The pyLSD input format differs from LSD in five ways:
1. FORM command declares molecular formula explicitly (LSD uses implicit formula from MULT sum)
2. MULT supports multiple hybridisation states and proton counts: `MULT 14 O (2 3) (0 1)`
3. ELIM command enables elimination of non-standard correlations (required for 4J HMBC)
4. SHIX/SHIH commands assign chemical shift values to atoms, preventing equivalent-atom ambiguity during isomer generation
5. PIEC command declares molecule must be fully connected (always 1)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features the CASE system needs for pyLSD integration to be functional. Missing any of these means the migration from direct LSD to pyLSD does not work.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **pyLSD input file writer** | pyLSD needs a different input format than LSD — FORM, PIEC, ambiguous MULT, SHIX/SHIH, ELIM | MEDIUM | Replaces/extends the existing LSD file writer. Must support all existing commands (MULT, HSQC, HMBC, COSY, BOND, LIST, PROP, DEFF, FEXP) plus the new ones. See ibuprofen example in Appendix A4 of Wenk thesis. CLI: `lucy lsd write-pylsd`. |
| **FORM command generation** | pyLSD requires explicit molecular formula via FORM | LOW | Format: `FORM C 13 H 18 O 2`. Parsed from compound formula string. Not used by direct LSD — verify not written there. This is a pyLSD-only command; existing code must not accidentally include it in LSD files. |
| **PIEC command generation** | pyLSD requires connectivity constraint | LOW | Always `PIEC 1` (fully connected molecule). Written immediately after FORM. |
| **Ambiguous MULT declaration** | Heteroatoms (O, N, S) often have multiple valid hybridisation states and proton counts | MEDIUM | Format: `MULT 14 O (2 3) (0 1)` — hybridisation and proton count are lists in parentheses. For unambiguous carbons, format remains `MULT 1 C 3 3`. pyLSD generates one LSD file per combination: O with (sp2, 0H) + O with (sp2, 1H) + O with (sp3, 0H) + O with (sp3, 1H) = 4 combinations for one oxygen atom. Default values from Wenk thesis Table A16 must be encoded as agent knowledge. |
| **ELIM command generation** | Required to allow HMBC correlations with bond range extending beyond LSD default (>3J) | LOW | Format: `ELIM N M` where N = number of NSCs to eliminate, M = max bond distance allowed. For one suspect 4J correlation: `ELIM 1 4`. For two suspect: `ELIM 2 4`. Must be written ONLY when at least one HMBC has max bond count > 3. Without ELIM, the `2 4` in `HMBC X Y 2 4` is silently ignored by LSD. |
| **SHIX command generation (heavy atoms)** | Prevents pyLSD from treating atoms with identical MULT states as equivalent, which collapses the solution space incorrectly | MEDIUM | Format: `SHIX 1 18.082`. Written for every carbon atom. For heteroatoms with unknown shift, omit. Two atoms with identical MULT but different SHIX values are treated as non-interchangeable during isomer generation. Without SHIX, two CH3 groups at 22.37 and 22.37 ppm are collapsed to one assignment — correct for symmetric molecules, wrong when they differ. |
| **SHIH command generation (protons)** | Same as SHIX but for proton chemical shifts. Prevents proton-level equivalence collapse. | MEDIUM | Format: `SHIH 2 0.896`. Written for every HSQC-assigned proton. Diastereotopic protons get separate SHIH lines. |
| **HMBC extended bond range syntax** | 4J correlations need `HMBC X Y 2 4` instead of default `HMBC X Y` (2–3 bonds) | LOW | Already partially implemented as "possible_4J" flag. Must generate explicit min/max bond parameters. The lsd-engineer agent currently defers 4J correlations — new behavior is to write them with extended range instead. |
| **pyLSD execution wrapper** | Replace `lucy lsd run` with a wrapper that runs pyLSD and collects solutions | MEDIUM | pyLSD internally generates and runs N LSD files, then collects all solutions into one `.smi` file. The lucy CLI wrapper needs to handle pyLSD's output format, which differs from direct LSD. Must detect both success (solutions found) and failure (zero solutions from all runs). |
| **Multi-run solution collection** | pyLSD produces solutions from N LSD runs; all must be merged before ranking | LOW | pyLSD handles this internally — it outputs a single solution file. The wrapper just needs to parse that file correctly. Solutions may be duplicates across runs (same structure found by different atom-state combinations); dedup before ranking. |
| **Agent knowledge: pyLSD file format** | lsd-engineer must write correct pyLSD files, not LSD files | HIGH | The lsd-engineer agent currently knows only LSD syntax. Must learn: FORM replaces implicit formula, PIEC required, MULT can have list arguments, SHIX/SHIH mandatory for non-trivial molecules, ELIM required when any HMBC uses `2 4`. This is a skill/agent update, not Python code. |
| **Constraint inventory: 4J tracking** | Constraint inventory JSON block must track which HMBC correlations are flagged as possible 4J | MEDIUM | New inventory fields: `suspected_4j_hmbcs` (list of C–H pairs), `elim_count` (N in ELIM command). Devils-advocate must verify: if any HMBC written with `2 4`, ELIM must be present with count >= number of such HMBCs. |

### Differentiators (Competitive Advantage)

Features that improve 4J handling beyond minimum viable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multi-file 4J exploration strategy** | When unsure which HMBCs are 4J (the common case), generate multiple pyLSD input files with different HMBC configurations and union the results | HIGH | Strategy: for K suspect HMBC correlations, test 2^K combinations (each suspect either included as 2–3J or excluded/extended to 4J). Union all solution sets. For K=3 (ibuprofen case), this is 8 runs. Wenk thesis §4.3.1 mentions this as planned improvement: "Multiple pyLSD input files with different configurations could be produced and executed." Not yet in Sherlock — lucy-ng could be first to implement. |
| **Atom exchange for grouped signals** | When two atoms share nearly identical shifts (grouped), use HMBC `(C1 C2) H` syntax to allow either atom as the correlation source — handles peak assignment ambiguity without re-running | MEDIUM | Already in pyLSD format: `HMBC (5 6) 7 2 3`. Wenk thesis §4.3.1 confirms this resolved a case where the candidate list was empty without it. Agent currently uses this syntax for grouped atoms (v4.0 bug fixed). Verify it's still working correctly after pyLSD migration. |
| **Aromatic 4J heuristic + extended range** | nmr-chemist heuristic identifies which HMBCs are probably 4J; lsd-engineer writes them with `2 4` instead of deferring them | MEDIUM | Currently (v6.0): nmr-chemist flags, lsd-engineer defers. New behavior: flagged correlations get `2 4` + ELIM rather than being dropped. This is the minimal fix for ibuprofen. Depends on: ELIM command generation, extended HMBC syntax. |
| **PROP constraints from neighbourhood detection** | Statistical neighbour detection produces forbidden/mandatory bonds — these should become PROP constraints in the pyLSD file | MEDIUM | Already detected via `lucy detect neighbours`. Currently only C=O is turned into BOND. PROP generalizes this: `LIST L3 14 15` + `PROP 1 0 L3 -` forbids atom 1 from bonding to anything in L3 (heteroatom list). The ibuprofen example shows systematic PROP usage for all non-O-bearing carbons. This is agent skill knowledge, not Python code. |
| **HETE/PROP heteroatom isolation** | Heteroatom-heteroatom bonds are usually absent in natural products; PROP can forbid them by default | LOW | `HETE L1; hetero atoms` + `PROP L1 0 L1 -; no hetero-hetero bonds`. Already detected by `lucy detect hhb`. Agent must translate the hhb result into HETE/PROP constraints, not just advisory notes. See ibuprofen example lines 5591–5592. |
| **UAT with pyLSD on ibuprofen** | Confirm pyLSD + ELIM + 4J extended range actually finds the correct ibuprofen structure | HIGH | The definitive validation that the approach works. Must produce ibuprofen (or a set containing ibuprofen) as a solution. Expected: 3 HMBCs flagged as 4J, written as `HMBC X Y 2 4`, ELIM 3 4 (or ELIM with appropriate count), SHIX/SHIH for all atoms, correct aromatic ring in top-ranked solution. This is the v4.0 failure case that started this whole track. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Statistical pre-filtering of 4J correlations** | Simpler than running multiple LSD files | v7.0 proved this is fundamentally non-viable: HOSE pair distance statistics produce 100% false positive rate because j5_plus dominates every atom type universally. Cannot distinguish 2J from 4J statistically. | Use pyLSD's ELIM + extended bond range. The constraint solver explores all bond configurations directly — no pre-filtering needed. |
| **Running all 2^K HMBC configurations in parallel** | Faster than sequential exploration | For K=3 suspect correlations, 8 runs is fine. For K=8 (larger molecules), 256 runs may overwhelm the system. Parallelism also complicates solution deduplication and progress tracking. | Run pyLSD once per configuration sequentially; stop early if correct structure found via ranking. Cap K at 4 (max 16 configurations). |
| **Writing LSD files for all molecules** | Some users may prefer direct LSD over pyLSD | pyLSD is a superset of LSD — any valid LSD file is also valid pyLSD input. If all atom states are unambiguous and no ELIM is needed, pyLSD produces exactly one LSD file and runs it. No need to maintain two writers. | Produce pyLSD files always. The format degrades gracefully to LSD behavior when no ambiguity exists. |
| **Exposing pyLSD's internal LSD files to the agent** | Transparency into which LSD files were generated | pyLSD's internal files are temp files, not intended for inspection. Exposing them adds debugging complexity with little benefit for CASE workflow. | Report solution count per run in CASE-PROGRESS.md. If all runs return zero, diagnostic specialist investigates. |
| **Replacing HOSE-based ranking with pyLSD's built-in ranking** | pyLSD can rank solutions internally | pyLSD's built-in ranking is disabled in Sherlock and replaced with HOSE-based prediction (Wenk thesis §3.1.4.2.4). The existing lucy-ng ranking (two-tier: match count + MAE) is better calibrated for this database. | Keep existing `lucy lsd rank`. pyLSD provides solutions; lucy-ng ranks them. |
| **Using ELIM for all HMBC correlations by default** | ELIM allows "invalid" correlations to be pruned, which seems useful as a general tool | ELIM is specifically for correlations that extend BEYOND LSD's default bond limits. Using it on normal 2–3J correlations does nothing useful but may mislead the agent into thinking those correlations are questionable. | Apply ELIM only when at least one HMBC has max bond distance > 3. Track this explicitly in the ELIM count (N in `ELIM N M`). |

---

## Feature Dependencies

```
pyLSD input file writer
    └── requires --> FORM command generation [NEW]
    └── requires --> PIEC command generation [NEW]
    └── requires --> Ambiguous MULT syntax [NEW]
    └── requires --> SHIX/SHIH generation [NEW]
    └── requires --> ELIM command generation [NEW]
    └── requires --> Extended HMBC bond range syntax [NEW — builds on existing `2 4` flag]
    └── replaces --> Existing LSD file writer [EXISTING]

ELIM command generation
    └── requires --> HMBC extended bond range syntax [NEW — must know which HMBCs need 2 4]
    └── requires --> nmr-chemist 4J flagging [EXISTING — v6.0 heuristic]

pyLSD execution wrapper
    └── requires --> pyLSD installed on system [EXISTING requirement, same as LSD]
    └── requires --> pyLSD input file writer [NEW]
    └── replaces --> lucy lsd run [EXISTING]
    └── produces --> unified solution file (same format as direct LSD)

Agent knowledge: pyLSD file format
    └── requires --> pyLSD input file writer [NEW — must know what to request]
    └── requires --> lsd-engineer skill update [NEW]
    └── enhances --> Constraint inventory: 4J tracking [NEW, below]

Constraint inventory: 4J tracking
    └── requires --> Existing constraint inventory JSON block [EXISTING — v4.0]
    └── requires --> Agent knowledge: pyLSD file format [NEW, above]
    └── enhances --> Devils-advocate verification [EXISTING]

Multi-file 4J exploration
    └── requires --> pyLSD input file writer [NEW]
    └── requires --> pyLSD execution wrapper [NEW]
    └── requires --> nmr-chemist 4J flagging [EXISTING — v6.0 heuristic]
    └── requires --> Coordinator multi-run orchestration [NEW agent skill]
    └── enhances --> aromatic ring sanity check [EXISTING — v4.0]

PROP constraints from neighbourhood detection
    └── requires --> lucy detect neighbours [EXISTING — v3.0]
    └── requires --> Agent knowledge: pyLSD file format (LIST/PROP syntax) [NEW]
    └── requires --> lsd-engineer skill update [NEW]
    └── enhances --> Solution quality (fewer wrong candidates)

UAT: ibuprofen with pyLSD
    └── requires --> pyLSD input file writer [NEW]
    └── requires --> ELIM + extended HMBC [NEW]
    └── requires --> SHIX/SHIH [NEW]
    └── requires --> Agent knowledge update [NEW]
    └── validates --> All table stakes features above
```

### Dependency Notes

- **ELIM requires knowing which HMBCs are 4J:** The count N in `ELIM N M` equals the number of HMBC lines with max bond distance > 3. The lsd-engineer must count these when constructing the ELIM line, not guess. If N is wrong (too low), some extended-range correlations are silently treated as standard correlations.
- **SHIX/SHIH are required for correct isomer enumeration:** Without them, pyLSD treats all CH3 groups with the same MULT as interchangeable, which can collapse real structural distinctions. For the ibuprofen case: two CH3 groups at 22.37 ppm ARE equivalent (the isobutyl CH3s) — but they must still have SHIH/SHIX lines so pyLSD correctly handles their cross-assignment.
- **Multi-file 4J exploration depends on the coordinator:** The coordinator (case.md orchestrator) must decide how many pyLSD runs to execute and which HMBC configurations to try. This is new orchestration logic that does not exist in any current agent.
- **PROP constraints are a skill update, not Python code:** The LIST/PROP generation from `lucy detect neighbours` output is agent reasoning — the agent reads the JSON output and decides which atoms go in which lists. No new CLI commands needed.

---

## MVP Definition

### Launch With (v8.0 core)

Minimum viable feature set to unblock ibuprofen CASE and validate pyLSD approach.

- [ ] **pyLSD input file writer** — Without this, nothing else works. Must produce correct FORM, PIEC, MULT, SHIX, SHIH, HSQC, HMBC (with explicit bond range), COSY, BOND, LIST, PROP, DEFF, FEXP, ELIM.
- [ ] **ELIM command generation** — Required for any HMBC correlation extended beyond 3J. Count = number of extended-range HMBCs in the file.
- [ ] **SHIX/SHIH generation** — Required for correct isomer enumeration. All carbons get SHIX; all HSQC-assigned protons get SHIH.
- [ ] **pyLSD execution wrapper** — Replace `lucy lsd run` or provide `lucy lsd run-pylsd`. Must collect solutions from pyLSD's unified output.
- [ ] **Agent knowledge: pyLSD file format** — lsd-engineer must know the full syntax. Update agent skill with FORM, PIEC, ambiguous MULT, SHIX/SHIH, ELIM, extended HMBC. This is the highest-leverage update: one skill change enables all the above.
- [ ] **Constraint inventory: 4J tracking** — Add `suspected_4j_hmbcs` and `elim_count` to JSON block. Devils-advocate verifies ELIM present when extended HMBCs exist.
- [ ] **UAT: ibuprofen with pyLSD** — Confirm correct structure found. Accept as milestone-complete only when ibuprofen is top-ranked solution.

### Add After Validation (v8.x)

- [ ] **PROP constraints from neighbourhood detection** — Trigger: ibuprofen solved, multi-compound UAT still fails on heteroatom-heavy compounds.
- [ ] **HETE/PROP for heteroatom isolation** — Trigger: UAT compounds with O-O or O-N bonds being incorrectly proposed.
- [ ] **Multi-file 4J exploration** — Trigger: cases where nmr-chemist cannot determine which HMBCs are 4J (uncertainty > 1 candidate).
- [ ] **Atom exchange for grouped signals** — Trigger: cases where peak grouping causes empty solution set; existing grouped HMBC syntax may already handle this.

### Future Consideration (v9+)

- [ ] **Multi-fragment injection + pyLSD** — Combine fragment library with pyLSD's ambiguous atom handling. Not blocking anything in v8.
- [ ] **Multi-compound UAT** — Six test compounds have 4J risk. After ibuprofen confirmed working, run all six.
- [ ] **Parallel multi-run execution** — Subprocess pool for 2^K configurations. Only needed for K > 4 (>16 runs).

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| pyLSD input file writer | HIGH | MEDIUM | P1 — foundation |
| ELIM command generation | HIGH | LOW | P1 — unblocks 4J |
| SHIX/SHIH generation | HIGH | LOW | P1 — required by format |
| pyLSD execution wrapper | HIGH | MEDIUM | P1 — replaces direct LSD |
| Agent knowledge: pyLSD format | HIGH | MEDIUM | P1 — lsd-engineer must know this |
| Constraint inventory: 4J tracking | HIGH | LOW | P1 — DA gate |
| UAT: ibuprofen with pyLSD | HIGH | LOW | P1 — validation |
| PROP from neighbourhood detection | MEDIUM | LOW | P2 — quality improvement |
| HETE/PROP heteroatom isolation | MEDIUM | LOW | P2 — reduces wrong candidates |
| Atom exchange for grouped signals | MEDIUM | LOW | P2 — edge case |
| Multi-file 4J exploration | HIGH | HIGH | P2 — powerful but complex |
| Parallel multi-run execution | LOW | MEDIUM | P3 — performance only |

**Priority key:**
- P1: Must have for v8.0 launch — unblocks ibuprofen CASE
- P2: Should have, add when core is validated
- P3: Nice to have, defer to v9+

---

## Concrete Format Reference

### pyLSD File Differences from Direct LSD

| Aspect | Direct LSD | pyLSD |
|--------|-----------|-------|
| Molecular formula | Implicit (sum of MULT atoms) | `FORM C 13 H 18 O 2` (explicit, first command) |
| Connectivity | Not declared | `PIEC 1` (always present) |
| Atom state | `MULT 1 C 3 3` (single value each) | `MULT 14 O (2 3) (0 1)` (list allowed) |
| Shift assignment | Not used | `SHIX 1 18.082` (heavy atom), `SHIH 2 0.896` (proton) |
| Extended correlations | Not supported | `ELIM 1 4` enables; `HMBC X Y 2 4` uses |
| Multiple runs | One LSD run | N runs (one per ambiguous state combo) |
| Output | `.sol` binary, convert with `outlsd` | Unified SMILES output (pyLSD handles conversion) |

### ELIM Semantics (from Wenk thesis §3.1.4.2.3)

`ELIM N M` means: "allow elimination of N correlations that have bond distance up to M." The two parameters are:
- N: maximum number of extended-range correlations the solver is allowed to treat as invalid
- M: maximum bond distance for those correlations (4 for 4J exploration)

Critical rule: ELIM only activates for HMBC/COSY lines where the declared max bond distance exceeds LSD defaults (>3 for HMBC, >4 for COSY). A standard `HMBC X Y` (no bond range) is never eligible for elimination.

For ibuprofen with 3 suspect 4J correlations: `ELIM 3 4`. This permits pyLSD to explore configurations where 0, 1, 2, or 3 of the suspect correlations are treated as too long to be valid.

### Ambiguous MULT for Common Heteroatoms (Wenk thesis Table A16)

| Atom | Possible Valencies | Possible Hybridisations | Possible H Counts |
|------|--------------------|------------------------|-------------------|
| O (unknown) | 2 | sp2, sp3 | 0, 1 |
| O (known carbonyl) | 2 | sp2 | 0 |
| O (known ether/hydroxyl) | 2 | sp3 | 0, 1 |
| N (unknown) | 3, 5 | sp1, sp2, sp3 | 0, 1, 2, 3 |
| C (sp2, quaternary) | 4 | sp2 | 0 |
| C (sp3, CH3) | 4 | sp3 | 3 |

---

## 4J Exploration Strategy (Concrete)

The problem: agent has a list of HMBC correlations where some are flagged as "possibly 4J" by nmr-chemist. The agent must decide how to handle them.

**Recommended strategy for v8.0 (minimal):**
1. nmr-chemist identifies suspect 4J correlations (aromatic W-pathway pattern, currently heuristic)
2. lsd-engineer writes them as `HMBC X Y 2 4` (extended range) instead of standard `HMBC X Y`
3. lsd-engineer counts N = number of extended HMBCs, writes `ELIM N 4`
4. Run once with pyLSD — the solver explores all valid bond distance configurations internally
5. If solutions include correct structure, done. If zero solutions, diagnostic specialist investigates.

**Extended strategy for v8.x (multi-file):**
For K suspect correlations where confidence is low:
1. Generate K+1 pyLSD input files: base file (all K as standard 2–3J) + one file per suspect excluded
2. Run each file separately, collect solution sets
3. Union all solutions, deduplicate by SMILES, re-rank by HOSE prediction
4. Report combined solution set to solution-analyst

The multi-file strategy is the approach Wenk thesis describes as "planned improvement" — it is not yet in Sherlock (as of thesis writing). Lucy-ng implementing it would exceed Sherlock's current capability.

---

## Competitor Feature Analysis

| Feature | Sherlock | Lucy-ng v6.0 (current) | Lucy-ng v8.0 (target) |
|---------|----------|------------------------|------------------------|
| pyLSD integration | Yes — primary solver | No — direct LSD only | Yes — primary solver |
| Ambiguous atom states (MULT lists) | Yes | No | Yes |
| ELIM for 4J exploration | Yes | No | Yes |
| SHIX/SHIH for atom differentiation | Yes — used always | No | Yes |
| FORM/PIEC commands | Yes | No | Yes |
| Multi-run for ambiguous states | Yes — automatic via pyLSD | No | Yes — via pyLSD |
| Multi-file 4J configurations | Partial (test impl.) | No | Planned (v8.x) |
| Autonomous 4J detection | No (heuristic only) | Heuristic (v6.0) | Heuristic + solver-based |
| PROP from neighbourhood stats | Yes | No (advisory only) | Yes (v8.x) |

---

## Sources

**HIGH confidence (authoritative):**
- Wenk, M. (2023). *Development of a System for Computer-Assisted Structure Elucidation of Small Organic Compounds.* PhD Thesis. (`background/wenk-thesis.txt` lines 2069–2268, 4640–4664, 5491–5625) — Complete pyLSD command reference, ibuprofen example, atom exchange feature, ELIM semantics, default heteroatom MULT values.
- `.planning/PROJECT.md` — v8.0 milestone definition, deferred features, v7.0 post-mortem (statistical 4J abandoned).
- `.planning/research/FEATURES.md` (v5.0) — Fragment library features; pattern for this document.
- Memory: v4.0 UAT findings — concrete 4J failure analysis for ibuprofen (three 4J HMBC correlations identified: C4a↔C6, C5a↔C7, with atom indices documented).

**MEDIUM confidence:**
- Wenk thesis §4.3.1 on atom exchange / multi-file approach: "Casekit and Sherlock already have a test implementation" — not yet in production. Confidence MEDIUM because exact behavior of test implementation is not described in detail.

---

*Feature research for: v8.0 pyLSD Integration and 4J Exploration*
*Researched: 2026-03-13*
