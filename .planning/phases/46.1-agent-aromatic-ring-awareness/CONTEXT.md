# Phase 46.1 Context: Agent Aromatic Ring Awareness

## Background

Commit `2d4ce88` added an aromatic ring sanity check to the ranking code:
- `RankedSolution.has_aromatic_ring: bool` — set via RDKit `GetIsAromatic()` for each ranked solution
- `RankingResult.warnings: list[str]` — populated when >= 4 experimental shifts fall in 110-160 ppm but zero solutions contain aromatic rings
- CLI (`lucy lsd rank`) surfaces these in both JSON (`"warnings"` key, `"has_aromatic_ring"` per solution) and text output (`WARNING:` prefix)

## Problem: Agents Don't Read or Act on This

Exploration of all 4 specialist agent files confirmed:

| Agent | File | Lines | Aromatic awareness |
|-------|------|-------|--------------------|
| solution-analyst | `~/.claude/agents/lucy-solution-analyst.md` | 228 | None. Check 1 mentions "aromatic CH at 120-160 ppm" as a shift example only |
| nmr-chemist | `~/.claude/agents/lucy-nmr-chemist.md` | 260 | Labels 120-160 ppm as "Aromatic, alkenes" in shift table, no detection logic |
| devils-advocate | `~/.claude/agents/lucy-devils-advocate.md` | 337 | None. Validates LSD syntax, not solution chemistry |
| lsd-engineer | `~/.claude/agents/lucy-lsd-engineer.md` | 368 | sp2 parity rule only |

## Required Changes

### 1. solution-analyst (PRIMARY)

**Where:** Chemical Plausibility Assessment section (currently 5 checks)

Add Check 6: Aromatic Ring Verification
- After running `lucy lsd rank --format json`, check the `warnings` array
- If aromatic warning present, flag ALL solutions as QUESTIONABLE/IMPLAUSIBLE if they lack `has_aromatic_ring: true`
- Report to coordinator with specific remediation: "Remove HMBC correlations between aromatic ring positions and benzylic/alpha substituents — likely 4J couplings"
- This is the critical gap that caused the v4.0 hallucination (analyst declared a 7-membered ring as ibuprofen)

**Where:** Message interface / ranking workflow

- Parse `warnings` from JSON output (currently not read)
- Include warnings in [RANKING-COMPLETE] message to coordinator

### 2. nmr-chemist

**Where:** [SETUP-COMPLETE] message template

Add an "Aromatic expectation" field:
- Count carbons in 110-160 ppm from the picked 13C spectrum
- If >= 4: report "Aromatic ring expected (N carbons in 110-160 ppm)"
- This propagates the expectation to downstream agents (especially solution-analyst)

### 3. devils-advocate (OPTIONAL)

**Where:** Structural Integrity Checks or post-iteration validation

Could add: "If NMR-chemist flagged aromatic expectation, verify solutions contain aromatic ring"
- This is defense-in-depth; solution-analyst is the primary consumer
- Lower priority than the other two changes

## v4.0 UAT Evidence

From the ibuprofen CASE1 team run:
- NMR-chemist correctly identified 5 sp2 carbons at 127.26, 129.38, 137.16, 140.78, 141.28 ppm
- All 7 final solutions had 0 aromatic atoms (5/7/9-membered ring isomers)
- Solution-analyst ranked them and declared rank #1 = ibuprofen (hallucinated)
- No agent flagged the aromatic/non-aromatic mismatch

The ranking code now catches this, but the agents need to be told to read and act on it.
