"""Tests for parser module."""

from pathlib import Path

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
