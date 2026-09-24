"""Biomarker risk scoring against cited reference bands.

All thresholds live in data/reference/biomarker_ranges.yaml — this module only
mechanically applies them. Band semantics: half-open [min, max); missing min or
max means unbounded on that side.
"""

from dataclasses import dataclass
from functools import lru_cache

from src.core.config import REFERENCE_DIR, load_yaml

RISK_ORDER = {"none": 0, "low": 1, "moderate": 2, "high": 3, "critical": 4}

# risk-band labels → condition keys in contraindications.yaml
_LABEL_CONDITIONS = {
    "prediabetes": "diabetes",
    "diabetes_range": "diabetes",
    "hypertension_stage1": "hypertension",
    "hypertension_stage2": "hypertension",
    "hypertensive_crisis": "hypertension",
    "mild_anemia": "anemia",
    "moderate_anemia": "anemia",
    "severe_anemia": "anemia",
}


@dataclass(frozen=True)
class RiskFlag:
    biomarker: str
    value: float
    unit: str
    label: str
    risk: str

    def as_dict(self) -> dict:
        return {
            "biomarker": self.biomarker,
            "value": self.value,
            "unit": self.unit,
            "label": self.label,
            "risk": self.risk,
        }


@lru_cache(maxsize=1)
def _ranges() -> dict:
    return load_yaml(REFERENCE_DIR / "biomarker_ranges.yaml")["biomarkers"]


def _match_band(bands: list[dict], value: float) -> dict:
    for band in bands:
        lo = band.get("min", float("-inf"))
        hi = band.get("max", float("inf"))
        if lo <= value < hi:
            return band
    raise ValueError(f"no band matches value {value}")


def hemoglobin_group(sex: str, pregnant: bool) -> str:
    if pregnant:
        return "pregnant"
    return "male_adult" if sex == "male" else "female_adult"


def score_biomarker(name: str, value: float, sex: str = "female", pregnant: bool = False) -> RiskFlag:
    spec = _ranges()[name]
    bands = spec["groups"][hemoglobin_group(sex, pregnant)] if "groups" in spec else spec["bands"]
    band = _match_band(bands, value)
    return RiskFlag(name, value, spec["unit"], band["label"], band["risk"])


def score_biomarkers(biomarkers: dict, sex: str, pregnant: bool = False) -> list[RiskFlag]:
    """Score every known biomarker present in the dict; unknown keys are ignored."""
    flags = []
    for name, value in biomarkers.items():
        if name in _ranges() and value is not None:
            flags.append(score_biomarker(name, float(value), sex, pregnant))
    return flags


def bp_category(flags: list[RiskFlag]) -> str | None:
    """Overall BP category = the more severe of systolic/diastolic (ACC/AHA 'or')."""
    bp = [f for f in flags if f.biomarker in ("systolic_bp", "diastolic_bp")]
    if not bp:
        return None
    worst = max(bp, key=lambda f: RISK_ORDER[f.risk])
    return worst.label


def derive_conditions(flags: list[RiskFlag]) -> list[str]:
    """Condition keys implied by risk bands, for the contraindication gate.

    Note: 'prediabetes' maps to the 'diabetes' rule (added-sugar exclusion applies
    to impaired fasting glucose as well); the distinct band label is preserved on
    the flag itself.
    """
    found: list[str] = []
    for f in flags:
        cond = _LABEL_CONDITIONS.get(f.label)
        if cond and cond not in found:
            found.append(cond)
    return found


def overall_risk(flags: list[RiskFlag]) -> str:
    if not flags:
        return "none"
    return max((f.risk for f in flags), key=lambda r: RISK_ORDER[r])
