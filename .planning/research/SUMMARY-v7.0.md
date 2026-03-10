# Research Summary: v7.0 Statistical 4J Detection

**Synthesized:** 2026-03-10
**Sources:** stack, features, architecture, pitfalls (4 parallel research agents)
**Overall confidence:** HIGH

## Key Findings

### 1. No New Dependencies Required
RDKit's `GetDistanceMatrix` (sub-microsecond per molecule) + existing SQLite database provide everything needed. No new Python packages.

### 2. HOSE Codes Are NOT the Right Tool for 4J Detection
HOSE codes encode per-atom environments, not pairwise bond-distance relationships. Direct bond-path mining from molecular graphs using RDKit is correct. However, HOSE codes at radius 2 are the right KEY for the statistics table (encoding carbon environment pairs).

### 3. LSD Natively Supports Extended Bond Range
`HMBC X Y 2 4` syntax allows 2-to-4 bond range — a middle ground between standard 2-3 bond and full deferral. `HMBC X Y 2 4` does NOT require ELIM (unlike `HMBC X Y 4`).

### 4. No Existing CASE System Has Automatic 4J Detection
Sherlock ignores 4J. WebCocon requires manual 4J-Flag annotation. ACD/SE uses reactive contradiction detection. Lucy-ng v7.0 would be a genuine competitive first.

### 5. Three-Tier Classification Recommended
| Probability | Classification | LSD Action |
|------------|----------------|------------|
| < 0.15 | unlikely_4j | Normal `HMBC X Y` (2-3 bonds) |
| 0.15 - 0.50 | possible_4j | `HMBC X Y 2 4` (extended range) |
| > 0.50 | likely_4j | Defer entirely |

### 6. False Positives Are More Dangerous Than False Negatives
Incorrectly deferring a valid 3J constraint is a NEW failure mode. WebCocon showed deferring too many correlations causes 1000x solution explosion (4 → 6,045). Cap at 3-4 deferred correlations.

### 7. Architecture Follows Existing Patterns
- New `coupling_path_stats` table (schema v7, additive migration)
- `CouplingPathStatsGenerator` following `BondPairStatsGenerator` pattern
- `detect_4j_coupling()` / `detect_4j_batch()` on `StatisticalDetector`
- CLI: `lucy detect 4j` / `lucy detect 4j-batch`
- Estimated generation: 13-26 hours (one-time, checkpointed)

### 8. Minimal Agent Changes
Replace heuristic shift-range check in nmr-chemist with one CLI call. lsd-engineer reads statistical risk scores instead of heuristic flags — same deferral mechanism. Run detection once during setup, not iteratively.

## Design Decisions

| Decision | Chosen | Alternative | Rationale |
|----------|--------|-------------|-----------|
| Statistics key | HOSE code pairs (R2) | Shift-bin pairs | HOSE R2 captures structural context (aromatic vs vinyl); shift bins can't distinguish |
| Storage | New table `coupling_path_stats` | Extend `hose_stats` | Pairwise relationship doesn't fit per-atom HOSE schema |
| Migration | ALTER TABLE (additive) | Full DB regeneration | New table is independent; no need to touch existing data |
| Detection timing | Once during setup | Every iteration | HMBC list and DB are static; results are deterministic |
| 4J action | Three-tier (include/extend/defer) | Binary (include/defer) | LSD HMBC bond range syntax enables middle ground |
| Thresholds | 0.15 / 0.50 (conservative) | 0.05 / 0.15 (aggressive) | False positives worse than false negatives |

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| False positives defer valid 3J | HIGH | MEDIUM | Conservative thresholds, cap at 3-4 deferrals |
| Generation takes >24 hours | LOW | MEDIUM | Checkpoint/resume pattern, test on 10K first |
| HOSE R2 data too sparse | MEDIUM | LOW | Fallback to R1 aggregation if needed |
| Agents don't use results correctly | HIGH | MEDIUM | UAT on ibuprofen mandatory |
| Schema change mid-milestone | MEDIUM | LOW | Design schema before generation code |

## Build Order (Dependencies)

```
Phase 1: Schema + Models (foundation)
    ↓
Phase 2: Generator + CLI generate command (database population)
    ↓
Phase 3: Detector + CLI detect commands (runtime detection)
    ↓
Phase 4: Agent skill updates (nmr-chemist, lsd-engineer, devils-advocate)
    ↓
Phase 5: UAT on ibuprofen (end-to-end validation)
```

## Detailed Research Files

- `.planning/research/STACK-v7.0-4j-detection.md` — Technology stack analysis
- `.planning/research/FEATURES-v7.0.md` — Feature landscape and specifications
- `.planning/research/architecture-v7.0-4j-detection.md` — Architecture design
- `.planning/research/PITFALLS-v7.0.md` — 11 pitfalls with mitigations
