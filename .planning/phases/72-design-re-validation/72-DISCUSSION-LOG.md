# Phase 72 — Discussion Log

**Date:** 2026-05-20
**Mode:** discuss (design-decision phase)
**Driver:** `.planning/v8.0-UAT-POSTMORTEM.md`

The four open design questions were presented with analysis + opinionated recommendations. The questions are interdependent; two (Q1, Q4) are partly empirical because the v8.0 evidence was confounded by the constraint-loss bug.

---

## Q1 — 4J handling approach
**Options:** (A) extended-bond-range primary, permutations fallback [recommended]; (B) keep pyLSD permutations primary, fix bugs; (C) decide empirically.
**Decision:** A — extended bond range (`HMBC X Y 2 4`) primary in a single run; permutations demoted to narrow fallback. → D-01, D-01a.

## Q2 — solver-path architecture
Not asked separately — follows from Q1. With A, the path collapses to one primary (normal LSD + bond range). → D-02, D-02a (single prominently-documented path solves agent reversion at the root).

## Q3 — constraint translation
**Options:** (A) generator emits native-only [recommended]; (B) keep runtime translation, force every path through it.
**Decision:** A — SYME→DUPL, DEFF NOT→DEFF F/FEXP at generation time; no emitted file contains non-native commands. → D-03, D-03a.

## Q4 — aromatic ring
**Options:** (A) test empirically first, force only if needed [recommended]; (B) always force benzene fragment on aromatic pattern; (C) rely purely on emergent.
**Decision:** A — controlled experiment with constraints preserved decides emergent-vs-forced. → D-04, D-04a, plus the experiment spec D-05.

---

## Net architecture (locked direction)
Single primary solver path = normal LSD + extended bond range; native-only generation so no path loses constraints; pyLSD permutation kept only as subordinate fallback; aromatic handling decided by a controlled CASE1 experiment that also validates the bond-range-primary choice and re-evaluates the Phase-65 hypothesis.

## Claude's Discretion (planner finalizes)
- Exact form of the throwaway native LSD file for the experiment
- Whether to include the optional permutation/forced-fragment comparison arms
- Structure of the decision document deliverable
