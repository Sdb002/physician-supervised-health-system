"""Nutrient targets: RDI baseline plus emphasis from findings.

Targets come from data/reference/rdi_values.yaml (cited RDAs). Findings - a
lab value's risk band, or a condition recorded on the patient - map to
emphasized nutrients via src/clinical/rules/deficiency_map.yaml. This module
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

# The reference intakes are for adults; rdi_values.yaml has no younger group.
ADULT_AGE = 19


@lru_cache(maxsize=1)
def _rdi() -> dict:
    return load_yaml(REFERENCE_DIR / "rdi_values.yaml")


@lru_cache(maxsize=1)
def _rules() -> dict:
    return load_yaml(_RULES_DIR / "deficiency_map.yaml")


def rdi_group(sex: str, pregnant: bool, age: int | None = None) -> str:
    """The reference-intake group. Without an age, the 19-50 group."""
    if pregnant:
        return "pregnant"
    prefix = "male" if sex == "male" else "female"
    if age is not None and age > 70:
        return f"{prefix}_over_70"
    if age is not None and age > 50:
        return f"{prefix}_51_70"
    return f"{prefix}_adult"


def findings_from_flags(flags: list[RiskFlag]) -> list[str]:
    found: list[str] = []
    for flag in flags:
        for fragment, finding in _LABEL_FINDINGS.items():
            if fragment in flag.label and finding not in found:
                found.append(finding)
    return found


def finding_nutrients(finding: str, conditions: list[str] | tuple[str, ...] = ()) -> list[str]:
    """The nutrients one finding emphasizes, less any a recorded condition
    rules out (`suppress`: potassium with kidney disease) - nutrient_targets'
    emphasis for that finding alone. Empty for a key that is not a finding."""
    rule = _rules()["findings"].get(finding)
    if rule is None:
        return []
    ruled_out: set[str] = set()
    for condition in conditions:
        ruled_out.update(((_rules().get("suppress") or {}).get(condition) or {}).get("nutrients") or [])
    return [n for n in rule["boost_nutrients"] if n not in ruled_out]


def nutrient_targets(sex: str, pregnant: bool, flags: list[RiskFlag],
                     conditions: list[str] | tuple[str, ...] = (),
                     age: int | None = None) -> dict:
    """RDI targets for the demographic group, plus the findings, the
    nutrients they emphasize and hard limits, with rationales quoted from
    the rules file.

    `conditions` are the patient's condition keys, recorded or derived. A
    recorded condition is a finding in its own right: a patient known to be
    hypertensive gets the hypertension emphasis on a day their pressure
    reads normal. A condition can also rule a nutrient out of the emphasis
    (`suppress` in the rules file), and an emphasized nutrient or a finding
    can carry a caution for the reviewing physician."""
    group = rdi_group(sex, pregnant, age)
    targets = dict(_rdi()["groups"][group])
    limits = dict(_rdi()["limits"])
    rules = _rules()

    findings = findings_from_flags(flags)
    findings += [c for c in conditions if c in rules["findings"] and c not in findings]

    emphasize: list[str] = []
    rationales: dict[str, str] = {}
    patient_rationales: dict[str, dict[str, str]] = {}

    def explain(key: str, rule: dict) -> None:
        rationales[key] = rule["rationale"].strip()
        if rule.get("patient_en"):
            patient_rationales[key] = {
                "en": rule["patient_en"].strip(),
                "bn": (rule.get("patient_bn") or rule["patient_en"]).strip(),
            }

    for finding in findings:
        rule = rules["findings"][finding]
        for nutrient in rule["boost_nutrients"]:
            if nutrient not in emphasize:
                emphasize.append(nutrient)
        explain(finding, rule)

    for condition in conditions:
        rule = (rules.get("suppress") or {}).get(condition)
        if rule is None or not set(rule["nutrients"]) & set(emphasize):
            continue
        emphasize = [n for n in emphasize if n not in rule["nutrients"]]
        explain(condition, rule)

    cautions = [rule["text"].strip() for key, rule in (rules.get("cautions") or {}).items()
                if key in emphasize or key in findings]

    return {
        "group": group,
        "targets": targets,
        "limits": limits,
        "findings": findings,
        "emphasize": emphasize,
        "rationales": rationales,
        "patient_rationales": patient_rationales,
        "cautions": cautions,
    }
