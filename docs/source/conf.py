# Configuration file for the Sphinx documentation builder.
"""
Sphinx configuration file for the Match List Change Detector documentation.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# Add module path for autodoc
import os
import sys
from typing import List
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath("../.."))


class Mock(MagicMock):
    """Mock class for external modules."""

    @classmethod
    def __getattr__(cls, name):
        """Return a MagicMock for any attribute."""
        return MagicMock()


MOCK_MODULES = ["fogis_api_client"]
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Match List Change Detector"
copyright = "2025, Match List Change Detector Team"
author = "Match List Change Detector Team"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

templates_path: List[str] = ["_templates"]
exclude_patterns: List[str] = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path: List[str] = ["_static"]
