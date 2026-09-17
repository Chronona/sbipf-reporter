sbipf-reporter
==============

SBI証券のポートフォリオCSVから、わかりやすいレポートを生成するCLIツール。

対応フォーマット: 端末表示（rich テーブル） | Markdown ファイル出力 | CSV ファイル出力

インストール
------------

.. code-block:: bash

   pip install sbipf-reporter

クイックスタート
----------------

.. code-block:: bash

   # ターミナルに表示
   sbipf-reporter report portfolio.csv

   # Markdown ファイルに出力
   sbipf-reporter report portfolio.csv --format md --output report.md

   # バージョン確認
   sbipf-reporter version

詳細ガイド
----------

.. toctree::
   :maxdepth: 2

   installation
   usage
   csv_format

API リファレンス
----------------

.. toctree::
   :maxdepth: 2

   python_api
   modules

開発者向け
----------

.. toctree::
   :maxdepth: 1

   development

設計判断の記録 (ADR)
--------------------

.. toctree::
   :maxdepth: 1

   adr/0001-profit-loss-rate-basis
   adr/0002-csv-structure-detection

----

:ref:`genindex` | :ref:`modindex` | :ref:`search`