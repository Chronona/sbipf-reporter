使い方
======

基本コマンド
------------

.. code-block:: bash

   sbipf-reporter report <CSVファイル>

例:

.. code-block:: bash

   sbipf-reporter report portfolio.csv

出力フォーマット
----------------

端末表示（デフォルト）:
    rich ライブラリによるカラフルなテーブルをコンソールに表示します。

.. code-block:: bash

   sbipf-reporter report portfolio.csv

Markdown 出力:
    Markdown テーブル形式でファイルに出力します。

.. code-block:: bash

   sbipf-reporter report portfolio.csv --format md --output report.md

出力例::

   # SBI証券ポートフォリオ

   | コード | 銘柄名 | 口座 | 買付日 | 数量 | 取得単価 | 現在値 | 評価額 | 損益 | 損益率 |
   |------|------|------|------|------|------|------|------|------|------|
   | 1234 | サンプル株式会社 | 特定 | 2024/01/15 | 100 | ¥1,000 | ¥1,200 | ¥120,000 | +¥20,000 | +20.00% |

   **合計**: 保有数 1件, 総資産 ¥120,000, 損益 +¥20,000 (+20.00%)

CSV 出力:
    元のCSVに損益率カラムを追加して出力します。

.. code-block:: bash

   sbipf-reporter report portfolio.csv --format csv --output report.csv

バージョン確認
--------------

.. code-block:: bash

   sbipf-reporter version

Python モジュールとして実行
----------------------------

.. code-block:: bash

   python -m sbipf_reporter report portfolio.csv
