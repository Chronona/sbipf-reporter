"""SBI証券CSVパーサー."""

from __future__ import annotations

import csv
import re
import unicodedata
import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

#: パース時に試行する文字コード（順に試す）
ENCODINGS = ("utf-8-sig", "cp932", "utf-8")

#: セクション見出しの形（例: ``株式(現物/特定預り)`` / ``投資信託(金額/NISA預り(成長投資枠))``）
_SECTION_RE = re.compile(r"^[^()]+\(.+/.+\)$")

#: 集計ブロックの先頭に現れるラベル
_AGGREGATE_LABELS = frozenset({"評価額", "含み損益", "前日比", "含み損益(%)", "前日比(%)"})

#: 数値として扱えないプレースホルダー（SBI証券CSVは未確定値を ``--`` で出力する）
_PLACEHOLDERS = frozenset({"", "-", "--", "---", "----"})


def _normalize(text: str) -> str:
    """全角/半角ゆれを吸収した比較用の文字列を返す.

    SBI証券のCSVは同じ見出しを全角括弧・半角括弧の両方で出力するため
    (例: 見出しは ``株式（現物/特定預り）`` だが合計行は ``株式(現物/特定預り)合計``)、
    NFKC 正規化と空白除去を行ってから比較する.

    Args:
        text: 正規化対象の文字列

    Returns:
        NFKC正規化し、空白を除去した文字列
    """
    return unicodedata.normalize("NFKC", text).replace(" ", "").replace("　", "").strip()


def _to_float(value: str) -> float:
    """CSVのセルを float に変換する.

    桁区切りカンマ・通貨記号・全角数字・符号付き表記を許容する.

    Args:
        value: CSVのセル文字列

    Returns:
        変換後の値

    Raises:
        ValueError: 数値として解釈できない場合
    """
    normalized = _normalize(value).replace(",", "").replace("¥", "").replace("\\", "")
    if normalized in _PLACEHOLDERS:
        raise ValueError(f"not a number: {value!r}")
    return float(normalized)


class AccountType(Enum):
    """SBI証券の口座区分.

    SBI証券のCSV出力に含まれるセクション見出しから自動判別される.
    見出しの ``/`` 以降（預り区分）だけを見て判定するため、
    ``株式（現物/特定預り）`` でも ``外国株式（現物/特定預り）`` でも同じ結果になる.

    Attributes:
        GENBUTSU: 現物（一般預りなど、特定でもNISAでもないもの）
        NISA_GROWTH: NISA成長投資枠
        NISA_TSUMITATE: NISAつみたて投資枠
        TOKUHU: 特定口座
        UNKNOWN: 判別不能
    """

    GENBUTSU = "現物"
    NISA_GROWTH = "NISA(成長)"
    NISA_TSUMITATE = "NISA(つみたて)"
    TOKUHU = "特定"
    UNKNOWN = "Unknown"


@dataclass
class Holding:
    """SBI証券CSVの1行分の保有金融商品情報を表すデータクラス.

    parse_sbi_csv() の戻り値としてリスト形式で返される.
    各フィールドはCSVの列から抽出され、数値は float/int に変換済み.

    Attributes:
        code: 証券コード（投資信託の場合は空文字）
        name: 銘柄名
        account_type: 口座区分（AccountType Enum）
        buy_date: 買付日（文字列、CSVの値そのまま）
        quantity: 保有数量
        average_price: 取得単価（円）
        current_price: 現在値（円）
        profit_loss: 損益額（円、負数は損失）
        evaluation_value: 評価額（円）
    """

    code: str
    name: str
    account_type: AccountType
    buy_date: str
    quantity: int
    average_price: float
    current_price: float
    profit_loss: float
    evaluation_value: float

    @property
    def acquisition_cost(self) -> float:
        """取得金額（円）.

        評価額から損益を差し引いて求める. 取得単価 × 数量 ではなく
        CSVが出力した評価額・損益から導出するため、CSV内で完結して整合する.
        """
        return self.evaluation_value - self.profit_loss

    @property
    def profit_loss_rate(self) -> float:
        """損益率（％）.

        取得金額を分母とする（損益 ÷ 取得金額 × 100）.
        ポートフォリオ全体の損益率と同じ基準なので、行と合計で定義が食い違わない.
        取得金額が 0 の場合は 0.0 を返す.
        """
        cost = self.acquisition_cost
        if cost == 0:
            return 0.0
        return self.profit_loss / cost * 100


@dataclass
class ColumnLayout:
    """CSV列レイアウト.

    ヘッダー行の列名から解決される. 列名で解決できなかった場合のみ
    「参考単価」の有無による位置ベースの推定にフォールバックする.

    Attributes:
        col_date: 買付日の列インデックス
        col_quantity: 数量の列インデックス
        col_average_price: 取得単価の列インデックス
        col_current_price: 現在値の列インデックス
        col_profit_loss: 損益の列インデックス
        col_evaluation_value: 評価額の列インデックス
        is_fund: 投資信託セクション（ヘッダーが「ファンド名」）なら True
    """

    col_date: int
    col_quantity: int
    col_average_price: int
    col_current_price: int
    col_profit_loss: int
    col_evaluation_value: int
    is_fund: bool = False


#: 正規化済みヘッダー名 -> ColumnLayout のフィールド名
_HEADER_TO_FIELD = {
    "買付日": "col_date",
    "数量": "col_quantity",
    "取得単価": "col_average_price",
    "現在値": "col_current_price",
    "損益": "col_profit_loss",
    "評価額": "col_evaluation_value",
}

#: 11列版（参考単価あり）の位置ベースフォールバック
_LAYOUT_WITH_REFERENCE = ColumnLayout(1, 2, 4, 5, 8, 10)

#: 10列版（参考単価なし）の位置ベースフォールバック
_LAYOUT_WITHOUT_REFERENCE = ColumnLayout(1, 2, 3, 4, 7, 9)


def _is_section_header(row: list[str]) -> bool:
    """セクション見出し行かどうかを判定する.

    SBI証券CSVのセクション見出しは「1セルだけが埋まった行」かつ
    ``<資産種別>（<取引区分>/<預り区分>）`` の形をしている.
    資産種別を限定しないので ``外国株式`` や ``債券`` のセクションも検出できる.

    Args:
        row: CSVの1行

    Returns:
        セクション見出し行なら True
    """
    populated = [c for c in row if c.strip()]
    if len(populated) != 1:
        return False
    header = _normalize(populated[0]).strip("【】[]")
    if header.endswith("合計"):
        return False
    return bool(_SECTION_RE.match(header))


def _detect_account_type(section_header: str) -> AccountType:
    """セクション見出しから口座区分を検出する.

    見出しの括弧内、さらに ``/`` 以降の預り区分だけを見て判定する.
    NISA を特定より先に判定するため、両方の語を含む見出しでも誤判定しない.

    Args:
        section_header: セクション見出しの文字列

    Returns:
        判別した AccountType（判別不能なら UNKNOWN）
    """
    header = _normalize(section_header).strip("【】[]")
    match = re.match(r"^[^()]+\((.+)\)$", header)
    inner = match.group(1) if match else header
    custody = inner.split("/", 1)[1] if "/" in inner else inner

    if "つみたて投資枠" in custody:
        return AccountType.NISA_TSUMITATE
    if "成長投資枠" in custody:
        return AccountType.NISA_GROWTH
    if "特定" in custody:
        return AccountType.TOKUHU
    if "NISA" in custody or "一般" in custody or "現物" in custody:
        return AccountType.GENBUTSU
    return AccountType.UNKNOWN


def _is_column_header(row: list[str]) -> bool:
    """データ列のヘッダー行（「銘柄（コード）」/「ファンド名」で始まる行）か判定する."""
    if not row:
        return False
    first = _normalize(row[0])
    return first == "ファンド名" or first.startswith("銘柄(")


def _detect_layout(header_row: list[str]) -> ColumnLayout:
    """ヘッダー行から列レイアウトを検出する.

    まず列名（買付日 / 数量 / 取得単価 / 現在値 / 損益 / 評価額）で
    インデックスを解決する. 「損益」と「損益（％）」は正規化後の完全一致で
    区別するため取り違えない.

    列名で解決できなかった場合は、従来どおり「参考単価」の有無で
    11列版 / 10列版の位置を推定する.

    Args:
        header_row: ヘッダー行

    Returns:
        検出した ColumnLayout
    """
    is_fund = bool(header_row) and _normalize(header_row[0]) == "ファンド名"

    indices: dict[str, int] = {}
    for i, cell in enumerate(header_row):
        field = _HEADER_TO_FIELD.get(_normalize(cell))
        if field is not None and field not in indices:
            indices[field] = i

    if len(indices) == len(_HEADER_TO_FIELD):
        return ColumnLayout(is_fund=is_fund, **indices)

    has_reference = any("参考単価" in _normalize(h) for h in header_row)
    fallback = _LAYOUT_WITH_REFERENCE if has_reference else _LAYOUT_WITHOUT_REFERENCE
    return ColumnLayout(
        col_date=fallback.col_date,
        col_quantity=fallback.col_quantity,
        col_average_price=fallback.col_average_price,
        col_current_price=fallback.col_current_price,
        col_profit_loss=fallback.col_profit_loss,
        col_evaluation_value=fallback.col_evaluation_value,
        is_fund=is_fund,
    )


def _split_code_and_name(raw: str, *, is_fund: bool) -> tuple[str, str]:
    """銘柄セルを証券コードと銘柄名に分解する.

    投資信託セクション（ヘッダーが「ファンド名」）では証券コードが存在しないため、
    セル全体を銘柄名として扱う. 株式セクションでは先頭の空白までをコードとみなすが、
    コードらしくない（数字・英大文字のみでない）場合は分割しない.

    Args:
        raw: 銘柄セルの文字列
        is_fund: 投資信託セクションなら True

    Returns:
        (証券コード, 銘柄名) のタプル
    """
    raw = raw.strip()
    if is_fund:
        return "", raw

    head, sep, tail = raw.partition(" ")
    if not sep or not re.fullmatch(r"[0-9A-Z]{3,8}", head):
        return "", raw
    return head, tail.strip()


def parse_sbi_csv(file_path: str | Path) -> list[Holding]:
    """SBI証券のポートフォリオCSVをパースし、保有銘柄リストを返す.

     対応するCSVフォーマット:

       - 11列版（参考単価あり）: 古いフォーマット
       - 10列版（参考単価なし）: 新しいフォーマット

     列はヘッダー行の列名から解決する（解決できない場合のみ
     「参考単価」の有無による位置推定にフォールバックする）.

     文字コードは utf-8-sig → cp932 → utf-8 の順で自動判定する.

    CSVの構造:
      - 【株式（現物/特定預り）】のようなセクション見出しから口座区分を判別
      - 「銘柄（コード）」または「ファンド名」行をデータ開始位置として検出
      - 「合計」行や集計行はスキップ

    データ行の変換に失敗した場合はその行を読み飛ばすが、
    黙って捨てずに UserWarning を送出する.

    Args:
        file_path: SBI証券CSVファイルのパス

    Returns:
        パース結果の Holding リスト

    Raises:
        RuntimeError: サポートする文字コードでデコードできなかった場合
    """
    holdings: list[Holding] = []

    for enc in ENCODINGS:
        try:
            with open(file_path, encoding=enc, newline="") as f:
                rows = list(csv.reader(f))
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError(f"Failed to decode {file_path} with any of {list(ENCODINGS)}")

    current_account_type = AccountType.UNKNOWN
    is_data_section = False
    layout: ColumnLayout | None = None

    for lineno, row in enumerate(rows, start=1):
        if not row or not any(cell.strip() for cell in row):
            continue

        first_cell = row[0].strip()
        normalized_first = _normalize(first_cell)

        # Section header (e.g. 【株式（現物/特定預り）】) — must be checked before
        # the data-header / aggregate checks so that unknown asset classes still reset state.
        if _is_section_header(row):
            current_account_type = _detect_account_type(first_cell)
            is_data_section = False
            layout = None
            continue

        # Column header row — marks the start of a data section
        if _is_column_header(row):
            layout = _detect_layout(row)
            is_data_section = True
            continue

        # Summary / aggregate rows
        if normalized_first.endswith("合計") or normalized_first in _AGGREGATE_LABELS:
            is_data_section = False
            layout = None
            continue

        if not is_data_section or layout is None:
            continue

        try:
            code, name = _split_code_and_name(row[0], is_fund=layout.is_fund)
            holdings.append(
                Holding(
                    code=code,
                    name=name,
                    account_type=current_account_type,
                    buy_date=row[layout.col_date].strip(),
                    quantity=int(_to_float(row[layout.col_quantity])),
                    average_price=_to_float(row[layout.col_average_price]),
                    current_price=_to_float(row[layout.col_current_price]),
                    profit_loss=_to_float(row[layout.col_profit_loss]),
                    evaluation_value=_to_float(row[layout.col_evaluation_value]),
                )
            )
        except (ValueError, IndexError) as exc:
            warnings.warn(
                f"{file_path}:{lineno}: データ行をパースできなかったためスキップしました "
                f"({exc}): {first_cell!r}",
                UserWarning,
                stacklevel=2,
            )
            continue

    return holdings
