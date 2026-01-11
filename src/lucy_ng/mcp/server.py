"""MCP server for lucy-ng NMR processing tools.

Exposes NMR processing and structure elucidation tools to AI agents
via the Model Context Protocol (MCP).
"""

from mcp.server.fastmcp import FastMCP

from lucy_ng.analysis import SymmetryAnalyzer
from lucy_ng.processing import DEPTGuidedPicker, HMBCGuidedPicker, SimplePeakPicker
from lucy_ng.readers import BrukerReader

# Create MCP server instance
mcp = FastMCP(
    name="lucy-ng",
    instructions="AI-powered Computer-Assisted Structure Elucidation for NMR data. "
    "Use these tools to read NMR spectra, pick peaks, analyze symmetry, "
    "dereplicate against databases, and generate LSD input for structure elucidation.",
)


# =============================================================================
# Spectrum Reading Tools
# =============================================================================


@mcp.tool()
def read_spectrum_1d(path: str) -> dict:
    """Read a Bruker 1D NMR spectrum and return metadata.

    Args:
        path: Path to Bruker experiment directory (e.g., "data/Ibuprofen/2")

    Returns:
        Dictionary with nucleus, frequency, points, ppm_range, and metadata
    """
    try:
        spectrum = BrukerReader.read_1d(path)
        return {
            "success": True,
            "nucleus": spectrum.nucleus,
            "frequency": spectrum.frequency,
            "solvent": spectrum.solvent,
            "points": len(spectrum.data),
            "ppm_min": float(spectrum.ppm_scale.min()),
            "ppm_max": float(spectrum.ppm_scale.max()),
            "metadata": spectrum.metadata,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def read_spectrum_2d(path: str) -> dict:
    """Read a Bruker 2D NMR spectrum and return metadata.

    Args:
        path: Path to Bruker experiment directory (e.g., "data/Ibuprofen/6")

    Returns:
        Dictionary with experiment_type, nuclei, frequency, shape, and ppm ranges
    """
    try:
        spectrum = BrukerReader.read_2d(path)
        return {
            "success": True,
            "experiment_type": spectrum.experiment_type,
            "f1_nucleus": spectrum.f1_nucleus,
            "f2_nucleus": spectrum.f2_nucleus,
            "frequency": spectrum.frequency,
            "shape": list(spectrum.data.shape),
            "f1_ppm_min": float(spectrum.f1_ppm_scale.min()),
            "f1_ppm_max": float(spectrum.f1_ppm_scale.max()),
            "f2_ppm_min": float(spectrum.f2_ppm_scale.min()),
            "f2_ppm_max": float(spectrum.f2_ppm_scale.max()),
            "metadata": spectrum.metadata,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Peak Picking Tools
# =============================================================================


@mcp.tool()
def pick_peaks_1d(path: str, threshold: float | None = None) -> dict:
    """Pick peaks from a 1D NMR spectrum.

    Uses threshold-based peak picking with noise estimation.

    Args:
        path: Path to Bruker 1D experiment directory
        threshold: Intensity threshold as fraction of max (0.0-1.0). Default 0.05.

    Returns:
        Dictionary with peak count and list of peaks (ppm, intensity)
    """
    try:
        spectrum = BrukerReader.read_1d(path)
        if threshold is None:
            threshold = 0.05
        peaks = SimplePeakPicker.pick_peaks(spectrum, threshold=threshold)
        return {
            "success": True,
            "count": len(peaks.peaks),
            "nucleus": spectrum.nucleus,
            "peaks": [
                {"ppm": float(p.position), "intensity": float(p.intensity)}
                for p in peaks.peaks
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def pick_hsqc_peaks(
    hsqc_path: str,
    dept135_path: str,
    dept90_path: str | None = None,
) -> dict:
    """Pick HSQC peaks using DEPT-guided algorithm.

    Uses DEPT-135 as ground truth for protonated carbons. Adaptively lowers
    HSQC threshold until all DEPT carbons are matched. This ensures all
    real correlations are found while minimizing noise.

    Args:
        hsqc_path: Path to HSQC experiment directory
        dept135_path: Path to DEPT-135 experiment directory
        dept90_path: Optional path to DEPT-90 for CH/CH3 disambiguation

    Returns:
        Dictionary with peaks, carbon multiplicities (CH, CH2, CH3), and statistics
    """
    try:
        hsqc = BrukerReader.read_2d(hsqc_path)
        dept135 = BrukerReader.read_1d(dept135_path)

        if dept90_path:
            dept90 = BrukerReader.read_1d(dept90_path)
            result = DEPTGuidedPicker.pick_hsqc_peaks_with_dept90(hsqc, dept135, dept90)
        else:
            result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

        return {
            "success": True,
            "dept_peaks_count": len(result.dept_peaks.peaks),
            "hsqc_peaks_count": len(result.peaks.peaks),
            "threshold_used": result.threshold_used,
            "iterations": result.iterations,
            "all_carbons_found": result.all_carbons_found,
            "carbon_multiplicities": result.carbon_multiplicities,
            "peaks": [
                {
                    "carbon_ppm": float(p.f1_position),
                    "proton_ppm": float(p.f2_position),
                    "intensity": float(p.intensity),
                    "multiplicity": result.carbon_multiplicities.get(
                        round(p.f1_position, 1)
                    ),
                }
                for p in result.peaks.peaks
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def pick_hmbc_peaks(
    hmbc_path: str,
    c13_path: str,
    hsqc_path: str,
    dept135_path: str | None = None,
) -> dict:
    """Pick HMBC peaks using guided algorithm.

    Filters HMBC peaks by requiring:
    1. Carbon (F1) position matches a known carbon from 13C or DEPT spectrum
    2. Proton (F2) position matches a proton from HSQC

    This removes noise peaks that would create false LSD constraints.

    Args:
        hmbc_path: Path to HMBC experiment directory
        c13_path: Path to 13C experiment directory
        hsqc_path: Path to HSQC experiment directory
        dept135_path: Optional DEPT-135 for additional carbon positions

    Returns:
        Dictionary with validated peaks and rejection statistics
    """
    try:
        hmbc = BrukerReader.read_2d(hmbc_path)
        c13 = BrukerReader.read_1d(c13_path)
        hsqc = BrukerReader.read_2d(hsqc_path)
        dept135 = BrukerReader.read_1d(dept135_path) if dept135_path else None

        result = HMBCGuidedPicker.pick_hmbc_peaks_from_spectra(
            hmbc=hmbc, carbon_spectrum=c13, hsqc=hsqc, dept135=dept135
        )

        return {
            "success": True,
            "reference_carbons": len(result.carbon_positions),
            "reference_protons": len(result.proton_positions),
            "raw_peak_count": result.raw_peak_count,
            "validated_count": result.validated_count,
            "rejected_count": result.rejected_count,
            "peaks": [
                {
                    "carbon_ppm": float(p.f1_position),
                    "proton_ppm": float(p.f2_position),
                    "intensity": float(p.intensity),
                }
                for p in result.peaks.peaks
            ],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# Analysis Tools
# =============================================================================


@mcp.tool()
def analyze_symmetry(
    molecular_formula: str,
    hsqc_path: str,
    dept135_path: str,
) -> dict:
    """Analyze molecular symmetry from spectroscopic data.

    Compares expected atom counts from molecular formula with observed
    NMR signals to detect equivalent atoms due to symmetry. This is
    critical for correct LSD input generation.

    Common symmetry patterns:
    - Para-disubstituted benzene: 2 equivalent CH carbons (2 pairs)
    - Isopropyl group: 2 equivalent CH3 carbons
    - tert-Butyl group: 3 equivalent CH3 carbons

    Args:
        molecular_formula: Molecular formula (e.g., "C13H18O2")
        hsqc_path: Path to HSQC experiment directory
        dept135_path: Path to DEPT-135 experiment directory

    Returns:
        Dictionary with symmetry analysis including:
        - signal_count vs expected_carbons
        - hydrogen budget (expected vs observed)
        - intensity analysis for potential equivalents
        - interpretation hints for AI reasoning
    """
    try:
        hsqc = BrukerReader.read_2d(hsqc_path)
        dept135 = BrukerReader.read_1d(dept135_path)
        dept_result = DEPTGuidedPicker.pick_hsqc_peaks(hsqc, dept135)

        result = SymmetryAnalyzer.analyze(molecular_formula, dept_result, hsqc)

        return {
            "success": True,
            "molecular_formula": result.molecular_formula,
            "signal_count": result.signal_count,
            "expected_carbons": result.expected_carbons,
            "missing_carbons": result.missing_carbons,
            "has_symmetry": result.has_symmetry,
            "hydrogen_budget": {
                "expected_h": result.hydrogen_budget.expected_h,
                "total_accounted": result.hydrogen_budget.total_accounted,
                "missing_h": result.hydrogen_budget.missing_h,
                "has_equivalents": result.hydrogen_budget.has_equivalents,
            },
            "intensity_report": {
                "peak_count": len(result.intensity_report.peaks),
                "has_potential_equivalents": result.intensity_report.has_potential_equivalents,
                "high_intensity_peaks": [
                    {
                        "carbon_ppm": float(p.carbon_shift),
                        "proton_ppm": float(p.proton_shift),
                        "multiplicity": p.multiplicity,
                        "relative_intensity": float(p.relative_intensity),
                        "is_potential_equivalent": p.is_potential_equivalent,
                    }
                    for p in result.intensity_report.peaks
                    if p.is_potential_equivalent
                ],
            },
            "summary": result.summary(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
