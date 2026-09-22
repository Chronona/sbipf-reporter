"""Tests for summary module."""
from __future__ import annotations

from pathlib import Path

import pytest

from sbipf_reporter.parser import AccountType, Holding, parse_sbi_csv
from sbipf_reporter.reporter import format_as_markdown
from sbipf_reporter.summary import summarize


def _holding(profit_loss: float, evaluation_value: float) -> Holding:
    return Holding(
        code="0000",
        name="テスト",
        account_type=AccountType.TOKUHU,
        buy_date="2025/01/01",
        quantity=1,
        average_price=0.0,
        current_price=0.0,
        profit_loss=profit_loss,
        evaluation_value=evaluation_value,
    )


def test_summarize_totals() -> None:
    """合計値を正しく集計する."""
    total = summarize([_holding(1000.0, 11000.0), _holding(-500.0, 9500.0)])

    assert total.count == 2
    assert total.total_evaluation == 20500.0
    assert total.total_profit_loss == 500.0
    assert total.total_cost == 20000.0
    assert total.profit_loss_rate == pytest.approx(2.5)


def test_summarize_empty() -> None:
    """保有0件でもゼロ除算せず 0.0 を返す."""
    total = summarize([])

    assert total.count == 0
    assert total.profit_loss_rate == 0.0


def test_summarize_zero_cost() -> None:
    """取得金額の合計が0でもゼロ除算しない."""
    assert summarize([_holding(1000.0, 1000.0)]).profit_loss_rate == 0.0


def test_summarize_worthless_portfolio() -> None:
    """評価額0・損益マイナスなら -100%（評価額でガードすると +0.00% になる）."""
    assert summarize([_holding(-1000.0, 0.0)]).profit_loss_rate == pytest.approx(-100.0)


def test_summary_matches_single_holding_rate() -> None:
    """1銘柄なら行の損益率と合計損益率が一致する."""
    holding = _holding(1000.0, 11000.0)

    assert summarize([holding]).profit_loss_rate == pytest.approx(holding.profit_loss_rate)


def test_markdown_and_summary_agree(tmp_path: Path) -> None:
    """Markdown出力の合計損益率が summarize() と一致する.

    旧実装は formatter.py と reporter.py が別々のガード条件で計算しており、
    評価額0・損益マイナスのとき terminal が +0.00%、markdown が -100.00% と
    食い違っていた.
    """
    holdings = [_holding(-1000.0, 0.0)]
    output_path = tmp_path / "out.md"
    format_as_markdown(holdings, output_path)

    expected = f"({summarize(holdings).profit_loss_rate:+.2f}%)"
    assert expected in output_path.read_text(encoding="utf-8")


def test_terminal_and_markdown_agree_on_fixture(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """同じCSVに対してターミナルとMarkdownの合計損益率が一致する."""
    from rich.console import Console

    from sbipf_reporter.formatter import print_summary

    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))

    captured = Console(record=True, width=120)
    monkeypatch.setattr("sbipf_reporter.formatter.Console", lambda: captured)
    print_summary(holdings)
    terminal_output = captured.export_text()

    output_path = tmp_path / "out.md"
    format_as_markdown(holdings, output_path)
    markdown_output = output_path.read_text(encoding="utf-8")

    rate = f"{summarize(holdings).profit_loss_rate:+.2f}%"
    assert rate in terminal_output
    assert rate in markdown_output
