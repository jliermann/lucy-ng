# Phase 20: System Audit - Research

**Researched:** 2026-02-06
**Domain:** Software architecture audit and intelligence classification
**Confidence:** HIGH

## Summary

Phase 20 requires auditing the entire lucy-ng codebase to classify every component by "intelligence level" — the amount of domain logic, decision-making, and filtering embedded in code vs. what should live in AI skill documents. This research identifies the actual inventory of components and provides a framework for classification.

**Key findings:**
- **15 MCP tools** exist (not 16 as stated in requirements — verified by code inspection)
- **9 CLI command groups** with 22 total commands (not 7 groups as stated)
- **CLAUDE.md** is 1,079 lines with 16 major sections and 57 subsections
- The most intelligence-heavy components are the DEPT-guided picker (289 lines), HMBC guided picker (226 lines), and LSD generator (478 lines, including heteroatom constraint logic)

**Primary recommendation:** Use a three-tier classification system with specific criteria per tier, then audit each component against these criteria to produce actionable migration recommendations.

## Standard Stack

No external tools needed — this is a code audit and documentation task.

### Audit Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `grep` | Pattern searching in source | Count decorators, find functions |
| `wc -l` | Line counting | Measure file sizes |
| Python AST inspection | Parse code structure | Extract function/class definitions |
| Markdown parsing | Section analysis | CLAUDE.md structure mapping |

### Classification Framework

The three-tier system from Architecture research:

| Tier | Definition | Keep or Migrate? |
|------|------------|------------------|
| **Tier 1** | Pure data access, no decisions | Keep as-is in code |
| **Tier 2** | Moderate intelligence (thresholds, strategies) | Keep code, document strategy in skill |
| **Tier 3** | Complex logic (multi-step algorithms, inference) | Refactor to thin wrapper, move logic to skill |

## Architecture Patterns

### Audit Workflow Pattern

```
1. INVENTORY
   ├─ List all MCP tools (@mcp.tool() decorator)
   ├─ List all CLI commands (@*.command() decorators)
   └─ Map CLAUDE.md sections

2. CLASSIFY
   ├─ For each component: identify "intelligence"
   ├─ Apply tier criteria
   └─ Document: what logic exists, where it lives

3. RECOMMEND
   ├─ Tier 1: "Keep as-is"
   ├─ Tier 2: "Document strategy in SKILL.md section X"
   └─ Tier 3: "Refactor: extract logic to skill, simplify to data wrapper"

4. REPORT
   └─ One row per component with specific action
```

### Intelligence Detection Criteria

**Tier 1 indicators (pure data access):**
- Single function call to library (BrukerReader, DatabaseQueryService)
- No conditional logic beyond error handling
- Returns raw data or simple transformations (type conversions)
- No iteration or aggregation beyond simple loops

**Tier 2 indicators (moderate intelligence):**
- Default parameter values (thresholds: 0.05, tolerances: 3.0 ppm)
- Strategy selection (adaptive algorithm, guided filtering)
- Simple filtering or validation rules
- Parameter interpretation (what "good" threshold means)

**Tier 3 indicators (complex logic):**
- Multi-step algorithms (adaptive thresholding loop)
- Inference from domain knowledge (carbonyl → sp2 oxygen pairing)
- Pattern matching with multiple conditions
- Cross-validation between data sources
- Heuristic-based decisions

### Component Inventory Results

**MCP Tools (15 total):**

| Category | Count | Tools |
|----------|-------|-------|
| Spectrum Reading | 2 | read_spectrum_1d, read_spectrum_2d |
| Peak Picking | 3 | pick_peaks_1d, pick_hsqc_peaks, pick_hmbc_peaks |
| Analysis | 1 | analyze_symmetry |
| Dereplication | 1 | dereplicate_c13 |
| LSD Integration | 3 | check_lsd_availability, generate_lsd_input, run_lsd |
| Ranking | 1 | rank_lsd_solutions |
| Prediction | 2 | predict_c13_shifts, get_hose_stats_info |
| NMRXiv | 1 | fetch_nmrxiv_dataset |
| Visualization | 1 | generate_correlation_diagram |

**CLI Command Groups (9 total, 22 commands):**

| Group | Command Count | Commands |
|-------|--------------|----------|
| `read` | 2 | 1d, 2d |
| `pick` | 4 | 1d, hsqc, hmbc, cosy |
| `analyze` | 1 | symmetry |
| `dereplicate` | 1 | c13 |
| `predict` | 3 | c13, build-table, info |
| `lsd` | 5 | check, generate, run, rank, analyze |
| `visualize` | 1 | diagram |
| `fetch` | 1 | nmrxiv |
| `database` | 4 | download, info, import, stats |

**CLAUDE.md Structure (1,079 lines):**

| Section | Approximate Lines | Type |
|---------|------------------|------|
| End-User Setup | ~60 | Setup instructions |
| Blind CASE Protocol | ~40 | Research methodology |
| Available Subskills | ~30 | Workflow routing |
| Structure Elucidation Workflow | ~30 | High-level process |
| NMR Quick Reference | ~80 | Domain knowledge tables |
| Common Pitfalls | ~90 | Error handling knowledge |
| Reference Data | ~20 | Database info |
| Dereplication | ~35 | Tool usage + interpretation |
| LSD Integration | ~250 | Complex domain rules |
| Manual LSD File Construction | ~70 | Template + checklist |
| Peak Picking | ~130 | Strategy + rationale |
| Decision Trees | ~90 | Workflow logic |
| Result Reporting | ~70 | Output templates |
| Quick Reference Card | ~50 | Summary tables |
| 13C Shift Prediction | ~45 | Tool usage |
| Developer Reference | ~90 | Architecture notes |

## Don't Hand-Roll

**Code analysis tools:**
- Don't write custom AST parsers — use Python's `ast` module
- Don't write custom regex for function extraction — use `grep` with patterns
- Don't manually count sections — use `grep "^##"` for markdown headers

**Classification tools:**
- Don't build a scoring system — use manual inspection with criteria checklist
- Don't automate intelligence detection — requires domain understanding

## Common Pitfalls

### Pitfall 1: Confusing Line Count with Intelligence

**What goes wrong:** Assuming large files = high intelligence, small files = low intelligence.

**Why it happens:** Lines of code measure size, not complexity or domain knowledge.

**How to avoid:**
- Read the actual code
- Identify decision points (if/else, loops with conditions)
- Look for domain constants (chemical shift ranges, tolerance values)
- Check for inference logic ("if carbonyl carbon, then pair with sp2 oxygen")

**Example:**
- `read_spectrum_1d` (15 lines): Tier 1 (pure wrapper)
- `pick_hsqc_peaks` (30 lines in MCP): Tier 2 (calls complex algorithm)
- `DEPTGuidedPicker.pick_hsqc_peaks` (150+ lines): Tier 3 (adaptive algorithm)

### Pitfall 2: MCP Tool ≠ Implementation

**What goes wrong:** Classifying MCP tools by their 20-line wrapper code instead of the underlying implementation.

**Why it happens:** MCP tools delegate to Python modules. The intelligence is in the module, not the tool.

**How to avoid:**
- Trace MCP tool → Python function → implementation
- Classify based on the deepest implementation
- Example: `pick_hsqc_peaks` MCP tool calls `DEPTGuidedPicker.pick_hsqc_peaks` (289 lines)

**Checklist:**
1. Find MCP tool definition in `mcp/server.py`
2. Identify function calls in tool body
3. Navigate to implementation file
4. Measure intelligence at implementation level

### Pitfall 3: Strategy vs. Implementation Confusion

**What goes wrong:** Unclear whether to move the algorithm (Tier 3) or just document the strategy (Tier 2).

**Why it happens:** Some algorithms are standard NMR practice (documented), others are custom heuristics (embedded knowledge).

**Guideline:**
- **Tier 2:** Algorithm is standard/published, implementation is library-appropriate (SciPy peak finding)
  - Action: Document WHEN to use and WHY (strategy), keep code
- **Tier 3:** Algorithm embeds custom heuristics or multi-source inference
  - Action: Refactor to let AI construct solution from skill knowledge

**Examples:**
- DEPT-guided picking: Standard practice (published), but adaptive threshold is custom → **Tier 2** (document adaptive strategy)
- Heteroatom constraint generation: Custom inference (carbonyl → oxygen pairing) → **Tier 3** (move logic to skill)

### Pitfall 4: Duplication Blindness

**What goes wrong:** Missing duplicated content between CLAUDE.md sections.

**Why it happens:** Long document, similar topics (LSD appears in multiple sections).

**How to detect:**
- Search for repeated terms: "LSD", "HMBC", "symmetry"
- Compare section purposes: is "LSD Integration" different from "Manual LSD File Construction"?
- Look for copy-paste patterns (same code examples, same tables)

**CLAUDE.md duplication candidates:**
- LSD rules appear in: LSD Integration (~250 lines), Manual LSD Construction (~70 lines), Common Pitfalls (LSD troubleshooting ~40 lines)
- Peak picking appears in: Peak Picking section (~130 lines), Common Pitfalls (Pitfall 3 ~30 lines), Workflow Steps (~20 lines)

## Code Examples

### Example 1: Tier 1 Classification (Pure Data Access)

**Component:** `read_spectrum_1d` MCP tool

```python
@mcp.tool()
def read_spectrum_1d(path: str) -> dict:
    """Read a Bruker 1D NMR spectrum and return metadata."""
    try:
        spectrum = BrukerReader.read_1d(path)  # Single library call
        return {
            "success": True,
            "nucleus": spectrum.nucleus,
            "frequency": spectrum.frequency,
            # ... simple field extraction
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

**Intelligence level:** None — pure wrapper around `BrukerReader.read_1d()`

**Recommendation:** Keep as-is (Tier 1)

### Example 2: Tier 2 Classification (Moderate Intelligence)

**Component:** `pick_peaks_1d` MCP tool

```python
@mcp.tool()
def pick_peaks_1d(path: str, threshold: float | None = None) -> dict:
    """Pick peaks from a 1D NMR spectrum."""
    try:
        spectrum = BrukerReader.read_1d(path)
        if threshold is None:
            threshold = 0.05  # Default threshold strategy
        peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=threshold)
        # ...
```

**Intelligence level:** Moderate
- Default threshold value (0.05) embeds domain knowledge
- "Adaptive" picker name suggests strategy

**Recommendation:** Keep tool, document strategy in SKILL.md:
- "Use threshold 0.05 for initial 1D picking"
- "Adjust if noise peaks appear or weak signals missed"
- Explain what "adaptive" means (use noise estimation)

### Example 3: Tier 3 Classification (Complex Logic)

**Component:** `generate_lsd_input` → `LSDInputGenerator.from_peak_data()`

**Intelligence indicators:**
1. **Heteroatom inference logic** (lines 380-420 in generator.py):
   ```python
   # Identify carbonyl carbons (160-220 ppm)
   carbonyl_atoms = [a for a in problem.atoms if 160 <= a.carbon_shift <= 220]

   # Pair carbonyl carbons with sp2 oxygens (C=O double bond)
   num_carbonyls = min(len(carbonyl_atoms), oxygen_count)
   for i in range(num_carbonyls):
       problem.add_constraint(LSDConstraint(
           atom1_index=carbonyl_atoms[i].index,
           atom2_index=sp2_oxygen_indices[i],
           constraint_type="BOND",
           reason="carbonyl C double-bonded to O",
       ))
   ```

2. **Multi-step inference:**
   - Step 1: Identify carbonyl carbons by chemical shift range
   - Step 2: Assign sp2 hybridization to oxygens for carbonyls
   - Step 3: Generate BOND constraints
   - Step 4: Remaining oxygens get sp3 hybridization

**Intelligence level:** High — embeds domain knowledge about:
- Chemical shift ranges (160-220 ppm = carbonyl)
- Hybridization rules (C=O both sp2)
- Constraint types (BOND for double bond)

**Recommendation:** Tier 3 refactor
- **Simplify tool:** Accept atom definitions + constraints as input
- **Move to skill:** "If carbon 160-220 ppm, likely carbonyl. Add sp2 oxygen and BOND constraint."
- **Let AI reason:** AI constructs LSD file from peak data + skill guidance

## State of the Art

| Approach | Current (v1.2) | Target (v2.0) |
|----------|---------------|---------------|
| Intelligence location | Embedded in Python code | Documented in skill |
| Tool complexity | Complex (multi-step algorithms) | Thin wrappers |
| Error handling | Python try/catch + validation | AI reasoning from skill knowledge |
| Documentation | CLAUDE.md (1,079 lines, duplicative) | Skill documents (modular, role-specific) |
| Agent pattern | Single agent uses tools | Multi-agent (supervisor + CASE) |

**Key evolution:** Tool-heavy → Skill-first architecture

## Open Questions

### Question 1: Should visualization tools be audited?

**What we know:**
- `generate_correlation_diagram` is complex (arrow routing, layout optimization)
- Listed in Architecture research as "keep as-is (not CASE-critical)"

**What's unclear:**
- Is visualization in scope for v2.0 migration?
- Should diagram generation logic move to skill?

**Recommendation:** Audit but mark as "defer refactoring" — focus on CASE-critical tools first.

### Question 2: How to handle CLI vs. MCP duplication?

**What we know:**
- Many CLI commands duplicate MCP tool functionality
- CLI adds formatting (text/JSON output)
- Both call same underlying Python modules

**What's unclear:**
- Should CLI commands be classified separately?
- Or just audit the shared underlying implementation once?

**Recommendation:** Classify underlying Python modules once, then note which interfaces (CLI/MCP) expose them. Both can share the same migration recommendation.

### Question 3: Database query tools — keep or simplify?

**What we know:**
- `dereplicate_c13` includes complex database selection logic (SQLite vs. SD files, auto-detection)
- Dereplication service includes matching algorithm with scoring

**What's unclear:**
- Is the database selection logic "intelligence" to extract?
- Or is it infrastructure that should stay in code?

**Recommendation:** Classify database selection as Tier 1 (infrastructure), but classify the matching/scoring logic as Tier 2 (document scoring interpretation in skill).

## Sources

### Primary (HIGH confidence)

**Source code inspection:**
- `/src/lucy_ng/mcp/server.py` — 15 MCP tools verified by counting `@mcp.tool()` decorators
- `/src/lucy_ng/cli/main.py` + submodules — 9 CLI groups, 22 commands verified by `grep`
- `/CLAUDE.md` — 1,079 lines, 16 sections, 57 subsections verified by `wc -l` and `grep`
- `/src/lucy_ng/lsd/generator.py` — 478 lines, heteroatom logic at lines 380-420
- `/src/lucy_ng/processing/dept_guided_picker.py` — 289 lines, adaptive algorithm
- `/src/lucy_ng/processing/hmbc_guided_picker.py` — 226 lines, guided filtering

**Architecture research:**
- `/.planning/research/ARCHITECTURE.md` — Three-tier classification system, tool inventory matrix

### Secondary (MEDIUM confidence)

**Requirements and State:**
- `/.planning/REQUIREMENTS.md` — AUDT-01 through AUDT-04 define audit scope
- `/.planning/STATE.md` — v2.0 vision: "AI as intelligence layer"

**Note on discrepancies:**
- Requirements state "16 MCP tools" but actual count is 15
- Requirements state "7 CLI command groups" but actual count is 9
- These are minor documentation errors, not research failures

## Metadata

**Confidence breakdown:**
- MCP tool count: HIGH — verified by decorator counting in source code
- CLI command count: HIGH — verified by decorator counting + manual inspection
- CLAUDE.md structure: HIGH — verified by line count and section enumeration
- Intelligence classification criteria: MEDIUM — framework is from research, application requires manual inspection per component
- Heteroatom logic location: HIGH — exact line numbers verified in source code

**Research date:** 2026-02-06
**Valid until:** 60 days (code structure stable, but logic may evolve with v2.0 work)

**Key insight:** The audit is NOT about counting lines or tools — it's about identifying WHERE domain knowledge currently lives (code vs. documentation) and recommending WHERE it SHOULD live (skill documents). The three-tier framework provides objective criteria for these recommendations.
