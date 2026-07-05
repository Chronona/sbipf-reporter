"""SBI証券CSVパーサー."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AccountType(Enum):
    """口座区分."""

    GENBUTSU = "現物"
    NISA_GROWTH = "NISA(成長)"
    NISA_TSUMITATE = "NISA(つみたて)"
    TOKUHU = "特定"
    UNKNOWN = "Unknown"


@dataclass
class Holding:
    """保有金融商品情報."""

    code: str
    name: str
    account_type: AccountType
    buy_date: str
    quantity: int
    average_price: float
    current_price: float
    profit_loss: float
    evaluation_value: float


@dataclass
class ColumnLayout:
    """CSV列レイアウト."""

    col_date: int
    col_quantity: int
    col_average_price: int
    col_current_price: int
    col_profit_loss: int
    col_evaluation_value: int


def _detect_account_type(section_header: str) -> AccountType:
    """セクション見出しから口座区分を検出する."""
    if "現物/特定預り" in section_header or "特定" in section_header:
        return AccountType.TOKUHU
    if "現物/NISA預り(成長投資枠)" in section_header or "成長投資枠" in section_header:
        return AccountType.NISA_GROWTH
    if (
        "現物/NISA預り(つみたて投資枠)" in section_header
        or "つみたて投資枠" in section_header
    ):
        return AccountType.NISA_TSUMITATE
    if "現物" in section_header:
        return AccountType.GENBUTSU
    return AccountType.UNKNOWN


def _detect_layout(header_row: list[str]) -> ColumnLayout:
    """ヘッダー行から列レイアウトを検出する.

    SBI証券CSVには2つのフォーマットが存在する:
    - 11列版: 参考単価, 取得単価, 現在値, ... (古いフォーマット)
    - 10列版: 取得単価, 現在値, ... (新しいフォーマット、参考単価なし)
    """
    headers = [h.strip() for h in header_row]

    # 11列版かどうかを「参考単価」の有無で判定
    has_reference = any("参考単価" in h for h in headers)

    if has_reference:
        return ColumnLayout(
            col_date=1,
            col_quantity=2,
            col_average_price=4,
            col_current_price=5,
            col_profit_loss=8,
            col_evaluation_value=10,
        )
    else:
        # 10列版: 参考単価がなく、取得単価が3列目
        return ColumnLayout(
            col_date=1,
            col_quantity=2,
            col_average_price=3,
            col_current_price=4,
            col_profit_loss=7,
            col_evaluation_value=9,
        )


def parse_sbi_csv(file_path: str | Path) -> list[Holding]:
    """SBI証券CSVファイルをパースして保有銘柄リストを返す.

    Args:
        file_path: CSVファイルのパス

    Returns:
        Holdingのリスト
    """
    holdings: list[Holding] = []

    encodings = ["utf-8-sig", "cp932", "utf-8"]
    for enc in encodings:
        try:
            with open(file_path, encoding=enc) as f:
                rows = list(csv.reader(f))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Failed to decode {file_path} with any of {encodings}")

    current_account_type = AccountType.UNKNOWN
    is_data_section = False
    layout: ColumnLayout | None = None

    for row in rows:
        if not row or len(row) == 0:
            continue

        first_cell = row[0].strip()

        # Skip empty rows
        if not first_cell:
            continue

        # Skip summary/aggregate rows
        if "合計" in first_cell or first_cell in ("評価額", "含み損益", "前日比"):
            is_data_section = False
            continue

        # Detect section header (column names row)
        if "銘柄（コード）" in first_cell or "ファンド名" in first_cell:
            layout = _detect_layout(row)
            is_data_section = True
            continue

        # Detect section boundary by header patterns
        clean_header = first_cell.strip("【】[]")
        if clean_header.startswith("株式（") or clean_header.startswith("投資信託（"):
            current_account_type = _detect_account_type(clean_header)
            is_data_section = False
            continue

        # Parse data rows
        if is_data_section and len(row) >= 10 and layout is not None:
            try:
                # Determine if stock or fund based on code pattern
                code_name = row[0].strip()

                if "," in code_name:
                    code_name = code_name.split(",")[0].strip()

                parts = code_name.split(" ", 1)
                code = parts[0] if parts else ""
                name = parts[1] if len(parts) > 1 else ""

                if (
                    first_cell.startswith("ｅＭＡＸＩＳ")
                    or first_cell.startswith("ｉＦｒｅｅ")
                    or first_cell.startswith("ＳＢＩ・")
                ):
                    code = ""
                    name = first_cell

                holdings.append(
                    Holding(
                        code=code,
                        name=name,
                        account_type=current_account_type,
                        buy_date=row[layout.col_date].strip(),
                        quantity=int(row[layout.col_quantity]),
                        average_price=float(row[layout.col_average_price]),
                        current_price=float(row[layout.col_current_price]),
                        profit_loss=float(row[layout.col_profit_loss]),
                        evaluation_value=float(row[layout.col_evaluation_value]),
                    )
                )
            except (ValueError, IndexError):
                continue

    return holdings
