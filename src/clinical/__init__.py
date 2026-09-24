"""Deterministic clinical core.

Every module in this package is pure rule-based computation with cited
thresholds. Nothing here may import from src.llm — enforced by
tests/test_llm_isolation.py.
"""
