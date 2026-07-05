# sbipf-reporter

[![CI](https://github.com/Chronona/sbipf-reporter/actions/workflows/ci.yml/badge.svg)](https://github.com/Chronona/sbipf-reporter/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![PyPI version](https://img.shields.io/pypi/v/sbipf-reporter)](https://pypi.org/project/sbipf-reporter/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

SBI証券のポートフォリオCSVからレポートを生成するCLIツール。

## 機能

- SBI証券CSVのパース（Shift-JIS / UTF-8 自動判別）
- 3形式のレポート出力: ターミナル(rich) / Markdown / CSV
- 11列・10列のCSVフォーマット両対応
- 口座区分（特定・NISA成長・NISAつみたて）の自動分類
- 投資信託にも対応

## インストール

```bash
pip install sbipf-reporter
```

## 使い方

```bash
# ターミナル表示（デフォルト）
sbipf-reporter report path/to/portfolio.csv

# Markdown出力
sbipf-reporter report path/to/portfolio.csv --format md --output portfolio.md

# CSV出力
sbipf-reporter report path/to/portfolio.csv --format csv --output portfolio.csv

# バージョン確認
sbipf-reporter version
```

## 出力例

```
  SBI証券ポートフォリオ
┌──────┬──────────────┬──────────┬──────┬──────────┬──────────┬────────────┬──────────────┬──────────┐
│ コード │ 銘柄名        │ 口座      │ 数量  │ 取得単価   │ 現在値     │ 評価額       │ 損益          │ 損益率     │
├──────┼──────────────┼──────────┼──────┼──────────┼──────────┼────────────┼──────────────┼──────────┤
│ 6758 │ ソニー        │ 特定      │   50 │  ¥9,850 │ ¥10,240 │   ¥512,000 │     ¥+1,950 │  +1.98% │
│ 7203 │ 新日鉄        │ NISA(成長)│  200 │    ¥695 │    ¥742 │   ¥148,400 │     ¥+9,400 │ +13.52% │
│ ...  │              │          │      │          │          │            │              │          │
├──────┴──────────────┴──────────┴──────┴──────────┴──────────┴────────────┴──────────────┴──────────┤
│ 合計: 保有数 16件, 総資産 ¥15,798,700, 損益 +¥563,700 (+3.70%)                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 対応CSVフォーマット

SBI証券のポートフォリオCSVには2種類のフォーマットがあり、自動判別します。

| フォーマット | 列数 | 特徴 |
|---|---|---|
| 11列版 | 11 | 参考単価を含む従来フォーマット |
| 10列版 | 10 | 参考単価なしの新しいフォーマット |

エンコーディングは UTF-8（BOM有無どちらも）・Shift-JIS を自動判別します。

## 開発

```bash
git clone https://github.com/Chronona/sbipf-reporter.git
cd sbipf-reporter
pip install -e ".[dev]"
pytest
```

## 免責事項 / Disclaimer

本ツールは **非公式** であり、株式会社SBI証券とは一切関係がありません。
SBI証券が提供・承認・サポートするものではありません。

This is an **unofficial** third-party tool and is not affiliated with,
endorsed by, or supported by SBI Securities.

## ライセンス

MIT
