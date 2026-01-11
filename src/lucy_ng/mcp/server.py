"""MCP server for lucy-ng NMR processing tools.

Exposes NMR processing and structure elucidation tools to AI agents
via the Model Context Protocol (MCP).
"""

from mcp.server.fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP(
    name="lucy-ng",
    instructions="AI-powered Computer-Assisted Structure Elucidation for NMR data. "
    "Use these tools to read NMR spectra, pick peaks, analyze symmetry, "
    "dereplicate against databases, and generate LSD input for structure elucidation.",
)


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
