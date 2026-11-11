"""Local lab-report reading: RapidOCR (PaddleOCR's PP-OCR models on ONNX
Runtime, https://github.com/RapidAI/RapidOCR) reads the text on this server,
and a rule-based parser (lab_report.py) picks out the biomarkers.

Nothing leaves the machine and no API key is needed. Like the Claude path in
src.llm.ocr_extract, the result only prefills the intake form: the physician
confirms every value before any clinical rule runs, and src/clinical,
src/diet and src/lifestyle never import this package.
"""
