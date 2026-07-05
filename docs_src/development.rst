開発ガイド
==========

セットアップ
------------

.. code-block:: bash

   git clone https://github.com/Chronona/sbipf-reporter.git
   cd sbipf-reporter
   pip install -e ".[dev]"

または uv を使用:

.. code-block:: bash

   uv sync --dev

プロジェクト構造
----------------

::

   sbipf-reporter/
   ├── src/sbipf_reporter/
   │   ├── __init__.py       # パッケージ定義
   │   ├── __main__.py       # python -m 対応
   │   ├── cli.py            # Typer CLI
   │   ├── parser.py         # CSV パーサー
   │   ├── reporter.py       # レポート出力
   │   └── formatter.py      # rich テーブル
   ├── tests/
   │   ├── test_parser.py
   │   ├── test_reporter.py
   │   └── fixtures/
   ├── docs_src/             # Sphinx ドキュメントソース
   ├── scripts/
   │   └── bump_version.py   # バージョン管理
   └── pyproject.toml

テスト
------

.. code-block:: bash

   pytest

Lint
----

.. code-block:: bash

   ruff check src/

型チェック
----------

.. code-block:: bash

   mypy src/

ドキュメントビルド
------------------

.. code-block:: bash

   sphinx-build -b html docs_src docs

バージョン管理
--------------

バージョンは pyproject.toml と __init__.py で管理します。
以下のスクリプトで更新できます:

.. code-block:: bash

   python scripts/bump_version.py --set X.Y.Z

CI/CD
-----

main ブランチに push すると自動で:

- テスト / ruff / mypy の実行
- TestPyPI への公開
- GitHub Pages へのドキュメントデプロイ

v* タグを push すると本番 PyPI にも公開されます。
