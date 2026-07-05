"""レポート出力フォーマッター."""

from __future__ import annotations

import csv
from enum import Enum
from pathlib import Path

from sbipf_reporter.parser import Holding


class OutputFormat(Enum):
    """レポート出力フォーマット.

    選択可能なフォーマット:
      - terminal: rich ライブラリによるカラフルなテーブル表示
      - md: Markdown 形式（GitHub等で参照可能）
      - csv: 損益率カラムを追加したCSV（Excel等で開く場合に便利）

    Attributes:
        TERMINAL: ターミナル表示（richテーブル）
        MD: Markdown形式ファイル出力
        CSV: CSV形式ファイル出力（損益率カラム追加）
    """

    TERMINAL = "terminal"
    MD = "md"
    CSV = "csv"


def format_as_csv(holdings: list[Holding], output_path: Path) -> None:
    """CSV形式でファイルに出力する.

    Args:
        holdings: 保有銘柄リスト
        output_path: 出力CSVファイルのパス
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "コード",
                "銘柄名",
                "口座",
                "買付日",
                "数量",
                "取得単価",
                "現在値",
                "評価額",
                "損益",
                "損益率",
            ]
        )

        for h in holdings:
            writer.writerow(
                [
                    h.code or "",
                    h.name,
                    h.account_type.value,
                    h.buy_date,
                    h.quantity,
                    h.average_price,
                    h.current_price,
                    h.evaluation_value,
                    h.profit_loss,
                    f"{h.profit_loss_rate:.2f}",
                ]
            )


def format_as_markdown(holdings: list[Holding], output_path: Path) -> None:
    """Markdown形式でファイルに出力する.

    Args:
        holdings: 保有銘柄リスト
        output_path: 出力Markdownファイルのパス
    """
    lines = [
        "# SBI証券ポートフォリオ",
        "",
        "| コード | 銘柄名 | 口座 | 買付日 | 数量 | 取得単価 | 現在値 | 評価額 | 損益 | 損益率 |",
        "|------|------|------|------|------|------|------|------|------|------|",
    ]

    for h in holdings:
        lines.append(
            f"| {h.code or '-'} | {h.name} | {h.account_type.value} | {h.buy_date} | {h.quantity:,} | "
            f"¥{h.average_price:,.0f} | ¥{h.current_price:,.0f} | ¥{h.evaluation_value:,.0f} | "
            f"¥{h.profit_loss:+,.0f} | {h.profit_loss_rate:+.2f}% |"
        )

    total_eval = sum(h.evaluation_value for h in holdings)
    total_profit = sum(h.profit_loss for h in holdings)
    total_rate = (total_profit / (total_eval - total_profit) * 100) if total_eval > total_profit else 0.0

    lines.extend(
        [
            "",
            (
                f"**合計**: 保有数 {len(holdings)}件, "
                f"総資産 ¥{total_eval:,.0f}, "
                f"損益 ¥{total_profit:+,.0f} ({total_rate:+.2f}%)"
            ),
        ]
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def output_report(holdings: list[Holding], output_format: OutputFormat, output_path: Path | None) -> None:
    """パース結果を指定フォーマットで出力する.

    TERMINAL の場合は rich ライブラリを使用してコンソールに表示.
    MD/CSV の場合は output_path にファイル出力.
    output_path が None の場合、デフォルトのファイル名
    (portfolio.md / portfolio.csv) を使用する.

    Args:
        holdings: パース済みの保有銘柄リスト
        output_format: 出力フォーマット（terminal / md / csv）
        output_path: 出力ファイルパス（terminalの場合は無視）
    """
    if output_format == OutputFormat.CSV:
        if output_path is None:
            output_path = Path("portfolio.csv")
        format_as_csv(holdings, output_path)
    elif output_format == OutputFormat.MD:
        if output_path is None:
            output_path = Path("portfolio.md")
        format_as_markdown(holdings, output_path)
    else:
        from sbipf_reporter.formatter import print_holdings, print_summary

        print_summary(holdings)
        print_holdings(holdings)
