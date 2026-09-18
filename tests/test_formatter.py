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


def test_print_summary_with_zero_cost_does_not_raise(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """取得金額の合計が0でも ZeroDivisionError にならない.

    ガードが `total_eval > 0` で分母が `total_eval - total_profit` だったため、
    評価額が正でも取得金額が0のとき分母0のまま除算に入っていた.
    """
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_zero_cost.csv"))
    output = _render_summary(monkeypatch, holdings)

    assert "+0.00%" in output


def test_print_summary_with_empty_holdings_does_not_raise(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """保有0件でも落ちない."""
    output = _render_summary(monkeypatch, [])

    assert "保有銘柄数: 0 件" in output


def test_print_summary_total_rate_of_worthless_portfolio(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """評価額0・損益マイナスなら合計損益率は -100%（旧ガードでは +0.00% になっていた）."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_worthless.csv"))
    output = _render_summary(monkeypatch, holdings)

    assert "-100.00%" in output
