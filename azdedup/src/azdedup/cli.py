"""CLI entrypoint — scan | dedup | verify | report | cleanup."""

from __future__ import annotations

import typer
from rich.console import Console

from azdedup import __version__
from azdedup.commands.dedup import run_dedup
from azdedup.commands.report import run_report
from azdedup.commands.scan import run_scan
from azdedup.commands.verify import run_verify
from azdedup.config import (
    load_dedup_config_from_env,
    load_report_config_from_env,
    load_scan_config_from_env,
    load_verify_config_from_env,
)

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
    inventory_path: str = typer.Option(
        "artifacts/dedup/ag1/Alansinv_1000000_*.csv",
        "--inventory-path",
        help="Glob for inventory CSV shards when --source inventory",
    ),
    apply_tags: bool = typer.Option(
        False,
        "--apply-tags/--dry-run-tags",
        help="Write meta tags to Azure (default: dry-run jsonl only)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-tag blobs even when dedup_etag matches",
    ),
) -> None:
    """Discovery & metadata pass (zero blob content reads)."""
    if source not in {"live", "inventory"}:
        raise typer.BadParameter("--source must be live or inventory")

    inventory_paths = [inventory_path] if source == "inventory" else []
    config = load_scan_config_from_env(
        account,
        containers=containers,
        prefix=prefix,
        concurrency=concurrency,
        source=source,
        inventory_paths=inventory_paths,
        apply_tags=apply_tags,
        force=force,
    )
    run_scan(config, console=console)


@app.command()
def dedup(
    stage: str = typer.Option(..., "--stage", help="partial | full | canonical"),
    account: str = typer.Option(..., "--account"),
    containers: str = typer.Option("all", "--containers"),
    prefix: str = typer.Option("", "--prefix"),
    concurrency: int = typer.Option(32, "--concurrency"),
    source: str = typer.Option("inventory", "--source", help="live | inventory"),
    inventory_path: str = typer.Option(
        "artifacts/dedup/ag1/Alansinv_1000000_*.csv",
        "--inventory-path",
        help="Glob for inventory CSV shards when --source inventory",
    ),
    read_bytes: int = typer.Option(1_048_576, "--read-bytes"),
    apply_tags: bool = typer.Option(
        False,
        "--apply-tags/--dry-run-tags",
        help="Write hash tags to Azure (default: dry-run jsonl only)",
    ),
    incremental: bool = typer.Option(False, "--incremental"),
    force: bool = typer.Option(
        False,
        "--force",
        help="Re-hash blobs even when dedup_etag matches",
    ),
    strategy: str = typer.Option(
        "container_priority",
        "--strategy",
        help="canonical only: oldest | shortest | container_priority",
    ),
) -> None:
    """Multi-stage hashing pipeline."""
    if stage not in {"partial", "full", "canonical"}:
        raise typer.BadParameter("--stage must be partial, full, or canonical")
    if source not in {"live", "inventory"}:
        raise typer.BadParameter("--source must be live or inventory")

    inventory_paths = [inventory_path] if source == "inventory" else []
    config = load_dedup_config_from_env(
        account,
        stage=stage,
        containers=containers,
        prefix=prefix,
        concurrency=concurrency,
        source=source,
        inventory_paths=inventory_paths,
        read_bytes=read_bytes,
        apply_tags=apply_tags,
        incremental=incremental,
        force=force,
        canonical_strategy=strategy,
    )
    run_dedup(config, console=console)


@app.command()
def verify(
    account: str = typer.Option(..., "--account"),
    sample_rate: float = typer.Option(0.001, "--sample-rate"),
    inventory_path: str = typer.Option(
        "artifacts/dedup/ag1/Alansinv_1000000_*.csv",
        "--inventory-path",
    ),
    containers: str = typer.Option("all", "--containers"),
) -> None:
    """Statistical spot verification."""
    config = load_verify_config_from_env(
        account,
        sample_rate=sample_rate,
        inventory_paths=[inventory_path],
        containers=containers,
    )
    run_verify(config, console=console)


@app.command()
def report(
    account: str = typer.Option(..., "--account"),
    format: str = typer.Option("table", "--format", help="table | json"),
    group_by: str = typer.Option("none", "--group-by", help="container | stage | none"),
    source: str = typer.Option("inventory", "--source", help="inventory | dry-run"),
    inventory_path: str = typer.Option(
        "artifacts/dedup/ag1/Alansinv_1000000_*.csv",
        "--inventory-path",
    ),
    sample_rate: float = typer.Option(1.0, "--sample-rate"),
) -> None:
    """Visibility & confidence metrics."""
    config = load_report_config_from_env(
        account,
        source=source,
        group_by=group_by,
        inventory_paths=[inventory_path],
        sample_rate=sample_rate,
    )
    run_report(config, fmt=format, console=console)


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
