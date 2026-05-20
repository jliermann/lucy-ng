"""
Controlled 3-arm LSD experiment for Phase 72 design re-validation.

Arm A: Emergent test -- no SKEL benzene, full native constraints preserved.
        D-04 question: does aromatic ring emerge from COSY/HMBC alone?
Arm B: Baseline reference -- verbatim iteration_03/compound_native.lsd.
        Expected: 2 solutions, both aromatic, ibuprofen in solution 2.
Arm C: Bond-range 4J test -- arm_a + HMBC X Y 2 4 for 3 known 4J W-path suspects.
        D-01 question: does extended bond range work? Does ring still emerge?

Results written to results.json in this directory.

LSD invocation note: LSD must be given the input file as a positional argument
(lsd arm_a.lsd), NOT via stdin redirection (lsd < arm_a.lsd). Stdin mode writes
OUTLSD format data to stdout, NOT to a .sol file. File-argument mode writes
arm_a.sol in the cwd. This was discovered and corrected during execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Skip guard: if LSD binaries not found, exit cleanly (CI-safe)
# ---------------------------------------------------------------------------
LSD_BIN = Path("/Users/steinbeck/Dropbox/develop/LSD/lsd")
OUTLSD_BIN = Path("/Users/steinbeck/Dropbox/develop/LSD/outlsd")

if not LSD_BIN.exists() or not OUTLSD_BIN.exists():
    print("SKIP: LSD binary not found at expected location")
    print(f"  LSD:    {LSD_BIN} {'OK' if LSD_BIN.exists() else 'MISSING'}")
    print(f"  outlsd: {OUTLSD_BIN} {'OK' if OUTLSD_BIN.exists() else 'MISSING'}")
    sys.exit(0)

import subprocess  # noqa: E402 (after skip guard)

from rdkit import Chem  # noqa: E402
from rdkit.Chem.inchi import InchiToInchiKey, MolToInchi  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXPERIMENT_DIR = Path(__file__).parent
IBUPROFEN_INCHI_KEY = "HEFNNWSXXWATRW-UHFFFAOYSA-N"
ARMS = ["arm_a", "arm_b", "arm_c"]

# ---------------------------------------------------------------------------
# RDKit helpers
# ---------------------------------------------------------------------------


def has_aromatic_ring(smiles: str) -> bool:
    """Return True if SMILES contains at least one 6-membered aromatic ring."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False
    rings = mol.GetRingInfo().AtomRings()
    return any(
        len(ring) == 6 and all(mol.GetAtomWithIdx(a).GetIsAromatic() for a in ring)
        for ring in rings
    )


def count_aromatic_atoms(smiles: str) -> int:
    """Return count of aromatic atoms in the molecule."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return 0
    return sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())


def smiles_to_inchi_key(smiles: str) -> str | None:
    """Convert SMILES to InChI key using RDKit."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    inchi = MolToInchi(mol)
    if inchi is None:
        return None
    return InchiToInchiKey(inchi)


def parse_smiles_file(smi_path: Path) -> list[str]:
    """Parse SMILES file: first whitespace-delimited field per non-empty line.

    Pattern from tests/test_lsd_regression.py _smiles_to_inchis (lines 52-78).
    Skips lines where Chem.MolFromSmiles returns None.
    """
    smiles_list: list[str] = []
    if not smi_path.exists():
        return smiles_list
    for raw_line in smi_path.read_text().splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        candidate = parts[0]
        if Chem.MolFromSmiles(candidate) is not None:
            smiles_list.append(candidate)
    return smiles_list


# ---------------------------------------------------------------------------
# LSD + outlsd runner
# ---------------------------------------------------------------------------


def run_arm(arm_name: str) -> dict:
    """Run one LSD arm: invoke LSD, rename .sol, run outlsd, return result dict."""
    lsd_file = EXPERIMENT_DIR / f"{arm_name}.lsd"
    sol_file = EXPERIMENT_DIR / f"{arm_name}.sol"
    smi_file = EXPERIMENT_DIR / f"{arm_name}_solutions.smi"
    default_sol = EXPERIMENT_DIR / "compound.sol"

    print(f"\n--- Running {arm_name} ---")
    print(f"  LSD input: {lsd_file.name}")

    # -- Step 1: Run LSD (file argument mode; .sol written to EXPERIMENT_DIR cwd) --
    # IMPORTANT: LSD must be given the lsd file as a positional argument (not stdin).
    # Stdin mode writes OUTLSD data to stdout, not to a .sol file.
    # File argument mode writes arm_a.sol/arm_b.sol/arm_c.sol to the cwd.
    lsd_result = subprocess.run(
        [str(LSD_BIN), str(lsd_file)],
        capture_output=True,
        text=True,
        cwd=EXPERIMENT_DIR,  # .sol lands here, named after the input file stem
    )

    if lsd_result.returncode != 0:
        print(f"  WARNING: LSD exited with code {lsd_result.returncode}")
        if lsd_result.stderr:
            print(f"  stderr: {lsd_result.stderr[:400]}")

    # -- Step 2: Read solution count from solncounter --
    solncounter_path = EXPERIMENT_DIR / "solncounter"
    solution_count = 0
    if solncounter_path.exists():
        try:
            solution_count = int(solncounter_path.read_text().strip())
        except ValueError:
            pass
    print(f"  solncounter: {solution_count} solutions")

    # -- Step 3: Locate arm-specific .sol file --
    # LSD file-argument mode writes arm_name.sol (same stem as the input lsd file)
    # No renaming needed; just verify it exists.
    if sol_file.exists():
        print(f"  Found solution file: {sol_file.name}")
    elif default_sol.exists():
        # Fallback: handle unexpected "compound.sol" naming
        default_sol.rename(sol_file)
        print(f"  Renamed compound.sol -> {sol_file.name}")
    else:
        print(f"  WARNING: {sol_file.name} not found in {EXPERIMENT_DIR}")

    # -- Step 4: Run outlsd (CORRECT pattern from orchestrator.py lines 281-291) --
    # Key: "5" argument (SMILES mode) + .sol file as stdin (NOT the .lsd file)
    smiles_list: list[str] = []
    if solution_count > 0 and sol_file.exists():
        outlsd_proc = subprocess.run(
            [str(OUTLSD_BIN), "5"],  # "5" = SMILES output mode -- REQUIRED
            stdin=sol_file.open(),   # .sol file as stdin -- NOT the .lsd file
            capture_output=True,
            text=True,
            timeout=60,
            cwd=EXPERIMENT_DIR,
        )
        smi_file.write_text(outlsd_proc.stdout)
        print(f"  outlsd stdout written to {smi_file.name} ({len(outlsd_proc.stdout)} bytes)")
        if outlsd_proc.stderr:
            print(f"  outlsd stderr: {outlsd_proc.stderr[:200]}")

        smiles_list = parse_smiles_file(smi_file)
        print(f"  Parsed {len(smiles_list)} valid SMILES from {smi_file.name}")
    else:
        print(f"  Skipping outlsd: solution_count={solution_count}, sol_exists={sol_file.exists()}")
        # Write empty smi file so the file always exists
        smi_file.write_text("")

    # -- Step 5: RDKit aromatic and ibuprofen checks --
    solutions = []
    for smi in smiles_list:
        aromatic = has_aromatic_ring(smi)
        n_aromatic_atoms = count_aromatic_atoms(smi)
        inchi_key = smiles_to_inchi_key(smi)
        is_ibuprofen = inchi_key == IBUPROFEN_INCHI_KEY
        solutions.append({
            "smiles": smi,
            "aromatic_ring": aromatic,
            "aromatic_atom_count": n_aromatic_atoms,
            "inchi_key": inchi_key,
            "is_ibuprofen": is_ibuprofen,
        })

    any_aromatic = any(s["aromatic_ring"] for s in solutions)
    ibuprofen_found = any(s["is_ibuprofen"] for s in solutions)
    aromatic_count = sum(1 for s in solutions if s["aromatic_ring"])

    print(f"  any_aromatic={any_aromatic} ({aromatic_count}/{len(solutions)}), ibuprofen_found={ibuprofen_found}")

    return {
        "arm": arm_name,
        "solution_count": solution_count,
        "parsed_smiles_count": len(smiles_list),
        "any_aromatic": any_aromatic,
        "aromatic_count": aromatic_count,
        "ibuprofen_found": ibuprofen_found,
        "solutions": solutions,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 60)
    print("Phase 72 Design Re-Validation Experiment")
    print("3-arm controlled LSD experiment on CASE1 (ibuprofen)")
    print("=" * 60)
    print(f"LSD binary: {LSD_BIN}")
    print(f"outlsd binary: {OUTLSD_BIN}")
    print(f"Experiment dir: {EXPERIMENT_DIR}")

    all_results = []
    for arm_name in ARMS:
        result = run_arm(arm_name)
        all_results.append(result)

    # Write results.json
    results_path = EXPERIMENT_DIR / "results.json"
    results_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults written to {results_path}")

    # Print summary table
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"{'Arm':<8} {'Solutions':>9} {'Aromatic?':>10} {'Ibuprofen?':>11}")
    print("-" * 42)
    for r in all_results:
        arm_label = r["arm"].upper().replace("_", " ")
        solutions = r["solution_count"]
        aromatic = "Y" if r["any_aromatic"] else "N"
        ibuprofen = "Y" if r["ibuprofen_found"] else "N"
        print(f"{arm_label:<8} {solutions:>9} {aromatic:>10} {ibuprofen:>11}")
    print("=" * 60)

    # Interpret D-04
    arm_a_result = next(r for r in all_results if r["arm"] == "arm_a")
    arm_b_result = next(r for r in all_results if r["arm"] == "arm_b")
    arm_c_result = next(r for r in all_results if r["arm"] == "arm_c")

    print("\n--- D-04 VERDICT ---")
    if arm_a_result["solution_count"] == 0:
        print("Arm A: 0 solutions -- UNDETERMINED (over-constrained without SKEL?)")
    elif arm_a_result["any_aromatic"]:
        print("Arm A: aromatic ring EMERGED without SKEL -- D-04 = EMERGENT")
        print("  -> Phase 74 does NOT need to implement SKEL forcing")
    else:
        print("Arm A: no aromatic solutions -- D-04 = FORCE-REQUIRED")
        print("  -> Phase 74 needs SKEL fragment insertion for aromatic compounds")

    print("\n--- D-01 VERDICT ---")
    if arm_c_result["solution_count"] > 0 and arm_c_result["any_aromatic"]:
        print("Arm C: extended bond range yields aromatic solutions -- D-01 = CONFIRMED")
    elif arm_c_result["solution_count"] > 0:
        print("Arm C: solutions found but none aromatic -- D-01 partial (ring still needs forcing)")
    else:
        print("Arm C: 0 solutions -- D-01 BLOCKED (over-constrained with 4J extended range)")

    print("\n--- Arm B SANITY CHECK ---")
    if arm_b_result["solution_count"] == 2 and arm_b_result["ibuprofen_found"]:
        print("Arm B: 2 solutions, ibuprofen found -- BASELINE CONFIRMED")
    else:
        print(f"Arm B: {arm_b_result['solution_count']} solutions, "
              f"ibuprofen={arm_b_result['ibuprofen_found']} -- UNEXPECTED (environment issue?)")


if __name__ == "__main__":
    main()
