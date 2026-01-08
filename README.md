# lucy-ng

AI-agent powered Computer-Assisted Structure Elucidation for organic natural products.

## Overview

lucy-ng is designed for programmatic, unattended structure elucidation from NMR spectroscopic data. Unlike GUI-focused tools, lucy-ng is built for AI-agent (Claude) driven workflows where the agent can iterate through the elucidation process until a structure is determined.

## Installation

```bash
pip install lucy-ng
```

For development:

```bash
pip install -e ".[dev]"
```

## Requirements

- Python 3.10+
- nmrglue for NMR file parsing
- LSD/pyLSD for structure elucidation (external)

## License

MIT
