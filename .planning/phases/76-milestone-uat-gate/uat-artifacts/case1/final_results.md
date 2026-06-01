# CASE Results: C13H18O2

**Formula:** C13H18O2 (MW 206.28, DBE 5)
**Date:** 2026-06-01
**Iterations completed:** 4
**Final solution count:** 1 (Iteration 4)
**Identified compound:** Ibuprofen — 2-(4-Isobutylphenyl)propanoic acid

---

## Top Candidate

| Rank | SMILES | Matched | MAE (ppm) | Quality | Plausibility |
|------|--------|---------|-----------|---------|--------------|
| 1 | `CC(C)Cc1ccc(C(C)C(=O)O)cc1` | 10/10 | 0.277 | Excellent | PLAUSIBLE |

*(solutions.smi stores the Kekulé form `CC(C)CC(=C1)C=CC(=C1)C(C)C(O)=O`; RDKit canonical SMILES and InChI are identical to Ibuprofen — confirmed.)*

---

## 13C Shift Comparison

| Exp (ppm) | Pred (ppm) | Dev (ppm) | Conf | Assignment |
|-----------|-----------|-----------|------|------------|
| 180.56 | 180.847 | +0.287 | 0.912 | COOH carbonyl |
| 140.84 | 140.736 | −0.104 | 0.920 | Ar-Cq ipso (alpha-CH side) |
| 136.96 | 138.404 | +1.444 | 0.902 | Ar-Cq ipso (isobutyl side) |
| 129.38 | 129.285 | −0.095 | 0.918 | Ar-CH ortho to alpha-CH (×2 equiv) |
| 127.26 | 127.450 | +0.190 | 0.918 | Ar-CH ortho to isobutyl (×2 equiv) |
| 45.03 | 45.027 | −0.003 | 0.989 | Isobutyl-CH2 (benzylic) |
| 44.90 | 45.092 | +0.192 | 0.908 | Alpha-CH (alpha to COOH) |
| 30.14 | 30.038 | −0.102 | 0.998 | Isobutyl-CH |
| 22.37 | 22.084 | −0.286 | 0.995 | gem-CH3 (×2 equiv) |
| 18.09 | 18.156 | +0.066 | 0.912 | Alpha-CH3 |

**Matched: 10/10 (100%) | MAE: 0.277 ppm | Max deviation: +1.444 ppm**

All predictions at HOSE radius 6 (maximum depth), indicating excellent database coverage for this structural environment.

---

## Chemical Plausibility Assessment

### Check 1: Functional Group Consistency

| Group | Exp shift | Typical range | Assessment |
|-------|-----------|--------------|------------|
| COOH C=O | 180.56 | 175–185 ppm | PASS |
| Ar-Cq (para-disubst.) | 140.84, 136.96 | 125–150 ppm | PASS |
| Ar-CH (para-disubst.) | 129.38, 127.26 | 125–135 ppm | PASS |
| Benzylic CH2 | 45.03 | 40–46 ppm | PASS |
| Alpha-CH (to COOH+Ar) | 44.90 | 42–47 ppm | PASS |
| Isobutyl CH | 30.14 | 27–34 ppm | PASS |
| gem-CH3 (isobutyl) | 22.37 | 20–24 ppm | PASS |
| Alpha-CH3 | 18.09 | 16–20 ppm | PASS |

### Check 2: Degree of Unsaturation

DBE = (2×13 + 2 − 18) / 2 = **5**. Ibuprofen: benzene ring (4) + C=O (1) = 5. **PASS.**

### Check 3: Strained Rings

Ibuprofen contains only a benzene ring (6-membered, aromatic, unstrained). DEFF ring3/ring4 exclusion applied throughout all iterations. **No strained rings. PASS.**

### Check 4: Systematic Deviations

Mean deviation: +0.159 ppm. Median: +0.031 ppm. No systematic offset. Largest single deviation: Ar-Cq ipso (isobutyl side) at +1.444 ppm — within acceptable range, consistent with HOSE code limitations for substituted aromatic ipso carbons. All other atoms within ±0.3 ppm. **No stereochemical or regiochemical inconsistency. PASS.**

### Check 5: Natural Product / Drug Likelihood

Ibuprofen is a well-established pharmaceutical (NSAID, approved 1969). The 2-arylpropanoic acid (profen) scaffold is common in both synthetic drugs and natural product-like chemistry. Para-substituted benzene ring, isobutyl chain, and carboxylic acid are all routine functional groups. **PASS.**

### Check 6: Aromatic Ring Verification (Two-Tier)

**Tier 1 (warnings array):** `lucy lsd rank` returned `"warnings": []`. Expected — the solution has `has_aromatic_ring: true`.

**Tier 2 (prediction-based):**

- Experimental: 4 signals in 110–160 ppm — 140.84, 136.96 (2× Cq), 129.38, 127.26 (2× pairs of equiv CH)
- Predicted: 6 shifts in 110–160 ppm — 140.74, 138.40 (2× Cq), 129.29×2, 127.45×2 (2× equiv CH pairs)
- The predicted para-symmetry pattern (2 inequivalent Cq + 2 pairs of equivalent CH) reproduces the experimental observation exactly.
- Equivalent pairs confirmed: pred 129.285/129.285 matches exp 129.38×2; pred 127.450/127.450 matches exp 127.26×2. **PASS.**

**Overall plausibility: PLAUSIBLE — all 6 checks pass.**

---

## Confidence Assessment

### Per-Atom Confidence

| Shift (ppm) | Assignment | Digital Res. | HOSE Quality | HMBC Support | Atom Confidence |
|-------------|------------|-------------|--------------|--------------|-----------------|
| 180.56 | COOH Cq | High | High (r=6, 0.912) | 3J to alpha-CH | High |
| 140.84 | Ar-Cq ipso | High | High (r=6, 0.920) | 3J benzylic HMBC | High |
| 136.96 | Ar-Cq para | High | High (r=6, 0.902) | 3J para-CH3 HMBC | High |
| 129.38 | Ar-CH ×2 | High | High (r=6, 0.918) | HSQC + equiv. COSY | High |
| 127.26 | Ar-CH ×2 | High | High (r=6, 0.918) | HSQC + equiv. COSY | High |
| 45.03 | Benzyl-CH2 | High | High (r=6, 0.989) | HMBC to Ar-Cq | High |
| 44.90 | Alpha-CH | High | High (r=6, 0.908) | 3J to COOH | High |
| 30.14 | Isobutyl-CH | High | High (r=6, 0.998) | BOND gem-dimethyl | High |
| 22.37 | gem-CH3 ×2 | Medium (0.13 ppm span) | High (r=6, 0.995) | BOND + HMBC | High |
| 18.09 | Alpha-CH3 | High | High (r=6, 0.912) | HMBC chain | High |

All 10 distinct carbon environments: **High** confidence. All HOSE predictions at radius 6 with confidence ≥ 0.902.

### Per-Structure Confidence

- 100% of atoms at High confidence
- 0 Low-confidence atoms
- MAE 0.277 ppm (well below 2.0 ppm threshold for High)
- 10/10 matched signals
- Chemical plausibility: PLAUSIBLE

**Overall structure confidence: High**

---

## Recommendation

**Accept top candidate as the identified structure: Ibuprofen, 2-(4-Isobutylphenyl)propanoic acid.**

`CC(C)Cc1ccc(C(C)C(=O)O)cc1`
InChI=1S/C13H18O2/c1-9(2)8-11-4-6-12(7-5-11)10(3)13(14)15/h4-7,9-10H,8H2,1-3H3,(H,14,15)

All 10 experimental 13C signals matched within 1.5 ppm. MAE 0.277 ppm at maximum HOSE radius. All chemical plausibility checks pass. The para-disubstituted aromatic symmetry pattern (2 Cq + 2×2 equivalent CH) is correctly reproduced. No ambiguities remain.

**Structure determination confidence: High**

---

*Report generated by solution-analyst, 2026-06-01. LSD iteration 4, 1 solution.*
