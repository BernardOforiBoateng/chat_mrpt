"""
Test Track A Improvements: TPR Workflow UX Enhancements

Tests for:
- A1.1: TPR data auto-detection and contextual welcome
- A1.2: Fuzzy keyword matching for facility and age group
- A1.3: Proactive visualization offers

Run with: pytest tests/test_track_a_improvements.py -v
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data_analysis_v3.core.agent import DataAnalysisAgent
from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
from app.data_analysis_v3.core.formatters import MessageFormatter


class TestA11_TPRDetection:
    """Test A1.1: TPR Data Auto-Detection"""

    def test_detects_tpr_data_with_standard_columns(self):
        """Should detect TPR data with standard columns"""
        agent = DataAnalysisAgent(session_id="test")

        # Create typical TPR data
        df = pd.DataFrame({
            'HealthFacility': ['Clinic A', 'Clinic B'],
            'FacilityType': ['primary', 'secondary'],
            'RDT_Positive': [10, 20],
            'RDT_Tested': [100, 200],
            'Microscopy_Positive': [5, 15],
            'Microscopy_Tested': [50, 150],
            'TPR': [0.1, 0.15],
            'AgeGroup': ['u5', 'o5']
        })

        is_tpr = agent._detect_tpr_data(df)
        assert is_tpr == True, "Should detect TPR data from column names"

    def test_rejects_non_tpr_data(self):
        """Should NOT detect non-TPR data"""
        agent = DataAnalysisAgent(session_id="test")

        # Create generic demographic data
        df = pd.DataFrame({
            'Ward': ['Ward 1', 'Ward 2'],
            'Population': [10000, 20000],
            'Poverty_Rate': [0.3, 0.4],
            'Education_Level': ['High', 'Medium']
        })

        is_tpr = agent._detect_tpr_data(df)
        assert is_tpr == False, "Should NOT detect TPR in generic demographic data"

    def test_detects_tpr_with_variant_column_names(self):
        """Should detect TPR with case/spacing variations"""
        agent = DataAnalysisAgent(session_id="test")

        df = pd.DataFrame({
            'health_facility': ['Clinic A'],
            'FACILITY_TYPE': ['primary'],
            'rdt_positive': [10],
            'total_tested': [100],
            'test_positivity_rate': [0.1],
            'u5': [50]
        })

        is_tpr = agent._detect_tpr_data(df)
        assert is_tpr == True, "Should detect TPR with variant column names"

    def test_handles_empty_dataframe(self):
        """Should handle empty DataFrame gracefully"""
        agent = DataAnalysisAgent(session_id="test")

        df = pd.DataFrame()
        is_tpr = agent._detect_tpr_data(df)
        assert is_tpr == False, "Should return False for empty DataFrame"

    def test_generates_contextual_welcome(self):
        """Should generate contextual welcome message"""
        agent = DataAnalysisAgent(session_id="test")

        df = pd.DataFrame({
            'HealthFacility': ['Clinic ' + str(i) for i in range(475)],
            'FacilityType': ['primary'] * 321 + ['secondary'] * 128 + ['tertiary'] * 26,
            'Ward': ['Ward ' + str(i % 112) for i in range(475)],
            'Total_Tested': [100] * 475,
            'RDT_Positive': [10] * 475,
        })

        welcome = agent._generate_tpr_welcome(df, 'Kano State', 475, 112, 44)

        # Check key components
        assert 'Welcome to ChatMRPT' in welcome
        assert 'Detected:' in welcome
        assert 'Test Positivity Rate (TPR)' in welcome
        assert 'Kano State' in welcome
        assert '475 facilities' in welcome
        assert '112 wards' in welcome
        assert "What we'll do together" in welcome
        assert '3-5 minutes' in welcome
        assert 'primary' in welcome
        assert 'secondary' in welcome
        assert 'tertiary' in welcome


class TestA12_FuzzyKeywordMatching:
    """Test A1.2: Fuzzy Keyword Matching"""

    def setup_method(self):
        """Setup test handler"""
        self.handler = TPRWorkflowHandler(session_id="test")

    # Facility Level Tests
    def test_facility_exact_keyword_primary(self):
        """Level 1: Exact match for 'primary'"""
        result = self.handler.extract_facility_level("primary")
        assert result == "primary"

    def test_facility_exact_number_1(self):
        """Level 1: Exact match for '1'"""
        result = self.handler.extract_facility_level("1")
        assert result == "primary"

    def test_facility_fuzzy_typo_prinary(self):
        """Level 2: Fuzzy match for typo 'prinary'"""
        result = self.handler.extract_facility_level("prinary")
        assert result == "primary", "Should match 'primary' from typo 'prinary'"

    def test_facility_fuzzy_typo_seconary(self):
        """Level 2: Fuzzy match for typo 'seconary'"""
        result = self.handler.extract_facility_level("seconary")
        assert result == "secondary", "Should match 'secondary' from typo 'seconary'"

    def test_facility_pattern_i_want_primary(self):
        """Level 3: Pattern match for 'I want primary'"""
        result = self.handler.extract_facility_level("I want primary facilities")
        assert result == "primary", "Should extract 'primary' from natural language"

    def test_facility_pattern_basic_facilities(self):
        """Level 3: Pattern match for 'basic facilities'"""
        result = self.handler.extract_facility_level("let's analyze basic facilities")
        assert result == "primary", "Should map 'basic' to 'primary'"

    def test_facility_pattern_community_health(self):
        """Level 3: Pattern match for 'community health centers'"""
        result = self.handler.extract_facility_level("community health centers")
        assert result == "primary", "Should map 'community' to 'primary'"

    def test_facility_pattern_district_hospitals(self):
        """Level 3: Pattern match for 'district hospitals'"""
        result = self.handler.extract_facility_level("district hospitals")
        assert result == "secondary", "Should map 'district' to 'secondary'"

    def test_facility_pattern_tertiary_specialist(self):
        """Level 3: Pattern match for 'specialist centers'"""
        result = self.handler.extract_facility_level("specialist centers")
        assert result == "tertiary", "Should map 'specialist' to 'tertiary'"

    def test_facility_pattern_all_facilities(self):
        """Level 3: Pattern match for 'all facilities'"""
        result = self.handler.extract_facility_level("all facilities combined")
        assert result == "all", "Should extract 'all' from phrase"

    def test_facility_no_match(self):
        """Should return None for unrelated input"""
        result = self.handler.extract_facility_level("show me the weather")
        assert result is None, "Should return None for unrelated input"

    # Age Group Tests
    def test_age_exact_keyword_u5(self):
        """Level 1: Exact match for 'u5'"""
        result = self.handler.extract_age_group("u5")
        assert result == "u5"

    def test_age_exact_number_1(self):
        """Level 1: Exact match for '1'"""
        result = self.handler.extract_age_group("1")
        assert result == "u5"

    def test_age_fuzzy_typo_pregant(self):
        """Level 2: Fuzzy match for typo 'pregant'"""
        result = self.handler.extract_age_group("pregant")
        assert result == "pw", "Should match 'pregnant' from typo 'pregant'"

    def test_age_pattern_under_five(self):
        """Level 3: Pattern match for 'under five'"""
        result = self.handler.extract_age_group("under five")
        assert result == "u5", "Should extract 'u5' from 'under five'"

    def test_age_pattern_children_under_5(self):
        """Level 3: Pattern match for 'children under 5'"""
        result = self.handler.extract_age_group("children under 5")
        assert result == "u5", "Should extract 'u5' from 'children under 5'"

    def test_age_pattern_pregnant_women(self):
        """Level 3: Pattern match for 'pregnant women'"""
        result = self.handler.extract_age_group("pregnant women")
        assert result == "pw", "Should extract 'pw' from 'pregnant women'"

    def test_age_pattern_maternal(self):
        """Level 3: Pattern match for 'maternal'"""
        result = self.handler.extract_age_group("maternal health")
        assert result == "pw", "Should map 'maternal' to 'pw'"

    def test_age_pattern_all_ages(self):
        """Level 3: Pattern match for 'all ages'"""
        result = self.handler.extract_age_group("all ages")
        assert result == "all_ages", "Should extract 'all_ages' from phrase"

    def test_age_no_match(self):
        """Should return None for unrelated input"""
        result = self.handler.extract_age_group("show me the data")
        assert result is None, "Should return None for unrelated input"


class TestA13_VisualizationOffers:
    """Test A1.3: Proactive Visualization Offers"""

    def setup_method(self):
        """Setup test formatter"""
        self.formatter = MessageFormatter(session_id="test")

    def test_facility_selection_has_visual_separators(self):
        """Should include visual separators in facility selection"""
        analysis = {
            'levels': {
                'primary': {'count': 321},
                'secondary': {'count': 128},
                'tertiary': {'count': 26}
            }
        }

        message = self.formatter.format_facility_selection('Kano State', analysis)

        # Check for visual separators
        assert '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' in message
        assert '💡 **Need help deciding?**' in message
        assert 'I have **2 interactive charts** ready:' in message
        assert '📊 Facility distribution by level' in message
        assert '📈 Test volumes (RDT vs Microscopy)' in message
        assert "Say **'show charts'**" in message

    def test_age_selection_has_visual_separators(self):
        """Should include visual separators in age selection"""
        analysis = {
            'state': 'Kano State',
            'facility_level': 'primary',
            'age_groups': ['u5', 'o5', 'pw']
        }

        message = self.formatter.format_age_group_selection(analysis)

        # Check for visual separators
        assert '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' in message
        assert '💡 **Want to see the data first?**' in message
        assert 'I have **2 charts** showing:' in message
        assert '📊 Test volumes by age group' in message
        assert '📈 Positivity rate comparisons' in message
        assert "Say **'show charts'**" in message

    def test_facility_selection_only_has_separators(self):
        """Should include separators when state is auto-selected"""
        analysis = {
            'state_name': 'Kano State',
            'levels': {
                'primary': {'count': 321},
                'secondary': {'count': 128},
                'tertiary': {'count': 26}
            }
        }

        message = self.formatter.format_facility_selection_only(analysis)

        # Check visual separators present
        assert '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' in message
        assert 'Need help deciding?' in message
        assert '2 interactive charts' in message


class TestEndToEndWorkflow:
    """Test E2E workflow with Track A improvements"""

    def test_natural_language_workflow(self):
        """Test full workflow with natural language inputs"""
        handler = TPRWorkflowHandler(session_id="test")

        # Test facility extraction from natural language
        facility = handler.extract_facility_level("I want to analyze primary health facilities")
        assert facility == "primary", "Should extract facility from natural language"

        # Test age group extraction from natural language
        age = handler.extract_age_group("children under five years")
        assert age == "u5", "Should extract age group from natural language"

    def test_typo_tolerant_workflow(self):
        """Test workflow handles typos gracefully"""
        handler = TPRWorkflowHandler(session_id="test")

        # Test typos in facility
        facility = handler.extract_facility_level("prinary")
        assert facility == "primary", "Should handle facility typo"

        # Test typos in age
        age = handler.extract_age_group("pregant")
        assert age == "pw", "Should handle age group typo"

    def test_backwards_compatibility(self):
        """Test that old exact keywords still work"""
        handler = TPRWorkflowHandler(session_id="test")

        # Old style: exact keywords
        assert handler.extract_facility_level("primary") == "primary"
        assert handler.extract_facility_level("secondary") == "secondary"
        assert handler.extract_facility_level("tertiary") == "tertiary"
        assert handler.extract_facility_level("all") == "all"

        assert handler.extract_age_group("u5") == "u5"
        assert handler.extract_age_group("o5") == "o5"
        assert handler.extract_age_group("pw") == "pw"
        assert handler.extract_age_group("all") == "all_ages"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
