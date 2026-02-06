# MCP Tool Audit

## Summary

- Tier 1 (keep as-is): 7 tools
- Tier 2 (document strategy in skill): 4 tools
- Tier 3 (refactor to thin wrapper, move logic to skill): 4 tools

**Total implementation code audited:** ~6,110 lines across 18 modules

---

## Tool Classifications

### read_spectrum_1d
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 39-61)
- **Implementation:** src/lucy_ng/readers/bruker.py -> BrukerReader.read_1d() (278 lines shared)
- **Intelligence detected:** None. Pure wrapper around nmrglue Bruker file parsing. Returns metadata dict with nucleus, frequency, ppm_range, solvent.
- **Recommendation:** Keep as-is. Pure data access wrapper around BrukerReader.read_1d(). No domain logic to migrate.

### read_spectrum_2d
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 65-90)
- **Implementation:** src/lucy_ng/readers/bruker.py -> BrukerReader.read_2d() (278 lines shared)
- **Intelligence detected:** None. Pure wrapper around nmrglue Bruker file parsing. Includes experiment type detection via pulse program pattern matching, but this is identification logic, not domain inference.
- **Recommendation:** Keep as-is. Pure data access wrapper around BrukerReader.read_2d(). The pulse program pattern matching (HMBC, HSQC, COSY detection) is mechanical identification, not NMR reasoning.

### pick_peaks_1d
- **Tier:** 2
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 99-126)
- **Implementation:** src/lucy_ng/processing/peak_picker.py -> AdaptivePeakPicker (237 lines)
- **Intelligence detected:** Two-pass adaptive algorithm with domain-tuned defaults: (1) initial pick with scipy.signal.find_peaks, (2) measure FWHM via peak_widths, (3) compute adaptive min_distance = median_fwhm * fwhm_factor (default 1.5), (4) re-pick with tighter spacing. Default threshold=0.05, fallback_min_distance_ppm=0.1 are NMR-specific tuning constants.
- **Recommendation:** Document the adaptive threshold strategy (start at 0.05, FWHM-based min_distance with 1.5x factor, fallback 0.1 ppm) in SKILL.md so the AI knows when to override defaults. Keep the SciPy peak-finding algorithm in Python -- it is a standard published method, not domain inference.

### pick_hsqc_peaks
- **Tier:** 3
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 130-180)
- **Implementation:** src/lucy_ng/processing/dept_guided_picker.py -> DEPTGuidedPicker (289 lines)
- **Intelligence detected:** Multi-step domain-aware algorithm: (1) picks DEPT-135 peaks as ground truth for all protonated carbons, (2) iteratively lowers HSQC threshold (start 0.10, step 0.5x, min 0.005) until all DEPT carbons have matching HSQC peaks, (3) extracts multiplicity from DEPT peak sign (positive = CH/CH3, negative = CH2), (4) optional DEPT-90 disambiguation (only CH visible in DEPT-90, so positive DEPT-135 peaks absent in DEPT-90 = CH3). The adaptive threshold loop and DEPT sign interpretation embed domain knowledge about NMR multiplicity editing experiments.
- **Recommendation:** Refactor: Move the DEPT-guided adaptive threshold strategy (start at 0.10, halve until all DEPT carbons matched, sign-based multiplicity assignment) to SKILL.md. The AI should understand WHY DEPT-135 positive = CH/CH3 and negative = CH2 (phase cycling in DEPT experiments), and WHEN to use DEPT-90 for disambiguation. Keep the numeric peak-matching algorithm in Python, but the AI should be able to instruct threshold adjustments and interpret multiplicity results.

### pick_hmbc_peaks
- **Tier:** 3
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 184-234)
- **Implementation:** src/lucy_ng/processing/hmbc_guided_picker.py -> HMBCGuidedPicker (226 lines)
- **Intelligence detected:** Cross-validation filtering with domain-specific tolerances: (1) collects reference carbon positions from 13C spectrum and DEPT-135, (2) collects reference proton positions from HSQC, (3) picks raw HMBC peaks, (4) validates each peak: carbon axis must match a known carbon position (+-1.5 ppm) AND proton axis must match a known proton position (+-0.1 ppm), (5) rejects peaks failing either criterion. The asymmetric tolerances (1.5 ppm for 13C vs 0.1 ppm for 1H) reflect inherent precision differences between carbon and proton dimensions in 2D NMR. The entire filtering logic is a domain-specific noise rejection strategy.
- **Recommendation:** Refactor: Move the cross-validation strategy (filter HMBC peaks against known 13C + HSQC positions) and the tolerance rationale (13C 1.5 ppm vs 1H 0.1 ppm due to inherent precision differences) to SKILL.md. The AI should understand WHY HMBC requires filtering (low-sensitivity experiment with t1 noise and 1J bleeding artifacts) and be able to adjust tolerances for edge cases. Keep the geometric matching algorithm in Python.

### analyze_symmetry
- **Tier:** 3
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 243-309)
- **Implementation:** src/lucy_ng/analysis/symmetry_analysis.py -> SymmetryAnalyzer (193 lines), src/lucy_ng/analysis/hydrogen_budget.py -> HydrogenBudgetAnalyzer (200 lines), src/lucy_ng/analysis/intensity_reporter.py -> IntensityReporter (183 lines)
- **Intelligence detected:** Three-layer domain inference: (1) HydrogenBudgetAnalyzer computes expected vs observed hydrogen count from molecular formula and HSQC multiplicities, using chemical shift heuristics (<30 ppm = likely CH3, >100 ppm = aromatic CH) for multiplicity disambiguation when DEPT-90 unavailable, estimates heteroatom-attached H (O, N) from formula. (2) IntensityReporter groups HSQC peaks by carbon, normalizes intensities relative to weakest signal, flags peaks with relative intensity >= 1.5 as potential equivalents (symmetry). (3) SymmetryAnalyzer combines both: expected_carbons from formula vs observed_signals, generates AI-readable summary with interpretation hints about common symmetric motifs (para-substituted benzene, gem-dimethyl, isopropyl). The shift-based multiplicity guessing and intensity-based equivalence detection are domain heuristics.
- **Recommendation:** Refactor: Move the symmetry detection strategy to SKILL.md -- specifically: (a) shift-based multiplicity guessing rules (<30 ppm CH3, >100 ppm aromatic CH), (b) intensity-based equivalence heuristic (>= 1.5x relative intensity suggests doubled signal from symmetric atoms), (c) common symmetric motifs and their spectroscopic signatures. The AI should reason about symmetry directly rather than relying on hard-coded heuristics. Keep the numerical intensity calculation in Python, but the AI should drive the interpretation.

### dereplicate_c13
- **Tier:** 2
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 318-463)
- **Implementation:** src/lucy_ng/dereplication/service.py -> DereplicationService (233 lines), src/lucy_ng/dereplication/matcher.py -> SpectrumMatcher (293 lines)
- **Intelligence detected:** In the MCP wrapper: database auto-detection chain (explicit path -> env var -> default path -> SD file fallback) with format detection. In SpectrumMatcher: variable tolerance by chemical shift region (aliphatic 0.8 ppm, aromatic 1.2 ppm, carbonyl 1.5 ppm), overlap_factor for symmetry-aware scoring, geometric mean of forward/backward coverage, DEPT mismatch penalty. The region-specific tolerances and scoring formula embed domain knowledge about typical prediction accuracy in different chemical shift ranges.
- **Recommendation:** Document the scoring strategy in SKILL.md: region-dependent tolerances (aliphatic 0.8, aromatic 1.2, carbonyl 1.5 ppm), why these vary (prediction accuracy differs by region), geometric mean scoring approach, and score interpretation thresholds (>0.85 strong, 0.65-0.85 possible, <0.50 no match). Keep the matching algorithm and database auto-detection in Python -- these are operational mechanics, not domain reasoning the AI needs to override.

### check_lsd_availability
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 472-491)
- **Implementation:** src/lucy_ng/lsd/runner.py -> LSDRunner.is_available() + is_outlsd_available() (400 lines shared)
- **Intelligence detected:** None. Checks PATH for `LSD` and `outlsd` binaries using shutil.which(). Pure environment check.
- **Recommendation:** Keep as-is. Pure environment probe. No domain logic.

### generate_lsd_input
- **Tier:** 3
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 495-617)
- **Implementation:** src/lucy_ng/lsd/generator.py -> LSDInputGenerator (478 lines)
- **Intelligence detected:** Highest concentration of domain logic in the codebase. In the MCP wrapper: experiment auto-discovery with pulse program pattern matching to classify DEPT-135, DEPT-90, 13C, HSQC, HMBC. In LSDInputGenerator: (1) chemical shift -> hybridization inference (100-160 ppm = sp2 for aromatic/alkene carbons), (2) carbonyl carbon detection via two shift ranges (165-185 ppm for esters/amides, 190-220 ppm for ketones/aldehydes), (3) sp2 oxygen pairing -- each carbonyl carbon gets a BOND constraint to an sp2 oxygen, (4) heteroatom hydrogen assignment from molecular formula deficit, (5) HMBC proton-to-carbon index mapping via HSQC cross-reference (HMBC gives proton shift, must find which carbon that proton is attached to via HSQC), (6) sp2 count parity enforcement (LSD requires even number of sp2 atoms). These are all domain inference steps that should be AI-driven decisions, not hard-coded rules.
- **Recommendation:** Refactor: This is the primary target for v2.0. Accept pre-constructed atom definitions (element, hybridization, H-count) and constraint lists from the AI. Move to SKILL.md: (a) carbonyl detection rules (165-185 ppm ester/amide, 190-220 ppm ketone/aldehyde), (b) hybridization inference (100-160 ppm = sp2), (c) sp2 oxygen pairing heuristic, (d) heteroatom H assignment strategy, (e) sp2 parity rule. The AI should make these decisions based on the full spectroscopic context, allowing it to handle edge cases (conjugated systems, unusual shifts) that hard-coded ranges miss. Keep LSD file formatting in Python.

### run_lsd
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 621-670)
- **Implementation:** src/lucy_ng/lsd/runner.py -> LSDRunner (400 lines), src/lucy_ng/lsd/parser.py -> LSDOutputParser (113 lines)
- **Intelligence detected:** None at the domain level. Subprocess management: finds LSD/outlsd executables, runs with timeout, parses solution count from stderr, converts solutions to SMILES via outlsd. The solution count extraction from stderr is parser logic, not domain reasoning.
- **Recommendation:** Keep as-is. Pure subprocess execution wrapper. The only "intelligence" is stderr parsing for solution counts, which is LSD output format knowledge, not NMR domain logic.

### rank_lsd_solutions
- **Tier:** 2
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 705-790)
- **Implementation:** src/lucy_ng/ranking/ranker.py -> SolutionRanker (205 lines), src/lucy_ng/prediction/predictor.py -> C13Predictor (277 lines)
- **Intelligence detected:** N:1 matching strategy (multiple predicted shifts can match the same experimental peak to handle symmetry), MAE calculation using ALL shifts (not just those within tolerance), HOSE radius fallback (6 -> 5 -> ... -> 1) with confidence weighting. In C13Predictor: confidence formula combining radius weight (50%), log-scaled match count (30%), and inverse std deviation (20%). These are reasonable but somewhat arbitrary weighting choices.
- **Recommendation:** Document the ranking strategy in SKILL.md: (a) N:1 matching handles molecular symmetry (equivalent carbons map to same experimental peak), (b) MAE quality thresholds (< 2.0 excellent, 2-3.5 good, 3.5-5 moderate, > 5 poor), (c) confidence calculation weights. The AI should understand WHY N:1 matching is needed and how to interpret MAE scores in context. Keep the prediction and matching algorithms in Python.

### predict_c13_shifts
- **Tier:** 2
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 885-948)
- **Implementation:** src/lucy_ng/prediction/predictor.py -> C13Predictor (277 lines)
- **Intelligence detected:** HOSE code generation with radius fallback strategy (try radius 6 first for most specific match, fall back to 5, 4, ... 1 for broader matches). Confidence formula: weighted combination of radius (50%), log-scaled match count (30%), std deviation (20%). Backend caching via `_prediction_cache` dict in server.py for performance.
- **Recommendation:** Document the HOSE prediction strategy in SKILL.md: (a) radius fallback meaning (higher radius = more specific chemical environment = more accurate but fewer matches), (b) confidence interpretation (what 0.3 vs 0.8 means practically), (c) known limitations (strained rings, unusual substituent effects). Keep the HOSE code generation and database lookup in Python -- this is a well-defined algorithmic operation.

### get_hose_stats_info
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 952-1001)
- **Implementation:** src/lucy_ng/database/manager.py -> DatabaseManager (729 lines shared)
- **Intelligence detected:** None. Pure database stats query: counts HOSE statistics entries and compound count. Auto-detects database in default paths.
- **Recommendation:** Keep as-is. Pure data access query returning database metadata. No domain logic.

### fetch_nmrxiv_dataset
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 1010-1068)
- **Implementation:** src/lucy_ng/nmrxiv/client.py -> NMRXivClient (454 lines)
- **Intelligence detected:** None at the NMR domain level. HTTP client with DOI/URL parsing, project/study identification, zip download and extraction. The identifier parsing (DOI, project ID, URL formats) is API knowledge, not NMR reasoning.
- **Recommendation:** Keep as-is. Pure HTTP client for NMRXiv data retrieval. No NMR domain logic to migrate.

### generate_correlation_diagram
- **Tier:** 1
- **MCP wrapper:** src/lucy_ng/mcp/server.py (lines 1077-1273)
- **Implementation:** src/lucy_ng/visualization/diagram_generator.py -> CorrelationDiagramGenerator (1151 lines)
- **Intelligence detected:** None at the NMR inference level. The MCP wrapper has input parsing logic (3 modes: sol_content, lsd_content, or explicit correlations list). The implementation is complex (1151 lines) but entirely visualization: RDKit molecule rendering, arrow routing with overlap avoidance, layout optimization, SVG building, J-coupling label placement. This is rendering logic, not NMR domain reasoning.
- **Recommendation:** Keep as-is. Pure visualization engine. The 1151-line implementation is complex but contains zero NMR domain inference -- it renders what it is told to render. No migration needed.

---

## Cross-Reference: Implementation Modules

| Module | Lines | Used By (MCP tools) | Tier |
|--------|-------|---------------------|------|
| readers/bruker.py | 278 | read_spectrum_1d, read_spectrum_2d | 1 |
| processing/peak_picker.py | 237 | pick_peaks_1d | 2 |
| processing/dept_guided_picker.py | 289 | pick_hsqc_peaks, generate_lsd_input | 3 |
| processing/hmbc_guided_picker.py | 226 | pick_hmbc_peaks, generate_lsd_input | 3 |
| analysis/symmetry_analysis.py | 193 | analyze_symmetry | 3 |
| analysis/hydrogen_budget.py | 200 | analyze_symmetry | 3 |
| analysis/intensity_reporter.py | 183 | analyze_symmetry | 3 |
| dereplication/service.py | 233 | dereplicate_c13 | 2 |
| dereplication/matcher.py | 293 | dereplicate_c13 | 2 |
| lsd/generator.py | 478 | generate_lsd_input | 3 |
| lsd/runner.py | 400 | check_lsd_availability, run_lsd | 1 |
| lsd/parser.py | 113 | run_lsd, rank_lsd_solutions | 1 |
| ranking/ranker.py | 205 | rank_lsd_solutions | 2 |
| prediction/predictor.py | 277 | rank_lsd_solutions, predict_c13_shifts | 2 |
| database/manager.py | 729 | get_hose_stats_info | 1 |
| nmrxiv/client.py | 454 | fetch_nmrxiv_dataset | 1 |
| visualization/diagram_generator.py | 1151 | generate_correlation_diagram | 1 |
