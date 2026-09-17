"""Tests for formatter module."""
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from sbipf_reporter.formatter import print_summary
from sbipf_reporter.parser import parse_sbi_csv


def _render_summary(monkeypatch, holdings) -> str:  # type: ignore[no-untyped-def]
    """print_summary の出力を文字列として取得する."""
    captured = Console(record=True, width=120)
    monkeypatch.setattr("sbipf_reporter.formatter.Console", lambda: captured)
    print_summary(holdings)
    return captured.export_text()


def test_summary_labels_holdings_count_not_holders(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """サマリーの見出しは「保有銘柄数」（「保有者数」ではない）."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    output = _render_summary(monkeypatch, holdings)

    assert "保有銘柄数: 16 件" in output
    assert "保有者数" not in output
