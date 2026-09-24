"""Nutrient targets: RDI baseline plus lab-driven emphasis.

Targets come from data/reference/rdi_values.yaml (cited RDAs). Risk flags map
to emphasized nutrients via src/clinical/rules/deficiency_map.yaml. This module
never invents numbers — it only selects from the reference files.
"""

from functools import lru_cache
from pathlib import Path

from src.clinical.risk_scoring import RiskFlag
from src.core.config import REFERENCE_DIR, load_yaml

_RULES_DIR = Path(__file__).resolve().parent / "rules"

# risk-band label fragments → finding keys in deficiency_map.yaml
_LABEL_FINDINGS = {
    "anemia": "anemia",
    "hypertension": "hypertension",
    "prediabetes": "diabetes",
    "diabetes_range": "diabetes",
}


@lru_cache(maxsize=1)
def _rdi() -> dict:
    return load_yaml(REFERENCE_DIR / "rdi_values.yaml")


@lru_cache(maxsize=1)
def _deficiency_map() -> dict:
    return load_yaml(_RULES_DIR / "deficiency_map.yaml")["findings"]


def rdi_group(sex: str, pregnant: bool) -> str:
    if pregnant:
        return "pregnant"
    return "male_adult" if sex == "male" else "female_adult"


def findings_from_flags(flags: list[RiskFlag]) -> list[str]:
    found: list[str] = []
    for flag in flags:
        for fragment, finding in _LABEL_FINDINGS.items():
            if fragment in flag.label and finding not in found:
                found.append(finding)
    return found


def nutrient_targets(sex: str, pregnant: bool, flags: list[RiskFlag]) -> dict:
    """RDI targets for the demographic group, plus emphasized nutrients and
    hard limits, with rationales quoted from the rules file."""
    group = rdi_group(sex, pregnant)
    targets = dict(_rdi()["groups"][group])
    limits = dict(_rdi()["limits"])

    emphasize: list[str] = []
    rationales: dict[str, str] = {}
    for finding in findings_from_flags(flags):
        rule = _deficiency_map()[finding]
        for nutrient in rule["boost_nutrients"]:
            if nutrient not in emphasize:
                emphasize.append(nutrient)
        rationales[finding] = rule["rationale"].strip()

    return {
        "group": group,
        "targets": targets,
        "limits": limits,
        "emphasize": emphasize,
        "rationales": rationales,
    }
