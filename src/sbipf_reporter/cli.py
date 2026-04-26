"""sbipf-reporter CLI."""

from __future__ import annotations

from pathlib import Path

import typer

from sbipf_reporter.formatter import print_holdings, print_summary
from sbipf_reporter.parser import parse_sbi_csv

app = typer.Typer()


@app.command()
def report(file: Path) -> None:
    """SBI証券CSVからポートフォリオレポートを出力."""
    holdings = parse_sbi_csv(file)
    print_summary(holdings)
    print_holdings(holdings)


@app.command()
def version() -> None:
    """バージョンを表示."""
    from sbipf_reporter import __version__
    typer.echo(f"sbipf-reporter v{__version__}")


if __name__ == "__main__":
    app()
