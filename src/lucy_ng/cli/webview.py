"""Lucy webview dashboard server CLI commands.

This module is import-safe: it does NOT import fastapi, uvicorn, or any module
from ``lucy_ng.webview.app`` at the top level.  All webview-extra imports are
deferred into command bodies or into the :func:`_require_webview` guard so that
the core ``lucy`` CLI stays importable without the optional extra (WV-08).
"""

from __future__ import annotations

import json
from pathlib import Path

import click


@click.group()
def webview() -> None:
    """Webview dashboard server commands."""


def _require_webview() -> None:
    """Raise a friendly :exc:`click.ClickException` when the webview extra is absent.

    Checks for both ``fastapi`` and ``uvicorn`` — if either is missing the
    optional extra is not fully installed.
    """
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError as exc:
        raise click.ClickException(
            "The webview extra is not installed.\n"
            "Install with: pip install lucy-ng[webview]"
        ) from exc


@webview.command("serve")
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option("--port", "-p", type=int, default=None, help="TCP port to listen on.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address.")
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    help="Open the dashboard in the default browser after starting.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def serve(
    analysis_dir: Path,
    port: int | None,
    host: str,
    open_browser: bool,
    output_format: str,
) -> None:
    """Start the webview server for ANALYSIS_DIR.

    Idempotent: if a server is already running for the directory, returns
    the existing state without starting a new process.
    """
    _require_webview()

    import lucy_ng.webview.server as server

    state = server.start(analysis_dir, port, host)

    if open_browser:
        import webbrowser

        webbrowser.open(state.url)

    if output_format == "json":
        click.echo(json.dumps({"url": state.url, "pid": state.pid, "port": state.port}))
    else:
        click.echo(f"Webview server running at {state.url}")
        click.echo(f"Stop with: lucy webview stop {analysis_dir}")


@webview.command("stop")
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def stop(analysis_dir: Path, output_format: str) -> None:
    """Stop the webview server for ANALYSIS_DIR."""
    import lucy_ng.webview.server as server

    stopped, pid = server.stop(analysis_dir)

    if output_format == "json":
        click.echo(json.dumps({"stopped": stopped, "pid": pid}))
    else:
        if stopped:
            click.echo(f"Webview server stopped (pid {pid})")
        else:
            click.echo("No running webview server found.")


@webview.command("status")
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format.",
)
def status(analysis_dir: Path, output_format: str) -> None:
    """Report webview server status for ANALYSIS_DIR."""
    import lucy_ng.webview.server as server

    st = server.status(analysis_dir)

    if output_format == "json":
        click.echo(
            json.dumps(
                {
                    "running": st is not None,
                    "url": st.url if st else None,
                    "pid": st.pid if st else None,
                }
            )
        )
    else:
        if st is not None:
            click.echo(f"running at {st.url} (pid {st.pid})")
        else:
            click.echo("not running")


@webview.command("_run", hidden=True)
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option("--port", type=int, required=True, help="Port to bind.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind address.")
def _run(analysis_dir: Path, port: int, host: str) -> None:
    """Internal foreground entrypoint for the detached uvicorn subprocess.

    This hidden subcommand is invoked by :func:`lucy_ng.webview.server.start`
    via a detached :class:`subprocess.Popen` call.  It should not be invoked
    directly by users (T-90-10: accepted risk — binds loopback only).
    """
    _require_webview()

    import uvicorn

    from lucy_ng.webview.app import create_app

    app = create_app(analysis_dir.resolve())
    uvicorn.run(app, host=host, port=port, log_level="warning")
