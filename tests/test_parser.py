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


def test_halfwidth_section_headers_are_detected() -> None:
    """半角括弧のセクション見出しでも口座区分を判別する.

    旧実装は見出しを全角括弧で決め打ち比較していたため、半角括弧のCSVでは
    セクションとして認識されず、全銘柄が UNKNOWN になっていた.
    """
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_halfwidth_sections.csv"))

    assert [h.account_type for h in holdings] == [
        AccountType.TOKUHU,
        AccountType.NISA_GROWTH,
        AccountType.NISA_TSUMITATE,
    ]
    assert AccountType.UNKNOWN not in [h.account_type for h in holdings]


def test_fullwidth_section_headers_still_detected() -> None:
    """全角括弧の既存フィクスチャも従来どおり判別できる（退行していない）."""
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_sample.csv"))

    assert AccountType.UNKNOWN not in [h.account_type for h in holdings]
    assert len([h for h in holdings if h.account_type == AccountType.TOKUHU]) == 2


def test_non_stock_section_headers_are_detected() -> None:
    """「株式（」で始まらないセクションも新しい見出しとして扱う.

    旧実装は見出しを 株式（ / 投資信託（ で決め打ちしていたため、
    外国株式や債券のセクションを認識できず、直前セクションの口座区分を
    引きずったまま銘柄を取り込んでいた.
    """
    holdings = parse_sbi_csv(Path("tests/fixtures/sbi_other_asset_sections.csv"))

    assert [(h.code, h.account_type) for h in holdings] == [
        ("6758", AccountType.TOKUHU),
        ("AAPL", AccountType.NISA_GROWTH),
        ("9999", AccountType.GENBUTSU),
    ]


def test_account_type_uses_custody_part_only() -> None:
    """口座区分は「/」以降の預り区分だけで判定する."""
    from sbipf_reporter.parser import _detect_account_type

    assert _detect_account_type("株式（現物/特定預り）") == AccountType.TOKUHU
    assert _detect_account_type("株式（信用/特定預り）") == AccountType.TOKUHU
    assert _detect_account_type("外国株式（現物/NISA預り（成長投資枠））") == AccountType.NISA_GROWTH
    assert _detect_account_type("投資信託（金額/NISA預り（つみたて投資枠））") == AccountType.NISA_TSUMITATE
    assert _detect_account_type("債券（現物/一般預り）") == AccountType.GENBUTSU


def test_nisa_is_matched_before_tokutei() -> None:
    """預り区分にNISAと特定の両方の語が現れてもNISAを優先する.

    旧実装は「特定」を先に判定していたため、このような見出しで
    誤って特定口座と判定していた.
    """
    from sbipf_reporter.parser import _detect_account_type

    assert _detect_account_type("株式（特定/NISA預り（成長投資枠））") == AccountType.NISA_GROWTH


def test_aggregate_rows_are_not_treated_as_section_headers() -> None:
    """「合計」で終わる1セル行を見出しとして誤検出しない."""
    from sbipf_reporter.parser import _is_section_header

    assert _is_section_header(["株式（現物/特定預り）", ""]) is True
    assert _is_section_header(["株式(現物/特定預り)合計", ""]) is False
    assert _is_section_header(["総合計", ""]) is False
    assert _is_section_header(["ポートフォリオ一覧", ""]) is False
    assert _is_section_header(["総件数：25件", ""]) is False
    # データ行は複数セルが埋まっているので見出しにならない
    assert _is_section_header(["6758 ソニー", "2025/03/12", "50"]) is False
