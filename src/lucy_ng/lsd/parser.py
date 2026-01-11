"""Parser for LSD output files."""

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LSDSolution:
    """Single solution from LSD.

    Represents one possible molecular structure found by LSD.

    Attributes:
        index: Solution number (1-based)
        smiles: SMILES string if available
        mol_block: MOL block content if available
        atoms: List of atom assignments (index, element, neighbors)
        bonds: List of bonds as (atom1, atom2) tuples
        source_file: Path to source file
    """

    index: int
    smiles: str | None = None
    mol_block: str | None = None
    atoms: list[dict] = field(default_factory=list)
    bonds: list[tuple[int, int]] = field(default_factory=list)
    source_file: Path | None = None

    def summary(self) -> str:
        """Return a summary of the solution."""
        lines = [f"Solution {self.index}:"]
        if self.smiles:
            lines.append(f"  SMILES: {self.smiles}")
        lines.append(f"  Atoms: {len(self.atoms)}")
        lines.append(f"  Bonds: {len(self.bonds)}")
        return "\n".join(lines)


class LSDOutputParser:
    """Parse LSD output files.

    LSD generates several output file types:
    - .sol files: Solution structures
    - .out files: Summary output
    - SMILES output from outlsd tool
    """

    @staticmethod
    def parse_solutions(output_dir: Path | str) -> list[LSDSolution]:
        """Parse all solution files from LSD output directory.

        Args:
            output_dir: Directory containing LSD output files

        Returns:
            List of parsed solutions, sorted by index
        """
        output_dir = Path(output_dir)
        solutions = []

        # Parse .sol files
        for sol_file in sorted(output_dir.glob("*.sol")):
            sol = LSDOutputParser.parse_sol_file(sol_file)
            if sol:
                solutions.append(sol)

        # Try to parse outlsd output for SMILES
        out_file = output_dir / "outlsd.out"
        if out_file.exists():
            smiles_list = LSDOutputParser.parse_outlsd_output(out_file)
            # Create index -> solution mapping for correct matching
            index_to_solution = {s.index: s for s in solutions}
            # Match SMILES to solutions by numeric index (outlsd outputs in order 1, 2, 3, ...)
            for i, smiles in enumerate(smiles_list):
                sol_index = i + 1  # outlsd SMILES are 1-indexed
                if sol_index in index_to_solution:
                    index_to_solution[sol_index].smiles = smiles

        return sorted(solutions, key=lambda s: s.index)

    @staticmethod
    def parse_sol_file(sol_path: Path | str) -> LSDSolution | None:
        """Parse a single .sol file.

        LSD .sol files contain bond connectivity information.
        Format varies but typically includes atom and bond lists.

        Args:
            sol_path: Path to .sol file

        Returns:
            LSDSolution if parsing succeeds, None otherwise
        """
        sol_path = Path(sol_path)
        if not sol_path.exists():
            return None

        content = sol_path.read_text()

        # Extract solution index from filename (e.g., "sol001.sol" -> 1)
        index = LSDOutputParser._extract_index_from_filename(sol_path.name)

        # Parse atoms and bonds from content
        atoms = LSDOutputParser._parse_atoms(content)
        bonds = LSDOutputParser._parse_bonds(content)

        return LSDSolution(
            index=index,
            atoms=atoms,
            bonds=bonds,
            source_file=sol_path,
        )

    @staticmethod
    def parse_outlsd_output(outlsd_path: Path | str) -> list[str]:
        """Parse outlsd SMILES output.

        The outlsd program converts LSD solutions to SMILES.

        Args:
            outlsd_path: Path to outlsd output file

        Returns:
            List of SMILES strings
        """
        outlsd_path = Path(outlsd_path)
        if not outlsd_path.exists():
            return []

        content = outlsd_path.read_text()
        smiles_list = []

        # SMILES are typically one per line
        for line in content.strip().split("\n"):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            # Basic SMILES validation: contains letters and possibly brackets, numbers, etc.
            if re.match(r"^[A-Za-z0-9@\[\]\(\)=#\-\+\\/\.]+$", line):
                smiles_list.append(line)

        return smiles_list

    @staticmethod
    def parse_summary_output(output: str) -> dict:
        """Parse LSD summary output for statistics.

        Args:
            output: LSD stdout content

        Returns:
            Dictionary with parsed statistics
        """
        stats = {
            "solution_count": 0,
            "execution_time": None,
            "status": "unknown",
        }

        # Look for solution count
        count_match = re.search(r"(\d+)\s+solution", output.lower())
        if count_match:
            stats["solution_count"] = int(count_match.group(1))

        # Look for timing information
        time_match = re.search(r"(\d+\.?\d*)\s*(sec|second|ms)", output.lower())
        if time_match:
            stats["execution_time"] = float(time_match.group(1))

        # Determine status
        if "error" in output.lower():
            stats["status"] = "error"
        elif "no solution" in output.lower():
            stats["status"] = "no_solution"
        elif stats["solution_count"] > 0:
            stats["status"] = "success"

        return stats

    @staticmethod
    def _extract_index_from_filename(filename: str) -> int:
        """Extract solution index from filename.

        Args:
            filename: e.g., "sol001.sol", "solution_3.sol"

        Returns:
            Index number (default 1 if not found)
        """
        # Try to find numbers in filename
        match = re.search(r"(\d+)", filename)
        if match:
            return int(match.group(1))
        return 1

    @staticmethod
    def _parse_atoms(content: str) -> list[dict]:
        """Parse atom information from solution content.

        Args:
            content: Solution file content

        Returns:
            List of atom dictionaries
        """
        atoms = []

        # Look for atom definition lines
        # Common formats: "1 C sp2 0" or "ATOM 1 C ..."
        for line in content.split("\n"):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            # Try to parse as atom definition
            parts = line.split()
            if len(parts) >= 2:
                # Check if first part is a number (atom index)
                if parts[0].isdigit():
                    try:
                        atom = {
                            "index": int(parts[0]),
                            "element": parts[1] if len(parts) > 1 else "C",
                        }
                        if len(parts) > 2:
                            atom["hybridization"] = parts[2]
                        if len(parts) > 3:
                            atom["h_count"] = parts[3]
                        atoms.append(atom)
                    except (ValueError, IndexError):
                        continue

        return atoms

    @staticmethod
    def _parse_bonds(content: str) -> list[tuple[int, int]]:
        """Parse bond information from solution content.

        Args:
            content: Solution file content

        Returns:
            List of (atom1, atom2) bond tuples
        """
        bonds = []

        # Look for bond definition lines
        # Common formats: "BOND 1 2" or "1-2" or connectivity matrix
        for line in content.split("\n"):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            # Try "BOND X Y" format
            if line.upper().startswith("BOND"):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        atom1 = int(parts[1])
                        atom2 = int(parts[2])
                        bonds.append((min(atom1, atom2), max(atom1, atom2)))
                    except ValueError:
                        continue

            # Try "X-Y" format
            elif "-" in line and len(line.split()) == 1:
                match = re.match(r"(\d+)-(\d+)", line)
                if match:
                    atom1 = int(match.group(1))
                    atom2 = int(match.group(2))
                    bonds.append((min(atom1, atom2), max(atom1, atom2)))

        # Remove duplicates while preserving order
        seen = set()
        unique_bonds = []
        for bond in bonds:
            if bond not in seen:
                seen.add(bond)
                unique_bonds.append(bond)

        return unique_bonds

    @staticmethod
    def solutions_to_smiles_list(solutions: list[LSDSolution]) -> list[str]:
        """Extract SMILES strings from solutions.

        Args:
            solutions: List of parsed solutions

        Returns:
            List of SMILES strings (empty strings for solutions without SMILES)
        """
        return [s.smiles or "" for s in solutions]
