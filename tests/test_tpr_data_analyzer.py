"""Unit coverage for the lightweight analytics used during the TPR workflow."""

from __future__ import annotations

import pandas as pd
import pytest

from app.data_analysis_v3.core.tpr_data_analyzer import TPRDataAnalyzer


@pytest.fixture
def analyzer():
    return TPRDataAnalyzer()


@pytest.fixture
def sample_tpr_data():
    return pd.DataFrame(
        {
            "State": ["Adamawa"] * 3 + ["Kwara"] * 3,
            "FacilityLevel": ["Primary", "Primary", "Secondary", "Primary", "Secondary", "Tertiary"],
            "HealthFacility": ["F1", "F2", "F3", "F4", "F5", "F6"],
            "WardName": ["Ward 1", "Ward 2", "Ward 3", "Ward 4", "Ward 5", "Ward 6"],
            "LGA": ["Yola", "Girei", "Yola", "Ilorin", "Offa", "Ilorin"],
            "Persons presenting with fever & tested by RDT <5yrs": [80, 70, 30, 60, 55, 25],
            "Persons presenting with fever & tested positive by RDT <5yrs": [20, 14, 6, 12, 11, 5],
            "Persons presenting with fever & tested by Microscopy <5yrs": [30, 28, 10, 20, 18, 8],
            "Persons presenting with fever & tested positive by Microscopy <5yrs": [6, 5, 2, 4, 3, 1],
            "Persons presenting with fever & tested by RDT >5yrs": [60, 50, 22, 45, 40, 18],
            "Persons presenting with fever & tested positive by RDT >5yrs": [12, 10, 4, 9, 8, 3],
            "Pregnant women tested by RDT": [18, 15, 6, 12, 9, 5],
            "Pregnant women tested positive by RDT": [3, 2, 1, 2, 1, 1],
        }
    )


def test_analyze_states_orders_by_data_volume(analyzer, sample_tpr_data):
    result = analyzer.analyze_states(sample_tpr_data)

    assert result["total_states"] == 2
    assert set(result["states"].keys()) == {"Adamawa", "Kwara"}
    assert result["states"]["Adamawa"]["total_tests"] > 0
    assert result["recommended"] in {"Adamawa", "Kwara"}


def test_analyze_states_without_state_column(analyzer):
    df = pd.DataFrame({"value": [1, 2, 3]})
    result = analyzer.analyze_states(df)

    assert result["total_states"] == 1
    assert result["states"]["All Data"]["facilities"] == 3


def test_analyze_facility_levels_flags_primary(analyzer, sample_tpr_data):
    result = analyzer.analyze_facility_levels(sample_tpr_data, "Adamawa")

    assert result["has_levels"] is True
    assert "primary" in result["levels"]
    assert result["levels"]["primary"]["recommended"] is True
    assert result["levels"]["all"]["recommended"] is False


def test_analyze_facility_levels_without_column(analyzer, sample_tpr_data):
    df = pd.DataFrame(
        {
            "State": ["Adamawa", "Adamawa"],
            "Site": ["Location A", "Location B"],
            "Tests": [10, 12],
        }
    )
    result = analyzer.analyze_facility_levels(df, "Adamawa")

    assert result["has_levels"] is False
    assert list(result["levels"].keys()) == ["all"]


def test_analyze_age_groups_returns_expected_keys(analyzer, sample_tpr_data):
    result = analyzer.analyze_age_groups(sample_tpr_data, "Adamawa", "primary")

    groups = result["age_groups"]
    assert set(groups.keys()) == {"under_5", "over_5", "pregnant"}
    assert bool(groups["under_5"]["has_data"]) is True
    assert groups["under_5"]["positivity_rate"] >= 0


def test_helper_column_detection(analyzer):
    df = pd.DataFrame({"StateName": [], "facility_level": [], "other": []})
    assert analyzer._find_column(df, ["state"]) == "StateName"
    assert analyzer._find_column(df, ["level"]) == "facility_level"
    assert analyzer._find_column(df, ["missing"]) is None


def test_helper_find_columns_by_patterns(analyzer):
    df = pd.DataFrame({"tested_total": [], "positive_total": [], "note": []})
    assert analyzer._find_columns_by_patterns(df, ["tested"]) == ["tested_total"]
    assert analyzer._find_columns_by_patterns(df, ["positive"]) == ["positive_total"]
