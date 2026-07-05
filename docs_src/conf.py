"""Sphinx configuration."""

import os
import sys

suppress_warnings = ["ref.duplicate"]

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import sbipf_reporter

project = "sbipf-reporter"
author = "Chronona"
release = sbipf_reporter.__version__
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


napoleon_google_docstring = True
napoleon_numpy_docstring = False
autodoc_member_order = "bysource"
