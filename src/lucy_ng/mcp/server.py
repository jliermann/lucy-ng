"""MCP server for lucy-ng NMR processing tools.

Exposes NMR processing and structure elucidation tools to AI agents
via the Model Context Protocol (MCP).
"""

from mcp.server.fastmcp import FastMCP

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


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
