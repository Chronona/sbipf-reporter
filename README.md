# sbipf-reporter

SBI証券のポートフォリオCSVからレポートを生成するCLIツール。

## インストール

```bash
pip install git+https://github.com/Chronona/sbipf-reporter.git
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

## 開発

```bash
git clone https://github.com/Chronona/sbipf-reporter.git
cd sbipf-reporter
pip install -e ".[dev]"
pytest
```
