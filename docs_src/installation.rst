インストール
============

pip（PyPI）
-----------

.. code-block:: bash

   pip install sbipf-reporter

TestPyPI からインストールする場合:

.. code-block:: bash

   pip install --index-url https://test.pypi.org/simple/ sbipf-reporter

uv
--

.. code-block:: bash

   uv pip install sbipf-reporter

ソースから
----------

.. code-block:: bash

   git clone https://github.com/Chronona/sbipf-reporter.git
   cd sbipf-reporter
   pip install .

動作条件
--------

- Python 3.12 以上
- OS: Windows / macOS / Linux
- SBI証券のポートフォリオCSV（Webサイトからダウンロード）
