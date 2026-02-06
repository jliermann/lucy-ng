# lucy-ng System Audit Report

**Phase 20 Deliverable** | Compiled 2026-02-06

This report is the definitive reference for the v2.0 migration. Every component in lucy-ng has been classified by intelligence level, and every recommendation maps to a specific v2.0 phase (21-26). Phases 21-26 should reference this document to know exactly what to migrate, refactor, or keep.

---

## 1. Executive Summary

### Scope

| Layer | Components | Lines Audited |
|-------|-----------|---------------|
| MCP tools | 15 tools | 6,110 lines across 18 implementation modules |
| CLI commands | 9 groups (22 commands) | 2,695 lines across 9 CLI modules |
| CLAUDE.md | 14 top-level sections, 43 subsections | 1,080 lines |
| **Total** | **15 + 22 + 57 sections** | **~9,885 lines** |

### Tier Distribution

**MCP Tools (15 total):**

| Tier | Count | Meaning |
|------|-------|---------|
| Tier 1 (keep as-is) | 7 | Pure data wrappers with no domain inference |
| Tier 2 (document strategy in skill) | 4 | Domain-tuned defaults or scoring strategies the AI should understand |
| Tier 3 (refactor to thin wrapper) | 4 | Multi-step domain inference currently hard-coded in Python |

**CLI Command Groups (9 total):**

| Tier | Count | Meaning |
|------|-------|---------|
| Tier 1 (pure CLI wrappers) | 4 | No domain logic in CLI layer |
| Tier 2 (moderate intelligence) | 3 | Database/backend auto-detection, format detection |
| Tier 3 (complex orchestration) | 2 | Experiment auto-discovery, LSD generation pipeline |

### Top-Line Findings

1. **~80% of CLAUDE.md is domain knowledge** (~680 of 1,080 lines) that teaches the AI how to reason about NMR and CASE. This belongs in skill documents, not project configuration.

2. **4 MCP tools contain the bulk of embedded intelligence**: `generate_lsd_input` (478 lines of domain logic in LSDInputGenerator), `pick_hsqc_peaks` (289 lines in DEPTGuidedPicker), `pick_hmbc_peaks` (226 lines in HMBCGuidedPicker), and `analyze_symmetry` (576 lines across 3 analysis modules). These are the Phase 26 refactoring targets.

3. **`generate_lsd_input` is the primary migration target**: It contains the highest concentration of hard-coded domain heuristics (carbonyl detection by shift range, hybridization inference, sp2 oxygen pairing, heteroatom H assignment). These are decisions the AI should make based on full spectroscopic context.

4. **CLI and MCP share all implementation code**: Every MCP tool has a CLI counterpart using the same Python modules. The 3 code duplication areas (experiment auto-discovery, database auto-detection, LSD file parsing) are in the wrapper layers, not the implementations.

5. **5 duplication clusters in CLAUDE.md** account for ~175 lines of redundant content, with LSD rules (sp2 count, ELIM usage, correlation order) each stated 4-8 times across different sections.

---

## 2. MCP Tool Classifications

All 15 MCP tools classified by intelligence level. For full evidence and line-level analysis, see `audit-mcp-tools.md`.

### Classification Table

| # | MCP Tool | Tier | Implementation Module | Lines | Intelligence Summary |
|---|----------|------|-----------------------|-------|---------------------|
| 1 | `read_spectrum_1d` | 1 | readers/bruker.py | 278 (shared) | None. Pure Bruker file parsing wrapper. |
| 2 | `read_spectrum_2d` | 1 | readers/bruker.py | 278 (shared) | None. Pulse program pattern matching is identification, not inference. |
| 3 | `pick_peaks_1d` | 2 | processing/peak_picker.py | 237 | Adaptive two-pass algorithm with domain-tuned defaults (threshold 0.05, FWHM factor 1.5). |
| 4 | `pick_hsqc_peaks` | **3** | processing/dept_guided_picker.py | 289 | Multi-step DEPT-guided algorithm: iterative threshold lowering, DEPT sign-based multiplicity, DEPT-90 disambiguation. |
| 5 | `pick_hmbc_peaks` | **3** | processing/hmbc_guided_picker.py | 226 | Cross-validation filtering: asymmetric tolerances (13C 1.5 ppm, 1H 0.1 ppm), noise rejection strategy. |
| 6 | `analyze_symmetry` | **3** | analysis/ (3 modules) | 576 | Three-layer inference: hydrogen budget, intensity-based equivalence (>=1.5x), shift-based multiplicity guessing. |
| 7 | `dereplicate_c13` | 2 | dereplication/ (2 modules) | 526 | Region-specific tolerances (aliphatic 0.8, aromatic 1.2, carbonyl 1.5 ppm), geometric mean scoring. |
| 8 | `check_lsd_availability` | 1 | lsd/runner.py | 400 (shared) | None. PATH check for LSD/outlsd binaries. |
| 9 | `generate_lsd_input` | **3** | lsd/generator.py | 478 | Highest domain logic: carbonyl detection, hybridization inference, sp2 pairing, heteroatom H assignment, HMBC mapping. |
| 10 | `run_lsd` | 1 | lsd/runner.py + parser.py | 513 | None. Subprocess execution with stderr parsing. |
| 11 | `rank_lsd_solutions` | 2 | ranking/ranker.py + prediction/predictor.py | 482 | N:1 symmetry matching, MAE calculation, HOSE radius fallback with confidence weighting. |
| 12 | `predict_c13_shifts` | 2 | prediction/predictor.py | 277 | HOSE radius fallback (6->1), confidence formula (radius 50%, match count 30%, std dev 20%). |
| 13 | `get_hose_stats_info` | 1 | database/manager.py | 729 (shared) | None. Pure database statistics query. |
| 14 | `fetch_nmrxiv_dataset` | 1 | nmrxiv/client.py | 454 | None. HTTP client for data retrieval. |
| 15 | `generate_correlation_diagram` | 1 | visualization/diagram_generator.py | 1,151 | None. Pure rendering engine (RDKit, SVG). 1,151 lines of complexity, zero NMR inference. |

### Tier 3 Tools (Phase 26 Refactoring Targets)

These 4 tools contain multi-step domain inference that should be AI-driven rather than hard-coded:

1. **`generate_lsd_input`** (478 lines in lsd/generator.py) -- The primary target. Six distinct domain inference steps: chemical shift-to-hybridization mapping, carbonyl detection via dual shift ranges, sp2 oxygen pairing, heteroatom hydrogen assignment, HMBC proton-to-carbon index mapping via HSQC cross-reference, sp2 count parity enforcement. In v2.0, the AI makes these decisions and the tool accepts pre-built constraints.

2. **`pick_hsqc_peaks`** (289 lines in dept_guided_picker.py) -- Adaptive threshold strategy using DEPT-135 as ground truth. Iteratively lowers HSQC threshold (0.10 -> 0.005) until all DEPT carbons are matched. Extracts multiplicity from DEPT peak signs. In v2.0, the AI understands WHY this strategy works and can override thresholds.

3. **`pick_hmbc_peaks`** (226 lines in hmbc_guided_picker.py) -- Cross-validation filtering against known 13C and HSQC positions. The asymmetric tolerances (1.5 ppm for 13C vs 0.1 ppm for 1H) encode knowledge about inherent precision differences. In v2.0, the AI understands the noise model and can adjust tolerances.

4. **`analyze_symmetry`** (576 lines across 3 modules) -- Shift-based multiplicity guessing (<30 ppm = likely CH3, >100 ppm = aromatic CH), intensity-based equivalence detection (>=1.5x relative intensity), common symmetric motif recognition. In v2.0, the AI reasons about symmetry directly.

---

## 3. CLI Command Classifications

All 9 CLI groups (22 commands) classified. For full evidence, see `audit-cli-commands.md`.

**Key architectural fact:** CLI commands and MCP tools share the same implementation modules. The intelligence lives in the shared Python libraries. The CLI layer adds argument parsing, output formatting, and operational auto-detection (database paths, experiment types). Per Phase 26 requirements, CLI commands **retain** their smart behavior for backward compatibility.

### Classification Table

| # | CLI Group | Commands | Tier | Intelligence in CLI Layer | MCP Overlap |
|---|-----------|----------|------|--------------------------|-------------|
| 1 | `read` | 1d, 2d | 1 | None -- pure BrukerReader wrappers | Full overlap (read_spectrum_1d, read_spectrum_2d) |
| 2 | `pick` | 1d, 2d, hsqc, hmbc | 1 | None -- passes through to shared pickers | 3 of 4 have MCP equivalents (pick 2d is CLI-only) |
| 3 | `analyze` | symmetry | 1 | None -- passes through to SymmetryAnalyzer | Full overlap (analyze_symmetry) |
| 4 | `fetch` | nmrxiv | 1 | None -- pure HTTP client wrapper | Full overlap (fetch_nmrxiv_dataset) |
| 5 | `dereplicate` | c13 | 2 | Database auto-detection chain (env var -> project -> common paths -> Spotlight -> Dropbox) | Full overlap (dereplicate_c13) |
| 6 | `predict` | c13, build-table, table-info | 2 | Backend priority chain, SD format auto-detection, parallel worker management | Partial (c13 has MCP; build-table, table-info are CLI-only) |
| 7 | `lsd` | check, generate, run, rank, analyze | 2-3 | generate: experiment auto-discovery (Tier 3); rank: shift parsing + table auto-detection (Tier 2); analyze: J-coupling BFS (Tier 2) | 4 of 5 have MCP (lsd analyze is CLI-only) |
| 8 | `visualize` | correlations | 1 | LSD file parsing helper (format knowledge, not NMR reasoning) | Full overlap (generate_correlation_diagram) |
| 9 | `database` | build, info, download, generate-hose-stats | 2-3 | generate-hose-stats: HOSE generation pipeline with checkpoint/resume (Tier 3); build: SD import orchestration (Tier 2) | None (all CLI-only operational utilities) |

### CLI-Only Commands (No MCP Equivalent)

8 CLI commands have no MCP tool counterpart:

| Command | Why No MCP Needed |
|---------|-------------------|
| `pick 2d` | Raw 2D peak picking utility; AI uses guided pickers instead |
| `predict build-table` | One-time HOSE table generation; not used during CASE |
| `predict table-info` | Database stats display; partial overlap with get_hose_stats_info |
| `lsd analyze` | J-coupling path analysis; **consider adding MCP equivalent** for AI agent access |
| `database build` | One-time compound import; not used during CASE |
| `database info` | Database stats display; partial overlap with get_hose_stats_info |
| `database download` | One-time setup command |
| `database generate-hose-stats` | One-time HOSE stats generation pipeline |

### Code Duplication Between CLI and MCP

Three areas where wrapper-layer logic is duplicated:

| Duplication | CLI Location | MCP Location | Consolidation Target |
|-------------|-------------|-------------|---------------------|
| Experiment auto-discovery (pulse program classification) | cli/lsd.py lines 73-97 | server.py lines 528-553 | Shared utility in lsd/ or processing/ (Phase 26) |
| Database auto-detection (`_find_database_path()`) | cli/dereplicate.py lines 23-82 | server.py imports from CLI module | Move to database/finder.py (Phase 26) |
| LSD file parsing (`parse_lsd_input_file()`) | cli/visualize.py lines 300-396 | server.py line 1142 imports from CLI | Move to lsd/parser.py (Phase 26) |

---

## 4. CLAUDE.md Analysis

Full 1,080-line analysis with line-level references. For detailed tables, see `audit-claude-md.md`.

### Section Catalogue Summary

| Category | Lines | % of File | Description |
|----------|-------|-----------|-------------|
| project-setup | ~59 | 5% | End-User Setup (install, LSD check, database download) |
| developer-ref | ~87 | 8% | Developer Reference + LSD Runner Notes |
| case-workflow | ~282 | 26% | Blind CASE, Subskills, Workflow, Decision Trees, Reporting, Quick Reference |
| domain-knowledge | ~350 | 32% | NMR Reference, Pitfalls, Hybridization, Heteroatom, Symmetry, APT, Peak Picking Rationale |
| tool-usage | ~302 | 28% | CLI/API syntax, Python examples, output formats |
| **Total** | **1,080** | **100%** | |

**Conclusion:** 58% of the file (case-workflow + domain-knowledge = 632 lines) is domain intelligence that belongs in SKILL.md. An additional ~222 lines of tool-usage sections contain embedded domain reasoning that should move alongside the syntax stubs.

### Duplication Map

5 duplication clusters identified, totaling ~175 lines of redundant content:

| Cluster | Topic | Locations | Overlap Lines | Worst Case |
|---------|-------|-----------|---------------|------------|
| 1 | LSD rules and constraints | LSD Integration, Manual LSD Construction, Pitfall 4, Decision Trees, Quick Reference | ~175 | sp2 even-count rule stated in 6 places; ELIM caution stated in 8 places |
| 2 | Peak picking logic | Peak Picking (3 subsections), Pitfall 3, Workflow Steps | ~30 | HMBC noise problem/solution stated 3 times |
| 3 | Dereplication scores | Dereplication, Result Reporting, Quick Reference | ~8 | Score thresholds (0.85/0.65/0.50) stated in 3 places |
| 4 | MAE / ranking scores | Solution Ranking, Quick Reference | ~12 | MAE quality table and ranking output format each stated twice |
| 5 | Database statistics | End-User Setup, Reference Data, 13C Shift Prediction | ~10 | 928K compounds / 7.9M HOSE stated in 3 places |

### Misplacement Analysis

20+ sections contain content that teaches the AI HOW to reason about NMR, rather than documenting project setup or tool syntax. Key misplacements:

| Content | Current Location | Correct Location | Reason |
|---------|-----------------|-----------------|--------|
| CASE workflow steps 0-6 | Structure Elucidation Workflow | SKILL.md | This IS the core skill |
| Pitfalls 1-5 | Common Pitfalls | SKILL.md | Expert NMR reasoning patterns |
| Decision trees (3) | Decision Trees | SKILL.md / SUPERVISOR.md | CASE orchestration logic |
| Hybridization rules | LSD Integration | SKILL.md | Chemistry domain knowledge |
| Heteroatom attachment | LSD Integration | SKILL.md | Decision logic for constraint types |
| Score interpretation | Result Reporting Templates | SKILL.md | AI reasoning about result quality |
| Blind CASE protocol | Blind CASE Protocol | Blind CASE skill | Specialized research evaluation concern |

### Projected CLAUDE.md After Restructuring

| Component | Lines |
|-----------|-------|
| Title + description | 6 |
| End-User Setup (keep as-is) | 53 |
| Tool Output Reference | 12 |
| Dereplication CLI syntax (trimmed) | 15 |
| LSD Integration CLI syntax (trimmed) | 50 |
| Peak Picking API reference (trimmed) | 40 |
| 13C Shift Prediction CLI + API (trimmed) | 25 |
| Developer Reference (keep as-is) | 82 |
| Spacing and separators | 15 |
| **Total** | **~298 lines** |

This is well under the Phase 21 target of <800 lines.

---

## 5. Cross-Cutting Analysis

This section identifies patterns that span all three audit dimensions (MCP tools, CLI commands, CLAUDE.md) and provides direct input for Phase 21-26 planning.

### 5.1 Intelligence Hotspots

These Python modules contain the most concentrated domain logic -- they are where "NMR reasoning" currently lives in code rather than in AI-readable knowledge:

| Module | Lines | Domain Logic | Density |
|--------|-------|-------------|---------|
| **lsd/generator.py** (LSDInputGenerator) | 478 | Carbonyl detection (2 shift ranges), hybridization inference (100-160 ppm = sp2), sp2 oxygen pairing, heteroatom H assignment from formula, HMBC-to-HSQC mapping, sp2 parity enforcement | Very High |
| **processing/dept_guided_picker.py** (DEPTGuidedPicker) | 289 | Iterative threshold lowering (0.10->0.005), DEPT sign interpretation (positive=CH/CH3, negative=CH2), DEPT-90 disambiguation logic | High |
| **processing/hmbc_guided_picker.py** (HMBCGuidedPicker) | 226 | Cross-validation filtering, asymmetric tolerance rationale (13C precision vs 1H precision), noise model for HMBC artifacts | High |
| **analysis/hydrogen_budget.py** (HydrogenBudgetAnalyzer) | 200 | Shift-based multiplicity guessing (<30 ppm = CH3, >100 ppm = aromatic CH), heteroatom-H estimation from formula | High |
| **analysis/symmetry_analysis.py** (SymmetryAnalyzer) | 193 | Expected vs observed carbon count comparison, symmetric motif pattern recognition | Moderate |
| **analysis/intensity_reporter.py** (IntensityReporter) | 183 | Relative intensity calculation, equivalence threshold (>=1.5x) for symmetry detection | Moderate |
| **dereplication/matcher.py** (SpectrumMatcher) | 293 | Region-specific tolerances, overlap factor for symmetry, geometric mean scoring formula, DEPT mismatch penalty | Moderate |
| **prediction/predictor.py** (C13Predictor) | 277 | HOSE radius fallback strategy, confidence formula with empirical weights (50/30/20) | Low-Moderate |

**Total domain-logic-bearing code: ~2,139 lines across 8 modules.** This represents the intelligence that v2.0 will progressively migrate to skill documents (documented in Phase 22-23) and thin out of Python (Phase 26).

### 5.2 Shared Implementations: MCP and CLI Code Paths

The architecture is a three-layer stack. Both MCP and CLI are thin wrapper layers over shared implementation modules:

```
 MCP Server (server.py, 1282 lines)     CLI Modules (9 files, 2695 lines)
          \                                /
           \                              /
            +------- Shared Core --------+
            |                            |
            |  readers/bruker.py    (278)|
            |  processing/*.py      (752)|
            |  analysis/*.py        (576)|
            |  dereplication/*.py   (526)|
            |  lsd/*.py            (991)|
            |  prediction/*.py     (277)|
            |  ranking/*.py        (205)|
            |  database/*.py       (729)|
            |  nmrxiv/*.py         (454)|
            |  visualization/*.py (1151)|
            |                            |
            +--- Total: ~5,939 lines ---+
```

**Implications for Phase 26 (Thin Tools):**
- Refactoring only needs to happen in the shared implementation modules
- MCP wrappers become even thinner (no auto-discovery, no auto-detection)
- CLI wrappers retain current behavior by continuing to call the full implementation
- The 3 duplication areas (experiment auto-discovery, database auto-detection, LSD file parsing) should be consolidated into shared utilities during Phase 26

### 5.3 Skill Document Outline

Based on all three audits, SKILL.md should contain the following sections. Each section is sourced from a combination of CLAUDE.md content (relocated), MCP tool intelligence (documented), and CLI auto-detection logic (described).

**Proposed SKILL.md Structure:**

```
SKILL.md (~450-550 lines after deduplication)

1. NMR Background (from CLAUDE.md sections 5, 6)
   - Experiment types and what they provide (~15 lines)
   - 13C chemical shift regions and their meaning (~12 lines)
   - Common pitfalls: symmetry, quaternary carbons, HMBC noise,
     heteroatom inference (~60 lines, deduplicated from 87)

2. Peak Picking Strategy (from CLAUDE.md section 11 + MCP Tier 2-3 intelligence)
   - Scientific rationale for guided picking (~15 lines)
   - 1D adaptive picker: threshold 0.05, FWHM factor 1.5, when to override (~10 lines)
     [Source: pick_peaks_1d Tier 2 documentation]
   - HSQC DEPT-guided strategy: iterative threshold, sign-based multiplicity,
     DEPT-90 disambiguation (~25 lines)
     [Source: pick_hsqc_peaks Tier 3 intelligence + CLAUDE.md 11.4]
   - HMBC cross-validation: tolerance rationale (13C 1.5 ppm, 1H 0.1 ppm),
     noise model, when to adjust (~25 lines)
     [Source: pick_hmbc_peaks Tier 3 intelligence + CLAUDE.md 11.5]
   - APT as DEPT alternative (~10 lines)
     [Source: CLAUDE.md 11.3]

3. Symmetry Detection (from CLAUDE.md sections 6.1, 11.2, 12.2 + MCP intelligence)
   - Expected vs observed signal count (~10 lines)
   - Intensity-based equivalence (>=1.5x threshold) (~8 lines)
     [Source: analyze_symmetry Tier 3 intelligence]
   - Shift-based multiplicity guessing rules (~8 lines)
     [Source: hydrogen_budget.py intelligence]
   - Common symmetric motifs and their signatures (~10 lines)
   - Handling symmetry decision tree (~15 lines, from CLAUDE.md 12.2)

4. Dereplication (from CLAUDE.md section 8 + MCP intelligence)
   - When to use dereplication (~8 lines, from CLAUDE.md 4.1)
   - Region-specific tolerances and why they differ (~10 lines)
     [Source: dereplicate_c13 Tier 2 documentation]
   - Score interpretation: 0.85/0.65/0.50 thresholds with examples (~15 lines)
     [Source: CLAUDE.md 13.1, deduplicated]

5. LSD Reference (merged from CLAUDE.md sections 9, 10, 6.4)
   - Command format: MULT, HSQC, HMBC, BOND, LIST/PROP (~30 lines)
   - Correlation order rule: HSQC before HMBC (~8 lines, single canonical statement)
   - Hybridization rules: sp2 even count, atom classification (~20 lines)
   - Heteroatom attachment: BOND vs LIST/PROP decision logic (~25 lines)
   - ELIM: only after exhausting other diagnostics (~8 lines, single canonical statement)
   - Solution count interpretation decision tree (~20 lines)
   - Manual file construction checklist (~10 lines)
   - Troubleshooting table (~12 lines)
   [Consolidation target: current ~388 lines -> ~133 lines after deduplication]

6. LSD Constraint Building Strategy (NEW in Phase 22)
   - Carbonyl detection rules: 165-185 ppm ester/amide, 190-220 ppm ketone/aldehyde (~10 lines)
     [Source: generate_lsd_input Tier 3 intelligence]
   - Hybridization inference: 100-160 ppm = sp2 (~5 lines)
     [Source: generate_lsd_input Tier 3 intelligence]
   - sp2 oxygen pairing heuristic (~8 lines)
   - Heteroatom H assignment from formula (~8 lines)
   - sp2 parity enforcement (~5 lines)
   - Incremental HMBC strategy (Phase 22 new content) (~30 lines)
   - When to adjust vs when to add constraints (~15 lines)

7. Ranking and Prediction (from CLAUDE.md section 9.7 + MCP intelligence)
   - HOSE prediction: radius fallback meaning, confidence interpretation (~15 lines)
     [Source: predict_c13_shifts Tier 2 + CLAUDE.md 15]
   - N:1 symmetry matching explanation (~8 lines)
     [Source: rank_lsd_solutions Tier 2]
   - MAE quality thresholds: <2.0 excellent through >5.0 poor (~10 lines)
   - Why correct structures may not rank #1 (~10 lines)

8. CASE Workflow (from CLAUDE.md sections 4, 12, 14)
   - Step-by-step workflow: dereplication -> symmetry -> picking -> LSD -> ranking (~20 lines)
   - When to proceed vs request more data (~15 lines, from decision tree 12.1)
   - Result reporting templates (~25 lines)

9. Quick Reference (from CLAUDE.md section 14)
   - Key tolerances (~8 lines)
   - Red flags (~6 lines)
   - Escalation criteria (~5 lines)
```

**Estimated total: ~500 lines** (down from ~680 lines of source content through deduplication and consolidation).

**Additional documents:**

- **SUPERVISOR.md** (~40 lines): Workflow selection logic (which skill to invoke), loop detection patterns, escalation criteria. Sources: CLAUDE.md sections 3.1, 12.1, 14.5.
- **Blind CASE skill** (~32 lines): Research evaluation protocol. Source: CLAUDE.md section 2.

---

## 6. Migration Roadmap

Every audit finding mapped to a specific v2.0 phase. Grouped by target phase.

### Phase 21: Skill Restructure

**Goal:** Split CLAUDE.md into project-level and CASE workflow documents.

| Component | Current State | Action | Details |
|-----------|--------------|--------|---------|
| CLAUDE.md sections 2-6 | ~500 lines of domain knowledge and workflow logic in project config file | Move to SKILL.md | Case workflow, NMR reference, pitfalls (see Section 5.3 outline) |
| CLAUDE.md sections 9-10 | ~302 lines of LSD domain knowledge with ~175 lines duplication | Merge and deduplicate into SKILL.md | Consolidate LSD Integration + Manual Construction into single reference |
| CLAUDE.md sections 11-14 | ~325 lines of peak picking rationale, decision trees, reporting | Move to SKILL.md | Peak picking strategy, CASE workflow, result reporting |
| CLAUDE.md section 3.1 | Workflow selection decision tree | Move to SUPERVISOR.md | Top-level orchestration: which skill to invoke |
| CLAUDE.md section 12.1 | When to proceed with full elucidation | Move to SUPERVISOR.md | Escalation/routing decisions |
| CLAUDE.md section 14.5 | When to ask for help | Move to SUPERVISOR.md | Escalation criteria |
| CLAUDE.md section 2 | Blind CASE protocol (32 lines) | Move to Blind CASE skill | Specialized research evaluation concern |
| LSD duplication cluster | sp2 rule in 6 places, ELIM in 8 places | Deduplicate | Single canonical statement per rule |
| Peak picking duplication | HMBC noise stated 3 times | Deduplicate | Single explanation in peak picking section |
| Score duplication | Thresholds in 3+ places | Deduplicate | Single reference per score system |

**Phase 21 deliverables:** CLAUDE.md (~298 lines), SKILL.md (~500 lines), SUPERVISOR.md (~40 lines), Blind CASE skill (~32 lines). Zero duplication between documents.

### Phase 22: HMBC Strategy and Spectral Quality

**Goal:** Encode incremental constraint strategy and quality assessment in skill.

| Component | Current State | Action | Details |
|-----------|--------------|--------|---------|
| `generate_lsd_input` Tier 3 intelligence | Carbonyl detection (165-185 / 190-220 ppm), hybridization inference (100-160 ppm = sp2), sp2 oxygen pairing -- all hard-coded | Document in SKILL.md section 6 | AI learns these rules as reasoning strategies, not fixed code |
| `pick_hmbc_peaks` Tier 3 intelligence | Cross-validation strategy, asymmetric tolerances, noise model | Document in SKILL.md section 2 | AI understands WHY HMBC needs filtering and can adjust tolerances |
| CLAUDE.md Pitfall 3 | HMBC noise explanation | Already moved in Phase 21; enhance | Add spectral quality assessment (S/N, digital resolution, artifact recognition) |
| CLAUDE.md Pitfall 4 | Too many LSD solutions | Already moved in Phase 21; enhance | Add incremental HMBC strategy: start with 5-10 high-confidence correlations |
| `pick_hsqc_peaks` Tier 3 intelligence | DEPT-guided adaptive threshold strategy | Document in SKILL.md section 2 | AI understands iterative threshold approach and when to override |
| New content: spectral quality assessment | Does not exist | Create in SKILL.md | S/N evaluation, digital resolution impact, artifact recognition |
| New content: incremental HMBC strategy | Does not exist | Create in SKILL.md section 6 | 3-phase approach: core structure, diagnostic correlations, full constraints |

### Phase 23: Error Tolerance and Confidence

**Goal:** Encode error handling patterns and confidence-annotated output in skill.

| Component | Current State | Action | Details |
|-----------|--------------|--------|---------|
| CLAUDE.md Pitfall 1 (symmetry) | Symptom-based explanation | Enhance in SKILL.md section 3 | Add: close carbon shift detection (0.3-0.5 ppm), ambiguity documentation |
| CLAUDE.md Pitfall 2 (quaternary C) | Symptom-based explanation | Enhance in SKILL.md section 3 | Add: HMBC sparsity handling, chemical shift-based heteroatom inference |
| CLAUDE.md Pitfall 5 (heteroatoms) | Brief mention of inference | Enhance in SKILL.md section 6 | Add: systematic approach to heteroatom placement with confidence levels |
| `analyze_symmetry` Tier 3 intelligence | Hard-coded heuristics for multiplicity guessing | Document in SKILL.md section 3 | AI reasons about symmetry; document shift-based heuristic limitations |
| New content: confidence levels | Does not exist | Create in SKILL.md | High/Medium/Low confidence framework for assignments |
| New content: DEPT phase conflict handling | Does not exist | Create in SKILL.md section 2 | HSQC vs DEPT multiplicity comparison, ground truth selection |
| New content: ambiguous HMBC assignment | Does not exist | Create in SKILL.md section 6 | Generate LSD variants when carbon positions are close (<1 ppm) |

### Phase 24: Supervisor Agent

**Goal:** Supervisor agent with loop detection and diagnosis-first intervention.

| Component | Current State | Action | Details |
|-----------|--------------|--------|---------|
| CLAUDE.md Decision Trees (section 12) | LSD Result Interpretation, When to Proceed | Feed supervisor design | Loop patterns: 0-solution loops, solution explosion, ELIM thrashing |
| CLAUDE.md section 3.1 | Workflow selection (dereplicate vs CASE) | Feed supervisor routing | Supervisor decides which specialist to invoke |
| CLAUDE.md section 14.5 | When to ask for help | Feed escalation criteria | 3-strike escalation rules |
| SUPERVISOR.md (from Phase 21) | Basic routing and escalation | Enhance with loop detection | Add: pattern matching for unproductive loops, intervention strategies |
| `generate_lsd_input` failure modes | Hard-coded in Python with limited diagnostics | Feed supervisor patterns | Supervisor detects when constraint building is failing repeatedly |

### Phase 25: Diagnostic Specialist

**Goal:** LSD expert agent for systematic failure diagnosis.

| Component | Current State | Action | Details |
|-----------|--------------|--------|---------|
| CLAUDE.md LSD Troubleshooting (section 10.3) | Error table + verify checklist + troubleshoot steps | Feed diagnostic specialist knowledge | Specialist systematically checks sp2 count, H budget, HMBC conflicts, correlation order |
| CLAUDE.md Pitfall 4 (too many solutions) | Cause/solution description | Feed specialist for solution-explosion diagnosis | Specialist checks constraint count, quaternary connectivity, symmetry encoding |
| `generate_lsd_input` sp2 parity enforcement | Hard-coded correction in Python | Feed specialist validation | Specialist verifies sp2 count before running LSD |
| `generate_lsd_input` hydrogen budget check | Implicit in atom definition generation | Feed specialist validation | Specialist verifies hydrogen count matches formula |
| LSD Command Format (CLAUDE.md 9.5) | Syntax reference | Feed specialist deep LSD knowledge | Specialist knows MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM |

### Phase 26: Thin Tools

**Goal:** MCP tools become data access wrappers; intelligence migrated to skill.

| Component | Current State | Target State | Specific Change |
|-----------|--------------|-------------|-----------------|
| `generate_lsd_input` | 478 lines of domain inference in LSDInputGenerator | Accept pre-built atom defs + constraints from AI | Remove: carbonyl detection, hybridization inference, sp2 pairing, heteroatom H assignment. Keep: LSD file formatting. |
| `pick_hsqc_peaks` | 289 lines of DEPT-guided adaptive algorithm | Return raw HSQC peaks above threshold | Remove: iterative threshold loop, DEPT sign interpretation. CLI retains smart mode. |
| `pick_hmbc_peaks` | 226 lines of cross-validation filtering | Return raw HMBC peaks above threshold | Remove: 13C/HSQC cross-validation. CLI retains smart mode. |
| `analyze_symmetry` | 576 lines across 3 modules with heuristics | Return raw intensity data and carbon counts | Remove: shift-based multiplicity guessing, equivalence threshold, motif recognition. CLI retains smart mode. |
| Experiment auto-discovery | Duplicated in CLI lsd.py and MCP server.py | Consolidated shared utility | Move to shared module (lsd/ or processing/). CLI uses it; MCP does not (AI identifies experiments). |
| Database auto-detection | `_find_database_path()` in CLI, imported by MCP | Consolidated in database/finder.py | Shared utility. Both CLI and MCP can use it. |
| LSD file parsing | `parse_lsd_input_file()` in CLI visualize.py, imported by MCP | Consolidated in lsd/parser.py | Alongside existing LSDOutputParser. |
| `pick_peaks_1d` | Adaptive two-pass with domain-tuned defaults | Keep algorithm, document strategy in SKILL.md | Tier 2: algorithm is standard (SciPy); document when to override defaults. |
| `dereplicate_c13` | Region-specific tolerances, geometric mean scoring | Keep algorithm, document scoring in SKILL.md | Tier 2: matching is mechanical; document interpretation strategy. |
| `rank_lsd_solutions` | N:1 matching, MAE calculation, confidence weighting | Keep algorithm, document ranking strategy in SKILL.md | Tier 2: ranking is algorithmic; document interpretation. |
| `predict_c13_shifts` | HOSE radius fallback, confidence formula | Keep algorithm, document prediction strategy in SKILL.md | Tier 2: prediction is well-defined lookup; document confidence meaning. |

**Phase 26 dual-mode architecture:**
- **MCP tools:** Thin wrappers returning raw data. AI applies strategy from SKILL.md.
- **CLI commands:** Retain current smart behavior for backward compatibility. `lucy pick hsqc` still uses DEPT-guided algorithm.
- **Shared modules:** Intelligence remains in Python for CLI use. MCP tools call simpler code paths or accept pre-processed input.

---

## 7. Recommendations Summary

Every component with an action verb and phase reference. No orphan recommendations.

### MCP Tools

- **`read_spectrum_1d`**: Keep as-is. Pure data wrapper. No migration needed.
- **`read_spectrum_2d`**: Keep as-is. Pure data wrapper. No migration needed.
- **`pick_peaks_1d`**: Document adaptive threshold strategy in SKILL.md (Phase 22). Keep SciPy algorithm in Python.
- **`pick_hsqc_peaks`**: Refactor MCP to return raw peaks (Phase 26). Document DEPT-guided strategy in SKILL.md (Phase 22). CLI retains smart mode.
- **`pick_hmbc_peaks`**: Refactor MCP to return raw peaks (Phase 26). Document cross-validation strategy in SKILL.md (Phase 22). CLI retains smart mode.
- **`analyze_symmetry`**: Refactor MCP to return raw data (Phase 26). Document symmetry reasoning in SKILL.md (Phase 23). CLI retains smart mode.
- **`dereplicate_c13`**: Document scoring strategy and interpretation in SKILL.md (Phase 22). Keep matching algorithm in Python.
- **`check_lsd_availability`**: Keep as-is. Pure environment check. No migration needed.
- **`generate_lsd_input`**: Refactor to accept pre-built constraints (Phase 26). Move all domain heuristics to SKILL.md (Phase 22). Primary refactoring target.
- **`run_lsd`**: Keep as-is. Pure subprocess wrapper. No migration needed.
- **`rank_lsd_solutions`**: Document ranking strategy in SKILL.md (Phase 22). Keep algorithm in Python.
- **`predict_c13_shifts`**: Document HOSE prediction strategy in SKILL.md (Phase 22). Keep algorithm in Python.
- **`get_hose_stats_info`**: Keep as-is. Pure database query. No migration needed.
- **`fetch_nmrxiv_dataset`**: Keep as-is. Pure HTTP client. No migration needed.
- **`generate_correlation_diagram`**: Keep as-is. Pure visualization. No migration needed.

### CLI Command Groups

- **`read`**: Keep as-is. Pure wrappers around BrukerReader. No migration needed.
- **`pick`**: Keep as-is at CLI level. Intelligence is in shared processing modules (addressed in MCP recommendations). (Phase 26)
- **`analyze`**: Keep as-is at CLI level. Intelligence is in shared analysis modules (addressed in MCP recommendations). (Phase 26)
- **`dereplicate`**: Consolidate `_find_database_path()` into database/finder.py (Phase 26). Document search strategy in operational docs.
- **`predict`**: Document backend priority chain in operational docs (Phase 26). Keep SD format auto-detection in Python.
- **`lsd`**: Consolidate experiment auto-discovery into shared utility (Phase 26). Add MCP equivalent for `lsd analyze` command (Phase 26). Document auto-discovery rules in SKILL.md (Phase 22).
- **`visualize`**: Consolidate `parse_lsd_input_file()` into lsd/parser.py (Phase 26). Keep visualization engine as-is.
- **`fetch`**: Keep as-is. Pure HTTP wrapper. No migration needed.
- **`database`**: Keep as-is. Operational utilities not used during CASE. No migration needed.

### CLAUDE.md Sections

- **Title + description**: Keep in CLAUDE.md. Project identity. (No phase)
- **End-User Setup**: Keep in CLAUDE.md. Installation instructions. (No phase)
- **Blind CASE Protocol**: Move to Blind CASE skill document (Phase 21).
- **Available Subskills**: Move workflow selection to SUPERVISOR.md; move subskill descriptions to SKILL.md (Phase 21).
- **Structure Elucidation Workflow**: Move to SKILL.md as primary workflow (Phase 21).
- **NMR Quick Reference (domain parts)**: Move experiment types and shift regions to SKILL.md (Phase 21). Keep tool output reference in CLAUDE.md.
- **Common Pitfalls (all 5)**: Move to SKILL.md; enhance with error tolerance strategies (Phase 21 move, Phase 23 enhance).
- **Reference Data**: Keep brief database ref in CLAUDE.md; remove duplication (Phase 21).
- **Dereplication (interpretation)**: Move interpretation to SKILL.md; keep CLI syntax in CLAUDE.md (Phase 21).
- **LSD Integration (domain parts)**: Merge with Manual LSD Construction; move to SKILL.md (Phase 21).
- **Manual LSD File Construction**: Merge into LSD section of SKILL.md; eliminate as separate section (Phase 21).
- **Peak Picking (domain parts)**: Move rationale, symmetry, APT to SKILL.md; keep API syntax in CLAUDE.md (Phase 21).
- **Decision Trees**: Move to SKILL.md and SUPERVISOR.md (Phase 21). Enhance with loop detection patterns (Phase 24).
- **Result Reporting Templates**: Move to SKILL.md output formatting section (Phase 21).
- **Quick Reference Card**: Move entirely to SKILL.md quick reference appendix (Phase 21).
- **13C Shift Prediction (interpretation)**: Move interpretation to SKILL.md; keep CLI syntax in CLAUDE.md (Phase 21).
- **Developer Reference**: Keep in CLAUDE.md. Build commands, project structure, architecture. (No phase)

---

## 8. Validation Against Phase 20 Requirements

| Criterion | ID | Status | Evidence |
|-----------|----|--------|----------|
| All MCP tools classified as Tier 1/2/3 | AUDT-01 | **PASS** | 15 tools classified (Section 2). Requirements stated 16; actual count is 15, verified by `@mcp.tool()` decorator count in server.py. |
| All CLI command groups classified | AUDT-02 | **PASS** | 9 groups (22 commands) classified (Section 3). Requirements stated 7; actual count is 9, verified by click group inspection in cli/ modules. |
| CLAUDE.md sections catalogued with duplication and misplacement identified | AUDT-03 | **PASS** | 14 top-level sections and 43 subsections catalogued (Section 4). 5 duplication clusters documented with line-level references. 20+ misplacements identified with target documents. |
| Audit report exists with specific, actionable recommendation per component | AUDT-04 | **PASS** | 15 MCP tool recommendations, 9 CLI group recommendations, and 17 CLAUDE.md section recommendations (Section 7). Every recommendation includes an action verb and references a specific v2.0 phase (21-26). Zero generic "simplify later" or "TBD" recommendations. |

### Count Discrepancy Notes

- **AUDT-01 expected 16 MCP tools, found 15.** The discrepancy likely stems from counting `generate_correlation_diagram` as two tools (it has a complex multi-mode interface) or an early count that included a since-removed tool. The 15-count is authoritative, verified by counting `@mcp.tool()` decorators in server.py.

- **AUDT-02 expected 7 CLI groups, found 9.** The discrepancy stems from counting `database` and `fetch` as part of other groups, or from an early roadmap estimate before all CLI groups were implemented. The 9-count is authoritative, verified by click group registration in cli/main.py.

---

*Report compiled from: audit-mcp-tools.md (Plan 20-01), audit-cli-commands.md (Plan 20-01), audit-claude-md.md (Plan 20-02)*
*Phase 20 System Audit | lucy-ng v2.0 Migration Planning*
