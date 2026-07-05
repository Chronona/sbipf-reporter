Python API
==========

sbipf-reporter は CLI ツールですが、Python コードから直接利用することもできます。

基本的な使い方
--------------

.. code-block:: python

   from sbipf_reporter import parse_sbi_csv, output_report, OutputFormat

   # CSV をパース
   holdings = parse_sbi_csv("portfolio.csv")

   # ターミナルに表示
   output_report(holdings, OutputFormat.TERMINAL)

   # Markdown ファイルに出力
   output_report(holdings, OutputFormat.MD, "report.md")

   # CSV ファイルに出力
   output_report(holdings, OutputFormat.CSV, "report.csv")

データ構造にアクセス
--------------------

.. code-block:: python

   from sbipf_reporter import parse_sbi_csv, AccountType

   holdings = parse_sbi_csv("portfolio.csv")

   for h in holdings:
       print(f"{h.name} ({h.code or '投信'})")
       print(f"  口座: {h.account_type.value}")
       print(f"  数量: {h.quantity:,}")
       print(f"  取得単価: ¥{h.average_price:,.0f}")
       print(f"  現在値: ¥{h.current_price:,.0f}")
       print(f"  評価額: ¥{h.evaluation_value:,.0f}")
       print(f"  損益: ¥{h.profit_loss:+,.0f}")
       print()

口座区分でフィルタ
------------------

.. code-block:: python

   from sbipf_reporter import parse_sbi_csv, AccountType, output_report, OutputFormat

   holdings = parse_sbi_csv("portfolio.csv")

   # NISA口座のみ抽出
   nisa = [
       h for h in holdings
       if h.account_type in (AccountType.NISA_GROWTH, AccountType.NISA_TSUMITATE)
   ]

   output_report(nisa, OutputFormat.TERMINAL)

API リファレンス
----------------

詳細は :ref:`modindex` を参照してください。
