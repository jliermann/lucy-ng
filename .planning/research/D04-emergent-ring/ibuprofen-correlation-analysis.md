# D-04 Emergent-Ring Analysis — Ibuprofen (CASE1, 2026-06-11 Opus-4.8 run)

**Question:** Why does the para-benzene ring NOT emerge from the data, forcing explicit ring-BONDs? Is the default 2J/3J HMBC assumption pulling the proposals away from the ring? **Short answer: yes — and the geometry shows exactly why.**

Graphic: `ibuprofen_correlations.svg` (structure with LSD atom numbering + the 8 HMBC arrows, rendered by `lucy visualize correlations` from the iteration_03 solution).

## Structure + LSD atom numbering

```
            COOH(1, 180.56)
             |
   H3C(13,18.09)\
            CH(9, 44.90)
             |
        C(2, 140.84)            <- ipso, alkyl/acid side (Cq)
          //      \
   (7,127.26)CH    CH(6,127.26)
        |              |
   (5,129.38)CH    CH(4,129.38)
          \\      /
        C(3, 136.96)            <- ipso, CH2 side (Cq)
             |
        CH2(8, 45.03)
             |
        CH(10, 30.14)
           /    \
  H3C(11,22.37)  CH3(12,22.37)
```
Ring (forced) order: **3–4–6–2–7–5–3** (para: C2 and C3 opposite). 2C-equivalent pairs by para symmetry: {4,5}@129.38 and {6,7}@127.26; iPr methyls {11,12}@22.37.

## Annotated ¹³C shifts (10 distinct signals → 13 C)

| LSD atom | δ (ppm) | mult | assignment |
|---|---|---|---|
| 1 | 180.56 | Cq | COOH |
| 2 | 140.84 | Cq | aromatic ipso (bears CH(CH₃)COOH) |
| 3 | 136.96 | Cq | aromatic ipso (bears CH₂) |
| 4, 5 | 129.38 | CH×2 | aromatic CH (ortho to C3) |
| 6, 7 | 127.26 | CH×2 | aromatic CH (ortho to C2) |
| 8 | 45.03 | CH₂ | benzylic ArCH₂ |
| 9 | 44.90 | CH | CH-COOH methine |
| 10 | 30.14 | CH | isopropyl methine |
| 11, 12 | 22.37 | CH₃×2 | isopropyl gem-dimethyl |
| 13 | 18.09 | CH₃ | α-CH₃ |

## Correlations actually used (true bond-path J in ibuprofen, computed)

**COSY (3J_HH, ortho):** H@129.38 ↔ H@127.26 → asserts a **hard adjacency** between a {4,5} carbon and a {6,7} carbon (ring edges 4–6 and 5–7).

**HMBC** (`HMBC X Y` = C_X ↔ H on C_Y; J = bonds from that H to C_X):

| HMBC | true J | what it relates | role |
|---|---|---|---|
| 1 ← 9 | 2J | COOH ← H(CH-COOH) | side-chain |
| 1 ← 13 | 3J | COOH ← H(α-CH₃) | side-chain |
| 3 ← 4 | **2J** | ipso-C3 ← H(ring CH) | **ring-internal** |
| 2 ← 6 | **2J** | ipso-C2 ← H(ring CH) | **ring-internal** |
| 4 ← 8 | 3J | ring CH ← H(ArCH₂) | ring↔substituent |
| 8 ← 4 | 3J | ArCH₂ ← H(ring CH) | ring↔substituent |
| 6 ← 9 | 3J | ring CH ← H(CH-COOH) | ring↔substituent |
| 10 ← 8 | 2J | iPr CH ← H(ArCH₂) | side-chain |

All 8 are genuine 2J/3J — the two **false para-4J** correlations (`HMBC 2 8`, `HMBC 8 6`, ArCH₂↔para-aromatic, ≥4 bonds) were correctly identified and removed (bisection diagnosis), which is what let the single correct solution appear. So the *final* set is "clean."

## THE CORE FINDING — why the ring can't close emergently

Of the **6 ring edges**, here is what the data actually constrains:

| ring edge | constrained by | strength |
|---|---|---|
| 4–6 | COSY ortho (3J_HH) | **HARD adjacency** ✓ |
| 5–7 | COSY ortho (3J_HH) | **HARD adjacency** ✓ |
| 3–4 | HMBC `3 4` | **ambiguous** — LSD reads HMBC as 2-OR-3J, so this does NOT assert adjacency |
| 6–2 | HMBC `2 6` | **ambiguous** — same |
| 2–7 | nothing direct | only via 2C-symmetry mirror |
| 5–3 | nothing direct | only via 2C-symmetry mirror |

**Only 2 of 6 ring edges are hard-pinned (the CH–CH edges, by COSY).** The two Cq–CH edges (3–4, 6–2) rest on HMBC, which LSD treats as the **ambiguous 2-or-3-bond range** — so they do not force adjacency. The remaining two Cq–CH edges (2–7, 5–3) have **no direct correlation at all** (only inferable through the 2C-equivalence).

**This is your hypothesis, confirmed and made precise:** the 2J/3J base assumption is decisive here. The only ring edges the H–C data *could* pin are the Cq–CH edges — and those come exclusively from HMBC, whose 2-vs-3J ambiguity means "HMBC 3 4" really says *"C3 and C4 are 2 OR 3 bonds apart,"* not *"C3–C4 bonded."* Under that reading, a non-aromatic skeleton that places those carbons 3 bonds apart (open polyene, 7-/8-ring) satisfies the **same** correlation set. With only 2 hard edges (COSY) and a symmetric para ring offering just 2 unique CH environments, the benzene ring is **genuinely under-determined by deduction** — hence iter-2's all-non-aromatic solution set, and the need to force the ring.

Note also the aromatic-J subtlety: the two ring-internal HMBC are **2J (ortho-CH→ipso)** — exactly the aromatic HMBC class that is **typically weak/unreliable**, while the **strong, diagnostic aromatic 3J (H→meta-Cq, H→para-ipso)** correlations were not in the picked set. So the ring is being asked to close on its weakest, most ambiguous correlations.

## Implications for a real emergent-ring mechanism

Pure LSD constraint-deduction cannot force this ring, because the data (under honest 2-3J ambiguity, for a 2-CH-environment para ring) does not uniquely determine it. Candidate directions to make emergence real (testable, none answer-biasing):

1. **Specific-J for diagnostic aromatic correlations.** Encode the *meta* H→Cq correlations as **3J-only** (LSD `HMBC X Y 3 3`) rather than the ambiguous range, and prefer the strong 3J network over the weak 2J ortho. With the COSY CH–CH edges (hard) + 3J-locked meta correlations + 2C-symmetry, the ring becomes determined. Requires the nmr-chemist to (a) pick the strong meta 3J correlations and (b) assert their J as 3 (chemist knowledge: ortho-Cq HMBC = weak 2J; meta = strong 3J).
2. **Aromatic-ring perception prior (most robust).** When ≥4 sp2 C in 110–160 ppm show a recognizable substitution pattern (here: 2 CH-pairs + 2 Cq = para-AA'BB'), *propose* the benzene ring as a candidate scaffold and let 13C-ranking validate it — emergence via **hypothesis generation + test**, not via constraint deduction (which is provably insufficient for symmetric rings). This is legitimate "emergence": triggered by the sp2/symmetry evidence, falsifiable by ranking, O/substituent positions left open.
3. **Richer HMBC extraction.** Capture the complete aromatic long-range network (the 3J H→meta/para correlations currently missing), which pins the unconstrained 2–7 and 5–3 edges.

**Honest limit:** for a para-disubstituted benzene with only two CH environments, options (1)/(3) help but the symmetry caps how much H–C data can ever pin; option (2) — perceive-and-test — is the realistic route to dependable emergence and avoids the explicit ring-BOND escalation while staying evidence-driven.

---
*Generated 2026-06-12 from CASE1 iteration_03 (Opus-4.8 run). Orchestrator/research artifact — NOT runtime skill (blind-UAT). Truth: ibuprofen `CC(C)Cc1ccc(C(C)C(=O)O)cc1`, C13H18O2.*
