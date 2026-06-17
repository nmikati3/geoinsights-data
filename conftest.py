"""Ensures the repository root is importable as a namespace package during tests.

This project intentionally has no ``__init__.py`` files (PEP 420 namespace
packages). Placing an (empty-purpose) conftest at the repo root makes pytest
add the root to ``sys.path`` so ``import geoinsights_data...`` resolves.
"""
