# CLAUDE.md Audit

## Summary

- **Total**: 1,080 lines across 14 top-level sections (## headings) and 43 subsections (### headings)
- **Project-level content** (keep in CLAUDE.md): ~225 lines
- **CASE workflow content** (move to SKILL.md): ~680 lines
- **Duplicated content** (deduplicate during migration): ~175 lines overlap
- **Net CLAUDE.md target**: ~225 lines (well under the Phase 21 target of <800 lines)

The current CLAUDE.md is roughly 80% domain knowledge and CASE workflow logic that teaches the AI _how to reason about NMR/CASE_, with only ~20% being genuine project-level instructions (setup, developer reference, architecture). Restructuring will dramatically reduce CLAUDE.md while concentrating domain intelligence in purpose-built skill documents.

---

## Section Catalogue

| # | Section (## heading) | Lines | Count | Category | Recommendation |
|---|----------------------|-------|-------|----------|----------------|
| 0 | Title + description | 1-6 | 6 | project-setup | Keep in CLAUDE.md |
| 1 | End-User Setup (First-Time Installation) | 7-59 | 53 | project-setup | Keep in CLAUDE.md |
| 2 | Blind CASE Protocol (For Research Evaluation) | 61-92 | 32 | case-workflow | Move to SKILL.md |
| 3 | Available Subskills | 94-120 | 27 | case-workflow | Move to SKILL.md |
| 4 | Structure Elucidation Workflow | 122-141 | 20 | case-workflow | Move to SKILL.md |
| 5 | NMR Quick Reference | 143-181 | 39 | domain-knowledge | Move to SKILL.md |
| 6 | Common Pitfalls and Solutions | 183-269 | 87 | domain-knowledge | Move to SKILL.md |
| 7 | Reference Data | 271-290 | 20 | tool-usage | Keep brief ref in CLAUDE.md (~5 lines); move details to SKILL.md |
| 8 | Dereplication | 293-321 | 29 | tool-usage | Keep CLI syntax in CLAUDE.md (~10 lines); move interpretation to SKILL.md |
| 9 | LSD Integration | 323-560 | 238 | tool-usage / domain-knowledge | Move to SKILL.md (canonical LSD reference) |
| 10 | Manual LSD File Construction | 562-625 | 64 | domain-knowledge | Move to SKILL.md (merge with LSD Integration) |
| 11 | Peak Picking | 627-749 | 123 | tool-usage / domain-knowledge | Move to SKILL.md |
| 12 | Decision Trees | 751-840 | 90 | case-workflow | Move to SKILL.md |
| 13 | Result Reporting Templates | 842-910 | 69 | case-workflow | Move to SKILL.md |
| 14 | Quick Reference Card | 912-954 | 43 | case-workflow / domain-knowledge | Move to SKILL.md |
| 15 | 13C Shift Prediction | 956-997 | 42 | tool-usage | Keep CLI syntax in CLAUDE.md (~8 lines); move interpretation to SKILL.md |
| 16 | Developer Reference | 999-1080 | 82 | developer-ref | Keep in CLAUDE.md |

### Detailed Subsection Catalogue

| # | Parent Section | Subsection (### heading) | Lines | Count | Category |
|---|---------------|--------------------------|-------|-------|----------|
| 1.1 | End-User Setup | 1. Install lucy-ng | 11-14 | 4 | project-setup |
| 1.2 | End-User Setup | 2. Check LSD Solver | 16-25 | 10 | project-setup |
| 1.3 | End-User Setup | 3. Verify Setup | 27-31 | 5 | project-setup |
| 1.4 | End-User Setup | 4. Download Compound Database | 33-47 | 15 | project-setup |
| 1.5 | End-User Setup | 5. Create Permissions File | 49-57 | 9 | project-setup |
| 2.1 | Blind CASE Protocol | If You Discover Compound Identity | 65-73 | 9 | case-workflow |
| 2.2 | Blind CASE Protocol | Data Sanitization | 75-81 | 7 | case-workflow |
| 2.3 | Blind CASE Protocol | Why This Matters | 83-90 | 8 | case-workflow |
| 3.1 | Available Subskills | Workflow Selection | 102-114 | 13 | case-workflow |
| 3.2 | Available Subskills | Default Behavior | 116-118 | 3 | case-workflow |
| 4.1 | Structure Elucidation Workflow | Workflow Steps | 128-140 | 13 | case-workflow |
| 5.1 | NMR Quick Reference | Experiment Types | 145-155 | 11 | domain-knowledge |
| 5.2 | NMR Quick Reference | 13C Chemical Shift Regions | 157-166 | 10 | domain-knowledge |
| 5.3 | NMR Quick Reference | Lucy-ng Tool Output Reference | 168-179 | 12 | tool-usage |
| 6.1 | Common Pitfalls | Pitfall 1: Symmetry | 185-200 | 16 | domain-knowledge |
| 6.2 | Common Pitfalls | Pitfall 2: Quaternary Carbons | 202-215 | 14 | domain-knowledge |
| 6.3 | Common Pitfalls | Pitfall 3: HMBC Noise | 217-230 | 14 | domain-knowledge |
| 6.4 | Common Pitfalls | Pitfall 4: Too Many LSD Solutions | 232-253 | 22 | domain-knowledge |
| 6.5 | Common Pitfalls | Pitfall 5: Heteroatom Positions | 255-267 | 13 | domain-knowledge |
| 7.1 | Reference Data | Compound Database | 273-289 | 17 | tool-usage |
| 8.1 | Dereplication | CLI Usage | 297-311 | 15 | tool-usage |
| 8.2 | Dereplication | Interpreting Results | 313-319 | 7 | domain-knowledge |
| 9.1 | LSD Integration | LSD File Structure | 325-341 | 17 | tool-usage |
| 9.2 | LSD Integration | Correlation Order (CRITICAL) | 343-362 | 20 | domain-knowledge |
| 9.3 | LSD Integration | Hybridization Rules | 364-389 | 26 | domain-knowledge |
| 9.4 | LSD Integration | Heteroatom Attachment Constraints | 391-443 | 53 | domain-knowledge |
| 9.5 | LSD Integration | LSD Command Format | 445-476 | 32 | tool-usage |
| 9.6 | LSD Integration | Converting LSD Solutions to SMILES | 478-506 | 29 | tool-usage |
| 9.7 | LSD Integration | Solution Ranking and MAE Interpretation | 508-552 | 45 | domain-knowledge |
| 9.8 | LSD Integration | LSD Runner Notes | 554-558 | 5 | developer-ref |
| 10.1 | Manual LSD File Construction | Template | 566-589 | 24 | domain-knowledge |
| 10.2 | Manual LSD File Construction | Checklist | 591-598 | 8 | domain-knowledge |
| 10.3 | Manual LSD File Construction | LSD Troubleshooting | 600-623 | 24 | domain-knowledge |
| 11.1 | Peak Picking | Scientific Rationale | 629-642 | 14 | domain-knowledge |
| 11.2 | Peak Picking | Molecular Symmetry | 644-654 | 11 | domain-knowledge |
| 11.3 | Peak Picking | Working with APT | 656-671 | 16 | domain-knowledge |
| 11.4 | Peak Picking | HSQC: DEPT-Guided Picker | 673-702 | 30 | tool-usage |
| 11.5 | Peak Picking | HMBC: Guided Picker | 704-737 | 34 | tool-usage |
| 11.6 | Peak Picking | Other 2D Spectra | 739-747 | 9 | tool-usage |
| 12.1 | Decision Trees | When to Proceed with Full Elucidation | 753-773 | 21 | case-workflow |
| 12.2 | Decision Trees | Handling Symmetry | 775-799 | 25 | case-workflow |
| 12.3 | Decision Trees | LSD Result Interpretation | 801-838 | 38 | case-workflow |
| 13.1 | Result Reporting Templates | Dereplication Results | 844-880 | 37 | case-workflow |
| 13.2 | Result Reporting Templates | LSD Results | 882-900 | 19 | case-workflow |
| 13.3 | Result Reporting Templates | Reporting Uncertainty | 902-908 | 7 | case-workflow |
| 14.1 | Quick Reference Card | Essential Workflow | 914-921 | 8 | case-workflow |
| 14.2 | Quick Reference Card | Red Flags to Watch For | 923-927 | 5 | domain-knowledge |
| 14.3 | Quick Reference Card | Key Tolerances | 929-934 | 6 | domain-knowledge |
| 14.4 | Quick Reference Card | Ranking Output Interpretation | 936-946 | 11 | domain-knowledge |
| 14.5 | Quick Reference Card | When to Ask for Help | 948-952 | 5 | case-workflow |
| 15.1 | 13C Shift Prediction | CLI Usage | 960-968 | 9 | tool-usage |
| 15.2 | 13C Shift Prediction | Python API | 970-978 | 9 | tool-usage |
| 15.3 | 13C Shift Prediction | Example Output | 980-995 | 16 | tool-usage |
| 16.1 | Developer Reference | Quick Reference | 1001-1018 | 18 | developer-ref |
| 16.2 | Developer Reference | Project Structure | 1020-1034 | 15 | developer-ref |
| 16.3 | Developer Reference | Technology Stack | 1036-1045 | 10 | developer-ref |
| 16.4 | Developer Reference | Critical Architecture Decisions | 1047-1079 | 33 | developer-ref |

---

## Duplication Map

### Cluster 1: LSD Rules and Constraints (~360 lines across 3 sections)

**Total duplicated lines**: ~302 lines in "LSD Integration" + ~64 lines in "Manual LSD File Construction" + ~22 lines in "Pitfall 4" = ~388 lines total, with ~175 lines of conceptual overlap.

#### Specific overlapping concepts:

**1a. MULT command syntax and file structure**
- **Canonical**: LSD Integration > LSD File Structure (lines 325-341) and LSD Command Format (lines 445-476) -- full syntax with examples
- **Duplicate**: Manual LSD File Construction > Template (lines 566-589) -- restates MULT syntax, HSQC/HMBC format, BOND syntax
- **Overlap**: The MULT command examples at lines 449-455 are nearly identical to lines 569-574. The HSQC/HMBC examples at lines 458-467 mirror lines 577-583. The BOND example at line 586 repeats the concept from lines 399-404.
- **Estimated overlap**: ~25 lines of duplicated command syntax

**1b. Correlation order rule (HSQC before HMBC)**
- **Canonical**: LSD Integration > Correlation Order (lines 343-362) -- full explanation with example and error message
- **Duplicate 1**: Manual LSD File Construction > Checklist item 5 (line 596) -- abbreviated version "HMBC correlations reference only defined H positions"
- **Duplicate 2**: Manual LSD File Construction > Troubleshooting table row 2 (line 607) -- restates the error and solution
- **Duplicate 3**: Manual LSD File Construction > Verify checklist item 4 (line 616) -- "All HSQC commands must come before any HMBC commands"
- **Estimated overlap**: ~10 lines restating the same rule in 4 places

**1c. sp2 even count rule**
- **Canonical**: LSD Integration > Hybridization Rules (lines 364-389) -- full explanation with atom lists and Caffeine example
- **Duplicate 1**: Manual LSD File Construction > Checklist item 3 (line 594) -- "sp2 count is EVEN"
- **Duplicate 2**: Manual LSD File Construction > Troubleshooting, first error row (line 606) -- mentions odd valences
- **Duplicate 3**: Manual LSD File Construction > Verify checklist item 2 (line 614) -- repeats sp2 count check
- **Duplicate 4**: Manual LSD File Construction > Troubleshoot step 1 (line 619) -- "Verify sp2 count is even"
- **Duplicate 5**: Decision Trees > LSD Result Interpretation (line 808) -- "sp2 count is even?"
- **Estimated overlap**: ~8 lines restating the same rule in 6 places

**1d. ELIM command usage and caution**
- **Canonical**: LSD Integration > LSD Command Format, ELIM section (lines 470-476) -- full explanation with warning
- **Duplicate 1**: LSD Integration > LSD File Structure (line 338) -- comment "; NO ELIM command on first run"
- **Duplicate 2**: Manual LSD File Construction > Template (line 588) -- "; NO ELIM on first run!"
- **Duplicate 3**: Manual LSD File Construction > Checklist item 7 (line 598) -- "NO ELIM command on first run"
- **Duplicate 4**: Manual LSD File Construction > Verify checklist item 3 (line 615) -- "NO ELIM on first run"
- **Duplicate 5**: Manual LSD File Construction > Troubleshoot steps 4-5 (lines 622-623) -- ELIM 1 0, ELIM 2 0 usage
- **Duplicate 6**: Decision Trees > LSD Result Interpretation (lines 812, 829, 834) -- "try ELIM 1 0", "Was ELIM used? Remove it first!"
- **Duplicate 7**: Quick Reference Card > Red Flags (line 927) -- "using ELIM when not needed"
- **Estimated overlap**: ~15 lines restating the same concept in 8 places

**1e. Heteroatom attachment (BOND vs LIST/PROP)**
- **Canonical**: LSD Integration > Heteroatom Attachment Constraints (lines 391-443) -- full with both approaches, examples, and decision table
- **Duplicate 1**: Manual LSD File Construction > Template (line 585-586) -- abbreviated BOND example
- **Duplicate 2**: Manual LSD File Construction > Checklist item 6 (line 597) -- "Heteroatom constraints added"
- **Duplicate 3**: Pitfall 5: Heteroatom Positions (line 267) -- "Use BOND or LIST/PROP constraints"
- **Duplicate 4**: Decision Trees > LSD Result Interpretation (line 837) -- "Add heteroatom constraints"
- **Estimated overlap**: ~8 lines

**1f. Solution count interpretation (0 / 1-10 / 10-100 / >100)**
- **Canonical**: Decision Trees > LSD Result Interpretation (lines 801-838) -- full decision tree
- **Duplicate 1**: Pitfall 4: Expected Results (lines 250-253) -- same 4 ranges with shorter descriptions
- **Duplicate 2**: Quick Reference Card > Red Flags (lines 926-927) -- "Zero LSD solutions" and "Thousands of LSD solutions"
- **Estimated overlap**: ~12 lines

**Recommendation**: Merge all LSD content into a single "LSD Reference" section in SKILL.md. The canonical source should be the current "LSD Integration" section, enhanced with the checklist from "Manual LSD File Construction" and the troubleshooting table. Remove all duplicated rules from Pitfalls, Decision Trees, and Quick Reference Card -- these sections should reference the single LSD section rather than restate rules.

---

### Cluster 2: Peak Picking Logic (~180 lines across 3 sections)

**Total lines**: ~123 lines in "Peak Picking" + ~14 lines in "Pitfall 3" + ~4 lines in "Workflow Steps" + ~14 lines in "Scientific Rationale overlap with Pitfall 3" = ~155 lines total, with ~30 lines of conceptual overlap.

#### Specific overlapping concepts:

**2a. HMBC noise problem and guided filtering solution**
- **Canonical**: Peak Picking > Scientific Rationale (lines 629-642) -- explains the problem and solution abstractly
- **Duplicate 1**: Peak Picking > HMBC: Guided Picker (lines 704-717) -- restates the same problem ("HMBC spectra are noisy with many artifacts") and the same filtering criteria
- **Duplicate 2**: Pitfall 3: HMBC Noise (lines 217-230) -- restates the same problem, same solution ("Always use guided HMBC picking"), same validation criteria
- **Specific overlap**: Lines 633-636 (noise leads to false correlations, artifacts) are restated at lines 708-713 and again at lines 219-228
- **Estimated overlap**: ~20 lines stating the same concept (HMBC is noisy, filter by matching 13C + HSQC positions) three times

**2b. Guided peak picking principle (cross-validate 2D against 1D)**
- **Canonical**: Peak Picking > Scientific Rationale (lines 637-642) -- lists DEPT/13C/HSQC/HMBC filtering chain
- **Duplicate**: Structure Elucidation Workflow > Workflow Steps, step 3 (lines 133-136) -- abbreviated version of the same chain: pick 1d, pick hsqc with dept, pick hmbc with c13+hsqc
- **Estimated overlap**: ~6 lines

**2c. Molecular symmetry in peak picking context**
- **Canonical**: Peak Picking > Molecular Symmetry (lines 644-654) -- Ibuprofen example with signal counts
- **Duplicate 1**: Pitfall 1: Signal Count != Atom Count (lines 185-200) -- same concept with different example (C13H18O2)
- **Duplicate 2**: Decision Trees > Handling Symmetry (lines 775-799) -- same concept as decision tree
- **Note**: These are not identical text, but all three sections teach the AI the same concept: "when observed signals < expected atoms, you have molecular symmetry." The Ibuprofen example at lines 648-652 directly overlaps with Pitfall 1's explanation at lines 187-198 (both discuss para-disubstituted benzene).
- **Estimated overlap**: ~15 lines across 3 instances of the same concept

**Recommendation**: Consolidate into one "Peak Picking" section in SKILL.md that covers the scientific rationale, the guided picking approach, and symmetry handling. The three Pitfall sections on symmetry, quaternary carbons, and HMBC noise should become subsections of a unified Peak Picking + Interpretation section rather than separate locations.

---

### Cluster 3: Dereplication Score Interpretation (~45 lines across 3 sections)

**Total lines**: ~7 lines in "Dereplication > Interpreting Results" + ~37 lines in "Result Reporting Templates > Dereplication Results" + ~2 lines in "Quick Reference Card > Key Tolerances"

#### Specific overlapping concepts:

**3a. Score threshold interpretation**
- **Canonical**: Result Reporting Templates > Dereplication Results (lines 844-880) -- full score table and reporting templates
- **Duplicate 1**: Quick Reference Card > Key Tolerances (line 933) -- "Dereplication: score > 0.85 strong, 0.65-0.85 possible, < 0.50 no match"
- **Duplicate 2**: Dereplication > Interpreting Results (lines 313-319) -- describes score/deviation ranking (different angle, but overlapping)
- **Estimated overlap**: ~8 lines

**Recommendation**: Keep a single score interpretation reference in SKILL.md's dereplication section.

---

### Cluster 4: MAE / Ranking Score Interpretation (~55 lines across 2 sections)

**Total lines**: ~45 lines in "LSD Integration > Solution Ranking and MAE Interpretation" + ~11 lines in "Quick Reference Card > Ranking Output Interpretation"

#### Specific overlapping concepts:

**4a. MAE quality thresholds table**
- **Canonical**: Solution Ranking and MAE Interpretation (lines 529-536) -- full table with 4 tiers
- **Duplicate**: Quick Reference Card > Key Tolerances (line 934) -- compressed single-line version: "MAE < 2.0 = Excellent, 2-3.5 = Good..."
- **Duplicate 2**: Quick Reference Card > Ranking Output Interpretation (lines 936-946) -- restates the ranking output format already shown at lines 518-523
- **Estimated overlap**: ~12 lines

**Recommendation**: Keep in one place in SKILL.md's ranking section.

---

### Cluster 5: Database Statistics (~15 lines across 3 sections)

**Total lines**: ~17 lines in "Reference Data > Compound Database" + ~5 lines in "End-User Setup > Download Compound Database" + ~2 lines in "13C Shift Prediction" introduction

#### Specific overlapping concepts:

**5a. Database size and contents**
- Lines 38-42 (setup section): "928K compounds (COCONUT + NMRShiftDB) with 13C NMR shifts", "7.9M HOSE statistics"
- Lines 281-289 (reference data section): Same stats in table form: "928,443 (COCONUT + NMRShiftDB)", "7.9M entries"
- Lines 957-958 (prediction section): "7.9M pre-computed HOSE statistics from 895K compounds"
- **Estimated overlap**: ~10 lines

**Recommendation**: Keep the database stats in one location (End-User Setup for download context), reference elsewhere.

---

## Misplaced Intelligence

The following sections contain content that teaches the AI HOW to reason about NMR and structure elucidation, rather than documenting project setup or tool syntax. This is domain intelligence that belongs in a CASE skill document.

| Section | Lines | What's Misplaced | Why It's Misplaced | Target Document |
|---------|-------|-----------------|-------------------|-----------------|
| Blind CASE Protocol | 61-92 | Research evaluation ethics, data sanitization workflow | Teaches AI how to handle blind evaluation scenarios -- this is CASE workflow logic, not project configuration | SKILL.md (CASE skill preamble) |
| Available Subskills > Workflow Selection | 102-114 | Decision tree for choosing subskill | Encodes AI decision logic for which approach to use | SKILL.md or SUPERVISOR.md |
| Structure Elucidation Workflow | 122-141 | Complete CASE workflow steps 0-6 | Core CASE methodology the AI follows -- this IS the skill | SKILL.md (primary workflow) |
| NMR Quick Reference > Experiment Types | 145-155 | Table of NMR experiments and what they show | Domain knowledge about NMR spectroscopy that helps the AI interpret data | SKILL.md (NMR background section) |
| NMR Quick Reference > 13C Chemical Shift Regions | 157-166 | Chemical shift assignment table (0-50 ppm = aliphatic, etc.) | Teaches AI to interpret shift values -- pure domain knowledge | SKILL.md (NMR background section) |
| Common Pitfalls (entire section) | 183-269 | 5 pitfalls with problem/cause/solution patterns | Encodes expert NMR reasoning: how to detect symmetry, handle quaternary carbons, filter noise, diagnose LSD problems, infer heteroatom positions | SKILL.md (troubleshooting section) |
| Dereplication > Interpreting Results | 313-319 | Score interpretation logic | Teaches AI how to evaluate dereplication quality | SKILL.md (dereplication section) |
| LSD Integration > Correlation Order | 343-362 | Rule about HSQC-before-HMBC with error diagnosis | LSD domain knowledge about file construction rules | SKILL.md (LSD section) |
| LSD Integration > Hybridization Rules | 364-389 | sp2 counting rules with Caffeine example | Chemistry domain knowledge about hybridization | SKILL.md (LSD section) |
| LSD Integration > Heteroatom Attachment | 391-443 | BOND vs LIST/PROP decision logic with examples | Teaches AI when to use which constraint approach | SKILL.md (LSD section) |
| LSD Integration > Solution Ranking | 508-552 | MAE interpretation, why correct structures may not rank #1, best practices | Teaches AI expert-level reasoning about ranking results | SKILL.md (ranking section) |
| Manual LSD File Construction (entire section) | 562-625 | Template, checklist, troubleshooting | Step-by-step domain procedure for manual file construction | SKILL.md (merge into LSD section) |
| Peak Picking > Scientific Rationale | 629-642 | Why guided picking is needed, what artifacts look like | NMR spectroscopy domain knowledge | SKILL.md (peak picking section) |
| Peak Picking > Molecular Symmetry | 644-654 | How to detect and interpret symmetry | CASE reasoning skill | SKILL.md (peak picking section) |
| Peak Picking > Working with APT | 656-671 | APT interpretation rules with cross-reference logic | NMR domain knowledge | SKILL.md (peak picking section) |
| Decision Trees (entire section) | 751-840 | Three decision trees encoding CASE workflow logic | These ARE the CASE skill's decision logic -- when to proceed, how to handle symmetry, how to interpret LSD results | SKILL.md (or SUPERVISOR.md for the top-level elucidation decision tree) |
| Result Reporting Templates (entire section) | 842-910 | Score interpretation tables, reporting templates | Teaches AI how to communicate results based on score thresholds | SKILL.md (output formatting section) |
| Quick Reference Card > Essential Workflow | 914-921 | 7-step workflow summary | Abbreviated version of the CASE workflow | SKILL.md (quick reference) |
| Quick Reference Card > Red Flags | 923-927 | Pattern recognition for NMR anomalies | Expert reasoning about what NMR anomalies mean | SKILL.md (quick reference) |
| Quick Reference Card > Key Tolerances | 929-934 | Numeric thresholds for matching | Domain-specific thresholds that guide AI reasoning | SKILL.md (quick reference) |
| Quick Reference Card > When to Ask for Help | 948-952 | Escalation criteria | CASE workflow decision logic | SKILL.md or SUPERVISOR.md |

### Correctly Placed Content (stays in CLAUDE.md)

| Section | Lines | Why It's Correct |
|---------|-------|------------------|
| Title + description | 1-6 | Project identity |
| End-User Setup | 7-59 | Installation and configuration -- exactly what CLAUDE.md is for |
| Reference Data > Compound Database | 271-290 | Database download reference (slight overlap with setup, but useful as standalone ref) |
| Dereplication > CLI Usage | 297-311 | CLI syntax reference |
| LSD Integration > LSD File Structure | 325-341 | Tool syntax reference (brief) |
| LSD Integration > LSD Command Format | 445-476 | Command syntax reference |
| LSD Integration > Converting Solutions to SMILES | 478-506 | CLI workflow reference |
| LSD Integration > LSD Runner Notes | 554-558 | Technical implementation note |
| NMR Quick Reference > Tool Output Reference | 168-179 | Tool API reference |
| Peak Picking > HSQC: DEPT-Guided Picker | 673-702 | Python API reference (keep API syntax, move rationale) |
| Peak Picking > HMBC: Guided Picker | 704-737 | Python API reference (keep API syntax, move rationale) |
| Peak Picking > Other 2D Spectra | 739-747 | Python API reference |
| 13C Shift Prediction > CLI Usage | 960-968 | CLI syntax reference |
| 13C Shift Prediction > Python API | 970-978 | Python API reference |
| Developer Reference (entire section) | 999-1080 | Build commands, project structure, architecture decisions |

---

## Migration Summary

### Destination Breakdown

| Destination | Sections Moving | Approx Lines | Notes |
|-------------|----------------|--------------|-------|
| **Keep in CLAUDE.md** | Title, End-User Setup, Tool Output Reference, CLI syntax stubs for dereplication/prediction/LSD, LSD Runner Notes, Developer Reference | ~225 | Core: setup (59) + brief tool syntax refs (~80) + developer ref (82) + misc (~4) |
| **Move to SKILL.md** | Structure Elucidation Workflow, NMR Quick Reference (domain parts), Common Pitfalls, LSD Integration (domain parts), Manual LSD File Construction, Peak Picking (domain/rationale parts), Result Reporting Templates, Quick Reference Card, 13C Shift Prediction (interpretation parts) | ~590 | The bulk of CASE intelligence. Consolidation will reduce from ~590 to ~450 after deduplication |
| **Move to SUPERVISOR.md** | Decision Trees > When to Proceed (lines 753-773), Available Subskills > Workflow Selection (lines 102-114), Quick Reference Card > When to Ask for Help (lines 948-952) | ~40 | Top-level orchestration decisions: which skill to invoke, when to escalate |
| **Move to Blind CASE skill** | Blind CASE Protocol (lines 61-92) | ~32 | Research evaluation protocol -- specialized concern, not general CASE workflow |
| **Deduplicate (remove)** | Overlapping LSD rules (ELIM, sp2, HSQC-before-HMBC in 6+ locations), duplicate HMBC noise explanations, repeated score thresholds, repeated database stats, redundant symmetry explanations | ~175 | Estimated removable overlap. Actual removal during migration; some will be absorbed into canonical versions |

### CLAUDE.md Size Projection

| Component | Lines |
|-----------|-------|
| Title + description | 6 |
| End-User Setup (keep as-is) | 53 |
| Tool Output Reference (from NMR Quick Reference) | 12 |
| Dereplication CLI syntax (trimmed) | 15 |
| LSD Integration CLI syntax (trimmed: file structure, command format, outlsd, runner notes) | 50 |
| Peak Picking API reference (trimmed: HSQC picker, HMBC picker, COSY syntax only) | 40 |
| 13C Shift Prediction CLI + API (trimmed) | 25 |
| Developer Reference (keep as-is) | 82 |
| Section separators and spacing | ~15 |
| **Total projected CLAUDE.md** | **~298 lines** |

This is well under the 800-line target. The reduction is dramatic because the current file is approximately 80% domain knowledge that will move to SKILL.md.

### Risk Assessment for Migration

| Risk | Mitigation |
|------|-----------|
| AI loses access to domain knowledge after migration | SKILL.md must be loaded by the CASE skill; verify skill loading before removing from CLAUDE.md |
| Tool syntax becomes disconnected from domain context | Keep brief "what it does" descriptions alongside CLI syntax in CLAUDE.md; detailed "how to interpret results" goes in SKILL.md |
| LSD consolidation misses edge cases | Use the "Manual LSD File Construction" checklist as the canonical pre-flight checklist in the consolidated LSD section |
| Quick Reference Card loses its value | Move entirely to SKILL.md as a quick-reference appendix -- its value is during CASE execution, not project setup |

---

## Appendix: Category Distribution

```
project-setup:    ~59 lines  ( 5%)  -- End-User Setup
developer-ref:    ~87 lines  ( 8%)  -- Developer Reference + LSD Runner Notes
case-workflow:    ~282 lines (26%)  -- Blind CASE, Subskills, Workflow, Decision Trees, Reporting, Quick Ref (partial)
domain-knowledge: ~350 lines (32%)  -- NMR Reference, Pitfalls, Hybridization, Heteroatom, Symmetry, Rationale, APT
tool-usage:       ~302 lines (28%)  -- CLI/API syntax, Python examples, output formats, file structure
                  -----
                  1,080 lines
```

Of the tool-usage category (~302 lines), approximately:
- ~80 lines are pure syntax (keep in CLAUDE.md)
- ~222 lines include domain reasoning embedded in tool-usage sections (move domain parts to SKILL.md, keep syntax stubs)
