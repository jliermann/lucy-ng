# Requirements: v9.0 CASE Reliability & Skill Consolidation

**Defined:** 2026-05-20
**Core Value:** AI agent autonomously determines compound structures from NMR — and the pipeline that produces the answer is reliable and uses the intended mechanism, not a manual bypass.
**Driver:** `.planning/v8.0-UAT-POSTMORTEM.md` (v8.0 found ibuprofen but bypassed its own pyLSD system).

## v1 Requirements

Requirements for v9.0 release. Outcome-level where possible so they survive the Phase-1 design decisions. Each maps to roadmap phases.

### Design Re-Validation (FIRST — gates all fixes)

- [ ] **DESIGN-01**: 4J-handling and aromatic-ring approach is decided and documented, with the Phase-65 hypothesis ("removing 4J HMBC makes the aromatic ring appear") re-evaluated against actual CASE evidence (ring had to be force-fragmented in the v8.0 UAT)
- [ ] **DESIGN-02**: Solver-path architecture is decided (single path vs normal-LSD + pyLSD dual path) together with a skill-documentation strategy that prevents the agent reverting to the better-documented path

### Reliability (design-agnostic, outcome-level)

- [ ] **RELI-01**: LSD solutions reliably convert to ranked SMILES with no silent solution loss — when the solver finds N solutions, the pipeline ranks them (covers the outlsd conversion / `lucy lsd run` exit-255 / empty-merge failures)
- [x] **RELI-02**: Every solver invocation runs with the COMPLETE validated constraint set — no silent constraint loss on any solver path (covers permutation-file constraint drop and the non-native-translation gap)
- [x] **RELI-03**: Aromatic compounds reliably yield aromatic-ring solutions in the ranked output (per the DESIGN-01 decision)

### Skill Consolidation

- [x] **SKILL-01**: All agent skills are correct against actual LSD-3.4.9 behavior — no commands taught that the binary rejects (e.g., SYME / DEFF NOT are non-native); native equivalents documented
- [x] **SKILL-02**: Skills give unambiguous single-solver-path guidance per DESIGN-02 (resolve the normal-LSD-vs-pyLSD documentation imbalance)
- [x] **SKILL-03**: devils-advocate gates detect the v8.0 failure modes — silent constraint loss, empty/zero merge despite per-run solutions, and post-validation file edits

### Post-UAT Fixes (Phase 77 — from 76-VERIFICATION.md forensics)

- [x] **FIX-01**: `lucy lsd run` produces real SMILES in solutions.smi and fails loud (non-zero exit, no false "success") when outlsd output is the error string / empty / non-SMILES; regression test covers happy + error paths
- [x] **FIX-02**: Cross-ring aromatic COSY equivalence pairs are emitted deterministically by tooling (from detected symmetry/grouping), so the aromatic ring emerges without manual atom-index reasoning or forced ring-BONDs; ring-BOND forcing demoted to documented escalation
- [x] **FIX-03**: Skill hygiene — deprecated lucy-case-agent.md retired; targeted skill-creator audit confirms v9.0 single-path + emergent/COSY guidance is prominent and flags dead/contradictory content *(NOTE: Phase 77 "retired" it only by frontmatter-rename + deprecation header — the physical 1291-line file lingered until it was actually DELETED under FIX-09 on 2026-06-10. "Retire" should have meant delete.)*
- [x] **FIX-04**: Peak-picker threshold replaced with SNR/MAD-absolute (noise = 1.4826·MAD, floor k=3 IUPAC LoD); solvent multiplet (CDCl₃ etc.) excluded before threshold/scale computation; per-peak SNR annotation added to Peak1D and JSON output; backwards-compatible (threshold param kept; use_snr=True is new default)
- [x] **FIX-05**: 13C intensity class-normalized 2C-equivalence detection for protonated aromatic CH (HSQC-confirmed, 100–165 ppm scope); output feeds `lucy analyze symmetry` / `lucy detect aromatic-cosy`; DO NOT modify detect_aromatic_cosy_pairs
- [x] **FIX-06**: Skill feedback loop — (a) DBE self-check procedural/mandatory in nmr-chemist after picking (O→carbonyl 160–220; N→amide/nitrile); (b) 5th quality loop-pattern QUALITY_CONVERGENCE_FAILURE in case.md detect_loops + loop-patterns.md + advisory-templates.md; budget = 1 re-look cycle; does NOT escalate to diagnostic specialist
- [ ] **FIX-07**: Long-range / 4J HMBC connectivity handling — false-positive long-range (4J) HMBC correlations must no longer be enforced as 2-3J bonds that exclude the correct structure. Exposed by the Phase-79 blind CASE9 UAT: `HMBC 1 8` (166.1↔70.2) + set 2 3 / 2 9 / 3 8 forced an impossible carbonyl→para-benzylic bond, excluding the true para-benzoate (`CC(C)OC(=O)c1ccc(C(C)O)cc1`). Must not reintroduce the v7.0 100%-FP statistical failure; must not regress the v4.0 ibuprofen 4J win. Approach (extended HMBC range / repaired pyLSD multi-run / narrow heuristic flag) to be chosen in discuss/research.
- [ ] **FIX-08**: Peak-picking integrity — 13C peak-picking must deterministically separate signal from noise so a fresh blind agent receives the real carbons (incl. weak quaternary carbonyls), never a noise-flooded list. Exposed by the Phase-80 blind CASE9 UAT: default `snr_floor=3.0` (IUPAC LoD) returned 76 peaks (~50 baseline ripple at SNR≈3, incl. 13 impossible >220 ppm), so the agent's manual curation dropped the genuine ester carbonyl (166.08 ppm, SNR 17) → DBE misallocated (benzene+O-ring instead of benzene+C=O) → para-benzoate excluded. No overcount guard exists: `analyze symmetry`/`symmetry_analysis.py` only model the undercount (equivalence) direction; 76-observed-vs-12-expected prints a silent negative and even confirmed the carbonyl-free skeleton. Fixes: snr_floor default 3→5; expose `--snr-floor` in `lucy pick 1d`; overcount guard + `missing_carbons<0` alarm; nmr-chemist SNR≥5/carbonyl-never-discard rules; CASE9/12 regression test. Must not regress prior passing CASE1.
- [x] **FIX-09**: Blind-UAT skill hygiene — every runtime file a fresh blind CASE instance loads (`~/.claude/commands/lucy-ng/case.md` + `references/`, and the 4 spawned team agents `lucy-nmr-chemist`/`lucy-lsd-engineer`/`lucy-solution-analyst`/`lucy-devils-advocate`, plus `lucy-diagnostic`) must contain ONLY compound-agnostic NMR/LSD domain knowledge. All blind-test contaminants must be removed: (L1) GSD dev-meta — phase numbers, decision IDs (D-xx/FIX-xx/DESIGN-xx), milestone versions (v2.1–v9.0), "UAT"/"gate"/"milestone"/"postmortem", experiment-arm labels (Arm A/B/C); (L2) answer-key — named test compounds (ibuprofen, para-benzoate), formulas tied to a test (C13H18O2/C12H16O3), test-answer SMILES, specific solution atom mappings (COSY 4 7, BOND 10 11, "iter3"), specific test-spectrum shifts ([44.90,45.03]), "CASE9 trap"/"CASE9"/"CASE1"; (L3) success-criteria — pass/fail gate definitions baked into runtime ("EMERGENT RING = CLEAN PASS", the `uat_criteria` step, "fails the Phase 78 UAT gate"). Exposed 2026-06-10 when a fresh CASE9 instance reported "Phase-78 gate passed — aromatic ring emerged" — it had read the gate criteria from its own skill files. ~52 leak sites inventoried across 6 active files. Gate criteria relocate to the orchestrator/verification tooling layer (`.planning/case-uat-gate-criteria.md` + `scripts/verify_case_solution.py`), not the runtime skill. Neutralization preserves all genuine domain knowledge; answer-key examples become abstract/illustrative.
- [x] **FIX-10**: Constraint-hardness guard — an uncertain structural inference must NEVER be encoded as a hard, solution-excluding LSD constraint (PROP/BOND). Statistical single-shift detections — especially `lucy detect neighbours` O/N inference — are advisory/ranking signals only; heteroatom (and other) placement that lacks DIRECT connectivity evidence (HMBC/HSQC/exchangeable-H) is left OPEN so LSD explores alternatives and 13C ranking discriminates. This is the third instance of the same meta-failure (after v3.0 Pitfall 6 erosion and the FIX-07 4J trap): uncertain interpretation → hard constraint → correct structure excluded. Exposed by CASE9 (isopropyl 4-(1-hydroxyethyl)benzoate, C12H16O3 — RDKit-verified: ZERO ring-oxygen): the nmr-chemist read `detect neighbours 150.80` → O 81% (post N-exclusion) and emitted hard `PROP 2 O 1`, forcing oxygen onto the aromatic carbon that actually bears a benzylic CH(OH)CH₃ → every post-iteration-3 solution carried ring-O → the true para-alkylbenzoate was excluded from the search space. 13C-prediction of the truth fits 8/9 signals; the 150.8 carbon predicts ~144 (a HOSE-DB weakness) — i.e. the O-heuristic is reasonable-but-wrong, which is exactly why it must not be a hard constraint. Fixes: (a) nmr-chemist rule (detect-neighbours = statistical prior/advisory; 145–160 ppm aromatic-C is ambiguous O-substituted vs EDG/benzylic-substituent, esp. when an sp3 C–O ~65–75 ppm could be benzylic; re-assert Pitfall 6); (b) lsd-engineer: no `PROP O`/hard heteroatom BOND from statistics alone, leave open, let ranking decide; (c) devils-advocate gate blocking/flagging a hard heteroatom-neighbour PROP/BOND lacking cited direct evidence; (d) optional tooling: `detect neighbours` output self-labels advisory + regression test. Scope is the constraint-hardness defect ONLY — benzene-ring emergence (D-04) and HMBC-pool richness remain separate CASE9 blockers.
- [ ] **FIX-11**: Aromatize/canonicalize SMILES before 13C prediction — `outlsd`/`lucy lsd run` emits **Kekulé** SMILES (aromatic ring written as e.g. `C(=C1)C=CC(=C1)`); feeding these directly to `lucy predict c13` makes the HOSE/predictor treat the ring as a non-aromatic diene → wrong aromatic shifts → wrong MAE/ranking. Exposed by the 2026-06-11 Opus-4.8 CASE9 run: the solution-analyst predicted on un-aromatized Kekulé SMILES, concluded "correct structure NOT in the LSD set, all 20 implausible, ESCALATE" — a FALSE ALARM the coordinator caught and retracted (the true structure WAS line 12; after RDKit canonicalization MAE 1.17, 11/12 ≤3 ppm, rank 1). Fix in the ranking/prediction pipeline (`lucy lsd rank` + `lucy predict c13`): run RDKit `MolFromSmiles`→sanitize/aromatize (or `MolToSmiles` canonical) before HOSE generation, so Kekulé input is handled transparently; + regression test on a Kekulé benzoate SMILES asserting it predicts identically to its canonical aromatic form. Belt-and-suspenders: a solution-analyst skill note to canonicalize before predicting.
- [ ] **FIX-12**: HMBC peak-picking integrity (S/N vs signal — HMBC analog of FIX-08) — `lucy pick hmbc` (and the guided-HMBC raw-pick path) thresholds on `-t/--threshold` = **fraction-of-max (default 0.05)** only; there is NO `--snr-floor`. Intense aliphatic/2J cross-peaks set the global max, so weak-but-real long-range correlations fall below 5%×max and are dropped. **Empirically proven on CASE1 (ibuprofen, HMBC expno 7):** the ring-diagnostic **3J-meta** cross-peaks H4→C2 (C≈141/H≈7.11) and H6→C3 (C≈137/H≈7.23) sit at **~0.6% of max** while the **2J-ortho** peaks are at ~22% — so the 3J-meta are ~35× weaker and ~8× below the default threshold → systematically discarded; they only appear at `-t 0.005`, buried in a 165-peak noise flood (no clean fraction-of-max gap between ~0.6% signal and ~0.5–2% noise). This is very likely the REAL emergent-ring blocker (D-04): with H4→C2 + H6→C3 recovered, the 6 ring edges are pinned (2J-ortho + COSY CH–CH + the recovered 3J-meta + 2C-symmetry) and the benzene ring can emerge without forced ring-BONDs. Fix: give the HMBC picker a **noise-relative SNR floor** (keep cross-peaks with SNR ≥ floor over the local 2D noise even at <1% of max; reject ~0.5–2%-of-max noise), expose `--snr-floor` in `lucy pick hmbc`, and consider per-row/region normalization so weak aromatic peaks aren't suppressed by intense aliphatic peaks. Regression (CASE1): at the new default the two 3J-meta cross-peaks are retained above the floor AND the noise stays out. See `.planning/research/D04-emergent-ring/`.

### UAT (milestone gate)

- [x] **UAT-03**: CASE1 blind re-run — **SOLVED 2026-06-11 on Opus 4.8** (model gate PASS). Single unique LSD solution `CC(C)Cc1ccc(C(C)C(=O)O)cc1` = ibuprofen, RDKit-canon-verified, MAE 2.233, aromatic confirmed, no manual `lucy lsd` bypass, no SKEL, no hard PROP O; the original 4J-ibuprofen trap was overcome (false para-4J HMBC 2 8 / 8 6 topologically identified + removed, no ELIM needed). Mechanism caveat = documented ring-BOND escalation (same as CASE9; emergent ring did NOT form — root cause now traced to HMBC picking, see FIX-12). Escalated at iteration 3 (one short of the strict ≥3-emergent-iterations gate rule) but well-justified by correct root-cause diagnosis.
- [x] **UAT-04**: CASE9 blind run (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3, nmrxiv D202) — **SOLVED 2026-06-11 on Opus 4.8** (model gate PASS, all agents claude-opus-4-8, no mismatch). Top structure `CC(C)OC(=O)c1ccc(C(C)O)cc1` is RDKit-canon-identical to the D202 truth, a genuine LSD solution (solutions.smi line 12), rank 1 on both tiers (11/12 ≤3 ppm, greedy-MAE 1.17, clean separation from rank 2 at 5.64). Mechanism = CONDITIONAL PASS: no SKEL, no hard PROP O; aromatic ring built via 6 explicit ring-BONDs as a DOCUMENTED escalation (emergent cross-ring-COSY attempted 3 iterations first, benzene fraction stayed ~5%, then logged Option-B ring-BOND forcing with O-positions left open for ranking). Caveats: emergent-ring (D-04) still unsolved (LSD builds C=O into the ring → forcing required); the prior 2026-06-10 Sonnet-4.6 run failed (wrong phenol ring-OH) — the earlier failures were substantially MODEL-driven (Sonnet vs Opus 4.8). See CASE9-UAT-04-PASS verdict.*

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Performance

- **PERF-01**: Parallel LSD binary execution across permutations (sequential is acceptable for ≤8 permutations; revisit only if UAT shows it is too slow)

### Heteroatom Ambiguity (carried from v8.0 deferral)

- **HETERO-01**: Multi-state MULT for ambiguous heteroatoms with combinatorial LSD runs
- **HETERO-02**: Automatic default state insertion for undefined heteroatom hybridisation/multiplicity

## Out of Scope

| Feature | Reason |
|---------|--------|
| Statistical 4J detection | v7.0 proved non-viable (100% false positive rate) |
| pyLSD as external dependency | Orchestration is implemented directly in Python |
| New domain features | v9.0 is reliability + consolidation of existing capabilities, not new functionality |
| Re-deriving v8.0 infrastructure from scratch | Repair/consolidate the shipped v8.0 code, do not rewrite wholesale |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DESIGN-01 | Phase 72 | Pending |
| DESIGN-02 | Phase 72 | Pending |
| RELI-01 | Phase 73 | Pending |
| RELI-02 | Phase 74 | Complete |
| RELI-03 | Phase 74 | Complete |
| SKILL-01 | Phase 75 | Complete |
| SKILL-02 | Phase 75 | Complete |
| SKILL-03 | Phase 75 | Complete |
| FIX-01 | Phase 77 | Complete |
| FIX-02 | Phase 77 | Complete |
| FIX-03 | Phase 77 | Complete |
| FIX-04 | Phase 79 | Complete |
| FIX-05 | Phase 79 | Complete |
| FIX-06 | Phase 79 | Complete |
| FIX-07 | Phase 80 | Mechanism delivered; blind UAT gate FAILED (upstream picker defect) |
| FIX-08 | Phase 81 | Code complete + verified |
| FIX-09 | Phase 82 | Complete (60 edits, 0 residual leaks verified) |
| FIX-10 | Phase 83 | Complete + verified (constraint-hardness guard) |
| FIX-11 | Phase 84 | Pending (canonicalize/aromatize SMILES before 13C prediction) |
| FIX-12 | Phase 85 | Pending (HMBC SNR-floor picking — emergent-ring root cause) |
| UAT-03 | Phase 78 + Opus 4.8 | **PASS 2026-06-11** (CASE1 ibuprofen SOLVED, RDKit-verified, single solution; conditional mechanism) |
| UAT-04 | Phase 83 + Opus 4.8 | **PASS 2026-06-11** (CASE9 SOLVED, RDKit-verified; conditional mechanism) |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-05-20*
*Traceability filled: 2026-05-20 — roadmapper assigned all 10 requirements to phases 72-76*
*v8.0 requirements (GATE/INPUT/ORCH/CLI/AGT/UAT-01/02) preserved in git history + ROADMAP.md phase sections + v8.0-UAT-POSTMORTEM.md*
