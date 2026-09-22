# ADR (Architecture Decision Records)

設計上の決定とその背景を記録します。

| ADR | 内容 |
| --- | --- |
| [0001](0001-profit-loss-rate-basis.rst) | 損益率の分母を取得金額に統一する |
| [0002](0002-unify-portfolio-summary.rst) | ポートフォリオ合計の算出を単一モジュールに一本化する |

## GitHub Pages に載せない理由

GitHub Pages（https://chronona.github.io/sbipf-reporter/）は**利用者向けの利用マニュアル**です。
ADR は開発の経緯を残すための記録であり、ツールの使い方を知りたい利用者には不要なので、
Sphinx のソースディレクトリ（`docs_src/`）ではなくここに置いています。

`docs_src/` に置くと Pages にデプロイされてしまうため、ADR を追加する際は
このディレクトリに置いてください。
