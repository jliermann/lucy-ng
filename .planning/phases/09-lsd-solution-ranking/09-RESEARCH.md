# Phase 8: LSD Solution Ranking — Research

## Summary

**Recommended approach:** Use HOSE code-based prediction via nmrshiftdb2, either through REST API or the Java CDK wrapper. This is the same method pyLSD uses for solution ranking.

**Key finding:** pyLSD already implements solution ranking using nmrshiftdb's HOSE code prediction. The ranking algorithm is simple: sum of absolute differences between experimental and predicted 13C shifts.

## pyLSD Ranking Algorithm

pyLSD uses nmrshiftdb2 for 13C prediction and ranks solutions by comparing experimental vs. predicted shifts.

**Algorithm:** Sum of absolute differences (SAD)
```
score = Σ |experimental_shift[i] - predicted_shift[i]|
```

Lower score = better match. Solutions sorted by score ascending.

**Requirements for pyLSD ranking:**
- At least one carbon must have experimental shift (SHIX command)
- Must use DUPL 0 or DUPL 1 to preserve all solutions for ranking

**Source:** [pyLSD Documentation](https://nuzillard.github.io/PyLSD/)

## Prediction Methods Available

### Option 1: HOSE Code via nmrshiftdb2 (Recommended)

**How it works:**
- HOSE codes encode atomic neighborhoods in spheres (up to 6 bonds)
- Match HOSE codes against nmrshiftdb2 database of known shifts
- Use average of matching shifts as prediction
- Fall back to smaller sphere count if no match

**Accuracy:** ~1.7 ppm MAE for 13C (traditional HOSE), ~2.7 ppm with neural networks

**Access methods:**

1. **REST API (simplest):**
   ```
   GET https://www.nmrshiftdb.org/NmrshiftdbServlet/nmrshiftdbaction/searchorpredict/smiles/{SMILES}/spectrumtype/13C
   ```
   Returns CML or JCAMP format with predictions per atom.

2. **nmrshiftdb_predictors_app (local):**
   - Docker container with FastAPI wrapper
   - POST SMILES list, get predictions
   - Requires: JDK, conda, rdkit
   - GitHub: [jvansan/nmrshiftdb_predictors_app](https://github.com/jvansan/nmrshiftdb_predictors_app)

3. **Java CDK directly:**
   - HOSECodeGenerator produces HOSE codes
   - BremserOneSphereHOSECodePredictor for shift prediction
   - casekit library: [steinbeck/casekit](https://github.com/steinbeck/casekit)

**Source:** [nmrshiftdb2 20 years paper](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/mrc.5418)

### Option 2: Graph Neural Networks

**nmrgnn (pip installable):**
- `pip install nmrgnn`
- Uses MDAnalysis for structure input (PDB format, not SMILES directly)
- Pre-trained model included
- GitHub: [ur-whitelab/nmrgnn](https://github.com/ur-whitelab/nmrgnn)
- Requires 3D coordinates

**nmr_sgnn:**
- Scalable GNN for NMR prediction
- Supports 13C target
- Uses RDKit, DGL, PyTorch
- GitHub: [hjm9702/nmr_sgnn](https://github.com/hjm9702/nmr_sgnn)

**Very Deep GCN (2024):**
- 54-layer deep graph convolutional network
- Competitive with DFT accuracy
- Journal of Natural Products 2024

**Source:** [Real-time prediction paper](https://pubs.rsc.org/en/content/articlelanding/2021/sc/d1sc03343c)

### Option 3: DFT Calculations

- Most accurate (~1-2 ppm) but computationally expensive
- Not practical for ranking many solutions quickly
- Out of scope for this phase

## Similarity Scoring Approaches

| Method | Formula | Properties |
|--------|---------|------------|
| SAD (Sum Abs Diff) | Σ\|exp - pred\| | Used by pyLSD, simple, interpretable |
| MAE (Mean Abs Error) | SAD / n | Normalized by carbon count |
| RMSE | √(Σ(exp-pred)²/n) | Penalizes large deviations more |
| Cosine similarity | (exp·pred)/(∥exp∥∥pred∥) | Shift-invariant, good for patterns |

**Recommendation:** Start with MAE (like pyLSD but normalized). Simple, interpretable, matches expected accuracy (~2 ppm).

## Architecture Decision

### Use nmrshiftdb2 REST API

**Pros:**
- No local dependencies (no Java, no Docker)
- Always up-to-date database
- Same method pyLSD uses
- Simple HTTP calls

**Cons:**
- Network dependency
- Rate limits possible
- Slower than local (network latency)

### Alternative: Local HOSE Code Database

Build a local prediction database from nmrshiftdb SD file:
1. Parse nmrshiftdb SD file (already have NMRShiftDBLoader)
2. Generate HOSE codes for each atom using RDKit
3. Store HOSE code → shift mappings
4. Predict by HOSE code lookup

**Pros:**
- No network dependency
- Fast (in-memory lookup)
- Full control

**Cons:**
- More implementation work
- Need to implement HOSE code generation (RDKit can do this)
- Database frozen at download time

## Implementation Recommendation

**Phase 1: REST API approach (MVP)**
1. Call nmrshiftdb2 REST API for each solution SMILES
2. Parse response (CML or JCAMP format)
3. Extract predicted shifts per atom
4. Match predicted shifts to experimental peaks
5. Calculate MAE score
6. Sort solutions by score

**Phase 2: Local prediction (future optimization)**
- Build local HOSE database from nmrshiftdb SD file
- Generate HOSE codes with RDKit
- Fast in-memory prediction

## Key Libraries

| Library | Purpose | Install |
|---------|---------|---------|
| requests | HTTP calls to nmrshiftdb2 | `pip install requests` |
| RDKit | SMILES parsing, atom indexing | Already have |
| nmrshiftdb SD file | Reference data | Already have in data/reference/ |

## What NOT to Hand-Roll

- **HOSE code generation**: Use RDKit or CDK
- **Shift prediction algorithm**: Use nmrshiftdb2 (proven, maintained)
- **Solution parsing**: Already have LSDSolution with SMILES

## Common Pitfalls

1. **Atom numbering mismatch**: SMILES atom order vs. LSD atom numbering may differ. Need to map experimental shifts to correct atoms.

2. **Missing predictions**: Some atoms may not have HOSE code matches. Handle gracefully.

3. **Equivalent carbons**: Symmetric molecules have fewer NMR peaks than atoms. Multiple atoms may map to same experimental peak.

4. **Assignment problem**: Matching N predicted shifts to M experimental peaks when N ≠ M requires optimal assignment (Hungarian algorithm or greedy).

## Sources

- [pyLSD GitHub](https://github.com/nuzillard/PyLSD)
- [pyLSD Documentation](https://nuzillard.github.io/PyLSD/)
- [nmrshiftdb2 Paper (2024)](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/mrc.5418)
- [casekit - Java NMR tools](https://github.com/steinbeck/casekit)
- [nmrshiftdb_predictors_app](https://github.com/jvansan/nmrshiftdb_predictors_app)
- [nmrgnn - GNN predictor](https://github.com/ur-whitelab/nmrgnn)
- [Stereo HOSE codes paper](https://pubs.acs.org/doi/10.1021/acsomega.9b00488)
- [Very Deep GCN for 13C (2024)](https://pubs.acs.org/doi/10.1021/acs.jnatprod.3c00862)

---
*Research completed: 2026-01-11*
