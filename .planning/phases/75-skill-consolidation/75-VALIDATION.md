---
phase: 75
slug: skill-consolidation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-24
---

# Phase 75 — Validation Strategy

> Markdown agent-skill consolidation. Validation = grep-based assertions on the skill files (native commands present, SYME/DEFF NOT absent, single-path structure, new DA gates) + pytest stays green (no Python touched, but Phase-74 DEFF-F-numbering / schema edits, if any, must not regress).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | grep on skill files + manual review; pytest for any incidental Python (DEFF-F numbering / schema) |
| **Config file** | none for skills |
| **Quick verify command** | shell `grep` patterns on the 5 skill files |
| **Full suite command** | `pytest -q` (regression — confirm no Python broke if a CLI/schema touch is needed) |
| **Estimated runtime** | <5s grep; ~5min full pytest if Python touched |

---

## Sampling Rate

- **After each skill-file task:** grep verification per task `<verify>`
- **After all tasks:** if any Python was touched (fragment DEFF-F numbering, schema), run `pytest -q`
- **Before phase close:** manual read of each rewritten section for coherence + cross-file consistency (lsd-engineer ↔ devils-advocate native-command sync)
- **Max feedback latency:** <5s grep

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 1 | SKILL-01 | No skill instructs writing SYME or DEFF NOT; native BOND/COSY + DEFF F/FEXP documented | grep | `grep -rn "^SYME\b\|DEFF NOT" ~/.claude/agents/lucy-*.md ~/.claude/commands/lucy-ng/ \| grep -v "NOT native\|error 102\|Do NOT write\|NEVER write\|not a native"` → must return empty (guidance lines allowed) | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | SKILL-01 | Phase-73 reality: no manual `outlsd 5 <` pipe; `lucy lsd run` produces solutions.smi | grep | `! grep -rn "outlsd 5 <" ~/.claude/agents/lucy-lsd-engineer.md ~/.claude/commands/lucy-ng/case.md` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | SKILL-02 | Single primary path: normal-LSD prominent; pyLSD demoted to subordinate "use ONLY when"; HMBC X Y 2 4 in main HMBC block | grep | `grep -n "use ONLY when\|####.*pyLSD" ~/.claude/agents/lucy-lsd-engineer.md` | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | SKILL-03 | devils-advocate has G5 (perm HMBC-only), G6 (empty merge vs solncounter), G7 (post-validation edit), G8 (reversion) | grep | `grep -cE "^\*\*G[5678]:" ~/.claude/agents/lucy-devils-advocate.md` returns 4 | ❌ W0 | ⬜ pending |

*Final task IDs filled by planner. Status: ⬜ pending · ✅ green · ❌ red.*

---

## Wave 0 Requirements

- [ ] Skill files exist (shipped) — no new files needed
- [ ] If DEFF-F numbering conflict (ring F1/F2 vs fragment goodlist F1) requires a `lucy fragment to-lsd` Python change → that becomes a Python task with pytest coverage
- [ ] If `ring_exclusion_enabled` needs the inventory schema (`additionalProperties`) updated → Python/schema task with test
- [ ] Otherwise pure markdown; rely on existing pytest suite for regression

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| lsd-engineer ↔ devils-advocate native-command consistency | SKILL-01 | The DA constraint-diff "SYME must persist" rule must become "BOND/COSY equivalence must persist" — cross-file coherence is judgment | Read both; confirm DA validates the native equivalence the engineer now writes |
| Single-path prose is genuinely unambiguous | SKILL-02 | A CASE agent reading cold must not be tempted back to pyLSD | Read lsd-engineer §Run LSD + pyLSD subsection; confirm pyLSD is clearly subordinate with explicit gate |
| G5-G8 gate logic is actionable | SKILL-03 | The new gates must give concrete grep/check + BLOCK criteria | Read each new gate; confirm it has a detection command + verdict |

---

## Scope Boundary

- **IN:** ~/.claude/agents/lucy-lsd-engineer.md, lucy-devils-advocate.md, lucy-nmr-chemist.md, lucy-solution-analyst.md, ~/.claude/commands/lucy-ng/case.md + references/ — SYME→BOND/COSY, DEFF NOT→DEFF F/FEXP, outlsd-pipe removal, single-path restructure, G5-G8 gates, SKEL-as-escalation note.
- **POSSIBLE small Python:** fragment DEFF-F numbering (F3+ when ring exclusion active) + schema additionalProperties — only if the open questions confirm a real conflict.
- **OUT:** the blind UAT (Phase 76) is the full proof that the consolidated skills make the agent solve via the intended mechanism.

---

## Validation Sign-Off

- [ ] No skill instructs SYME or DEFF NOT (only "do NOT use" guidance); native equivalents documented with ground-truth examples. Verify with the filtered grep: `grep -rn "^SYME\b\|DEFF NOT" ~/.claude/agents/lucy-*.md ~/.claude/commands/lucy-ng/ | grep -v "NOT native\|error 102\|Do NOT write\|NEVER write\|not a native"` → empty
- [ ] No manual outlsd-pipe instruction (Phase-73 solutions.smi reality)
- [ ] Single prominent solver path; pyLSD subordinate; HMBC X Y 2 4 in main block
- [ ] devils-advocate G5-G8 present + actionable
- [ ] lsd-engineer ↔ devils-advocate native-command consistency
- [ ] If Python touched: pytest green
- [ ] `nyquist_compliant: true`

**Approval:** pending
