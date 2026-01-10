"""Data models for LSD (Logic for Structure Determination) integration."""

from dataclasses import dataclass, field
from enum import Enum


class Hybridization(Enum):
    """Atom hybridization state for LSD."""

    SP = 1  # Triple bond or allene
    SP2 = 2  # Double bond, aromatic
    SP3 = 3  # Single bonds only


@dataclass
class LSDAtom:
    """Atom definition for LSD input.

    Corresponds to the MULT command in LSD:
    MULT atom_num element hybridization h_count [charge]

    Attributes:
        index: Atom number (1-based, as used in LSD)
        element: Chemical element symbol (C, N, O, S, etc.)
        hybridization: sp, sp2, or sp3
        hydrogen_count: Number of directly bonded hydrogens
        charge: Formal charge (-1, 0, 1, 2)
        carbon_shift: 13C chemical shift in ppm (optional)
        proton_shift: 1H chemical shift in ppm (optional, for attached H)
    """

    index: int
    element: str
    hybridization: Hybridization
    hydrogen_count: int
    charge: int = 0
    carbon_shift: float | None = None
    proton_shift: float | None = None

    def __post_init__(self) -> None:
        """Validate atom parameters."""
        valid_elements = {"C", "N", "O", "S", "P", "F", "Cl", "Br", "I", "Si", "B"}
        if self.element not in valid_elements:
            raise ValueError(f"Invalid element: {self.element}. Valid: {valid_elements}")
        if self.index < 1:
            raise ValueError(f"Atom index must be >= 1, got {self.index}")
        if self.hydrogen_count < 0:
            raise ValueError(f"Hydrogen count must be >= 0, got {self.hydrogen_count}")
        if self.charge not in (-1, 0, 1, 2):
            raise ValueError(f"Charge must be -1, 0, 1, or 2, got {self.charge}")

    def to_mult_line(self) -> str:
        """Generate LSD MULT command line.

        Returns:
            String like "MULT 1 C 2 0" or "MULT 1 N 3 1 1" (with charge)
        """
        parts = [
            "MULT",
            str(self.index),
            self.element,
            str(self.hybridization.value),
            str(self.hydrogen_count),
        ]
        if self.charge != 0:
            parts.append(str(self.charge))
        return " ".join(parts)


@dataclass
class LSDCorrelation:
    """NMR correlation for LSD input.

    Represents HSQC (direct), HMBC (long-range), or COSY (H-H) correlations.

    Attributes:
        atom1_index: First atom index (carbon for HSQC/HMBC, H for COSY)
        atom2_index: Second atom index (H position for HSQC/HMBC, H for COSY)
        correlation_type: "HSQC", "HMBC", or "COSY"
        min_bonds: Minimum bond distance (for HMBC, default 2)
        max_bonds: Maximum bond distance (for HMBC, default 3)
    """

    atom1_index: int
    atom2_index: int
    correlation_type: str
    min_bonds: int = 2
    max_bonds: int = 3

    def __post_init__(self) -> None:
        """Validate correlation parameters."""
        valid_types = {"HSQC", "HMBC", "COSY", "HMQC"}
        if self.correlation_type not in valid_types:
            raise ValueError(
                f"Invalid correlation type: {self.correlation_type}. Valid: {valid_types}"
            )
        if self.atom1_index < 1 or self.atom2_index < 1:
            raise ValueError("Atom indices must be >= 1")

    def to_lsd_line(self) -> str:
        """Generate LSD correlation command line.

        Returns:
            String like "HSQC 1 1" or "HMBC 1 2 2 3"
        """
        if self.correlation_type in ("HSQC", "HMQC"):
            return f"{self.correlation_type} {self.atom1_index} {self.atom2_index}"
        elif self.correlation_type == "HMBC":
            return (
                f"HMBC {self.atom1_index} {self.atom2_index} "
                f"{self.min_bonds} {self.max_bonds}"
            )
        elif self.correlation_type == "COSY":
            return f"COSY {self.atom1_index} {self.atom2_index}"
        else:
            raise ValueError(f"Unknown correlation type: {self.correlation_type}")


@dataclass
class LSDProblem:
    """Complete LSD problem definition.

    Contains all atoms and correlations needed to generate an LSD input file.

    Attributes:
        atoms: List of atom definitions
        correlations: List of NMR correlations
        molecular_formula: Molecular formula string (e.g., "C13H18O2")
        name: Problem name for identification
        comments: Optional comments for the input file
    """

    atoms: list[LSDAtom] = field(default_factory=list)
    correlations: list[LSDCorrelation] = field(default_factory=list)
    molecular_formula: str | None = None
    name: str = "problem"
    comments: list[str] = field(default_factory=list)

    def add_atom(self, atom: LSDAtom) -> None:
        """Add an atom to the problem."""
        self.atoms.append(atom)

    def add_correlation(self, correlation: LSDCorrelation) -> None:
        """Add a correlation to the problem."""
        self.correlations.append(correlation)

    def get_atom_by_index(self, index: int) -> LSDAtom | None:
        """Get atom by index."""
        for atom in self.atoms:
            if atom.index == index:
                return atom
        return None

    def get_correlations_for_atom(self, index: int) -> list[LSDCorrelation]:
        """Get all correlations involving an atom."""
        return [
            c for c in self.correlations
            if c.atom1_index == index or c.atom2_index == index
        ]

    def validate(self) -> list[str]:
        """Validate the problem for common issues.

        Returns:
            List of warning/error messages (empty if valid)
        """
        issues = []

        # Check for duplicate atom indices
        indices = [a.index for a in self.atoms]
        if len(indices) != len(set(indices)):
            issues.append("Duplicate atom indices found")

        # Check that correlation atoms exist
        atom_indices = set(indices)
        for corr in self.correlations:
            if corr.atom1_index not in atom_indices:
                issues.append(f"Correlation references non-existent atom {corr.atom1_index}")
            # Note: atom2 in HSQC/HMBC refers to H position, which may equal atom1

        # Check for atoms without correlations
        corr_atoms = set()
        for corr in self.correlations:
            corr_atoms.add(corr.atom1_index)
        uncorrelated = atom_indices - corr_atoms
        if uncorrelated:
            issues.append(f"Atoms without correlations: {sorted(uncorrelated)}")

        return issues

    @property
    def carbon_count(self) -> int:
        """Count of carbon atoms."""
        return sum(1 for a in self.atoms if a.element == "C")

    @property
    def heteroatom_count(self) -> int:
        """Count of non-carbon heavy atoms."""
        return sum(1 for a in self.atoms if a.element != "C")

    def summary(self) -> str:
        """Return a summary of the problem."""
        lines = [
            f"LSD Problem: {self.name}",
            f"  Molecular formula: {self.molecular_formula or 'not specified'}",
            f"  Atoms: {len(self.atoms)} ({self.carbon_count} C, {self.heteroatom_count} hetero)",
            f"  Correlations: {len(self.correlations)}",
        ]

        # Count correlation types
        type_counts: dict[str, int] = {}
        for corr in self.correlations:
            type_counts[corr.correlation_type] = type_counts.get(corr.correlation_type, 0) + 1
        for ctype, count in sorted(type_counts.items()):
            lines.append(f"    {ctype}: {count}")

        return "\n".join(lines)
