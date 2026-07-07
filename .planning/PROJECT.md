# lucy-ng

**AI-agent powered Computer-Assisted Structure Elucidation for organic natural products**

## What This Is

Lucy-ng is an AI-agent skill for Computer-Assisted Structure Elucidation (CASE) of organic natural products from NMR spectroscopy data. The AI agent is the intelligence layer -- it reasons about spectra, detects problems, and drives the elucidation process. The Python tools are thin wrappers around external libraries (nmrglue, LSD, RDKit) that give the agent access to NMR data and solvers. The skill (CLAUDE.md) encodes domain expertise and workflow strategy.

## Core Value

An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## Current Milestone: v9.2 CASE Web-View

**Goal:** A read-only web dashboard makes a CASE run observable live (and after the fact) — purely informative, no control functions.

**Target features:**
- `lucy webview serve/stop/status` — standalone FastAPI server (optional extra `lucy-ng[webview]`) rendering any `analysis/` folder read-only with auto-refresh
- Run-status widget (iteration / active phase / elapsed)
- Top-structures widget (RDKit depiction + MAE/rank)
- Scrollable log widget (`CASE-PROGRESS.md`)
- `case.md` integration: orchestrator starts the server at run start and reports the URL
- Server outlives `terminate_team` (user stops it via `lucy webview stop`)

Design spec: `docs/superpowers/specs/2026-07-02-case-webview-design.md`. Stage 2 (deferred, NOT this milestone): rendered spectra tabs + data tables.


**Carried seed:** CASE4 azulene-regiochemistry-enumeration gap (4th defect class surfaced by the v9.1 blind UAT) — the di-methyl-ethyl class is now searched, but the exact chamazulene regiochemistry is not enumerated. See `.planning/todos/pending/2026-06-25-case4-azulene-regiochemistry-enumeration-gap.md`.

### v9.1 CASE Final-Answer Correctness & Verification Gates — SHIPPED ✅ (2026-06-29)

**Goal (met):** Close the three "clean-but-wrong" CASE failure classes (low MAE, plausible, but wrong) with verification gates, proven end-to-end by blind UATs.

**Outcome:** Three defect classes fixed + blind-validated. **RANK** — `lucy lsd rank` + `lucy predict c13` unified onto one DB-first prediction path. **IDENT** — installed `lucy identify` (shared deterministic core, reachable from any CASE data dir) + analyst tentative-naming + post-solution devils-advocate `G-IDENT` gate stop parametric naming hallucination. **MULT** — per-family multiplicity search + MAE-independent SEARCHED-not-RANKED `coverage_gate` + binding DA `G-MULT` flag close the wrong-class exclusion. **Blind-UAT gate** — five blind runs (RDKit-verified): CASE5 indigo / CASE6 citronellol / CASE7 virgiline / CASE8 eugenol PASS; CASE4 chamazulene conditional. Live-confirmed: `lucy identify` all 3 verdict branches; `G-IDENT` both branches; MULT fires/dormant correctly. Full archive: `milestones/v9.1-ROADMAP.md` + audit `milestones/v9.1-MILESTONE-AUDIT.md`. One deferred follow-up (the carried seed above).

### v9.0 CASE Reliability & Skill Consolidation — SHIPPED ✅

**Goal (met):** Make the CASE system work end-to-end via the intended mechanism — fix the tooling bugs the v8.0 UAT exposed, consolidate the skill/tool architecture, and re-answer the open 4J/aromatic design question — verified by a passing blind UAT on CASE1 **and** CASE9.

**Outcome:** AND-gate met cleanly on Opus 4.8. CASE9 (UAT-04) solved (`CC(C)OC(=O)c1ccc(C(C)O)cc1`, MAE 1.17). CASE1 (UAT-03) a CLEAN EMERGENT PASS — ibuprofen rank 1 (exact InChIKey, RDKit-verified), benzene ring emerged from constraints with **0 ring-BONDs / SKEL / SYME / DEFF NOT**, no manual bypass. **D-04 resolved to "emergent."** A substantial earlier-failure root cause turned out to be model-driven (a stale `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` override, now `inherit`). Full archive: `milestones/v9.0-ROADMAP.md`.

## Current State

**Version:** v9.1 shipped 2026-06-29 (v9.0 shipped 2026-06-17)
**Codebase:** Python package (`src/lucy_ng/`), test suite **1131 passing** at v9.1 close
**Database:** SQLite with 928K compounds, 7.9M HOSE statistics + fragment library (2.4M SSCs)
**Agent definitions:** 4-agent CASE team + case.md orchestrator (in `repo/.claude/`, symlinked into `~/.claude`)
**New CLI (v9.1):** `lucy identify` (structure→identity gate); `lucy pick hsqc` now reports `multiplicity_edited`; `lucy lsd rank` unified onto the shared 13C predictor.

**What shipped in v9.1:** Three "clean-but-wrong" CASE failure classes closed with verification gates, blind-validated end-to-end. RANK (ranker↔predict unified, ibuprofen MAE 2.23→0.24); IDENT (`lucy identify` + post-solution `G-IDENT` gate stop naming hallucination); MULT (per-family multiplicity search + MAE-independent `coverage_gate` + binding `G-MULT` flag). Validated by 5 blind UATs (CASE5/6/7/8 PASS, CASE4 conditional), each RDKit-verified.

**What shipped in v9.0:** End-to-end CASE reliability — `lucy lsd run`/outlsd plumbing; native-only constraint translation (SYME→BOND/COSY, DEFF NOT→DEFF F/FEXP); peak-picking SNR-floors (FIX-08/12); constraint-hardness guard (FIX-10); blind-UAT skill decontamination (FIX-09). Validated: CASE9 solved + CASE1 clean emergent pass.

**Known deferred:** CASE4 azulene-regiochemistry-enumeration gap (4th defect class; exact chamazulene regiochemistry not yet reachable). See STATE.md Deferred Items.

## Architecture

- **Skill** (CLAUDE.md/SKILL.md): Domain expertise, workflow strategy, error handling knowledge -- the intelligence layer
- **Thin Tools**: Minimal Python CLI wrappers around nmrglue, LSD, RDKit, SQLite
- **Multi-Agent**: CASE agent (autonomous elucidation) + CASE orchestrator (loop detection, advisory intervention) + diagnostic specialist (deep LSD failure analysis)
- **Database**: SQLite with 928K compounds and 7.9M HOSE statistics

## Requirements

### Validated

- Read 1D Bruker NMR files (1H, 13C) — v1.0
- Read 2D Bruker NMR files (HSQC, HMBC, COSY) — v1.0
- Automated peak picking for 1D spectra — v1.0
- Automated peak picking for 2D spectra (DEPT-guided, HMBC-guided) — v1.0
- Generate LSD/pyLSD input file format — v1.0
- Execute LSD/pyLSD and parse results — v1.0
- CLI interface for all operations (7 command groups) — v1.0
- MCP server exposing tools for Claude (13 tools) — v1.0
- HOSE-based 13C shift prediction for solution ranking — v1.0
- NMRXiv dataset fetching — v1.0
- SQLite database for 928K compounds (COCONUT + NMRShiftDB) — v1.1
- Database-backed dereplication (~100x faster) — v1.1
- Database-backed 13C prediction with 7.9M HOSE statistics — v1.2
- MCP tool for checking prediction capability (get_hose_stats_info) — v1.2
- Sub-command skills following GSD pattern (sanitise, dereplicate, case, predict, status) — v2.1
- CASE orchestrator with real agent spawning, progress monitoring, loop detection, diagnostic delegation — v2.1
- Autonomous CASE agent definition with full skill knowledge and CASE-PROGRESS.md writing — v2.1
- AI-driven dataset sanitisation (compound identity removal, no CLI) — v2.1
- Diagnostic specialist agent reworked for orchestrator integration — v2.1
- Statistical hybridisation detection from HOSE database (sp1/sp2/sp3) — v3.0
- Statistical neighbourhood detection (forbidden/mandatory bond partners) — v3.0
- Hetero-hetero bond allowance detection from bond pair statistics — v3.0
- Signal grouping detection (close shifts within 0.25 ppm tolerance) — v3.0
- Two-tier ranking (match count priority prevents MAE hallucination) — v3.0
- Badlist filters (3/4-membered strained ring exclusion via DEFF NOT) — v3.0
- CASE agent integration with statistical detection and chemistry-first hierarchy — v3.0

### Validated (v4.0)

- 5-agent CASE team architecture (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate) — v4.0
- Team-based orchestrator skill replacing single-agent Task() spawning — v4.0
- Constraint inventory managed by lsd-engineer (read previous file, never reconstruct from memory) — v4.0
- Pre-run LSD validation by devils-advocate (diff vs previous, sp2, H budget, DEFF NOT, SYME) — v4.0
- Post-run solution quality review by solution-analyst (chemical plausibility, aromatic ring verification) — v4.0
- Real-time peer feedback protocol (any agent can flag issues in any other agent's work) — v4.0
- CASE-PROGRESS.md updated for team workflow (multi-agent contributions per iteration) — v4.0
- Aromatic ring awareness: nmr-chemist flags expectation, solution-analyst verifies, remediation guidance for 4J — v4.0
- Diagnostic specialist integration with team context (constraint inventory, analysis/ paths) — v4.0

### Validated (v5.0)

- Fragment library: 2.4M SSCs from 928K compounds with two-phase search engine — v5.0
- DEFF/FEXP goodlist injection validated with LSD smoke test — v5.0
- Agent team integration: lsd-engineer fragment search, devils-advocate file verification — v5.0
- Self-search recall 100% (fingerprint indexing validated) — v5.0

### Validated (v6.0)

- Factored case.md orchestrator (<500 lines) with extracted reference files (progress-format, loop-patterns, advisory-templates) — v6.0
- Archived legacy monolithic lucy-case-agent.md with deprecation header — v6.0
- Shared NMR reference tables (nmr-basics.md) referenced by agents instead of inlined — v6.0
- 4J HMBC coupling awareness: nmr-chemist flags, lsd-engineer defers, solution-analyst verifies via prediction — v6.0
- Orchestrator structured message validation with RESEND-REQUIRED protocol — v6.0
- Natural-language trigger phrases in all 5 skill descriptions + routing decision tree — v6.0
- Dry-run confirmation gate in sanitise, HOSE miss recovery in predict, 0-match guidance in dereplicate — v6.0
- Version compatibility check in status skill, smoke test mode in CASE orchestrator — v6.0

### Validated (v9.0 / v9.1)

- End-to-end CASE reliability: lsd-run/outlsd plumbing, native-only constraints, peak-picking SNR-floors, constraint-hardness guard, blind-UAT skill decontamination — v9.0
- Ranker↔predict unification: one DB-first 13C prediction path (RANK-01/02/03) — v9.1
- Tool-derived identity gate: installed `lucy identify` + analyst tentative-naming + post-solution devils-advocate `G-IDENT` (IDENT-01/02/03) — v9.1
- Aliphatic multiplicity coverage: per-family LSD search + MAE-independent `coverage_gate` + binding `G-MULT` flag + `pick hsqc multiplicity_edited` detector (MULT-01/02/03/04) — v9.1
- Blind-UAT validation gate: 5 RDKit-verified blind runs (CASE5/6/7/8 pass, CASE4 conditional) (UAT-01/02/03) — v9.1

### Deferred

- [ ] CASE4 azulene-regiochemistry-enumeration gap — exact chamazulene regiochemistry not reachable (di-methyl-ethyl class is searched). 4th defect class surfaced by v9.1 UAT-01. (todo `2026-06-25-case4-azulene-regiochemistry-enumeration-gap`)
- [ ] 4J HMBC coupling handling via pyLSD (Priority 1 — v7.0 statistical approach failed, pyLSD solver-based approach next)
- [ ] Multi-compound CASE comparison UAT (blocked on 4J handling or non-aromatic test compounds)
- [ ] Support for COSY correlations in LSD constraints (Priority 3)
- [ ] NP-likeness scoring for solution filtering (Priority 4 — RDKit built-in)
- [ ] Multi-fragment sequential injection (FRAG-05)
- [ ] Solvent-aware 13C prediction
- [ ] Stereochemistry handling (E/Z, R/S)
- [ ] Interactive CASE mode with user feedback loop

### Out of Scope

- NMR spectrum prediction from structures - use HOSE codes instead
- GUI or web visualization - purely programmatic interface
- Non-Bruker vendor formats (Varian, JEOL, etc.) - Bruker only for v1
- SENECA integration - requires Java GUI rebuild, deferred

## Constraints

- Python 3.10+ required
- Open source only - no proprietary dependencies
- Open data formats - no vendor lock-in
- Must interface with existing LSD/pyLSD CLI tools

## Context

### Background

Lucy was the original CASE software created by the project author and sold to Bruker. Lucy-ng represents a complete reimagining for the AI-agent era, prioritizing programmatic interfaces over GUI interactions.

### Strategic Reference

See `background/sherlock-analysis.md` — deep comparison of Sherlock CASE (Wenk PhD thesis) vs lucy-ng capabilities. Updated post-v4.0 with gap closure status and prioritized next milestones. Key finding: 4 of 5 critical gaps closed (v3.0/v4.0); fragment library (24.5M SSCs) is the remaining major gap for Sherlock parity.

### Problem

Existing NMR processing tools like nmrium are GUI-focused, making it difficult for AI agents to interact with them programmatically. An unattended system that can iterate through structure elucidation without human intervention requires a different architecture.

### Target Users

- Cheminformatics researchers
- Natural products chemists
- AI/ML researchers working on structure elucidation

### NMR Data Requirements

Minimum viable spectral data for v1:
- 1D: 1H and 13C spectra
- 2D: HSQC (direct C-H correlations) and HMBC (long-range correlations)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid CLI + MCP interface | MCP provides structured tools for agent iteration; CLI enables testing and scripting | Good |
| Bruker-only for v1 | Focus on most common format, expand vendor support later | Good |
| LSD/pyLSD as primary solvers | Established CASE tools with CLI interface | Good |
| nmrglue for NMR parsing | Most mature, BSD licensed, native Bruker support | Good |
| Pydantic v2 for models | Type safety, validation, JSON serialization | Good |
| DEPT-guided adaptive thresholding | Lower HSQC threshold until all DEPT carbons matched | Good |
| HMBC-guided peak picking | Filter by requiring C match in 13C/DEPT and H match in HSQC | Good |
| N:1 shift matching for ranking | Handles molecular symmetry correctly | Good |
| SQLite for dereplication DB | Portable, no server, formula-indexed for fast lookup | Good |
| HOSE codes for prediction | Pure Python, no external services, reasonable accuracy | Good |
| AI as intelligence layer | v2.0: Domain knowledge belongs in skill, not Python code | Good |
| Multi-agent CASE | v2.0: Supervisor prevents loops, specialists handle subtasks | Revisit — v2.0 defined on paper only, v2.1 delivers working orchestration |
| Error tolerance as skill knowledge | v2.0: Teach AI to detect close shifts, ambiguity -- not Python machinery | Good |
| MCP removed, CLI-only | v2.0: Single interface, AI uses thin CLI via Bash | Good |
| GSD-pattern sub-commands | v2.1: Skills as ~/.claude/commands/lucy-ng/*.md with Task() agent spawning | Good |
| /lucy-ng:case NEVER dereplicates | v2.1: Absolute separation — dereplication is a separate sub-command | Good |
| Sanitisation is AI-only | v2.1: No CLI for sanitise — requires AI reasoning to identify compound identifiers | Good |
| Orchestration via Task() | v2.1: Orchestrator spawns agents using Task() with model: inherit | Good |
| Hybrid context inlining | v2.1: ~500-700 lines critical knowledge inlined in agents, detailed references via file paths | Good |
| Per-pattern intervention counters | v2.1: Track failures separately per loop pattern, 10-cycle escalation | Good |
| Diagnostic delegation threshold | v2.1: Specialist spawned after 2 failed basic interventions with same pattern | Good |
| Data-driven statistical detection | v3.0: Replace agent guesswork with HOSE database statistics (inspired by Sherlock CASE) | Good |
| Chemistry-first hierarchy | v3.0: NMR evidence (DEPT/HSQC/HMBC) always overrides statistical detection | Good |
| Two-tier ranking | v3.0: Match count primary, MAE secondary — prevents hallucination from wrong structures with coincidentally low MAE | Good |
| Badlist via DEFF NOT | v3.0: Hardcoded strained ring exclusion in agent knowledge rather than automated filtering | Good — but agent drops across iterations |
| Schema migration chain | v3.0: ALTER TABLE v3→v4→v5→v6 with backward-compatible queries | Good |
| Team-based CASE | v4.0: 5-agent team (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate) replacing single autonomous agent. Peer feedback eliminates constraint loss. | Good — all v3.0 bugs fixed |
| Constraint inventory in LSD headers | v4.0: JSON block tracking all constraint types, read-previous-never-reconstruct rule, DA reconciliation | Good |
| Coordinator-as-sole-writer | v4.0: Agents post via SendMessage, coordinator writes CASE-PROGRESS.md — prevents corruption | Good |
| Aromatic ring awareness | v4.0: Post-ranking sanity check when NMR evidence shows aromatic pattern but solutions lack rings | Good — caught in UAT |
| Separate fragment DB | v5.0: lucy-ng-fragments.db (605 MB) independent from main DB (2.8 GB) — prevents Dropbox sync contention | Good |
| 2 ppm fingerprint bins | v5.0: 256-bit fingerprint with 2 ppm bins validated by 100% self-search recall on 1K sample | Good |
| DEFF goodlist over badlist | v5.0: DEFF/FEXP constrains structures TO contain fragment (positive constraint, more powerful than exclusion) | Good — LSD smoke test confirms |
| Fragment persistence rule | v5.0: Copy DEFF F1/FEXP from previous LSD file, never reconstruct — same as DEFF NOT rule | Good |
| UAT deferral for 4J risk | v5.0: All 6 compounds have 4J HMBC risk, deferred CASE comparison to avoid confounding variables | Pending — need non-aromatic compounds |
| Factored case.md with references | v6.0: Extract progress-format, loop-patterns, advisory-templates to references/ for on-demand loading | Good |
| 4J heuristic flagging | v6.0: nmr-chemist flags potential 4J in aromatic systems, lsd-engineer defers, solution-analyst verifies via prediction | Good — heuristic, statistical detection still needed |
| Message validation protocol | v6.0: Orchestrator enforces required fields with RESEND-REQUIRED fallback | Good |
| Trigger phrase pattern | v6.0: "Use when:" prefix in skill descriptions for NL intent routing | Good |
| Dry-run gate in sanitise | v6.0: READ-ONLY scan, manifest report, exact "proceed" required before writes | Good |
| Smoke test mode | v6.0: --smoke-test flag for 1-iteration CASE pipeline validation | Good |
| Statistical 4J detection abandoned | v7.0: HOSE pair distance statistics produce 100% false positive rate — j5_plus dominates universally. Approach fundamentally non-viable. | Failed |
| pyLSD for 4J handling | v7.0 post-mortem: Use constraint solver to explore 4J possibilities directly rather than statistical pre-filtering | Pending |

## Technical State

**Version:** v6.0 (shipped 2026-03-10)
**Codebase:** ~20,974 lines Python, 867 tests
**Tech stack:** Python 3.10+, Pydantic v2, nmrglue, RDKit, NumPy, SQLite, Click
**Database:** v6 schema with 928K compounds, 7.89M HOSE statistics + fragment library (2.4M SSCs, 605 MB)
**Agent definitions:** ~3,600 lines across 6 files (5 agents + orchestrator skill)

**Capabilities:**
- 11 CLI command groups, 30+ commands (thin data-access wrappers)
- 4 statistical detection commands: hybridisation, neighbours, hhb, grouping
- Fragment library: build, search, to-lsd, info commands
- Two-tier ranking with badlist strained ring exclusion + aromatic ring sanity check
- SQLite databases: compound DB (928K compounds, COCONUT + NMRShiftDB) + fragment DB (2.4M SSCs)
- 7.89M HOSE statistics for 13C prediction and statistical detection
- Full CASE pipeline: peak picking → statistical detection → fragment search → LSD generation → solving → ranking
- Sub-command skills: status, dereplicate, predict, sanitise, case (in ~/.claude/commands/lucy-ng/)
- 5-agent CASE team with fragment integration: lsd-engineer searches+injects fragments, devils-advocate verifies files
- Diagnostic specialist: lucy-diagnostic.md (constraint inventory-aware, team context)
- CASE orchestrator: spawns 5-agent team via TeamCreate, monitors CASE-PROGRESS.md, detects 4 loop patterns
- Constraint inventory: JSON tracking in LSD file headers, DA reconciliation gate, DEFF/FEXP tracking

**Known tech debt:**
- 4J HMBC couplings through aromatic rings: heuristic flagging in v6.0, statistical approach failed in v7.0 — next approach: pyLSD integration
- Multi-compound CASE UAT deferred — all test compounds have 4J risk
- 2 minor integration gaps from v6.0 audit (INTL-03 aromatic expectation relay, INTL-04 4J status field validation) — cosmetic

---
### v9.0 Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single solver path (D-02) | v8.0 agent reverted to better-documented normal-LSD; one path removes the ambiguity | Good |
| Native-only constraint translation (D-03) | SYME/DEFF NOT are lucy-ng abstractions, not native LSD-3.4.9; translate to BOND/COSY + DEFF F/FEXP at the boundary | Good |
| Emergent aromatic ring (D-04) | Ring should arise from sp2 MULT + HMBC anchors + cross-ring COSY + ring-size exclusion, not a forced SKEL/ring-BOND | Good — confirmed by CASE1 UAT-03 (0 ring-BONDs) |
| SNR-floor peak picking (FIX-08/FIX-12) | Fraction-of-max masks weak quaternary carbonyls (13C) and ring-diagnostic 3J-meta cross-peaks (HMBC) | Good |
| Constraint-hardness guard (FIX-10) | An uncertain inference must never become a hard, solution-excluding LSD constraint | Good |
| `CLAUDE_CODE_SUBAGENT_MODEL=inherit` | A stale `=sonnet` override silently forced all subagents to Sonnet 4.6 and drove earlier CASE failures | Good — Opus 4.8 then solved both cases |

---
*Last updated: 2026-07-07 — v9.2 webview milestone COMPLETE (phases 90–92, WV-01..08). Phase 92 wired the CASE orchestrator (`case.md`) to auto-launch `lucy webview serve <analysis>` at run-start (before the first `[BEGIN]`), print the dashboard URL + manual `lucy webview stop` hint, and leave the server running past `terminate_team` (survives via `start_new_session=True`); browser is not auto-opened by design. Live-verified on a CASE1 run; a follow-up fix (`f782ea8`) writes the CASE-PROGRESS.md header at run-start so the dashboard log is populated from t=0. Next: run `/gsd-complete-milestone` to archive the webview milestone.*
