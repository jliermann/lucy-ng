# CLI Command Audit

## Summary

- 9 groups, 22 commands total
- Tier 1 (pure CLI wrappers): 4 groups
- Tier 2 (moderate intelligence): 3 groups
- Tier 3 (complex orchestration): 2 groups

**Total CLI code audited:** 2,695 lines across 9 modules

**Key finding:** CLI commands and MCP tools share the same implementation modules. The intelligence lives in the shared Python libraries, not in the CLI or MCP wrappers themselves. The main difference is that CLI commands include database/backend auto-detection logic and text/JSON formatting, while MCP tools include similar auto-detection plus dict result formatting.

**Important:** Per Phase 26 requirements, CLI commands retain their smart behavior for backward compatibility. The recommendations below describe what intelligence the AI should ALSO know about (documented in skill), not intelligence to remove from CLI.

---

## Group Classifications

### read (2 commands)

| Command | Tier | Intelligence | Shared with MCP? |
|---------|------|-------------|-------------------|
| 1d      | 1    | None -- pure BrukerReader wrapper with text/json formatting | Yes (read_spectrum_1d) |
| 2d      | 1    | None -- pure BrukerReader wrapper with text/json formatting | Yes (read_spectrum_2d) |

**CLI module:** src/lucy_ng/cli/read.py (98 lines)

**Group-level recommendation:** Keep as-is. Both commands are thin wrappers around BrukerReader with output formatting. No domain logic in CLI layer. Identical to MCP tools in function.

---

### pick (4 commands)

| Command | Tier | Intelligence | Shared with MCP? |
|---------|------|-------------|-------------------|
| 1d      | 1    | None -- passes through to AdaptivePeakPicker with optional user-specified threshold | Yes (pick_peaks_1d) |
| 2d      | 1    | None -- passes through to PeakPicker2D with default threshold 0.05 | No (no MCP equivalent) |
| hsqc    | 1    | None -- passes through to DEPTGuidedPicker, all intelligence in implementation | Yes (pick_hsqc_peaks) |
| hmbc    | 1    | None -- passes through to HMBCGuidedPicker, all intelligence in implementation | Yes (pick_hmbc_peaks) |

**CLI module:** src/lucy_ng/cli/pick.py (228 lines)

**Group-level recommendation:** Keep as-is at CLI level. All domain intelligence lives in the shared processing modules (DEPTGuidedPicker, HMBCGuidedPicker, AdaptivePeakPicker), which are already classified in the MCP audit as Tier 2-3. The CLI layer adds only argument parsing and output formatting. The `pick 2d` command has no MCP equivalent -- consider adding one for completeness, or leave it as a CLI-only utility for raw 2D picking.

---

### analyze (1 command)

| Command  | Tier | Intelligence | Shared with MCP? |
|----------|------|-------------|-------------------|
| symmetry | 1    | None -- passes through to SymmetryAnalyzer, all intelligence in implementation | Yes (analyze_symmetry) |

**CLI module:** src/lucy_ng/cli/analyze.py (77 lines)

**Group-level recommendation:** Keep as-is at CLI level. The CLI command is a thin wrapper around SymmetryAnalyzer (classified as Tier 3 in MCP audit). The domain heuristics (shift-based multiplicity guessing, intensity-based equivalence detection) live entirely in the analysis/ modules. CLI adds only HSQC/DEPT reading and output formatting.

---

### dereplicate (1 command)

| Command | Tier | Intelligence | Shared with MCP? |
|---------|------|-------------|-------------------|
| c13     | 2    | Database auto-detection chain (env var -> project path -> common paths -> Spotlight search -> Dropbox path), SD file fallback with gz decompression, format detection (COCONUT vs NMRShiftDB from filename) | Yes (dereplicate_c13) |

**CLI module:** src/lucy_ng/cli/dereplicate.py (326 lines)

**Group-level recommendation:** The CLI has its own database auto-detection implementation (`_find_database_path()` at lines 23-82) which is also imported by the MCP tool. This is operational intelligence (where to find the database) rather than NMR domain intelligence. The NMR matching logic is in the shared DereplicationService/SpectrumMatcher modules. Document the database search strategy in operational docs, but no NMR domain logic needs to move to SKILL.md from the CLI layer specifically.

---

### predict (3 commands)

| Command     | Tier | Intelligence | Shared with MCP? |
|-------------|------|-------------|-------------------|
| c13         | 2    | Backend priority chain (explicit db -> explicit table -> auto-detect db -> auto-detect table) with fallback messaging | Yes (predict_c13_shifts) |
| build-table | 2    | SD format auto-detection (checks first 10 molecules for "Spectrum 13C 0" vs "CNMR_SHIFTS" fields), parallel worker management | No (no MCP equivalent) |
| table-info  | 1    | None -- pure stats display | No (partial overlap with get_hose_stats_info) |

**CLI module:** src/lucy_ng/cli/predict.py (362 lines)

**Group-level recommendation:** The CLI adds backend auto-detection and SD format auto-detection on top of the shared C13Predictor/HOSELookupTable modules. The format detection (`_detect_sd_format()` at lines 294-312) is data format knowledge, not NMR reasoning. The `build-table` command is a CLI-only data pipeline tool (build HOSE lookup table from SD files) with no MCP equivalent. Document the backend priority chain in operational docs. No NMR domain logic to move to SKILL.md from CLI layer.

---

### lsd (5 commands)

| Command  | Tier | Intelligence | Shared with MCP? |
|----------|------|-------------|-------------------|
| check    | 1    | None -- checks LSD/outlsd binary availability | Yes (check_lsd_availability) |
| generate | 3    | Experiment auto-discovery with pulse program classification (DEPT-135, DEPT-90, 13C, 1H detection from pulse program names) -- duplicated from MCP wrapper. Calls same DEPTGuidedPicker + HMBCGuidedPicker + LSDInputGenerator pipeline. | Yes (generate_lsd_input) |
| run      | 1    | None -- passes through to LSDRunner with timeout and output dir | Yes (run_lsd) |
| rank     | 2    | Shift parsing from CLI string or Bruker spectrum, table auto-detection (`_get_default_table_path()` searches project/package/home dirs) | Yes (rank_lsd_solutions) |
| analyze  | 2    | J-coupling path analysis with optional structure drawing. Uses LSDSolutionAnalyzer for BFS-based path length computation on molecular graph. | No (no MCP equivalent) |

**CLI module:** src/lucy_ng/cli/lsd.py (574 lines)

**Group-level recommendation:** The `generate` command is the most intelligence-heavy CLI command, with experiment auto-discovery logic (lines 73-97) that duplicates the MCP wrapper's auto-discovery (lines 528-553 in server.py). This duplication should be consolidated into a shared utility. The actual domain logic (carbonyl detection, hybridization inference, sp2 pairing) lives in LSDInputGenerator (Tier 3 in MCP audit). The `analyze` command's J-coupling analysis (BFS path finding on molecular graph) is algorithmic, not domain-heuristic, and has no MCP equivalent -- consider adding one for AI agent access. Document the experiment auto-discovery strategy (pulse program classification rules) in SKILL.md so the AI can handle edge cases.

---

### visualize (1 command)

| Command      | Tier | Intelligence | Shared with MCP? |
|--------------|------|-------------|-------------------|
| correlations | 1    | None at NMR level -- CLI string parsing helpers (parse_correlation_string, parse_shifts, parse_lsd_input_file) convert CLI arguments to data structures. LSD input file parser (lines 300-396) converts MULT/HSQC/HMBC/COSY commands to LSDProblem objects. | Yes (generate_correlation_diagram) |

**CLI module:** src/lucy_ng/cli/visualize.py (396 lines)

**Group-level recommendation:** Keep as-is. The CLI adds LSD file parsing (parse_lsd_input_file, 97 lines) and CLI argument parsing helpers. The LSD parser is format knowledge (parsing MULT/HSQC/HMBC text commands), not NMR reasoning. The visualization engine (CorrelationDiagramGenerator, 1151 lines) is shared and classified as Tier 1 in MCP audit. Note: the MCP tool imports `parse_lsd_input_file` from this CLI module (line 1142 in server.py) -- consider moving this parser to a shared location (e.g., lsd/parser.py).

---

### fetch (1 command)

| Command | Tier | Intelligence | Shared with MCP? |
|---------|------|-------------|-------------------|
| nmrxiv  | 1    | None -- pure wrapper around NMRXivClient with identifier parsing and progress output | Yes (fetch_nmrxiv_dataset) |

**CLI module:** src/lucy_ng/cli/fetch.py (146 lines)

**Group-level recommendation:** Keep as-is. Pure HTTP client wrapper. No NMR domain logic in either CLI or implementation layer.

---

### database (4 commands)

| Command             | Tier | Intelligence | Shared with MCP? |
|---------------------|------|-------------|-------------------|
| build               | 2    | Orchestrates import from multiple SD file sources (NMRShiftDB + COCONUT) with progress callbacks and batch sizing | No (no MCP equivalent) |
| info                | 1    | None -- displays database statistics | Partial (get_hose_stats_info covers HOSE stats only) |
| download            | 1    | None -- downloads from Figshare URL, decompresses, verifies | No (no MCP equivalent) |
| generate-hose-stats | 3    | Three generation modes (SDF direct, legacy in-memory, resumable chunked), HOSE code generation with hosegen library, Welford's algorithm for incremental statistics, checkpoint/resume capability. SDF mode reads directly from COCONUT file for correct 1-based atom indexing. | No (no MCP equivalent) |

**CLI module:** src/lucy_ng/cli/database.py (488 lines)

**Group-level recommendation:** The `generate-hose-stats` command is a complex data pipeline tool with three modes and checkpoint/resume capability. Its intelligence is in data engineering (chunking, Welford's online algorithm, resume from checkpoint), not NMR domain reasoning. The `build` command orchestrates SD file import with progress tracking. None of these have MCP equivalents because they are one-time setup commands, not analysis tools. Keep as-is -- these are operational utilities that the AI agent would never invoke during structure elucidation.

---

## Cross-Reference: CLI vs MCP Overlap

| CLI Group | CLI Commands | MCP Equivalents | Shared Implementation |
|-----------|-------------|----------------|----------------------|
| read | 1d, 2d | read_spectrum_1d, read_spectrum_2d | readers/bruker.py |
| pick | 1d, 2d, hsqc, hmbc | pick_peaks_1d, pick_hsqc_peaks, pick_hmbc_peaks | processing/*.py |
| analyze | symmetry | analyze_symmetry | analysis/*.py |
| dereplicate | c13 | dereplicate_c13 | dereplication/*.py |
| predict | c13, build-table, table-info | predict_c13_shifts, get_hose_stats_info | prediction/*.py |
| lsd | check, generate, run, rank, analyze | check_lsd_availability, generate_lsd_input, run_lsd, rank_lsd_solutions | lsd/*.py |
| visualize | correlations | generate_correlation_diagram | visualization/*.py |
| fetch | nmrxiv | fetch_nmrxiv_dataset | nmrxiv/client.py |
| database | build, info, download, generate-hose-stats | (none) | database/*.py |

**CLI-only commands (no MCP equivalent):** pick 2d, predict build-table, predict table-info, lsd analyze, database build, database info, database download, database generate-hose-stats (8 commands)

**MCP-only tools (no CLI equivalent):** None -- all MCP tools have CLI counterparts.

## Duplication Notes

1. **Experiment auto-discovery:** Duplicated between `lsd generate` CLI (lines 73-97) and `generate_lsd_input` MCP (lines 528-553). Should be consolidated into a shared utility function.

2. **Database auto-detection:** `_find_database_path()` in cli/dereplicate.py is imported by MCP server.py (line 13). This is already shared but lives in the CLI module -- should be moved to a shared location (e.g., database/finder.py).

3. **LSD file parsing:** `parse_lsd_input_file()` in cli/visualize.py is imported by MCP server.py (line 1142). This parser should be moved to lsd/parser.py alongside LSDOutputParser.
