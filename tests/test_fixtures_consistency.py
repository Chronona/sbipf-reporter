"""フィクスチャが内部整合していることを検証する.

sbi_sample 系のフィクスチャは README の出力例の元データでもあるため、
明細・セクション合計・総合計が互いに矛盾しないことを保証する.

適用している規約:
  株式  評価額 = 数量 × 現在値 / 取得金額 = 数量 × 取得単価
  投信  評価額 = 数量 × 現在値 / 10000 / 取得金額 = 数量 × 取得単価 / 10000
        （基準価額は1万口あたりで表示されるため）
  共通  損益 = 評価額 - 取得金額
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

FUND_UNIT = 10000
SAMPLE_FIXTURES = [
    "sbi_sample.csv",
    "sbi_enclosed_headers.csv",
    "sbi_square_brackets.csv",
]

#: 明細の整合性を検証する全フィクスチャ（列数は自動判別する）
ALL_FIXTURES = sorted(p.name for p in Path("tests/fixtures").glob("*.csv"))


def _rows(fixture: str) -> list[list[str]]:
    return list(csv.reader((Path("tests/fixtures") / fixture).open(encoding="utf-8")))


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


@pytest.mark.parametrize("fixture", SAMPLE_FIXTURES)
def test_rows_are_internally_consistent(fixture: str) -> None:
    """各明細行で 評価額 = 数量 × 現在値、損益 = 評価額 - 取得金額 が成り立つ."""
    is_fund = False
    checked = 0

    for row in _rows(fixture):
        if not row:
            continue
        first = row[0].strip()
        if first in ("銘柄（コード）", "ファンド名"):
            is_fund = first == "ファンド名"
            continue
        if len(row) < 11 or not row[2].strip().isdigit():
            continue

        quantity = int(row[2])
        average_price = float(row[4])
        current_price = float(row[5])
        profit_loss = float(row[8])
        evaluation_value = float(row[10])

        unit = FUND_UNIT if is_fund else 1
        assert evaluation_value == pytest.approx(quantity * current_price / unit), first
        assert profit_loss == pytest.approx(
            (current_price - average_price) * quantity / unit
        ), first
        checked += 1

    assert checked == 16, f"{fixture}: 検証した明細が16件ではない"


@pytest.mark.parametrize("fixture", SAMPLE_FIXTURES)
def test_aggregate_rows_match_their_details(fixture: str) -> None:
    """セクション合計と総合計が、対応する明細の合計と一致する."""
    is_fund = False
    section = {"ev": 0.0, "pl": 0.0}
    total = {"ev": 0.0, "pl": 0.0}
    snapshot: dict[str, float] | None = None
    verified = 0

    for row in _rows(fixture):
        if not row:
            continue
        first = row[0].strip()

        if first in ("銘柄（コード）", "ファンド名"):
            is_fund = first == "ファンド名"
            continue

        if snapshot is not None and _is_number(first):
            assert float(first) == pytest.approx(snapshot["ev"]), f"{fixture}: 評価額の合計"
            assert float(row[1]) == pytest.approx(snapshot["pl"]), f"{fixture}: 損益の合計"
            snapshot = None
            verified += 1
            continue

        if "合計" in first:
            snapshot = dict(total) if first == "総合計" else dict(section)
            section = {"ev": 0.0, "pl": 0.0}
            continue

        if len(row) >= 11 and row[2].strip().isdigit():
            unit = FUND_UNIT if is_fund else 1
            evaluation_value = int(row[2]) * float(row[5]) / unit
            profit_loss = float(row[8])
            for acc in (section, total):
                acc["ev"] += evaluation_value
                acc["pl"] += profit_loss

    # セクション合計5件 + 総合計1件
    assert verified == 6, f"{fixture}: 検証した集計行が6件ではない"


@pytest.mark.parametrize("fixture", SAMPLE_FIXTURES)
def test_sample_fixtures_hold_identical_data(fixture: str) -> None:
    """3つのフィクスチャは見出しの括弧だけが違い、数値は同一である."""
    def numbers(name: str) -> list[str]:
        return [c for row in _rows(name) for c in row if _is_number(c)]

    assert numbers(fixture) == numbers("sbi_sample.csv")


def _number(value: str) -> float:
    """桁区切りカンマを許容して数値に変換する."""
    return float(value.replace(",", ""))


@pytest.mark.parametrize("fixture", ALL_FIXTURES)
def test_every_fixture_row_is_internally_consistent(fixture: str) -> None:
    """全フィクスチャの明細行で 評価額・損益 が数量と単価から導ける.

    11列版（参考単価あり）と10列版を列ヘッダーから判別する.
    """
    is_fund = False
    has_reference = True
    checked = 0

    for row in _rows(fixture):
        if not row:
            continue
        first = row[0].strip()

        if first in ("銘柄（コード）", "ファンド名"):
            is_fund = first == "ファンド名"
            has_reference = any("参考単価" in c for c in row)
            continue

        populated = [c for c in row if c != ""]
        if len(populated) < 10 or not row[2].strip().replace(",", "").isdigit():
            continue

        if has_reference:
            average_price, current_price = _number(row[4]), _number(row[5])
            profit_loss, evaluation_value = _number(row[8]), _number(row[10])
        else:
            average_price, current_price = _number(row[3]), _number(row[4])
            profit_loss, evaluation_value = _number(row[7]), _number(row[9])

        quantity = int(_number(row[2]))
        unit = FUND_UNIT if is_fund else 1

        assert evaluation_value == pytest.approx(quantity * current_price / unit), (
            f"{fixture}: {first}: 評価額"
        )
        assert profit_loss == pytest.approx(
            (current_price - average_price) * quantity / unit
        ), f"{fixture}: {first}: 損益"
        checked += 1

    assert checked > 0, f"{fixture}: 明細行が1件も検証されなかった"
