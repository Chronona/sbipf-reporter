"""独立した参照実装との差分検証で見つかった不具合の回帰テスト.

各テストは「修正前の実装で失敗すること」を確認して追加している.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from sbipf_reporter.formatter import print_summary
from sbipf_reporter.parser import AccountType, Holding, parse_sbi_csv
from sbipf_reporter.reporter import format_as_markdown
from sbipf_reporter.summary import summarize

FIXTURES = Path("tests/fixtures")


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


# --- 損益率の基準 -------------------------------------------------------------


def test_profit_loss_rate_is_based_on_acquisition_cost() -> None:
    """行の損益率は取得金額基準（評価額基準ではない）."""
    holding = _holding(profit_loss=1000.0, evaluation_value=11000.0)
    assert holding.acquisition_cost == 10000.0
    assert holding.profit_loss_rate == pytest.approx(10.0)


def test_profit_loss_rate_matches_total_rate_for_single_holding() -> None:
    """1銘柄だけなら行の損益率と合計損益率は一致する（定義が同じ基準）."""
    holding = _holding(profit_loss=1000.0, evaluation_value=11000.0)
    assert holding.profit_loss_rate == pytest.approx(summarize([holding]).profit_loss_rate)


def test_profit_loss_rate_zero_cost_does_not_raise() -> None:
    """取得金額0でもゼロ除算しない."""
    assert _holding(profit_loss=1000.0, evaluation_value=1000.0).profit_loss_rate == 0.0


# --- 集計のゼロ除算 / 符号 ----------------------------------------------------


def test_print_summary_with_zero_cost_does_not_raise() -> None:
    """取得金額合計が0でも print_summary が落ちない（旧実装は ZeroDivisionError）."""
    print_summary(parse_sbi_csv(FIXTURES / "sbi_zero_cost.csv"))


def test_print_summary_with_empty_holdings_does_not_raise() -> None:
    """保有0件でも print_summary が落ちない."""
    print_summary([])


def test_total_rate_of_worthless_portfolio_is_minus_100() -> None:
    """評価額0・損益マイナスの合計損益率は -100%（旧実装のターミナル表示は +0.00%）."""
    holdings = parse_sbi_csv(FIXTURES / "sbi_worthless.csv")
    assert summarize(holdings).profit_loss_rate == pytest.approx(-100.0)


def test_markdown_and_summary_agree_on_total_rate(tmp_path: Path) -> None:
    """Markdown出力とサマリーの合計損益率が一致する（旧実装は分岐条件が別物だった）."""
    holdings = parse_sbi_csv(FIXTURES / "sbi_worthless.csv")
    output_path = tmp_path / "out.md"
    format_as_markdown(holdings, output_path)
    expected = f"({summarize(holdings).profit_loss_rate:+.2f}%)"
    assert expected in output_path.read_text(encoding="utf-8")


# --- セクション見出しの検出 ---------------------------------------------------


def test_halfwidth_section_headers_are_detected() -> None:
    """半角括弧のセクション見出しでも口座区分を判別する（旧実装は全件 UNKNOWN）."""
    holdings = parse_sbi_csv(FIXTURES / "sbi_halfwidth_sections.csv")
    assert [h.account_type for h in holdings] == [AccountType.TOKUHU, AccountType.NISA_GROWTH]


def test_non_stock_section_headers_are_detected() -> None:
    """「株式（」で始まらないセクション（外国株式など）も新しい口座区分として扱う.

    旧実装は見出しを認識できず、直前セクションの口座区分を引きずっていた.
    """
    holdings = parse_sbi_csv(FIXTURES / "sbi_foreign_stock.csv")
    assert [h.account_type for h in holdings] == [AccountType.TOKUHU, AccountType.NISA_GROWTH]
    assert holdings[1].code == "AAPL"


# --- 投資信託の銘柄名 ---------------------------------------------------------


def test_fund_names_are_not_split_into_code_and_name() -> None:
    """投信はセル全体が銘柄名になる（旧実装は名前を空白で切ってコード扱いしていた）."""
    holdings = parse_sbi_csv(FIXTURES / "sbi_funds_various.csv")
    assert [h.code for h in holdings] == ["", "", ""]
    assert [h.name for h in holdings] == [
        "たわらノーロード 先進国株式",
        "ニッセイ外国株式インデックスファンド",
        "楽天・全米株式インデックス・ファンド",
    ]


def test_known_prefix_fund_names_still_parse() -> None:
    """従来ハードコードで対応していた投信名も引き続き銘柄名として扱われる."""
    holdings = parse_sbi_csv(FIXTURES / "sbi_sample.csv")
    funds = [h for h in holdings if not h.code]
    assert len(funds) == 5
    assert funds[0].name.startswith("ｅＭＡＸＩＳ")


# --- 数値パース ---------------------------------------------------------------


def test_thousand_separators_are_parsed() -> None:
    """桁区切りカンマ入りの数値を読める（旧実装は行ごと無言で捨てていた）."""
    holdings = parse_sbi_csv(FIXTURES / "sbi_thousand_separators.csv")
    assert len(holdings) == 1
    assert holdings[0].quantity == 1000
    assert holdings[0].evaluation_value == 10240000.0


def test_placeholder_values_in_unused_columns_do_not_drop_rows() -> None:
    """使わない列が「--」でも行は落ちない."""
    assert len(parse_sbi_csv(FIXTURES / "sbi_placeholder_values.csv")) == 2


def test_unparsable_row_warns_instead_of_silently_skipping(tmp_path: Path) -> None:
    """パース不能な行はスキップするが警告を出す（旧実装は無言で握り潰していた）."""
    csv_path = tmp_path / "broken.csv"
    csv_path.write_text(
        '"株式（現物/特定預り）",\n'
        '"銘柄（コード）","買付日","数量","参考単価","取得単価","現在値",'
        '"前日比","前日比（％）","損益","損益（％）","評価額",\n'
        '"6758 ソニー","2025/03/12",50,9800,9850,10240,+120,+1.19,+19500,+3.96,512000,\n'
        '"9999 壊れ","2025/03/12",XX,9800,9850,10240,+120,+1.19,+19500,+3.96,512000,\n',
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="スキップ"):
        holdings = parse_sbi_csv(csv_path)
    assert len(holdings) == 1


# --- 既存フィクスチャが退行していないこと -------------------------------------


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [("sbi_sample.csv", 16), ("sbi_enclosed_headers.csv", 16), ("sbi_square_brackets.csv", 16), ("sbi_10col.csv", 3)],
)
def test_existing_fixtures_parse_without_warnings(fixture: str, expected: int) -> None:
    """既存フィクスチャは警告なしで従来どおりの件数がパースできる."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        holdings = parse_sbi_csv(FIXTURES / fixture)
    assert len(holdings) == expected
