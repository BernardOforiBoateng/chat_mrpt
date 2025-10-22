"""Validate the conversational helpers used by the refreshed TPR workflow."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.data_analysis_v3.core.formatters import MessageFormatter
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler


@pytest.fixture
def formatter():
    return MessageFormatter("test-session")


def test_facility_selection_formatter_lists_recommendations(formatter):
    analysis = {
        "levels": {
            "primary": {"name": "Primary", "count": 12, "rdt_tests": 4200, "microscopy_tests": 1800, "recommended": True},
            "secondary": {"name": "Secondary", "count": 5, "rdt_tests": 2200, "microscopy_tests": 900},
            "all": {"name": "All", "count": 17},
        }
    }

    message = formatter.format_facility_selection("Adamawa", analysis)

    assert "primary" in message.lower()
    assert "recommended" in message.lower()
    assert "just type which level you'd like" in message.lower()


def test_age_group_selection_formatter_prompts_for_inputs(formatter):
    analysis = {
        "state": "Adamawa",
        "facility_level": "primary",
        "age_groups": {
            "u5": {"tests_available": 1200, "total_tests": 1200, "total_positive": 240},
            "o5": {"tests_available": 900, "total_tests": 900, "total_positive": 120},
            "pw": {"tests_available": 450, "total_tests": 450, "total_positive": 60},
        },
        "total_tests": 2550,
    }

    message = formatter.format_age_group_selection(analysis)

    lowered = message.lower()
    assert "step 2" in lowered
    assert "u5" in lowered and "pw" in lowered
    assert "just type which group you'd like" in lowered


def test_tool_results_formatter_passes_through_output(formatter):
    tool_output = """📊 **TPR Analysis Complete for Adamawa**\n\nSummary block"""
    message = formatter.format_tool_tpr_results(tool_output)
    assert message == tool_output


class TestStrictExtraction:
    """The extraction helpers now rely on explicit keywords only."""

    @pytest.fixture
    def handler(self):
        return TPRWorkflowHandler("session", Mock(), Mock())

    def test_facility_extraction_requires_explicit_tokens(self, handler):
        assert handler.extract_facility_level("primary") == "primary"
        assert handler.extract_facility_level("2") == "secondary"
        assert handler.extract_facility_level("all") == "all"
        assert handler.extract_facility_level("yes") is None

    def test_age_group_extraction_requires_explicit_tokens(self, handler):
        assert handler.extract_age_group("u5") == "u5"
        assert handler.extract_age_group("3") == "pw"
        assert handler.extract_age_group("all") == "all_ages"
        assert handler.extract_age_group("kids") is None
