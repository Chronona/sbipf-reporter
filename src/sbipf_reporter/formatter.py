"""richテーブルフォーマッター."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from sbipf_reporter.parser import Holding


def format_holdings_table(holdings: list[Holding]) -> Table:
    """Holdingリストからrichテーブルを生成する.

    Args:
        holdings: 保有銘柄リスト

    Returns:
        rich.Table インスタンス
    """
    table = Table(title="SBI証券ポートフォリオ")

    table.add_column("コード", style="cyan", no_wrap=True)
    table.add_column("銘柄名", style="bold")
    table.add_column("口座", style="magenta")
    table.add_column("数量", justify="right")
    table.add_column("取得単価", justify="right")
    table.add_column("現在値", justify="right")
    table.add_column("評価額", justify="right")
    table.add_column("損益", justify="right")
    table.add_column("損益率", justify="right")

    for h in holdings:
        profit_rate = (
            (h.profit_loss / h.evaluation_value * 100)
            if h.evaluation_value != 0
            else 0.0
        )
        profit_str = f"{h.profit_loss:+,.0f}"
        rate_str = f"{profit_rate:+.2f}%"
        eval_str = f"{h.evaluation_value:,.0f}"

        table.add_row(
            h.code or "-",
            h.name,
            h.account_type.value,
            f"{h.quantity:,}",
            f"¥{h.average_price:,.0f}",
            f"¥{h.current_price:,.0f}",
            f"¥{eval_str}",
            f"¥{profit_str}",
            rate_str,
        )

    return table


def print_summary(holdings: list[Holding]) -> None:
    """サマリー情報を出力する.

    Args:
        holdings: 保有銘柄リスト
    """
    console = Console()

    total_eval = sum(h.evaluation_value for h in holdings)
    total_profit = sum(h.profit_loss for h in holdings)
    total_rate = (
        (total_profit / (total_eval - total_profit) * 100) if total_eval > 0 else 0
    )

    console.print()
    console.print(f"[bold]保有者数:[/bold] {len(holdings)} 件")
    console.print(f"[bold]総資産:[/bold] ¥{total_eval:,.0f}")
    console.print(f"[bold]総損益:[/bold] ¥{total_profit:+,.0f} ({total_rate:+.2f}%)")
    console.print()


def print_holdings(holdings: list[Holding]) -> None:
    """Holdingリストをテーブル形式で出力する.

    Args:
        holdings: 保有銘柄リスト
    """
    console = Console()
    table = format_holdings_table(holdings)
    console.print(table)
