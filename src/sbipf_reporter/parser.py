"""SBI証券CSVパーサー."""

from __future__ import annotations

import csv
import re
import unicodedata
import warnings
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


def _normalize(text: str) -> str:
    """全角/半角のゆれを吸収した比較用の文字列を返す.

    SBI証券のCSVは同じ見出しを全角括弧・半角括弧の両方で出力する.
    実際、見出しが ``株式（現物/特定預り）`` でも合計行は
    ``株式(現物/特定預り)合計`` のように半角で出力される.
    NFKC正規化で括弧の全角/半角を揃えてから比較する.

    Args:
        text: 正規化対象の文字列

    Returns:
        NFKC正規化し、前後の空白を除去した文字列
    """
    return unicodedata.normalize("NFKC", text).strip()


def _to_float(value: str) -> float:
    """CSVのセルを float に変換する.

    SBI証券のCSVは数値を桁区切りカンマ付きで出力することがある
    (例: ``"1,000"``). 素の ``float()`` はこれを解釈できないため、
    NFKC正規化で全角数字・全角記号を吸収したうえで、桁区切りカンマと
    通貨記号を除去してから変換する.

    Args:
        value: CSVのセル文字列

    Returns:
        変換後の値

    Raises:
        ValueError: 数値として解釈できない場合
    """
    normalized = unicodedata.normalize("NFKC", value).strip()
    for char in (",", "\u00a5", "\\", " ", "\u3000"):
        normalized = normalized.replace(char, "")
    return float(normalized)


class AccountType(Enum):
    """SBI証券の口座区分.

    SBI証券のCSV出力に含まれるセクション見出しから自動判別される.
    例: 「株式（現物/特定預り）】【 特定口座】」→ TOKUHU

    Attributes:
        GENBUTSU: 現物口座
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
    def profit_loss_rate(self) -> float:
        if self.evaluation_value == 0:
            return 0.0
        return self.profit_loss / self.evaluation_value * 100


@dataclass
class ColumnLayout:
    """CSV列レイアウト.

    Attributes:
        col_date: 買付日の列インデックス
        col_quantity: 数量の列インデックス
        col_average_price: 取得単価の列インデックス
        col_current_price: 現在値の列インデックス
        col_profit_loss: 損益の列インデックス
        col_evaluation_value: 評価額の列インデックス
        is_fund: 投資信託セクション（列ヘッダーが「ファンド名」）なら True
    """

    col_date: int
    col_quantity: int
    col_average_price: int
    col_current_price: int
    col_profit_loss: int
    col_evaluation_value: int
    is_fund: bool = False


#: セクション見出しの形（例: ``株式(現物/特定預り)`` / ``投資信託(金額/NISA預り(成長投資枠))``）
_SECTION_RE = re.compile(r"^[^()]+\(.+/.+\)$")


def _is_section_header(row: list[str]) -> bool:
    """セクション見出し行かどうかを判定する.

    SBI証券CSVのセクション見出しは「1セルだけが埋まった行」かつ
    ``<資産種別>(<取引区分>/<預り区分>)`` の形をしている.
    資産種別を限定しないので ``外国株式`` や ``債券`` のセクションも検出できる.

    データ行は複数セルが埋まっているため誤検出しない.
    「合計」で終わる行は集計行なので見出しとして扱わない.

    Args:
        row: CSVの1行

    Returns:
        セクション見出し行なら True
    """
    populated = [cell for cell in row if cell.strip()]
    if len(populated) != 1:
        return False
    header = _normalize(populated[0]).strip("【】[]")
    if header.endswith("合計"):
        return False
    return bool(_SECTION_RE.match(header))


def _detect_account_type(section_header: str) -> AccountType:
    """セクション見出しから口座区分を検出する.

    見出しの括弧内、さらに ``/`` 以降の預り区分だけを見て判定する.
    括弧の全角/半角は内部の NFKC 正規化で吸収する.

    Args:
        section_header: セクション見出しの文字列

    Returns:
        判別した AccountType（判別不能なら UNKNOWN）
    """
    header = _normalize(section_header).strip("【】[]")
    match = re.match(r"^[^()]+\((.+)\)$", header)
    inner = match.group(1) if match else header
    # 「取引区分/預り区分」のうち預り区分だけを見る。資産種別や取引区分に
    # 紛らわしい語が含まれていても誤判定しない。
    custody = inner.split("/", 1)[1] if "/" in inner else inner

    # NISA を特定より先に判定する（両方の語を含む見出しでの取り違えを防ぐ）。
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
    """データ列のヘッダー行かどうかを判定する.

    株式セクションは「銘柄（コード）」、投資信託セクションは「ファンド名」で始まる.

    Args:
        row: CSVの1行

    Returns:
        列ヘッダー行なら True
    """
    if not row:
        return False
    first = _normalize(row[0])
    return first == "ファンド名" or first.startswith("銘柄(")


def _is_fund_header(row: list[str]) -> bool:
    """列ヘッダーが投資信託セクションのもの（「ファンド名」）か判定する."""
    return bool(row) and _normalize(row[0]) == "ファンド名"


def _detect_layout(header_row: list[str]) -> ColumnLayout:
    """ヘッダー行から列レイアウトを検出する.

    SBI証券CSVには2つのフォーマットが存在する:
    - 11列版: 参考単価, 取得単価, 現在値, ... (古いフォーマット)
    - 10列版: 取得単価, 現在値, ... (新しいフォーマット、参考単価なし)

    あわせて、列ヘッダーが「ファンド名」か「銘柄（コード）」かで
    投資信託セクションかどうかを判別し is_fund に持たせる.
    """
    headers = [h.strip() for h in header_row]
    is_fund = _is_fund_header(header_row)

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
            is_fund=is_fund,
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
            is_fund=is_fund,
        )


def _split_code_and_name(raw: str, *, is_fund: bool) -> tuple[str, str]:
    """銘柄セルを証券コードと銘柄名に分解する.

    投資信託には証券コードが存在しないため、セル全体を銘柄名として扱う.
    株式は先頭の空白までをコードとみなすが、コードらしくない
    （数字・英大文字のみでない）場合は分割せず、全体を銘柄名とする.
    銘柄名に空白を含むファンドを誤って分割しないための保険.

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

     ヘッダー行の「参考単価」の有無で自動判別する.

     文字コードは utf-8-sig → cp932 → utf-8 の順で自動判定する.

    CSVの構造:
      - 【株式（現物/特定預り）】のようなセクション見出しから口座区分を判別
      - 「銘柄（コード）」または「ファンド名」行をデータ開始位置として検出
        （どちらの見出しかで株式/投資信託を判別する）
      - 「合計」行や集計行はスキップ

    Args:
        file_path: SBI証券CSVファイルのパス

    Returns:
        パース結果の Holding リスト

    データ行の変換に失敗した場合はその行を読み飛ばすが、
    黙って捨てずに UserWarning を送出する. 欠落に気づけないまま
    実際より少ない資産額が表示されるのを防ぐため.
    警告をエラーとして扱いたい場合は warnings.simplefilter("error") を使う.

    Raises:
        RuntimeError: サポートする文字コードでデコードできなかった場合
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

    for lineno, row in enumerate(rows, start=1):
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
        if _is_column_header(row):
            layout = _detect_layout(row)
            is_data_section = True
            continue

        # Detect section boundary.
        # 資産種別を限定せず、「1セルだけが埋まった <資産種別>(<取引区分>/<預り区分>)」
        # の形の行を見出しとみなす。外国株式や債券のセクションも検出できる。
        if _is_section_header(row):
            current_account_type = _detect_account_type(first_cell)
            is_data_section = False
            continue

        # Parse data rows
        if is_data_section and len(row) >= 10 and layout is not None:
            try:
                # 株式か投資信託かは、銘柄名ではなく列ヘッダー
                # （「銘柄（コード）」/「ファンド名」）から判別する。
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
