# Feature Landscape: Multi-Agent CASE System

**Domain:** AI-powered Computer-Assisted Structure Elucidation (CASE) for NMR spectroscopy
**Researched:** 2026-02-06
**Context:** v2.0 transformation from tool-heavy to AI-first architecture

## Executive Summary

The Virgiline (CASE7) failure revealed that robust CASE requires:
1. **AI reasoning about errors** - not Python machinery detecting them
2. **Incremental constraint strategy** - encoded as skill knowledge, not CLI logic
3. **Multi-agent supervision** - detecting and breaking unproductive loops
4. **Thin tools** - giving data access without imposing intelligence

Current system (v1.2) has 16 MCP tools and extensive Python intelligence. The v2.0 transformation pushes domain knowledge into skills where the AI can reason about it, reduces tools to thin wrappers, and adds multi-agent orchestration to prevent loops.

---

## Table Stakes

Features essential for robust multi-agent CASE. Missing = system gets stuck.

### TS-1: Supervisor Agent with Loop Detection

**What:** Dedicated supervisor agent monitors CASE agent behavior and detects unproductive patterns.

**Why expected:** Multi-agent orchestration research shows supervisor-based patterns prevent the "bag of agents" failure mode where adding agents without coordination creates more meetings than progress.

**Complexity:** Medium

**Loop patterns to detect:**
- **ELIM thrashing** - Adding ELIM command repeatedly without diagnosing root cause
- **Peak picking oscillation** - Adjusting thresholds repeatedly without progress
- **Constraint churning** - Adding/removing constraints randomly
- **Zero-solution loop** - Getting 0 solutions, tweaking constraints, getting 0 again
- **Solution explosion** - Getting 1000+ solutions, minor tweaks, still 1000+

**Intervention strategies:**
- After 3 failed attempts with same pattern → escalate to user
- After ELIM added → require diagnosis of which HMBC correlation is suspect
- After 5 peak picking adjustments → require spectral quality assessment
- After 2 zero-solution attempts → require sp2/hydrogen count validation

**Implementation notes:**
- Supervisor sees full conversation history
- Uses temporal pattern matching (not just state)
- Can inject diagnostic questions to CASE agent
- Human-in-the-loop for escalation, not micro-management

**Sources:**
- [Multi-agent supervisor patterns](https://arxiv.org/html/2601.19121)
- [Coordination overhead vs task complexity](https://www.kore.ai/blog/choosing-the-right-orchestration-pattern-for-multi-agent-systems)

---

### TS-2: CASE Skill with Incremental HMBC Strategy

**What:** Skill instructions teaching incremental constraint addition strategy.

**Why expected:** The "throw everything in" approach fails on difficult cases. Structure Elucidator 2025 documentation emphasizes incremental constraint addition for crowded spectral regions.

**Complexity:** Low (skill update, not code)

**Skill knowledge to encode:**

#### Phase 1: Core Structure from High-Confidence Signals
```
Start with HSQC only (direct C-H correlations - these are always correct).
Add HMBC correlations for:
- Well-separated quaternary carbons (>2 ppm from neighbors)
- Carbonyl region signals (>160 ppm, usually unambiguous)
- Aromatic region CH peaks (if benzene ring present)

Goal: 5-20 solutions showing core scaffold
```

#### Phase 2: Resolve Ambiguity with Diagnostic Correlations
```
If multiple scaffolds remain:
- Add HMBC correlations that distinguish between candidates
- Focus on HMBC to quaternary carbons (most informative)
- Avoid crowded aliphatic regions initially

If solutions differ in heteroatom placement:
- Add BOND constraints for C-O or C-N based on shift
```

#### Phase 3: Refine with Full Constraint Set
```
Only after scaffold is determined:
- Add remaining HMBC correlations
- Include aliphatic region correlations
- Use ELIM only if truly necessary

If aliphatic signals overlap (within 0.5 ppm):
- Document ambiguity
- Try both assignments if solutions differ
```

**What skill MUST NOT say:**
- "Run lucy pick hmbc and use all correlations" (this is the failure mode)
- "If LSD returns 0 solutions, try ELIM" (this skips diagnosis)

**What skill MUST say:**
- "Start with 5-10 high-confidence HMBC correlations"
- "If 0 solutions, check sp2 count and hydrogen budget BEFORE trying ELIM"
- "Close carbon shifts (<0.5 ppm apart) create assignment ambiguity"

**Sources:**
- [Incremental constraint addition](https://www.acdlabs.com/technical-support/current-software-versions/structure-elucidator-suite/)
- [HMBC ambiguity handling](https://pubs.acs.org/doi/10.1021/acs.jcim.7b00653)

---

### TS-3: Error Tolerance as AI Knowledge (Not Python Detection)

**What:** Skill teaches AI to detect and reason about common spectroscopic ambiguities.

**Why expected:** The AI can see the data and reason about it. Building Python machinery to detect every edge case is brittle and removes the intelligence from where it belongs.

**Complexity:** Low (skill content) + Medium (remove existing Python detection)

**Ambiguity patterns the AI must learn:**

#### Close Carbon Shifts (Aliphatic Crowding)
```
Pattern: Multiple carbons within 0.3-0.5 ppm in 10-40 ppm region
Why it happens: Saturated CH2/CH3 have narrow shift ranges
What AI should do:
  - Identify close shifts proactively
  - Document: "Carbons 3, 5, 7 at 22.1-22.4 ppm may be ambiguous"
  - Try multiple HMBC assignments if LSD fails
  - Don't force constraints that assume exact assignment

Example from Virgiline: 5 carbons in 22-28 ppm range
```

#### DEPT Phase Inversion Issues
```
Pattern: HSQC shows CH peak but DEPT-135 phase is negative (CH2-like)
Why it happens: Unusual J-coupling, DEPT setup error, or HSQC artifact
What AI should do:
  - Compare HSQC multiplicity with DEPT phase
  - If conflict: "Signal at X ppm: HSQC suggests CH, DEPT suggests CH2"
  - Use HSQC as ground truth (direct measurement more reliable)
  - Document uncertainty in LSD comments

Example: HSQC doublet at 45 ppm, DEPT-135 negative
```

#### Ambiguous HMBC Assignment
```
Pattern: HMBC cross-peak could be assigned to either of two close carbons
Why it happens: Digital resolution limits, peak overlap, close shifts
What AI should do:
  - Identify when carbon positions are close (<1 ppm)
  - Note: "HMBC from H-8 to ~25 ppm could be C-5 (24.8) or C-7 (25.3)"
  - Generate two LSD input variants if critical for scaffold
  - Don't over-constrain with arbitrary choice

Example: HMBC to 138.5 ppm could be C-3 (138.4) or C-6 (138.7)
```

#### Quaternary Carbon HMBC Sparsity
```
Pattern: Quaternary carbon has no or very few HMBC correlations
Why it happens: HMBC is insensitive, quaternary C are distant from H
What AI should do:
  - Check if other constraints place quaternary C unambiguously
  - If not: use chemical shift to constrain heteroatom attachment
  - Don't assume missing HMBC = no connection (may be weak signal)

Example: Carbonyl at 173 ppm with only 1 HMBC visible
```

**What to remove from Python code:**
- Automatic HMBC conflict resolution (let AI reason about conflicts)
- Hard thresholds for "too close" (context-dependent)
- Automatic constraint relaxation (AI should decide strategy)

**What Python should provide:**
- Raw peak lists with positions and intensities
- Distance calculations (e.g., "these carbons are 0.3 ppm apart")
- Validation that peaks exist in reference spectra

**Sources:**
- [Peak overlap in metabolomics](https://www.nature.com/articles/s41597-025-06245-5)
- [Ambiguous assignment challenges](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-13-S3-S4)

---

### TS-4: Diagnostic Specialist Agent

**What:** Specialist agent that diagnoses WHY LSD failed (0 solutions or 1000+ solutions).

**Why expected:** The CASE agent gets stuck trying fixes without understanding the root cause. A specialist can systematically check common failure modes.

**Complexity:** Medium

**Diagnostic checklist for 0 solutions:**

1. **sp2 Count Validation**
   - Extract all atom definitions from LSD file
   - Count atoms with hybridization=2
   - Check: Is count EVEN?
   - Common fix: Convert one N from sp2→sp3 or vice versa

2. **Hydrogen Budget**
   - Sum: (CH3 count × 3) + (CH2 count × 2) + (CH count × 1)
   - Compare to molecular formula H count
   - Common fix: Wrong multiplicity assignment

3. **HMBC Conflict Detection**
   - Check if HMBC implies impossible geometry
   - Example: C-1 HMBC to H-3, but C-1 and C-3 are >4 bonds apart in all solutions
   - Common fix: HMBC is artifact, add to ELIM list

4. **Correlation Order**
   - Verify all HSQC commands appear before HMBC
   - Verify all referenced H positions are defined
   - Common fix: Reorder correlation commands

**Diagnostic checklist for 1000+ solutions:**

1. **Constraint Count**
   - How many HMBC correlations are defined?
   - Rule of thumb: Need ~N correlations for N-carbon molecule
   - Common fix: Add more HMBC correlations

2. **Quaternary Carbon Connectivity**
   - Are all quaternary carbons connected via HMBC?
   - Quaternary C with 0 HMBC = floating, causes explosion
   - Common fix: Find weak HMBC peaks, lower threshold

3. **Heteroatom Constraints Missing**
   - Are carbonyl C-O bonds defined?
   - Are N-CH3 attachments defined?
   - Common fix: Add BOND or LIST/PROP constraints

4. **Symmetry Not Encoded**
   - Does signal count match formula atom count?
   - If not, are SYME constraints present?
   - Common fix: Add symmetry constraints

**Output format:**
```markdown
## LSD Diagnostic Report

**Problem:** 0 solutions found

**Findings:**
1. ✅ sp2 count: 8 (EVEN) - OK
2. ❌ Hydrogen budget: Expected 22 H, LSD defines 24 H
3. ⚠️  HMBC conflict: Correlation C-1 to H-7 unlikely (>4 bonds)

**Recommended fixes:**
- Check multiplicity of C-5 (may be CH not CH2)
- Try adding ELIM 1 0 to allow removing suspicious correlation

**Root cause:** Multiplicity assignment error
```

**Sources:**
- [Constraint satisfaction diagnostics](https://www.geeksforgeeks.org/artificial-intelligence/constraint-satisfaction-problems-csp-in-artificial-intelligence/)

---

### TS-5: Thin Peak Picker Tools (Remove Intelligence)

**What:** Reduce MCP tools to thin wrappers. Remove Python logic that second-guesses the AI.

**Why expected:** On difficult cases, the AI agent bypasses CLI wrappers and reasons directly on the data anyway. The "smart" tools just get in the way.

**Complexity:** Medium (refactor existing tools)

**Current tools to simplify:**

| Current Tool | What to Keep | What to Remove |
|--------------|--------------|----------------|
| `pick_hsqc_peaks` | Read HSQC, extract peaks above threshold | DEPT-guided adaptive thresholding |
| `pick_hmbc_peaks` | Read HMBC, extract peaks above threshold | Carbon/proton position validation filtering |
| `analyze_symmetry` | Count signals, count formula atoms | Interpretation hints, automatic equivalence detection |
| `generate_lsd_input` | Build MULT/HSQC commands from peak list | HMBC auto-inclusion, constraint generation |

**New thin tool design:**

```python
@mcp.tool()
def read_2d_peaks(spectrum_path: str, threshold: float = 0.05) -> dict:
    """Read 2D spectrum and return ALL peaks above threshold.

    No filtering, no validation, no intelligence.
    Just give the AI the data and let it reason.

    Returns:
        {
            "peaks": [
                {"f1_ppm": 138.5, "f2_ppm": 7.24, "intensity": 0.82},
                ...
            ],
            "f1_nucleus": "13C",
            "f2_nucleus": "1H"
        }
    """
```

**What the AI does with raw peaks:**
- Cross-reference HMBC F1 with 13C peak list manually
- Decide which HMBC correlations to include in LSD
- Detect close carbon shifts and document ambiguity
- Build LSD file incrementally with commentary

**Why this is better:**
- AI sees the same data a human would see
- AI can make context-dependent decisions
- AI can document reasoning ("excluding HMBC to 138.7 because it's within 0.2 ppm of 138.5 and likely artifact")
- Tool simplification reduces maintenance burden

**What Python still does well:**
- Read binary Bruker files (nmrglue)
- Extract peaks from 2D matrices (SciPy)
- Run LSD subprocess (shell integration)
- Query SQLite database (SQL)

**Sources:**
- [Human-in-the-loop evolution](https://siliconangle.com/2026/01/18/human-loop-hit-wall-time-ai-oversee-ai/)

---

## Differentiators

Features that make this approach unique. Not expected, but high value.

### DIFF-1: AI-Readable Spectral Quality Assessment

**What:** Skill teaches AI to assess spectral quality and predict which steps will be problematic.

**Value proposition:** Proactive problem detection. "This HMBC has low S/N in the aliphatic region - expect assignment ambiguity in Phase 3."

**Complexity:** Low (skill content)

**Quality indicators to teach:**

#### Signal-to-Noise Indicators
```
High S/N (>100:1): Clean peak picking, reliable correlations
Medium S/N (20-100:1): Most peaks reliable, check weak correlations
Low S/N (<20:1): Expect noise peaks, aggressive filtering needed

How to assess:
- Compare max peak intensity to baseline region intensity
- Check for "grainy" appearance in 2D spectra
- Look for peak count >> expected (indicates noise)
```

#### Digital Resolution
```
High resolution (>1024 points in F1): Can distinguish 0.2 ppm shifts
Medium resolution (512 points): 0.5 ppm resolution limit
Low resolution (<256 points): 1+ ppm resolution, expect overlap

Impact on CASE:
- Low resolution → close carbons will alias
- Document: "HMBC F1 resolution 0.8 ppm, C-5/C-7 distinction marginal"
```

#### Spectral Artifacts
```
Common HMBC artifacts:
- 1J correlations (F1 = HSQC carbon, should be suppressed)
- t1 noise (vertical streaks at strong proton positions)
- Baseline roll (F1 baseline not flat)

What AI should do:
- Identify 1J peaks: "HMBC shows C-H correlation to same H as HSQC - artifact"
- Identify t1 noise: "Vertical artifacts at 7.2 ppm (solvent H)"
- Lower confidence in correlations near artifacts
```

**Deliverable:** Section in CASE skill titled "Spectral Quality Assessment" with examples and heuristics.

---

### DIFF-2: Constraint Satisfaction Explorer Specialist

**What:** Specialist agent that generates multiple LSD input variants for ambiguous cases.

**Value proposition:** When assignment is genuinely ambiguous, try both interpretations systematically instead of guessing.

**Complexity:** Medium

**Use cases:**

#### Close Carbon Assignment
```
Problem: HMBC cross-peak to F1=25.2 ppm
        Candidates: C-5 at 25.0 ppm, C-7 at 25.4 ppm

Explorer generates 2 LSD variants:
- Variant A: HMBC to atom 5
- Variant B: HMBC to atom 7

Run both, compare solutions:
- If variant A gives 1-10 solutions, variant B gives 0 → C-5 correct
- If both give solutions → need additional data to resolve
```

#### Heteroatom Placement
```
Problem: Molecular formula C9H10O2 (2 oxygens)
        Possible: Two isolated OH, or one ester, or one ether + one OH

Explorer generates 3 LSD variants:
- Variant A: Both O as sp3 (two OH)
- Variant B: One O as sp2 carbonyl
- Variant C: BOND constraint for ester linkage

Ranking by MAE determines most likely structure
```

**Implementation:**
- Explorer agent spawned by CASE agent when ambiguity detected
- Generates 2-5 variants (not exhaustive)
- Runs LSD on all variants in parallel
- Reports back which variants succeeded
- CASE agent uses MAE ranking to select best

**Sources:**
- [Fuzzy structure generation for ambiguous constraints](https://www.sciencedirect.com/science/article/abs/pii/S0377221798003646)

---

### DIFF-3: Confidence-Annotated Output

**What:** All analysis steps include confidence levels and uncertainty documentation.

**Value proposition:** Transparent AI reasoning. User can see which assignments were certain vs. guessed.

**Complexity:** Low (prompt engineering)

**Output format example:**

```markdown
## Peak Assignments

### High Confidence (>90%)
- C-1 at 173.2 ppm: Carbonyl (HMBC to 3 protons)
- C-2 at 128.5 ppm: Aromatic CH (HSQC doublet)

### Medium Confidence (60-90%)
- C-5 at 25.0 ppm: Aliphatic CH2 (DEPT negative, but close to C-7)
- HMBC C-1 to H-3: 2J or 3J unclear (both geometries possible)

### Low Confidence (<60%)
- C-7 vs C-9 assignment: Both at ~22 ppm, HMBC assignment ambiguous
- Quaternary C-4: No HMBC correlations visible (may be HSQC artifact)

## Ambiguity Resolution Strategy
1. Proceed with high-confidence assignments only
2. Generate 2 LSD variants for C-7/C-9 ambiguity
3. Use MAE ranking to resolve C-4 uncertainty
```

**Why this matters:**
- User can verify high-confidence assignments first
- Low-confidence areas flag where additional NMR might help
- Research paper can report: "5 of 13 carbons required ambiguity resolution"

---

### DIFF-4: LSD Solution Explainer Specialist

**What:** Specialist agent that explains WHY a solution structure satisfies (or violates) the NMR constraints.

**Value proposition:** Answer "Why is this the #1 ranked solution when this other structure looks more reasonable?"

**Complexity:** Medium

**Explanation format:**

```markdown
## Solution 1: CC1CCC(C1)C(=O)C (MAE=2.3 ppm, Rank #1)

### Constraint Satisfaction
✅ All HSQC correlations satisfied
✅ 8 of 9 HMBC correlations satisfied
⚠️ HMBC C-1 to H-7 not satisfied (4 bonds in solution, should be 2-3)

### Shift Prediction Quality
✅ Carbonyl at 173 ppm: predicted 171 (Δ=2 ppm) - excellent
✅ Aromatic region: MAE=1.2 ppm - good
⚠️ Aliphatic region: MAE=3.8 ppm - moderate

### Structural Features
- Cyclopentanone ring (common motif)
- Methyl ketone (consistent with carbonyl shift)
- Predicted ring strain: low

### Why This Ranks #1
The MAE is dominated by well-predicted carbons (8 of 10 within 3 ppm).
The one HMBC violation is likely a 4J correlation (possible but unusual).
Alternative Solution #2 has lower MAE (2.1) but violates 3 HMBC correlations.
```

**Use case:**
- User reviews top 5 solutions
- Asks: "Why is solution 3 ranked below solution 1?"
- Explainer generates comparative report
- Highlights which constraints differ, which shifts differ

**Sources:**
- [Explainable AI for constraint satisfaction](https://www.sciencedirect.com/topics/computer-science/constraint-satisfaction-problems)

---

## Anti-Features

Features to deliberately NOT build. Common mistakes in this domain.

### AF-1: Automatic HMBC Conflict Resolution

**What NOT to build:** Python code that detects HMBC conflicts and automatically removes "suspicious" correlations.

**Why avoid:** This removes human/AI judgment. A 4-bond HMBC correlation may be unusual but real (W-coupling, through-space). Automatic removal may discard critical constraints.

**What to do instead:**
- Tool reports: "HMBC C-1 to H-7 is 4 bonds in solution (unusual)"
- AI decides: Keep it, remove it, or try both
- Skill teaches when 4J correlations are plausible

**Root cause of temptation:** Python programmer wants to "help" by removing "bad" data. But the AI is better positioned to judge context.

---

### AF-2: Automatic Symmetry Constraints

**What NOT to build:** Python code that detects equivalent atoms from HSQC intensities and automatically generates SYME commands.

**Why avoid:**
- Intensity ratios are approximate (2.3x vs 2.0x doesn't mean 3 vs 2 equivalents)
- Symmetry detection requires structural reasoning (para-benzene vs meta-benzene)
- False symmetry detection over-constrains LSD

**What to do instead:**
- Tool reports: "C-3 at 128.5 ppm has 2.1x intensity vs median"
- AI reasons: "2.1x suggests 2 equivalent positions, consistent with para-substitution"
- AI manually writes SYME commands with commentary

**Root cause of temptation:** Symmetry analysis (v1.0 feature) was built to "help" the AI. In practice, the AI ignores it and reasons from raw data.

---

### AF-3: Automatic Threshold Tuning

**What NOT to build:** Adaptive peak picking that iteratively adjusts threshold until "optimal" peak count is reached.

**Why avoid:**
- "Optimal" is context-dependent (depends on S/N, what you're looking for)
- Hides decision from AI (threshold becomes a magic number)
- May over-fit to noisy data

**What to do instead:**
- Tool exposes threshold as parameter
- AI tries threshold=0.05, gets 200 peaks, notes "too many, likely noise"
- AI tries threshold=0.10, gets 45 peaks, notes "matches expected count"
- AI documents: "Used threshold=0.10 for HMBC based on expected peak count"

**Root cause of temptation:** DEPT-guided HSQC picking (v1.0 feature) worked well. Tried to generalize to HMBC, but context is different.

---

### AF-4: One-Shot LSD Generation

**What NOT to build:** A "smart" LSD generator that includes all HMBC correlations and all heteroatom constraints in one shot.

**Why avoid:**
- Incremental strategy is more robust
- One-shot works for easy cases, fails for hard cases
- AI can't see intermediate results to adjust strategy

**What to do instead:**
- Tool builds MULT and HSQC commands from peak list
- AI manually adds HMBC correlations in phases (5-10 at a time)
- AI generates multiple LSD files (Phase1.lsd, Phase2.lsd, Phase3.lsd)
- AI can see solution count at each phase and adjust

**Root cause of temptation:** Automation bias. "Why make the AI do manual work?" But the manual work IS the intelligence.

---

### AF-5: Solution Ranking by Single Metric

**What NOT to build:** Ranking that uses ONLY MAE or ONLY constraint satisfaction count.

**Why avoid:**
- MAE can be low for wrong structure if most carbons are in crowded regions
- Constraint satisfaction can be high if constraints are weak
- Need multi-criteria ranking

**What to do instead:**
- Tool reports MAE, constraint satisfaction, and structural reasonableness
- AI weighs criteria based on context
- AI can ask Explainer specialist for comparative report

**Root cause of temptation:** Simple ranking is easier to implement and explain. But chemistry is complex.

---

## Feature Dependencies

```
Supervisor Agent (TS-1)
    ↓ monitors
CASE Agent with Incremental Strategy (TS-2)
    ↓ uses
Thin Peak Picker Tools (TS-5)
    ↓ provides data to
Error Tolerance Knowledge (TS-3)
    ↓ reasons about
Diagnostic Specialist (TS-4)
    ↓ called when stuck

Optional specialists:
- Constraint Explorer (DIFF-2) - called for ambiguous cases
- Solution Explainer (DIFF-4) - called for user questions
```

---

## MVP Recommendation

For v2.0 MVP, prioritize:

1. **TS-2: Incremental HMBC Strategy Skill** (easiest, highest impact)
   - Rewrite CASE section of CLAUDE.md
   - Add examples from literature
   - Remove "throw everything in" guidance

2. **TS-5: Simplify Peak Picking Tools** (reduces code complexity)
   - Keep `read_2d_peaks(threshold)` - raw peaks only
   - Remove DEPT-guided adaptive logic
   - Remove HMBC filtering logic

3. **TS-3: Error Tolerance Skill Content** (medium effort)
   - Document close-shift detection patterns
   - Document DEPT phase inversion
   - Document ambiguous HMBC assignment

4. **TS-1: Basic Supervisor** (enables iteration)
   - Detect 3 consecutive zero-solution attempts
   - Detect ELIM command addition
   - Inject: "Have you validated sp2 count and hydrogen budget?"

Defer to post-MVP:
- **TS-4: Diagnostic Specialist** - Can be simulated by skill content initially
- **DIFF-2: Constraint Explorer** - Nice to have, not essential
- **DIFF-4: Solution Explainer** - User can ask questions manually

---

## Quality Gates

Before declaring v2.0 complete:

- [ ] CASE skill includes incremental HMBC strategy with 3 phases
- [ ] CASE skill includes error tolerance patterns (close shifts, DEPT conflicts, HMBC ambiguity)
- [ ] Supervisor detects and intervenes in at least 3 loop patterns
- [ ] MCP tools reduced from 16 to <10 (removed intelligence, kept data access)
- [ ] Virgiline (CASE7) passes: correct structure in top 5 solutions
- [ ] System documents ambiguity instead of guessing ("C-5/C-7 assignment unclear")

---

## Sources

**Multi-Agent Orchestration:**
- [LLMs as Orchestrators for Constraint-Compliant Optimization](https://arxiv.org/html/2601.19121)
- [Multi-Agent Orchestration: The New Operating System](https://www.kore.ai/blog/what-is-multi-agent-orchestration)
- [Supervisor-Based Orchestration Patterns](https://www.kore.ai/blog/choosing-the-right-orchestration-pattern-for-multi-agent-systems)

**Loop Detection and Intervention:**
- [Human-in-the-Loop Evolution: AI Oversee AI](https://siliconangle.com/2026/01/18/human-loop-hit-wall-time-ai-oversee-ai/)
- [Agentic AI Governance and Intervention Patterns](https://www.detectionatscale.com/p/ai-security-operations-2025-patterns)

**NMR Structure Elucidation:**
- [Structure Elucidator Suite 2025 Features](https://www.acdlabs.com/technical-support/current-software-versions/structure-elucidator-suite/)
- [HMBC Correlation Network Reconstruction](https://pubs.acs.org/doi/10.1021/acs.jcim.7b00653)
- [NMR-Solver: Automated Structure Elucidation Framework](https://www.arxiv.org/pdf/2509.00640)

**Spectroscopy Ambiguity:**
- [NMRexp Database: Chemical Shift Variations](https://www.nature.com/articles/s41597-025-06245-5)
- [Peak Overlap and Assignment Challenges](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-13-S3-S4)

**Constraint Satisfaction:**
- [Soft Constraints in CSP](https://arxiv.org/abs/1303.5427)
- [Constraint Satisfaction Problems Overview](https://www.geeksforgeeks.org/artificial-intelligence/constraint-satisfaction-problems-csp-in-artificial-intelligence/)
