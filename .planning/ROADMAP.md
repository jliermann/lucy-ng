# lucy-ng Roadmap

## Milestone 1.0 — Core CASE Pipeline

### Phase 1: Foundation
**Goal**: Project structure, dependencies, and NMR library evaluation

- Set up Python package structure with modern tooling (pyproject.toml)
- Research and evaluate NMR parsing libraries (nmrglue, bruker-reader, etc.)
- Establish core data models for spectra and peaks
- Basic test infrastructure

**Research**: NMR parsing library selection

---

### Phase 2: 1D NMR Reading
**Goal**: Read Bruker 1D spectra (1H, 13C) reliably

- Implement Bruker 1D file reader (fid, acqus, procs)
- Parse acquisition and processing parameters
- Handle spectrum data (real/imaginary, processed)
- Data structures for 1D spectra with metadata

---

### Phase 2.1: 1D Carbon Dereplication (INSERTED)
**Goal**: Validate pipeline with 1D dereplication against nmrshiftdb

- Peak picking from 1D 13C spectrum
- Download/query reference data from nmrshiftdb by molecular formula
- Match observed peaks against reference spectra
- Score and rank candidate structures
- Return dereplication results (match/no match/candidates)

**Depends on:** Phase 2
**Research**: nmrshiftdb API/data format, matching algorithms

---

### Phase 3: 2D NMR Reading
**Goal**: Read Bruker 2D spectra (HSQC, HMBC)

- Implement Bruker 2D file reader (ser, acqu2s)
- Parse 2D acquisition parameters (F1/F2 dimensions)
- Handle 2D data matrices
- Data structures for 2D spectra with correlation information

---

### Phase 4: Peak Picking
**Goal**: Automated peak detection for 1D and 2D spectra

- 1D peak picking algorithm (threshold, noise estimation)
- 2D peak picking (local maxima, cross-peak detection)
- Peak list data structures
- Peak filtering and validation

**Research**: Peak picking algorithms and thresholds

---

### Phase 4.1: 2D Peak Picking Validation (INSERTED)
**Goal**: Validate that 2D peak picking produces scientifically reasonable results

- Cross-validate HSQC peaks against 1D 13C peaks
- Every HSQC F1 position should correspond to a 1D 13C peak
- Develop validation utility for peak list quality assurance
- Tolerance-based matching between 2D F1 and 1D peak positions

**Depends on:** Phase 4
**Rationale**: Ensure 2D peak picking is physically plausible before using peaks for structure elucidation

---

### Phase 4.2: DEPT-Guided Adaptive HSQC Peak Picking (INSERTED)
**Goal**: Use DEPT data as ground truth to adaptively tune HSQC peak picking

- Read DEPT-135 spectrum to identify all protonated carbons
- Use DEPT peaks as validation targets for HSQC
- Adaptively lower HSQC threshold until all DEPT carbons are matched
- Filter HSQC peaks to only those corresponding to real carbons
- Return validated, noise-free HSQC peak list

**Depends on:** Phase 4.1
**Rationale**: DEPT provides definitive ground truth for which carbons carry hydrogens; HSQC must find all of them

---

### Phase 5: LSD Integration
**Goal**: Generate input files and execute LSD/pyLSD solvers

- Research LSD/pyLSD input file format
- Generate constraint files from peak data
- Execute LSD/pyLSD as subprocess
- Parse and structure solution output

**Research**: LSD/pyLSD file formats and CLI interface

---

### Phase 5.1: HMBC-Guided Peak Picking (INSERTED)
**Goal**: Filter HMBC peaks using validated carbon and proton positions

- Use 13C/DEPT peaks as valid carbon positions
- Use HSQC proton positions as valid proton positions
- Filter HMBC to only peaks matching both constraints
- Reduce noise and improve LSD constraint quality

**Depends on:** Phase 5
**Rationale**: HMBC noise produces spurious correlations; filtering by known positions improves LSD results

---

### Phase 5.2: Symmetry Detection from Spectroscopic Data (INSERTED)
**Goal**: Detect molecular symmetry to properly handle equivalent atoms in LSD input

- Hydrogen counting: Compare MF hydrogen count with carbon-assigned H sum
- Detect "missing" hydrogens indicating equivalent carbons
- Intensity analysis: Identify doubled signals from relative peak intensities
- Pattern recognition: Recognize symmetric motifs (para-substituted benzene, isopropyl, etc.)
- Generate proper atom definitions for equivalent positions
- Support LSD SYME commands for equivalent atom constraints

**Depends on:** Phase 5.1
**Rationale**: Molecular symmetry causes fewer NMR signals than atoms; without handling this, LSD fails with valence errors

---

### Phase 6: CLI Interface
**Goal**: Command-line interface for all operations

- CLI framework setup (click or typer)
- Commands for reading spectra
- Commands for peak picking
- Commands for LSD execution
- Workflow commands (full pipeline)

---

### Phase 7: MCP Server
**Goal**: Model Context Protocol tools for Claude agent integration

- MCP server setup
- Tool definitions for all operations
- Structured input/output schemas
- Agent-friendly error handling and feedback

---

### Phase 8: HOSE-Based 13C Spectrum Predictor
**Goal**: Build pure Python 13C NMR predictor using HOSE codes and COCONUT database

- HOSE code generation wrapper using hosegen library
- Build lookup table from COCONUT SD file (~895K molecules)
- Predictor class with fallback to shorter HOSE radii
- Confidence scoring based on match count and variance
- CLI command for shift prediction
- MCP tool for agent integration

**Research**: Completed - evaluated nmrgnn, CASCADE, nmr_mpnn (all had dependency issues); HOSE codes selected

---

### Phase 9: LSD Solution Ranking
**Goal**: Rank LSD solutions by similarity between experimental 13C spectrum and predicted spectrum

- Use Phase 8 predictor for candidate structure shifts
- Compare predicted shifts with experimental 13C peaks
- Score solutions by spectrum similarity (e.g., MAE, RMSE, or cosine similarity)
- Rank and filter solutions by prediction quality
- Return ranked solution list with confidence scores

**Depends on:** Phase 8 (HOSE Predictor)

---

### Phase 10: NMRXiv Dataset Fetching
**Goal**: Fetch spectroscopic datasets from nmrxiv.org for structure elucidation

- Research NMRXiv API and data access methods
- Implement dataset fetching by identifier or search criteria
- Parse and convert NMRXiv data to lucy-ng formats
- CLI command for dataset retrieval
- MCP tool for agent integration

**Depends on:** Phase 6 (CLI Interface)

---

## Progress

| Phase | Status | Plans |
|-------|--------|-------|
| 1. Foundation | Complete | 01-01-PLAN.md, 01-01-SUMMARY.md |
| 2. 1D NMR Reading | Complete | 01-02-PLAN.md, 01-02-SUMMARY.md |
| 2.1 1D Carbon Dereplication | Complete | 01-02.1-PLAN.md, 01-02.1-SUMMARY.md |
| 3. 2D NMR Reading | Complete | 01-03-PLAN.md, 01-03-SUMMARY.md |
| 4. Peak Picking | Complete | 01-04-PLAN.md, 01-04-SUMMARY.md |
| 4.1 2D Peak Validation | Complete | 01-04.1-PLAN.md, 01-04.1-SUMMARY.md |
| 4.2 DEPT-Guided Adaptive HSQC | Complete | 01-04.2-PLAN.md, 01-04.2-SUMMARY.md |
| 5. LSD Integration | Complete | 01-05-PLAN.md, 01-05-SUMMARY.md |
| 5.1 HMBC-Guided Peak Picking | Complete | — |
| 5.2 Symmetry Detection | Complete | — |
| 6. CLI Interface | Complete | 01-06-PLAN.md, 01-06-SUMMARY.md |
| 7. MCP Server | Complete | 01-07-PLAN.md |
| 8. HOSE-Based 13C Predictor | Complete | 01-08-PLAN.md, 01-08-SUMMARY.md |
| 9. LSD Solution Ranking | Complete | 01-09-PLAN.md, 01-09-SUMMARY.md |
| 10. NMRXiv Dataset Fetching | Complete | 01-10-PLAN.md, 01-10-SUMMARY.md |

---

## Milestone 1.0 Status — COMPLETE

Core CASE Pipeline fully implemented:

- **13 MCP Tools**: Spectrum reading, peak picking, analysis, dereplication, LSD integration, shift prediction, solution ranking, data fetching
- **Full CLI**: 7 command groups with JSON output support
- **Python API**: Direct library access for all functionality
- **414+ Tests**: Comprehensive test coverage
- **Documentation**: README, User Guide, Architecture, MCP Integration, AI Guide
- **13C Prediction**: HOSE-code based predictor
- **Solution Ranking**: LSD solutions ranked by 13C spectrum similarity
- **Data Fetching**: Download NMR data from NMRXiv by DOI

**12/12 phases complete** — Milestone 1.0 achieved!

---
*Last updated: 2026-01-12*
