---
phase: 39-agent-integration
researched: 2026-02-11
researcher: Claude (gsd-phase-researcher)
confidence: HIGH
---

# Phase 39 Research: Agent Integration

**Goal:** CASE agent autonomously uses statistical detection to write better-constrained LSD files

## Executive Summary

Phase 39 integrates all statistical detection CLI commands (Phases 34-37) into the autonomous CASE agent's workflow. This is primarily a **knowledge engineering task** rather than code implementation—the CLI commands are complete and working, the agent just needs to learn HOW and WHEN to use them.

**Key insight:** This is about teaching the agent a **chemistry-first hierarchy**: NMR evidence (DEPT, HSQC, HMBC) takes priority, statistical detection augments but doesn't override. The agent must understand threshold overrides for edge cases and document ambiguity rather than blindly trusting statistics.

**Estimated effort:** 5-7 days
- Agent knowledge update: 2-3 days (write detection protocol, examples, edge cases)
- Integration testing: 2-3 days (ibuprofen with aromatic detection, verify correct constraints)
- Documentation: 1 day (update CLAUDE.md with detection workflow)

**Success pattern:** Ibuprofen test case should produce correct aromatic phenylpropanoic acid structure at rank #1 (not cyclohexadiene), with hybridisation constraints from `lucy detect hybridisation` correctly identifying sp2 aromatic carbons in 120-140 ppm range.

---

## 1. Current State Analysis

### 1.1 What's Already Complete

**Phase 34: Hybridisation Detection ✓**
- CLI: `lucy detect hybridisation <db> <shift>`
- Returns: sp3/sp2/sp1 frequency distribution
- Database: Extended with hybridisation columns (sp3_count, sp2_count, sp1_count)
- Default threshold: 1% (filters rare states)

**Phase 35: Neighbourhood Detection ✓**
- CLI: `lucy detect neighbours <shift>`
- Returns: Forbidden (<1%) and mandatory (>95%) bond partners
- Database: Extended with neighbor columns (has_carbon_neighbor, etc.)
- Elements tracked: C, O, N, S, halogen

**Phase 36: HHB Detection ✓**
- CLI: `lucy detect hhb <db> <formula>`
- Returns: Allowed hetero-hetero bond pairs (>1% frequency)
- Use case: Decide whether to add O-O, N-N, O-N constraints

**Phase 37: Signal Grouping ✓**
- CLI: `lucy analyze grouping <shifts>`
- Returns: Clusters within 0.25 ppm tolerance, multiplicity-aware
- Use case: Generate LSD parenthesized atom lists for ambiguous assignments

**Phase 38: Two-Tier Ranking and Badlist ✓**
- Ranking: Match count first, MAE second (prevents hallucinations)
- Badlist: DEFF NOT patterns for 3/4-membered rings already in agent knowledge

### 1.2 Current Agent Architecture

**Location:** `~/.claude/agents/lucy-case-agent.md` (currently ~700 lines)

**Structure:**
```markdown
<role> — Agent identity and prohibitions
<inlined_critical_knowledge>
  1. NMR Background (40 lines)
  2. Spectral Quality Assessment (100 lines)
  3. LSD Command Reference (200 lines)
  4. Incremental HMBC Strategy (120 lines)
  5. CASE Workflow (150 lines)
  6. Error Tolerance (90 lines)
  7. Confidence Scoring (60 lines)
  8. CASE-PROGRESS.md Format (80 lines)
</inlined_critical_knowledge>
<workflow> — Step-by-step execution
```

**Key characteristics:**
- **All knowledge is inlined** (doesn't read external files during execution)
- **Thin CLI tools** (Bash commands, no Python API)
- **Document-driven** (CASE-PROGRESS.md is primary output)
- **Autonomous** (makes decisions, orchestrator only intervenes on loops)

### 1.3 Where Statistical Detection Fits

**Current agent workflow (Step 4: LSD Generation):**

```
1. Assess spectral quality (S/N, resolution)
2. Pick peaks (13C, DEPT, HSQC, HMBC)
3. Assign multiplicities (CH3/CH2/CH/Cq)
4. Write LSD file:
   - MULT definitions (from DEPT/HSQC)
   - HSQC correlations
   - Heteroatom constraints (formula-based guessing)
   - First batch of HMBC correlations
5. Run LSD, iterate
```

**NEW workflow with statistical detection:**

```
1. Assess spectral quality (S/N, resolution)
2. Pick peaks (13C, DEPT, HSQC, HMBC)
3. Assign multiplicities (CH3/CH2/CH/Cq)
4. STATISTICAL DETECTION (NEW):
   a. For each 13C shift, query hybridisation (sp2/sp3)
   b. For carbonyl/aromatic shifts, query neighbors (mandatory O? forbidden halogen?)
   c. For formula with multiple heteroatoms, query HHB (allow N-O? forbid O-O?)
   d. For close shifts, query grouping (ambiguous CH/CH3 at 30.1/30.3?)
5. Write LSD file:
   - MULT definitions WITH hybridisation hints (MULT 1 C 2 0 for sp2)
   - HSQC correlations
   - Heteroatom constraints WITH neighbor detection (PROP for mandatory O)
   - ELIM forbidden neighbors (if detected)
   - LIST for signal grouping (if detected)
   - First batch of HMBC correlations
6. Run LSD, iterate
```

---

## 2. Chemistry-First Hierarchy (Critical Design Principle)

### 2.1 The Principle

**Rule:** NMR experimental evidence ALWAYS takes priority over statistical detection.

**Why:** Statistical detection uses database frequencies (~7.9M observations from COCONUT + NMRShiftDB). These are TYPICAL patterns, not universal laws. Edge cases exist:
- Peroxides have O-O bonds (<1% in database, but valid)
- Unusual functional groups have atypical neighbors
- Conjugation shifts hybridisation expectations

**Hierarchy:**

| Priority | Evidence Type | Trust Level | When to Override |
|----------|---------------|-------------|------------------|
| 1 (HIGHEST) | DEPT sign | 100% | NEVER — CH2 negative peaks are definitive |
| 2 | HSQC correlations | 95% | Only if spectral quality is poor (SNR < 10) |
| 3 | HMBC correlations | 80% | Can exclude with ELIM if conflict detected |
| 4 | Chemical shift ranges | 70% | General guidelines (carbonyl >160 ppm) |
| 5 (LOWEST) | Statistical detection | 60% | Override if NMR evidence contradicts |

### 2.2 Application Examples

**Example 1: Hybridisation Detection Contradicts DEPT**

Scenario:
- 13C shift at 132.5 ppm
- DEPT-135: negative peak → CH2 (definitive)
- `lucy detect hybridisation 132.5`: returns sp2 = 92%, sp3 = 8%

**Correct response:**
```markdown
## Statistical Detection vs NMR Evidence

Shift 132.5 ppm shows sp2 = 92% in database (aromatic carbon).
However, DEPT-135 shows NEGATIVE peak → CH2 (saturated, sp3).

**Resolution:** TRUST DEPT. This is likely a CH2 group adjacent to conjugated system
(e.g., allylic position), causing downfield shift. NMR trumps statistics.

LSD definition: MULT 5 C 3 2  ; sp3 CH2, not sp2 (DEPT wins)
```

**Example 2: Neighbor Detection Suggests Oxygen, But No Oxygen in Formula**

Scenario:
- 13C shift at 65.3 ppm
- Molecular formula: C10H16 (no oxygen)
- `lucy detect neighbours 65.3`: returns O mandatory = 98%

**Correct response:**
```markdown
## Statistical Detection Error

Shift 65.3 ppm suggests O neighbor (98% frequency in database).
However, molecular formula C10H16 contains NO oxygen.

**Resolution:** Statistical detection is WRONG. This is likely a carbon alpha to
nitrogen or sulfur (if formula allows), or a quaternary carbon in strained ring system.
Do NOT add oxygen to formula. Ignore neighbor detection result.
```

**Example 3: HHB Detection Forbids O-O, But Evidence Suggests Peroxide**

Scenario:
- Molecular formula: C8H14O4
- 13C shifts at 83.2 ppm, 84.1 ppm (characteristic of C-O-O-C)
- `lucy detect hhb C8H14O4`: returns O-O forbidden (0.3% frequency)

**Correct response:**
```markdown
## Rare But Valid: Peroxide Functional Group

Statistical detection forbids O-O bonds (0.3% frequency).
However, two carbons at 83-84 ppm with formula containing 4 oxygens suggest peroxide.

**Resolution:** OVERRIDE statistics. Allow O-O bond in LSD file.
Document reasoning in CASE-PROGRESS.md: "Peroxide functional group suspected
based on characteristic C-O-O shifts. Rare but chemically valid."

LSD constraints:
MULT 5 C 3 1   ; carbon at 83.2 ppm
MULT 6 C 3 1   ; carbon at 84.1 ppm
MULT 15 O 3 0  ; peroxide oxygen #1
MULT 16 O 3 0  ; peroxide oxygen #2
BOND 5 15      ; C-O
BOND 15 16     ; O-O (allowed despite statistics)
BOND 16 6      ; O-C
```

### 2.3 Decision Tree for Conflicts

```
IF (statistical detection contradicts NMR evidence):
    1. Check spectral quality:
       - SNR > 30 → TRUST NMR
       - SNR < 10 → Consider statistics as tiebreaker

    2. Check molecular formula:
       - Formula forbids element → IGNORE neighbor detection
       - Formula allows element → Statistics augment, don't override

    3. Document reasoning in CASE-PROGRESS.md:
       - "Hybridisation detection suggests sp2, but DEPT shows CH2 → TRUST DEPT"
       - "Neighbor detection suggests O, but formula is hydrocarbon → IGNORE"

    4. Use statistics as HINTS, not RULES:
       - sp2 detection = "likely aromatic" (check HMBC for ring closure)
       - Mandatory O neighbor = "check for carbonyl or ether" (don't force it)
```

---

## 3. Statistical Detection Protocol (What Agent Must Learn)

### 3.1 When to Call Each Command

**Hybridisation Detection:**

| When to Call | Shifts to Query | Use Case |
|--------------|-----------------|----------|
| After 13C peak picking | 120-160 ppm range | Disambiguate aromatic (sp2) from aliphatic (sp3) |
| Before MULT definitions | Carbonyl region (160-220 ppm) | Confirm sp2 for C=O carbon |
| When DEPT/HSQC ambiguous | Any shift with conflicting evidence | Tiebreaker for multiplicity |

**CLI usage:**
```bash
lucy detect hybridisation 132.5 --radius 3 --window 2.0 --format json
```

**Agent interpretation:**
- sp2 > 80% → Likely aromatic or carbonyl, set MULT hybridisation to 2
- sp3 > 80% → Saturated, set MULT hybridisation to 3
- Mixed distribution (40-60%) → Ambiguous, use NMR evidence as tiebreaker

**Neighbourhood Detection:**

| When to Call | Shifts to Query | Use Case |
|--------------|-----------------|----------|
| After heteroatom counting | 160-220 ppm (carbonyl) | Confirm mandatory O for C=O |
| For C-X bonds | 50-90 ppm | Detect mandatory O/N/halogen neighbors |
| Before heteroatom constraints | Any shift with heteroatom evidence | Identify forbidden partners |

**CLI usage:**
```bash
lucy detect neighbours 175.3 --mode strict --format json
```

**Agent interpretation:**
- Forbidden (<1%) → Add ELIM constraint or LIST exclusion
- Mandatory (>95%) → Add PROP constraint for "must have neighbor"
- Typical (1-95%) → No constraint, let LSD explore

**HHB Detection:**

| When to Call | When | Use Case |
|--------------|------|----------|
| After molecular formula confirmed | Formula with 2+ heteroatoms | Decide if N-O, O-O, N-N bonds allowed |
| Before heteroatom BOND constraints | Any formula with O2+ or N2+ | Avoid over-constraining rare bonds |

**CLI usage:**
```bash
lucy detect hhb data/reference/lucy-ng-derep.db C13H18O2 --format json
```

**Agent interpretation:**
- O-O forbidden → Don't add O-O BOND (unless peroxide evidence)
- N-O allowed → Consider N-oxide or hydroxylamine structures
- N-N allowed → Consider hydrazine derivatives

**Signal Grouping:**

| When to Call | When | Use Case |
|--------------|------|----------|
| After 13C peak picking | Any time peaks are closer than 0.5 ppm | Identify ambiguous assignments |
| Before HMBC constraint writing | Close quaternary carbons | Generate parenthesized lists for LSD |

**CLI usage:**
```bash
lucy analyze grouping "130.2,130.4,155.1,155.3" --tolerance 0.25 --format json
```

**Agent interpretation:**
- Grouped signals → Use LSD LIST and parenthesized HMBC: `HMBC (5 6) 10`
- Isolated signals → Standard HMBC: `HMBC 5 10`

### 3.2 Integration Workflow

**Step 4 (LSD Generation) - EXPANDED:**

```markdown
4. Statistical Detection Phase (NEW):

   a. Run hybridisation detection for all 13C shifts:
      ```bash
      for shift in 13C_peaks:
          lucy detect hybridisation $shift --format json > hyb_$shift.json
      ```

   b. Classify carbons by hybridisation:
      - sp2 carbons (>80% sp2): Likely aromatic or carbonyl
      - sp3 carbons (>80% sp3): Saturated
      - Ambiguous (40-60%): Flag for manual inspection

   c. Run neighborhood detection for heteroatom-bearing carbons:
      ```bash
      for shift in 50-90_ppm_range + 160-220_ppm_range:
          lucy detect neighbours $shift --format json > nbr_$shift.json
      ```

   d. Identify constraints:
      - Forbidden neighbors (<1%): Consider ELIM or LIST exclusion
      - Mandatory neighbors (>95%): Add PROP constraint

   e. Run HHB detection if formula has 2+ heteroatoms:
      ```bash
      lucy detect hhb <db> <formula> --format json > hhb.json
      ```

   f. Run signal grouping for close shifts:
      ```bash
      lucy analyze grouping "$all_13C_shifts" --format json > grouping.json
      ```

   g. Document all detection results in CASE-PROGRESS.md:
      - Which shifts were queried
      - What constraints were identified
      - Any conflicts with NMR evidence (and resolution)
      - Any threshold overrides applied

5. Write LSD file WITH statistical constraints:

   a. MULT definitions:
      ```
      ; Use hybridisation detection to set sp2/sp3
      MULT 1 C 2 0   ; 155.2 ppm: sp2 (92% aromatic)
      MULT 2 C 2 1   ; 132.5 ppm: sp2 (88% aromatic)
      MULT 3 C 3 2   ; 30.1 ppm: sp3 (96% saturated)
      ```

   b. Heteroatom constraints WITH neighbors:
      ```
      ; Carbonyl at 175.3 ppm: O mandatory (98%)
      MULT 10 C 2 0   ; carbonyl carbon (sp2)
      MULT 14 O 2 0   ; carbonyl oxygen (sp2)
      BOND 10 14      ; C=O double bond

      ; Neighbor constraint: C10 must have O neighbor (mandatory)
      LIST L_carbonyl 10
      ELEM L_oxygen O
      PROP L_carbonyl 1 L_oxygen  ; enforces mandatory O
      ```

   c. Forbidden neighbor constraints:
      ```
      ; Halogen forbidden at 155.2 ppm (0% in database)
      ELEM L_halogen F Cl Br I
      LIST L_aromatic 1 2
      PROP L_aromatic 0 L_halogen  ; no halogen neighbors
      ```

   d. Signal grouping for ambiguous assignments:
      ```
      ; Close signals at 130.2/130.4 ppm (ambiguous)
      LIST L_close 5 6
      ; Use parenthesized HMBC:
      HMBC (5 6) 10   ; either carbon 5 or 6 correlates to H10
      ```
```

### 3.3 Threshold Override Examples

**When to use --mode relaxed:**

```bash
# Rare molecule with unusual functional groups
lucy detect neighbours 85.3 --mode relaxed --format json

# Effect: Changes thresholds from 1%/95% to 0.1%/99%
# Use case: Peroxide, aziridine, or other statistically rare but chemically valid groups
```

**When to use --min-frequency / --max-frequency:**

```bash
# Allow slightly more flexibility on neighbor detection
lucy detect neighbours 170.5 --min-frequency 0.005 --max-frequency 0.98 --format json

# Effect: Forbidden = <0.5%, Mandatory = >98%
# Use case: Borderline cases where 1%/95% is too strict
```

**When to override radius:**

```bash
# Try tighter structural context (more specific)
lucy detect hybridisation 132.5 --radius 4 --format json

# Effect: Uses HOSE codes with larger sphere (more detail)
# Use case: Default radius 3 returns ambiguous distribution, try radius 4 for specificity
```

### 3.4 Documentation Requirements

**CASE-PROGRESS.md entry for statistical detection:**

```markdown
## Iteration 1: Initial LSD with Statistical Constraints

**Time:** 2026-02-11 14:32:15
**LSD file:** analysis/iteration_01/compound.lsd
**Solution count:** 47

**Statistical Detection Results:**

Hybridisation:
- 155.2 ppm: sp2 = 92%, sp3 = 8% → Aromatic (MULT 2)
- 132.5 ppm: sp2 = 88%, sp3 = 12% → Aromatic (MULT 2)
- 30.1 ppm: sp3 = 96%, sp2 = 4% → Saturated (MULT 3)

Neighbors:
- 175.3 ppm: O mandatory (98%) → Added PROP constraint for C=O
- 65.2 ppm: O typical (45%) → No constraint (let LSD decide)
- 155.2 ppm: Halogen forbidden (0%) → Added PROP exclusion

HHB (C13H18O2):
- O-O: 0.3% (forbidden) → No O-O bonds allowed
- N-N: N/A (no nitrogen in formula)

Signal Grouping:
- No close signals detected (minimum spacing: 1.2 ppm)

**Constraints added:**
- Hybridisation: 3 carbons set to sp2 based on database (120-160 ppm range)
- Mandatory O neighbor for carbonyl carbon at 175.3 ppm (PROP constraint)
- Forbidden halogen neighbors for aromatic carbons (PROP exclusion)
- DEFF NOT patterns for strained rings (from badlist)

**Chemistry-first hierarchy applied:**
- DEPT shows CH2 at 132.5 ppm (negative peak), but statistics suggest sp2
- Resolution: TRUST DEPT, set to sp3 despite statistics (documented conflict)

**Why:** Statistical detection provides initial constraints to reduce search space.
NMR evidence takes priority when conflicts arise. Expecting solution count to drop
significantly with hybridisation hints.

**HMBC correlations used:** 5/34 (high-confidence batch only)
```

---

## 4. Implementation Strategy

### 4.1 Three-Plan Structure

**Plan 39-01: Agent Knowledge Update**

Scope:
- Add "Statistical Detection Protocol" section to lucy-case-agent.md
- Document chemistry-first hierarchy with examples
- Update "CASE Workflow" section (Step 4) with detection commands
- Add "Common Pitfalls" for detection (when NOT to trust statistics)

Content:
1. When to call each detection command (timing in workflow)
2. How to interpret results (threshold meanings)
3. How to write LSD constraints from detection output
4. Conflict resolution (NMR vs statistics)
5. Threshold overrides (--mode relaxed, custom thresholds)
6. Documentation requirements (CASE-PROGRESS.md format)

Location: Insert after "LSD Command Reference" section, before "Incremental HMBC Strategy"

**Plan 39-02: Chemistry-First Hierarchy Rules**

Scope:
- Document evidence priority levels (DEPT > HSQC > statistical detection)
- Add decision tree for conflict resolution
- Provide 5-10 real-world examples (peroxide, allylic CH2, etc.)
- Create "When to Override" guidelines

Content:
1. Evidence priority table (5 levels)
2. Conflict resolution flowchart
3. Override examples with CLI commands
4. Edge case handling (rare functional groups)
5. Documentation requirements for overrides

Location: New section "Chemistry-First Hierarchy" in lucy-case-agent.md

**Plan 39-03: Integration Testing with Ibuprofen**

Scope:
- Run full CASE workflow on ibuprofen with statistical detection enabled
- Verify correct aromatic structure at rank #1 (not cyclohexadiene)
- Verify hybridisation detection correctly identifies sp2 aromatic carbons
- Document all detection queries and results

Success criteria:
1. Agent calls `lucy detect hybridisation` for aromatic region (120-140 ppm)
2. Agent sets MULT hybridisation to 2 for aromatic carbons (6 expected)
3. Agent calls `lucy detect neighbours` for C-O ether carbon (~65 ppm)
4. LSD solution count < 50 (statistical constraints reduce search space)
5. Correct ibuprofen structure ranks #1 (SMILES matches known structure)
6. No cyclohexadiene solutions in top 10 (badlist + hybridisation prevent this)
7. CASE-PROGRESS.md documents all detection results with reasoning

Testing approach:
- Use existing data/Ibuprofen/ test dataset
- Run /lucy-ng:case with updated agent
- Compare against v2.1 baseline (should rank better with constraints)

### 4.2 Knowledge Engineering Challenges

**Challenge 1: Balancing Verbosity vs Clarity**

Problem: Agent needs enough detail to use commands correctly, but too much knowledge bloats the 700-line agent file.

Solution:
- Keep examples MINIMAL (1-2 per concept)
- Use tables for reference (when to call, how to interpret)
- Reference full syntax from CLI --help (don't duplicate)
- Focus on REASONING, not syntax memorization

**Challenge 2: Teaching "When Not to Use" Detection**

Problem: Agent might over-rely on statistics, ignoring NMR evidence.

Solution:
- Lead with "Chemistry-First Hierarchy" section (priority explicit)
- Add "Common Mistakes" subsection with examples of wrong usage
- Require documentation of conflicts in CASE-PROGRESS.md
- Test with edge cases (peroxide, strained rings, unusual shifts)

**Challenge 3: Threshold Override Decision Logic**

Problem: When should agent use --mode relaxed vs strict?

Solution:
- Default to strict (1%/95% thresholds)
- Use relaxed ONLY when:
  - Molecular formula suggests rare functional group (peroxide, aziridine)
  - NMR evidence contradicts strict detection (document reasoning)
  - Iteration count > 5 with no convergence (loosen constraints)
- Document override reasoning EVERY time

**Challenge 4: Integration with Existing Pitfalls**

Problem: Existing agent knowledge has Pitfalls 1-7 (symmetry, quaternary carbons, etc.). Statistical detection adds new failure modes.

Solution:
- Add "Pitfall 8: Over-Trusting Statistical Detection"
- Add "Pitfall 9: Ignoring Detection When It's Right"
- Cross-reference with existing pitfalls (Pitfall 2 + detection = better quaternary carbon constraints)

### 4.3 Testing Matrix

| Test Case | Detection Type | Expected Behavior | Success Metric |
|-----------|----------------|-------------------|----------------|
| Ibuprofen | Hybridisation | Aromatic carbons (sp2) detected at 120-140 ppm | Correct structure at rank #1 |
| Peroxide compound | HHB + Neighbors | O-O allowed despite <1%, documented override | Agent documents reasoning, allows O-O |
| Allylic CH2 | Hybridisation | Statistics suggest sp2, DEPT shows CH2 → TRUST DEPT | MULT set to sp3 with conflict note |
| Carbonyl region | Neighbors | O mandatory at 175 ppm → PROP constraint added | LSD file has PROP for C=O |
| Close signals | Grouping | 130.2/130.4 clustered → Parenthesized HMBC | LSD has `HMBC (5 6) 10` syntax |
| Hydrocarbon | Neighbors | O/N suggested but formula forbids → IGNORE | Agent documents formula check |

---

## 5. Risks and Mitigations

### 5.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Agent ignores detection results | Medium | High | Add explicit "MUST call detection" requirements in workflow |
| Agent trusts statistics over NMR | High | Critical | Lead with chemistry-first hierarchy, test with edge cases |
| Agent calls detection too often (slow) | Medium | Low | Document "when to call" with specific shift ranges |
| Detection commands fail (bad database) | Low | High | Check database schema version in agent preamble |
| Threshold overrides used incorrectly | Medium | Medium | Require documentation of override reasoning every time |

### 5.2 Knowledge Engineering Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Agent doesn't understand hierarchy | High | Critical | Test with conflicting evidence cases, verify resolution |
| Examples too complex (agent confused) | Medium | Medium | Keep examples minimal, focus on decision logic |
| Agent over-constrains with statistics | Medium | High | Add "let LSD explore" guidance, test solution count |
| Documentation bloat (700 → 1000 lines) | High | Low | Consolidate tables, use references to CLI help |

### 5.3 Integration Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Detection breaks existing CASE runs | Low | High | Test regression on sarocladone A, existing compounds |
| Orchestrator confused by detection output | Low | Medium | Detection results go in CASE-PROGRESS.md (already monitored) |
| CLI commands changed since Phase 37 | Very Low | Medium | Verify CLI --help output before writing knowledge |

---

## 6. Open Questions for Planner

### Q1: Should agent call detection for ALL shifts or just suspicious ones?

**Options:**

A. Call detection for EVERY 13C shift (comprehensive, slow)
B. Call detection only for specific regions (120-160 aromatic, 160-220 carbonyl, 50-90 C-X)
C. Call detection only when DEPT/HSQC evidence is ambiguous (minimal, fast)

**Recommendation:** Option B (selective by shift range)

**Rationale:**
- Option A: Too slow (30-50 CLI calls per compound), marginal benefit
- Option C: Misses opportunities (aromatic detection even when DEPT clear)
- Option B: Balances thoroughness with performance (~10-15 calls per compound)

**Shift ranges to query:**
- 120-160 ppm: Hybridisation (aromatic detection)
- 160-220 ppm: Hybridisation + Neighbors (carbonyl detection)
- 50-90 ppm: Neighbors (C-O, C-N detection)
- <50 ppm: Skip (aliphatic region, rarely ambiguous)

### Q2: Should detection results be cached across iterations?

**Context:** Agent runs 3-10 LSD iterations. Detection results don't change between iterations (same shifts).

**Options:**

A. Re-run detection every iteration (safest, redundant)
B. Cache detection results in first iteration, reuse in subsequent iterations
C. Cache results in JSON files, check if exists before querying

**Recommendation:** Option A for Phase 39 (defer caching to Phase 40)

**Rationale:**
- Detection commands are fast (~100ms per query)
- Caching adds complexity (file management, cache invalidation)
- Agent can re-run detection in 1-2 seconds total per iteration
- Premature optimization

### Q3: How to handle detection failures (no data)?

**Context:** Some shifts may not be in database (extreme outliers, database coverage gaps).

**Options:**

A. Fail the CASE run (too strict)
B. Warn and continue without constraints (silent failure)
C. Document missing data, use chemical shift heuristics as fallback

**Recommendation:** Option C (document + fallback)

**Rationale:**
- Option A: Breaks CASE on edge cases unnecessarily
- Option B: Agent might not notice, under-constrain LSD
- Option C: Transparent, uses existing shift range knowledge from Pitfall sections

**Fallback heuristics:**
- 120-160 ppm: Assume sp2 (aromatic/alkene)
- 160-220 ppm: Assume sp2 + O neighbor (carbonyl)
- 50-90 ppm: Assume O/N neighbor (C-X bond)

### Q4: Should signal grouping be automatic or manual trigger?

**Context:** Signal grouping is useful for close shifts, but not all compounds have them.

**Options:**

A. Always call `lucy analyze grouping` for all shifts (comprehensive)
B. Call only if minimum spacing < 0.5 ppm detected (conditional)
C. Let agent decide based on symmetry analysis (manual)

**Recommendation:** Option A (always call, fast command)

**Rationale:**
- Grouping command is very fast (no database query, just clustering)
- Returns empty groups if no close signals (harmless)
- Agent can ignore results if no groups detected
- Simpler logic than conditional calling

### Q5: How to integrate with existing Pitfall 6 (heteroatom constraints)?

**Context:** Pitfall 6 currently teaches "don't over-constrain heteroatoms, use LIST/PROP for flexibility". Statistical detection adds neighbor constraints.

**Options:**

A. Replace Pitfall 6 with detection-based approach
B. Keep Pitfall 6, add detection as supplementary validation
C. Merge Pitfall 6 and detection into unified heteroatom strategy

**Recommendation:** Option C (merge into unified strategy)

**Rationale:**
- Pitfall 6 is about constraint strategy (don't guess)
- Detection provides DATA to make better decisions
- Combined approach: "Use detection to identify mandatory neighbors, then express with LIST/PROP"

**New unified Pitfall 6:**
```markdown
### Pitfall 6: Heteroatom Constraint Strategy

**Principle:** Express what you KNOW (from NMR + statistics), not what you GUESS.

**Workflow:**
1. Query neighbor detection for C-X bonds (50-90 ppm, 160-220 ppm)
2. Identify mandatory neighbors (>95% frequency)
3. Express with LIST/PROP, not hardcoded BOND (flexibility)
4. For ambiguous (1-95%), use LSD exploration (no constraint)

**Example:**
```bash
lucy detect neighbours 65.3 --format json
# Returns: O mandatory (97%)

LSD file:
ELEM L_oxygen O
LIST L_c_x 8
PROP L_c_x 1 L_oxygen  ; enforces mandatory O, but doesn't specify WHICH O
```

This replaces guessing with data-driven constraints while preserving flexibility.
```

---

## 7. Success Metrics

### 7.1 Agent Behavior Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Detection calls per compound | 10-15 | Count Bash calls to `lucy detect` in agent run |
| Hybridisation constraints in LSD | >50% of carbons | Parse MULT lines, count hybridisation hints |
| Neighbor constraints in LSD | >0 for carbonyl/C-X | Parse PROP lines, verify presence |
| Conflicts documented | 100% | Grep CASE-PROGRESS.md for "conflict" or "override" |
| NMR priority respected | 100% | Manual review of conflict resolutions |

### 7.2 Structure Elucidation Metrics

| Metric | Baseline (v2.1) | Target (v3.0) | Test Case |
|--------|-----------------|---------------|-----------|
| Ibuprofen rank | #3 (cyclohexadiene #1) | #1 (correct aromatic) | Ibuprofen CASE run |
| Solution count | 120 avg | <50 avg | Statistical constraints reduce search space |
| MAE at rank #1 | 2.13 ppm | <2.5 ppm | Correct structure should have good MAE |
| Aromatic detection accuracy | N/A | >90% | Verify sp2 carbons in 120-140 ppm range |

### 7.3 Documentation Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Detection results in CASE-PROGRESS.md | 100% | Every detection call documented |
| Conflict resolution reasoning | 100% | Every override has "because..." explanation |
| Chemistry-first priority mentioned | >80% of conflicts | Grep for "DEPT/HSQC/NMR" in conflict notes |

---

## 8. Effort Estimation

### 8.1 Task Breakdown

| Task | Effort (days) | Dependencies | Risk |
|------|---------------|--------------|------|
| Write detection protocol section | 1.5 | None | Low |
| Write chemistry-first hierarchy section | 1.0 | None | Medium |
| Add threshold override examples | 0.5 | Protocol complete | Low |
| Update CASE workflow (Step 4) | 1.0 | Protocol complete | Low |
| Merge Pitfall 6 with detection | 0.5 | Hierarchy complete | Medium |
| Update CLAUDE.md with detection workflow | 0.5 | All agent updates complete | Low |
| Ibuprofen integration test | 1.5 | All updates complete | High |
| Edge case testing (peroxide, allylic) | 1.0 | Ibuprofen passing | Medium |
| Regression testing (sarocladone, etc.) | 1.0 | Integration tests passing | Medium |

**Total estimated effort:** 8.5 days

**Critical path:** Detection protocol → CASE workflow update → Ibuprofen test

**Parallel work:** Chemistry-first hierarchy and threshold overrides can be written simultaneously with detection protocol.

### 8.2 Risk Multipliers

| Risk Factor | Multiplier | Justification |
|-------------|------------|---------------|
| Knowledge engineering complexity | 1.2x | Teaching hierarchy to agent is subtle |
| Edge case discovery | 1.1x | May find new conflicts during testing |
| Agent behavior unpredictability | 1.3x | Agent may not follow instructions perfectly |

**Risk-adjusted estimate:** 8.5 × 1.2 × 1.1 × 1.3 = **14.6 days worst case**

**Recommended timeline:** 7-10 days (median between best/worst case)

---

## 9. Plan Structure Recommendation

### Plan 39-01: Update lucy-case-agent.md with Statistical Detection Workflow

**Objective:** Add detection protocol section to agent knowledge

**Scope:**
- New section: "Statistical Detection Protocol" (~150 lines)
- Updated section: "CASE Workflow Step 4" (~50 lines)
- Updated section: "Pitfall 6" (merge with detection) (~80 lines)

**Content:**
1. When to call each detection command (table format)
2. How to interpret results (threshold meanings)
3. How to write LSD constraints from detection output (examples)
4. Documentation requirements (CASE-PROGRESS.md template)

**Location:** Insert after "LSD Command Reference", before "Incremental HMBC Strategy"

**Success criteria:**
- Agent successfully calls detection commands in correct workflow order
- Detection results appear in CASE-PROGRESS.md with reasoning
- LSD files contain detection-based constraints (MULT hybridisation, PROP neighbors)

**Estimated effort:** 2-3 days

---

### Plan 39-02: Add Chemistry-First Hierarchy Rules and Threshold Override Examples

**Objective:** Teach agent evidence priority and conflict resolution

**Scope:**
- New section: "Chemistry-First Hierarchy" (~120 lines)
- New subsection: "Threshold Overrides" (~60 lines)
- New subsection: "When Not to Use Detection" (~40 lines)

**Content:**
1. Evidence priority table (5 levels)
2. Conflict resolution decision tree
3. 5-10 real-world examples (peroxide, allylic CH2, formula mismatch, etc.)
4. Override CLI examples (--mode relaxed, custom thresholds)
5. Edge case handling guidelines

**Location:** After "Statistical Detection Protocol"

**Success criteria:**
- Agent resolves conflicts correctly (DEPT > statistics)
- Agent documents reasoning for overrides
- Agent uses --mode relaxed appropriately (rare functional groups)
- Agent doesn't over-constrain with statistics

**Estimated effort:** 2 days

---

### Plan 39-03: Create Integration Test with Ibuprofen (verify correct aromatic structure found)

**Objective:** Validate detection-augmented CASE on known test case

**Scope:**
- Full CASE run on data/Ibuprofen/
- Verify aromatic detection (sp2 identification)
- Verify neighbor detection (C-O ether bond)
- Verify solution ranking (correct structure #1)
- Document all detection queries and results

**Success criteria:**
1. Agent calls `lucy detect hybridisation` for 6 aromatic carbons (120-140 ppm)
2. Agent sets MULT hybridisation to 2 for aromatic carbons
3. Agent calls `lucy detect neighbours` for C-O carbon (~65 ppm)
4. LSD solution count < 50 (constraints reduce search space)
5. Correct ibuprofen structure ranks #1
6. No cyclohexadiene in top 10 (badlist + hybridisation prevent)
7. CASE-PROGRESS.md documents all detection with reasoning

**Test data:** tests/data/Ibuprofen/ (Bruker NMR dataset)

**Baseline comparison:** v2.1 result (cyclohexadiene at rank #1)

**Regression tests:**
- Sarocladone A (ensure existing CASE still works)
- Any other v2.1 successful compounds

**Estimated effort:** 3 days (1.5 integration, 1 edge cases, 0.5 regression)

---

## 10. Dependencies and Blockers

### 10.1 Prerequisites

| Dependency | Status | Notes |
|------------|--------|-------|
| Phase 34 (hybridisation CLI) | ✓ COMPLETE | `lucy detect hybridisation` working |
| Phase 35 (neighborhood CLI) | ✓ COMPLETE | `lucy detect neighbours` working |
| Phase 36 (HHB CLI) | ✓ COMPLETE | `lucy detect hhb` working |
| Phase 37 (signal grouping CLI) | ✓ COMPLETE | `lucy analyze grouping` working |
| Phase 38 (two-tier ranking + badlist) | ✓ COMPLETE | Agent already has badlist knowledge |
| Database v6 schema | ✓ COMPLETE | All detection columns present |

**No blockers.** All dependencies satisfied.

### 10.2 Downstream Impact

| Affected Component | Impact | Mitigation |
|-------------------|--------|------------|
| CASE agent file size | Grows from ~700 to ~900 lines | Consolidate tables, use references |
| CASE runtime | Increases by ~2-3 seconds per iteration | Acceptable (detection queries fast) |
| CASE-PROGRESS.md size | Grows with detection results | Already append-only, not a problem |
| Orchestrator monitoring | Must parse new detection sections | Already reads CASE-PROGRESS.md, no changes needed |

**Low impact.** Changes are isolated to agent knowledge.

---

## 11. Summary: What You Need to Know to Plan Well

### 11.1 Key Insights

1. **This is knowledge engineering, not code**: All CLI commands exist and work. The challenge is teaching the agent HOW and WHEN to use them.

2. **Chemistry-first hierarchy is critical**: Agent must respect NMR evidence over statistics. This requires explicit priority levels and conflict resolution examples.

3. **Selective detection is sufficient**: Don't query ALL shifts (slow), query specific regions (aromatic, carbonyl, C-X bonds) where detection adds value.

4. **Ibuprofen is the perfect test case**: Known failure mode (cyclohexadiene hallucination) should be fixed by aromatic detection.

5. **Integration risk is manageable**: Detection results go in CASE-PROGRESS.md (already monitored), agent behavior changes are testable.

### 11.2 Critical Decisions

| Decision | Recommendation | Rationale |
|----------|----------------|-----------|
| When to call detection | Selective (by shift range) | Balances thoroughness with performance |
| Evidence priority | DEPT > HSQC > detection | NMR experimental evidence always wins |
| Threshold overrides | Document every override | Transparency for debugging |
| Caching detection results | No caching (Phase 39) | Premature optimization |
| Detection failure handling | Document + fallback heuristics | Graceful degradation |

### 11.3 Three-Plan Structure

**39-01: Agent Knowledge Update (2-3 days)**
- Detection protocol section (~150 lines)
- CASE workflow update (~50 lines)
- Pitfall 6 merge (~80 lines)

**39-02: Chemistry-First Hierarchy (2 days)**
- Evidence priority table
- Conflict resolution decision tree
- 5-10 examples (peroxide, allylic CH2, etc.)
- Threshold override guidance

**39-03: Integration Testing (3 days)**
- Ibuprofen CASE run (verify aromatic detection)
- Edge case testing (peroxide, formula mismatch)
- Regression testing (sarocladone A, etc.)

### 11.4 Success Pattern

**Observable truth after Phase 39:**
```bash
# Run CASE on ibuprofen
/lucy-ng:case data/Ibuprofen C13H18O2

# Expected behavior:
1. Agent calls `lucy detect hybridisation 132.5` (aromatic region)
2. Agent sets MULT hybridisation to 2 for 6 aromatic carbons
3. Agent calls `lucy detect neighbours 65.3` (C-O ether)
4. LSD file has PROP constraint for mandatory O neighbor
5. Solution count < 50 (constraints reduce search space)
6. Correct ibuprofen ranks #1 (not cyclohexadiene)
7. CASE-PROGRESS.md documents all detection with reasoning
```

**Phase 39 is ready to plan.**

---

## 12. References

### 12.1 Completed Phase Documentation

| Phase | Research File | Key Learnings |
|-------|---------------|---------------|
| 34 | phases/34-hybridisation-detection/34-RESEARCH.md | sp2/sp3/sp1 detection, 1% threshold, radius fallback |
| 35 | phases/35-neighbourhood-detection/35-RESEARCH.md | Forbidden (<1%), mandatory (>95%), sphere 1 parsing |
| 36 | phases/36-hhb-and-ring-detection/36-RESEARCH.md | HHB frequency, ring statistics, peroxide edge case |
| 37 | phases/37-signal-grouping/37-RESEARCH.md | 0.25 ppm tolerance, multiplicity-aware grouping |
| 38 | phases/38-two-tier-ranking-and-badlist/38-RESEARCH.md | Match count first, badlist patterns, ibuprofen hallucination |

### 12.2 Agent Architecture Documentation

| File | Lines | Content |
|------|-------|---------|
| ~/.claude/agents/lucy-case-agent.md | ~700 | Current agent knowledge (to be extended) |
| CLAUDE.md | ~400 | Project-level instructions |
| ROADMAP.md | ~850 | Phase definitions and progress |

### 12.3 CLI Command References

| Command | Help | Example Output |
|---------|------|----------------|
| `lucy detect hybridisation --help` | Full syntax | shift → sp2/sp3/sp1 frequencies |
| `lucy detect neighbours --help` | Threshold overrides | shift → forbidden/mandatory elements |
| `lucy detect hhb --help` | Formula-based detection | formula → allowed bond pairs |
| `lucy analyze grouping --help` | Clustering parameters | shifts → grouped clusters |

---

_Researched: 2026-02-11_
_Researcher: Claude (gsd-phase-researcher)_
_Confidence: HIGH_
