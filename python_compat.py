#!/usr/bin/env python3
"""
Python 3.13+ compatibility module for the match list change detector.

This module provides compatibility fixes for Python 3.13+ import issues
that cause KeyError exceptions during module imports.
"""

import importlib
import sys
from typing import Any


def ensure_module_available(module_name: str) -> None:
    """
    Ensure a module is available in sys.modules.

    Args:
        module_name: Name of the module to ensure is available
    """
    if module_name not in sys.modules:
        try:
            module = importlib.import_module(module_name)
            sys.modules[module_name] = module
        except ImportError:
            # If we can't import it, create a placeholder
            pass


def fix_python_313_imports() -> None:
    """
    Apply compatibility fixes for Python 3.13+ import issues.

    This function should be called before importing modules that have
    known compatibility issues with Python 3.13+.
    """
    # List of modules that commonly cause KeyError issues in Python 3.13+
    problematic_modules = [
        "http",
        "http.server",
        "http.client",
        "http.cookies",
        "http.cookiejar",
        "logging",
        "logging.handlers",
        "_compat_pickle",
        "pickle",
        "urllib",
        "urllib.parse",
        "urllib.request",
        "urllib.error",
    ]

    # Ensure all problematic modules are available
    for module_name in problematic_modules:
        ensure_module_available(module_name)

    # Special handling for specific modules
    try:
        import http

        if "http" not in sys.modules:
            sys.modules["http"] = http

        import http.client
        import http.cookiejar
        import http.cookies
        import http.server
    except (ImportError, KeyError):
        pass

    try:
        import logging

        if "logging" not in sys.modules:
            sys.modules["logging"] = logging

        import logging.handlers
    except (ImportError, KeyError):
        pass

    try:
        import pickle  # nosec

        if "pickle" not in sys.modules:
            sys.modules["pickle"] = pickle

        # Try to import _compat_pickle if it exists
        try:
            import _compat_pickle

            if "_compat_pickle" not in sys.modules:
                sys.modules["_compat_pickle"] = _compat_pickle
        except ImportError:
            pass
    except (ImportError, KeyError):
        pass


def safe_import(module_name: str, fallback: Any = None) -> Any:
    """
    Safely import a module with fallback handling.

    Args:
        module_name: Name of the module to import
        fallback: Fallback value if import fails

    Returns:
        The imported module or fallback value
    """
    try:
        fix_python_313_imports()
        return importlib.import_module(module_name)
    except (ImportError, KeyError) as e:
        print(f"Warning: Failed to import {module_name}: {e}")
        return fallback


# Apply fixes immediately when this module is imported
fix_python_313_imports()
