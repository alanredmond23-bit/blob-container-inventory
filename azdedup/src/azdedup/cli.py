"""CLI entrypoint — scan | dedup | verify | report | cleanup."""

from __future__ import annotations

import typer
from rich.console import Console

from azdedup import __version__

app = typer.Typer(
    name="azdedup",
    help="Fast, safe, incremental deduplication of Azure Blob Storage at hyperscale.",
    no_args_is_help=True,
)
console = Console()


def _stub(name: str) -> None:
    console.print(f"[yellow]{name}[/yellow] not implemented — see docs/AZDEDUP_IMPLEMENTATION_PLAN.md")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V"),
) -> None:
    if version:
        console.print(f"azdedup {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def scan(
    account: str = typer.Option(..., "--account", help="Storage account name"),
    containers: str = typer.Option("all", "--containers"),
    prefix: str = typer.Option("", "--prefix"),
    concurrency: int = typer.Option(64, "--concurrency"),
    source: str = typer.Option("live", "--source", help="live | inventory"),
) -> None:
    """Discovery & metadata pass (zero blob content reads)."""
    _stub(f"scan account={account} containers={containers} source={source}")


@app.command()
def dedup(
    stage: str = typer.Option(..., "--stage", help="partial | full | canonical"),
    account: str = typer.Option(..., "--account"),
    containers: str = typer.Option("all", "--containers"),
    concurrency: int = typer.Option(32, "--concurrency"),
    incremental: bool = typer.Option(False, "--incremental"),
) -> None:
    """Multi-stage hashing pipeline."""
    _stub(f"dedup stage={stage} incremental={incremental}")


@app.command()
def verify(
    account: str = typer.Option(..., "--account"),
    sample_rate: float = typer.Option(0.001, "--sample-rate"),
) -> None:
    """Statistical spot verification."""
    _stub("verify")


@app.command()
def report(
    account: str = typer.Option(..., "--account"),
    format: str = typer.Option("table", "--format", help="table | json"),
) -> None:
    """Visibility & confidence metrics."""
    _stub(f"report format={format}")


@app.command()
def cleanup(
    account: str = typer.Option(..., "--account"),
    mode: str = typer.Option("tag-only", "--mode", help="tag-only | move | delete"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Optional deletion / quarantine (never default)."""
    if mode == "delete" and not confirm:
        raise typer.BadParameter("delete requires --confirm")
    _stub(f"cleanup mode={mode} dry_run={dry_run}")


if __name__ == "__main__":
    app()
