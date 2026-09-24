"""Threshold validation table — doubles as the thesis validation table.

Every case cites the band it exercises in data/reference/biomarker_ranges.yaml
(ADA 2024 glucose, ACC/AHA 2017 blood pressure, WHO 2011 hemoglobin).
"""

import pytest

from src.clinical.risk_scoring import (
    bp_category,
    derive_conditions,
    overall_risk,
    score_biomarker,
    score_biomarkers,
)

GLUCOSE_CASES = [
    (65, "hypoglycemia", "high"),
    (70, "normal", "none"),
    (99.9, "normal", "none"),
    (100, "prediabetes", "moderate"),
    (125.9, "prediabetes", "moderate"),
    (126, "diabetes_range", "high"),
    (300, "diabetes_range", "high"),
]

SYSTOLIC_CASES = [
    (110, "normal", "none"),
    (119.9, "normal", "none"),
    (120, "elevated", "low"),
    (129.9, "elevated", "low"),
    (130, "hypertension_stage1", "moderate"),
    (140, "hypertension_stage2", "high"),
    (179.9, "hypertension_stage2", "high"),
    (180, "hypertensive_crisis", "critical"),
]

DIASTOLIC_CASES = [
    (70, "normal", "none"),
    (80, "hypertension_stage1", "moderate"),
    (90, "hypertension_stage2", "high"),
    (120, "hypertensive_crisis", "critical"),
]

HEMOGLOBIN_CASES = [
    # (value, sex, pregnant, label, risk)
    (14.0, "male", False, "normal", "none"),
    (12.5, "male", False, "mild_anemia", "moderate"),
    (10.0, "male", False, "moderate_anemia", "high"),
    (7.9, "male", False, "severe_anemia", "critical"),
    (12.0, "female", False, "normal", "none"),
    (11.5, "female", False, "mild_anemia", "moderate"),
    (11.0, "female", True, "normal", "none"),
    (10.5, "female", True, "mild_anemia", "moderate"),
    (9.0, "female", True, "moderate_anemia", "high"),
    (6.9, "female", True, "severe_anemia", "critical"),
]


@pytest.mark.parametrize("value,label,risk", GLUCOSE_CASES)
def test_fasting_glucose_bands(value, label, risk):
    flag = score_biomarker("fasting_glucose", value)
    assert (flag.label, flag.risk) == (label, risk)


@pytest.mark.parametrize("value,label,risk", SYSTOLIC_CASES)
def test_systolic_bands(value, label, risk):
    flag = score_biomarker("systolic_bp", value)
    assert (flag.label, flag.risk) == (label, risk)


@pytest.mark.parametrize("value,label,risk", DIASTOLIC_CASES)
def test_diastolic_bands(value, label, risk):
    flag = score_biomarker("diastolic_bp", value)
    assert (flag.label, flag.risk) == (label, risk)


@pytest.mark.parametrize("value,sex,pregnant,label,risk", HEMOGLOBIN_CASES)
def test_hemoglobin_bands(value, sex, pregnant, label, risk):
    flag = score_biomarker("hemoglobin", value, sex, pregnant)
    assert (flag.label, flag.risk) == (label, risk)


def test_bp_category_takes_more_severe_component():
    flags = score_biomarkers({"systolic_bp": 135, "diastolic_bp": 70}, "male")
    assert bp_category(flags) == "hypertension_stage1"
    flags = score_biomarkers({"systolic_bp": 118, "diastolic_bp": 92}, "male")
    assert bp_category(flags) == "hypertension_stage2"


def test_derive_conditions():
    flags = score_biomarkers(
        {"fasting_glucose": 130, "systolic_bp": 145, "diastolic_bp": 92, "hemoglobin": 9.0},
        sex="female",
    )
    assert set(derive_conditions(flags)) == {"diabetes", "hypertension", "anemia"}


def test_prediabetes_maps_to_diabetes_rule():
    flags = score_biomarkers({"fasting_glucose": 110}, "male")
    assert derive_conditions(flags) == ["diabetes"]


def test_overall_risk_and_unknown_keys_ignored():
    flags = score_biomarkers(
        {"fasting_glucose": 95, "hemoglobin": 7.0, "unknown_marker": 42},
        sex="female",
    )
    assert len(flags) == 2
    assert overall_risk(flags) == "critical"
    assert overall_risk([]) == "none"
