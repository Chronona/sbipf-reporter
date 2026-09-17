"""ポートフォリオ全体の集計.

ターミナル表示・Markdown 出力の双方がこのモジュールを使うことで、
合計損益率の定義が出力フォーマットによってブレないようにする.
"""

from __future__ import annotations

from dataclasses import dataclass

from sbipf_reporter.parser import Holding


@dataclass(frozen=True)
class PortfolioSummary:
    """ポートフォリオ全体の集計結果.

    Attributes:
        count: 保有銘柄数
        total_evaluation: 評価額の合計（円）
        total_profit_loss: 損益の合計（円）
        total_cost: 取得金額の合計（円）
    """

    count: int
    total_evaluation: float
    total_profit_loss: float
    total_cost: float

    @property
    def profit_loss_rate(self) -> float:
        """合計損益率（％）.

        取得金額の合計を分母とする（損益合計 ÷ 取得金額合計 × 100）.
        Holding.profit_loss_rate と同じ基準.
        取得金額の合計が 0 の場合は 0.0 を返す（ゼロ除算を起こさない）.
        """
        if self.total_cost == 0:
            return 0.0
        return self.total_profit_loss / self.total_cost * 100


def summarize(holdings: list[Holding]) -> PortfolioSummary:
    """保有銘柄リストから集計値を求める.

    Args:
        holdings: 保有銘柄リスト

    Returns:
        集計結果の PortfolioSummary
    """
    total_evaluation = sum(h.evaluation_value for h in holdings)
    total_profit_loss = sum(h.profit_loss for h in holdings)
    return PortfolioSummary(
        count=len(holdings),
        total_evaluation=total_evaluation,
        total_profit_loss=total_profit_loss,
        total_cost=total_evaluation - total_profit_loss,
    )
