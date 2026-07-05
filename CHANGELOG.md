# Changelog

## [Unreleased]

### Documentation
- README.md を充実（バッジ・機能一覧・出力例・対応フォーマット・ライセンスを追加）
- docstring 強化（公開関数すべてに Args/Returns を記載）
- CHANGELOG.md を新規作成

## [0.1.1] - 2026-07-05

### Fixed
- 文字コード自動判別対応（utf-8-sig / cp932 / utf-8 の fallback）
- 【】で囲まれたセクションヘッダーに対応
- 10列CSVフォーマット（参考単価なし）に対応し、列レイアウトを自動検出

### Added
- `__main__.py` 追加（`python -m sbipf_reporter` 対応）
- Conventional Commits による自動バージョンアップ CI ワークフロー

## [0.1.0] - 2026-07-05

### Added
- SBI証券CSVパーサーの実装
- CLIレポート出力機能
- レポート出力形式の拡張（Markdown / CSV対応）
- プロジェクト構成と CI 環境の整備（pytest / ruff / mypy）
