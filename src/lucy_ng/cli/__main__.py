"""Entry point for ``python -m lucy_ng.cli``.

Allows the lucy-ng CLI to be invoked as::

    python -m lucy_ng.cli <command> [args...]

This is used as a subprocess-launch fallback by :func:`lucy_ng.webview.server.start`
when the ``lucy`` script is not on PATH (e.g. in an editable/dev install).
"""

from lucy_ng.cli import cli

if __name__ == "__main__":
    cli()
