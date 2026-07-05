"""sbipf-reporter CLI."""

from __future__ import annotations

from pathlib import Path

import typer

from sbipf_reporter.parser import parse_sbi_csv
from sbipf_reporter.reporter import OutputFormat, output_report

app = typer.Typer()


@app.command()
def report(
    file: Path,
    format: OutputFormat = OutputFormat.TERMINAL,
    output: Path | None = None,
) -> None:
    """SBI証券CSVからポートフォリオレポートを出力.

    対応フォーマット:
      - terminal: ターミナルに rich テーブル表示（デフォルト）
      - md: Markdown ファイル出力
      - csv: CSV ファイル出力

    使用例:
      sbipf-reporter report portfolio.csv
      sbipf-reporter report portfolio.csv --format md --output report.md
      sbipf-reporter report portfolio.csv --format csv --output report.csv

    Args:
        file: SBI証券のポートフォリオCSVファイルのパス
        format: 出力フォーマット（terminal / md / csv）
        output: 出力ファイルパス（formatがmd/csvの場合に指定）
    """
    holdings = parse_sbi_csv(file)
    output_report(holdings, format, output)


@app.command()
def version() -> None:
    """バージョンを表示."""
    from sbipf_reporter import __version__

    typer.echo(f"sbipf-reporter v{__version__}")


if __name__ == "__main__":
    app()
