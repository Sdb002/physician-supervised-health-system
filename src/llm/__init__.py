"""LLM layer: OCR extraction and report phrasing ONLY.

Nothing in this package makes clinical decisions. OCR output is a prefill the
physician must confirm; report text is a rephrasing of an already-approved
assessment. src/clinical, src/diet, and src/lifestyle never import this package
(enforced by tests/test_llm_isolation.py).
"""
