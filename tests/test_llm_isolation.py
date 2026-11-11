"""AST check: the deterministic packages never import src.llm.

This is the architectural guarantee that no clinical decision can depend on
LLM output. Applies to src/clinical, src/diet, and src/lifestyle.
"""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
ISOLATED_PACKAGES = ("clinical", "diet", "lifestyle")
FORBIDDEN_PREFIX = "src.llm"


def _imports_in(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def scan_for_llm_imports(base: Path, packages=ISOLATED_PACKAGES) -> list[str]:
    offenders = []
    for package in packages:
        for py_file in sorted((base / package).rglob("*.py")):
            for module in _imports_in(py_file):
                if module == FORBIDDEN_PREFIX or module.startswith(FORBIDDEN_PREFIX + "."):
                    offenders.append(f"{py_file.relative_to(base)} imports {module}")
    return offenders


def test_deterministic_packages_never_import_llm():
    offenders = scan_for_llm_imports(SRC)
    assert offenders == [], "LLM isolation violated:\n" + "\n".join(offenders)


def test_scanner_catches_planted_import(tmp_path):
    """The scanner itself must detect a violation, not silently pass."""
    pkg = tmp_path / "clinical"
    pkg.mkdir()
    (pkg / "bad.py").write_text("from src.llm.client import get_client\n", encoding="utf-8")
    (pkg / "worse.py").write_text("import src.llm\n", encoding="utf-8")
    (pkg / "fine.py").write_text("import math\n", encoding="utf-8")
    offenders = scan_for_llm_imports(tmp_path, packages=("clinical",))
    assert len(offenders) == 2


def test_deterministic_packages_never_import_the_ocr_reader():
    """Lab-slip OCR (src/ocr) only prefills the intake form for the physician
    to confirm; no clinical rule may read its output directly."""
    offenders = []
    for package in ISOLATED_PACKAGES:
        for py_file in sorted((SRC / package).rglob("*.py")):
            offenders += [f"{py_file.relative_to(SRC)} imports {module}"
                          for module in _imports_in(py_file)
                          if module == "src.ocr" or module.startswith("src.ocr.")]
    assert offenders == [], "OCR isolation violated:\n" + "\n".join(offenders)
