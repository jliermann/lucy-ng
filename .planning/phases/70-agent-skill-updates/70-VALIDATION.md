---
phase: 70
slug: agent-skill-updates
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-19
---

# Phase 70 — Validation Strategy

> Per-phase validation contract for markdown-only skill updates.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | grep + manual review (no pytest tests — markdown-only phase) |
| **Config file** | none |
| **Quick verify command** | shell `grep` patterns on the 3 skill files |
| **Full suite command** | `pytest -q` (regression — confirms no Python broke) |
| **Estimated runtime** | <5 seconds for grep checks; ~5 minutes full pytest |

---

## Sampling Rate

- **After every task commit:** Run grep verification commands per task `<verify>` block
- **After all tasks:** Run full `pytest -q` to confirm no Python regression (skill files are markdown, but agents reference paths/commands that must still resolve)
- **Before `/gsd:verify-work`:** Manually read each modified section once to confirm coherent prose
- **Max feedback latency:** <5 seconds for grep; full suite optional

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 1 | AGT-01, AGT-02 | — | lsd-engineer §"Run LSD" contains routing-block | grep | `grep -A 5 "pylsd_mode" ~/.claude/agents/lucy-lsd-engineer.md` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | AGT-02 | — | lsd-engineer ITERATION-COMPLETE has per-permutation table template | grep | `grep "per_permutation_table\|defer_set" ~/.claude/agents/lucy-lsd-engineer.md` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | AGT-04 | — | devils-advocate Check 4 contains G4 with K>3 BLOCK message | grep | `grep -A 3 "G4:" ~/.claude/agents/lucy-devils-advocate.md` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | AGT-03 | — | case.md unchanged (CLI-agnostic per D-17a/b) | grep | `git diff ~/.claude/commands/lucy-ng/case.md` returns empty | ✅ | ⬜ pending |

*Final task IDs filled in by planner. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Skill files exist at expected paths (already shipped — verified by Phase 68 + 69)
- [ ] No new test files needed (markdown-only edits)
- [ ] No new Python dependencies needed

*All infrastructure pre-existing.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Routing block prose clarity | AGT-02 | Markdown clarity is judgment-based | Read §"Run LSD" cold; confirm a CASE-agent could follow the conditional without ambiguity |
| G4 block-message clarity | AGT-04 | Block-message educates user; clarity is judgment-based | Read G4 block-message; confirm it explains 2^N cap, references PyLSDOrchestrator ValueError, and gives nmr-chemist actionable priorization direction |
| ITERATION-COMPLETE table template legibility | AGT-02 | Markdown-table mono-space-rendering | Read template; confirm column-order is parseable by case.md loop-detection logic AND legible to human reviewer |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify (all grep-based for skill files)
- [ ] No 3 consecutive tasks without automated verify (only 3-4 tasks expected total)
- [ ] Wave 0 needs nothing (markdown only)
- [ ] Feedback latency < 5s for grep, < 5min full pytest
- [ ] Manual reviews documented in `<done>` blocks
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
