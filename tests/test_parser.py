"""Tests for parser module."""
from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from sbipf_reporter.parser import AccountType, Holding, parse_sbi_csv


def test_parse_sbi_csv_returns_list() -> None:
    """Test that parse_sbi_csv returns a list."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    assert isinstance(holdings, list)


def test_parse_sbi_csv_holdings_count() -> None:
    """Test that parser extracts correct number of holdings."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    assert len(holdings) == 16


def test_parse_sbi_csv_stocks_only() -> None:
    """Test that parser extracts stock holdings (not funds)."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    stocks = [h for h in holdings if h.code and h.code.isdigit()]
    assert len(stocks) == 11


def test_parse_sbi_csv_first_holding() -> None:
    """Test that parser extracts correct data for first stock."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    stock = next(h for h in holdings if h.code == "6758" and h.account_type == AccountType.TOKUHU)
    assert stock.name == "ソニー"
    assert stock.buy_date == "2025/03/12"
    assert stock.quantity == 50
    assert stock.average_price == 9850.0
    assert stock.current_price == 10240.0
    assert stock.profit_loss == 1950.0
    assert stock.evaluation_value == 51200.0


def test_parse_sbi_csv_nisa_growth() -> None:
    """Test that parser correctly identifies NISA growth account type."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    nisa_growth = [h for h in holdings if h.account_type == AccountType.NISA_GROWTH]
    assert len(nisa_growth) == 13  # 10 stocks + 3 investment trusts


def test_parse_sbi_csv_nisa_tsumitate() -> None:
    """Test that parser correctly identifies NISA tsumitate account type."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    nisa_tsumitate = [h for h in holdings if h.account_type == AccountType.NISA_TSUMITATE]
    assert len(nisa_tsumitate) == 1
    assert nisa_tsumitate[0].name == "ｅＭＡＸＩＳ Ｓｌｉｍ 全世界株式（オール・カントリー）"


def test_parse_sbi_csv_investment_trust() -> None:
    """Test that parser extracts investment trust funds."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))
    funds = [h for h in holdings if not h.code or not h.code.isdigit()]
    assert len(funds) == 5


def test_holding_dataclass() -> None:
    """Test Holding dataclass creation."""
    holding = Holding(
        code="6758",
        name="ソニー",
        account_type=AccountType.GENBUTSU,
        buy_date="2025/03/12",
        quantity=50,
        average_price=9850.0,
        current_price=10240.0,
        profit_loss=1950.0,
        evaluation_value=51200.0,
    )
    assert holding.code == "6758"
    assert holding.name == "ソニー"
    assert holding.account_type == AccountType.GENBUTSU


def test_parse_sbi_csv_enclosed_headers() -> None:
    """Test parsing CSV with 【】 enclosed section headers."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_enclosed_headers.csv"))
    assert len(holdings) == 16
    # Verify account types are still detected correctly
    tokuhu = [h for h in holdings if h.account_type == AccountType.TOKUHU]
    assert len(tokuhu) == 2  # 6758 ソニー (two entries in sample)
    nisa_growth = [h for h in holdings if h.account_type == AccountType.NISA_GROWTH]
    assert len(nisa_growth) == 13
    nisa_tsumitate = [h for h in holdings if h.account_type == AccountType.NISA_TSUMITATE]
    assert len(nisa_tsumitate) == 1


def test_parse_sbi_csv_square_brackets() -> None:
    """Test parsing CSV with [] enclosed section headers."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_square_brackets.csv"))
    assert len(holdings) == 16
    tokuhu = [h for h in holdings if h.account_type == AccountType.TOKUHU]
    assert len(tokuhu) == 2
    nisa_growth = [h for h in holdings if h.account_type == AccountType.NISA_GROWTH]
    assert len(nisa_growth) == 13
    nisa_tsumitate = [h for h in holdings if h.account_type == AccountType.NISA_TSUMITATE]
    assert len(nisa_tsumitate) == 1


def test_parse_sbi_csv_10col_format() -> None:
    """Test parsing CSV without reference price column (10-col format)."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_10col.csv"))
    assert len(holdings) == 3

    tokuhu = [h for h in holdings if h.account_type == AccountType.TOKUHU]
    assert len(tokuhu) == 2
    assert tokuhu[0].code == "6758"
    assert tokuhu[0].average_price == 9800.0
    assert tokuhu[0].current_price == 10240.0
    assert tokuhu[0].evaluation_value == 51200.0

    nisa_growth = [h for h in holdings if h.account_type == AccountType.NISA_GROWTH]
    assert len(nisa_growth) == 1
    assert nisa_growth[0].code == "4755"
    assert nisa_growth[0].average_price == 300.0
    assert nisa_growth[0].current_price == 320.0
    assert nisa_growth[0].evaluation_value == 64000.0


def test_parse_thousand_separators() -> None:
    """桁区切りカンマ付きの数値を含む行をパースできる."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_thousand_separators.csv"))

    assert len(holdings) == 1
    holding = holdings[0]
    assert holding.quantity == 1000
    assert holding.average_price == 9850.0
    assert holding.current_price == 10240.0
    assert holding.profit_loss == 390000.0
    assert holding.evaluation_value == 10240000.0


def test_unparsable_row_warns_instead_of_silently_skipping(tmp_path: Path) -> None:
    """パース不能な行はスキップするが UserWarning を出す.

    旧実装は except で無言スキップしていたため、資産額が実際より
    少なく表示されてもユーザーが気づけなかった.
    """
    csv_path = tmp_path / "broken.csv"
    csv_path.write_text(
        '"株式（現物/特定預り）",\n'
        '"銘柄（コード）","買付日","数量","参考単価","取得単価","現在値",'
        '"前日比","前日比（％）","損益","損益（％）","評価額",\n'
        '"6758 ソニー","2025/03/12",50,9800,9850,10240,+120,+1.19,+19500,+3.96,512000,\n'
        '"9999 壊れ","2025/03/12",XX,9800,9850,10240,+120,+1.19,+19500,+3.96,512000,\n',
        encoding="utf-8",
    )

    with pytest.warns(UserWarning, match="スキップ") as record:
        holdings = parse_sbi_csv(csv_path)

    assert len(holdings) == 1
    assert "broken.csv:4" in str(record[0].message)
    assert "9999 壊れ" in str(record[0].message)


def test_valid_fixtures_parse_without_warnings() -> None:
    """正常なCSVでは警告を出さない（誤検知しない）."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert len(parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))) == 16
        assert len(parse_sbi_csv(Path("tests/fixtures/sbi_10col.csv"))) == 3
