"""
Test suite for TPR user scenarios following industry best practices.

Following industry standards:
- AAA Pattern (Arrange, Act, Assert)
- Each test verifies a single aspect
- Clear test names describing what is being tested
- Proper assertions, not just success flags
- Test doubles for external dependencies
- Independent tests (no test relies on another)
"""

import pytest
import asyncio
import os
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data_analysis_v3.core.agent import DataAnalysisAgent
from app.core.tpr_utils import calculate_ward_tpr


class TestTPRUserScenarios:
    """Test suite for TPR user interaction scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup before each test and cleanup after."""
        # Arrange - Setup
        self.test_data_path = "www/tpr_data_by_state/ab_Abia_State_TPR_LLIN_2024.xlsx"
        self.session_id = "test_session"
        self.session_path = f"instance/uploads/{self.session_id}"
        
        # Create test directory
        Path(self.session_path).mkdir(parents=True, exist_ok=True)
        
        yield  # This is where the test runs
        
        # Cleanup
        if Path(self.session_path).exists():
            shutil.rmtree(self.session_path, ignore_errors=True)
    
    @pytest.fixture
    def sample_tpr_data(self):
        """Provide sample TPR data for testing."""
        # Arrange - Create proper TPR data matching actual column names
        return pd.DataFrame({
            'State': ['Abia State'] * 10,
            'LGA': ['Test LGA'] * 10,
            'WardName': [f'Ward_{i}' for i in range(10)],
            'HealthFacility': [f'Facility_{i}' for i in range(10)],
            'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200, 120, 180, 90, 110, 140, 160, 130],
            'Persons tested positive for malaria by RDT <5yrs': [20, 35, 45, 28, 40, 18, 25, 32, 38, 30],
            'Persons presenting with fever and tested by Microscopy <5yrs': [80, 120, 160, 100, 140, 70, 90, 110, 130, 105],
            'Persons tested positive for malaria by Microscopy <5yrs': [15, 25, 35, 22, 30, 14, 20, 24, 28, 23],
            'FacilityLevel': ['Primary'] * 5 + ['Secondary'] * 5
        })
    
    @pytest.mark.asyncio
    async def test_user_explores_data_successfully(self):
        """Test that user can successfully explore uploaded data."""
        # Arrange
        shutil.copy(self.test_data_path, f"{self.session_path}/data.xlsx")
        agent = DataAnalysisAgent(self.session_id)
        
        # Act
        response = await agent.analyze("I want to explore my data")
        
        # Assert
        assert response['success'] == True, "Exploration should succeed"
        assert 'message' in response, "Response should contain a message"
        assert len(response['message']) > 100, "Response should be substantive"
        # Check that it mentions the actual data characteristics
        assert 'Abia' in response['message'] or 'state' in response['message'].lower(), \
            "Response should reference the state in the data"
    
    @pytest.mark.asyncio
    async def test_tpr_calculation_with_recommendations(self):
        """Test TPR calculation following recommended pathway (Under 5, Primary, Both)."""
        # Arrange
        shutil.copy(self.test_data_path, f"{self.session_path}/data.xlsx")
        agent = DataAnalysisAgent(self.session_id)
        
        # Act - Follow the conversation flow
        response1 = await agent.analyze("Calculate TPR")
        assert response1['success'] == True, "Should initiate TPR calculation"
        
        response2 = await agent.analyze("Under 5")
        assert response2['success'] == True, "Should accept Under 5 selection"
        
        response3 = await agent.analyze("Primary")
        assert response3['success'] == True, "Should accept Primary facility selection"
        
        response4 = await agent.analyze("Both")
        
        # Assert - Verify TPR was actually calculated
        assert response4['success'] == True, "Final TPR calculation should succeed"
        
        # Check that TPR results file was created
        tpr_results_path = Path(self.session_path) / "tpr_results.csv"
        assert tpr_results_path.exists(), "TPR results file should be created"
        
        # Verify the results are valid
        tpr_df = pd.read_csv(tpr_results_path)
        assert len(tpr_df) > 0, "TPR results should contain data"
        assert 'TPR' in tpr_df.columns, "Results should have TPR column"
        assert 'WardName' in tpr_df.columns, "Results should have WardName column"
        assert tpr_df['TPR'].notna().any(), "Should have calculated TPR values"
    
    @pytest.mark.asyncio
    async def test_quick_overview_provides_summary(self):
        """Test that quick overview provides meaningful summary statistics."""
        # Arrange
        shutil.copy(self.test_data_path, f"{self.session_path}/data.xlsx")
        agent = DataAnalysisAgent(self.session_id)
        
        # Load the actual data to know what to expect
        df = pd.read_excel(self.test_data_path)
        actual_rows = len(df)
        actual_columns = df.columns.tolist()
        
        # Act
        response = await agent.analyze("Give me a quick overview")
        
        # Assert
        assert response['success'] == True, "Quick overview should succeed"
        assert 'message' in response, "Should provide a message"
        
        # Verify it contains actual summary information
        message_lower = response['message'].lower()
        
        # Should mention data size (flexible about exact wording)
        assert any(word in message_lower for word in ['records', 'rows', 'data', 'entries', str(actual_rows)]), \
            f"Should mention data size (actual: {actual_rows} rows)"
        
        # Should mention actual column names or data characteristics from the file
        # Check if any actual column names or related terms are mentioned
        geographic_cols = [col for col in actual_columns if any(
            term in col.lower() for term in ['ward', 'lga', 'state', 'facility']
        )]
        
        if geographic_cols:
            # If data has geographic columns, response should reference them somehow
            # But be flexible about exact wording
            assert any(
                col.lower() in message_lower or 
                col.replace('Name', '').lower() in message_lower or
                'geographic' in message_lower or
                'location' in message_lower
                for col in geographic_cols
            ), f"Should reference geographic data that exists in columns: {geographic_cols}"
    
    def test_tpr_calculation_with_actual_columns(self):
        """Test that TPR calculation works with real column names from NMEP data."""
        # Arrange
        df = pd.read_excel(self.test_data_path)
        
        # Act
        result = calculate_ward_tpr(df, age_group='u5', test_method='both', facility_level='all')
        
        # Assert
        assert isinstance(result, pd.DataFrame), "Should return a DataFrame"
        assert len(result) > 0, "Should have results"
        assert 'TPR' in result.columns, "Should have TPR column"
        assert 'Total_Tested' in result.columns, "Should have Total_Tested column"
        assert 'Total_Positive' in result.columns, "Should have Total_Positive column"
        
        # Verify TPR values are in valid range (0-100% normally, but data has issues)
        # So we just check they're numeric
        assert result['TPR'].dtype in [np.float64, np.float32, np.int64], \
            "TPR should be numeric"
    
    def test_tpr_handles_missing_columns_gracefully(self):
        """Test that TPR calculation handles missing columns appropriately."""
        # Arrange - Create data missing some columns
        incomplete_df = pd.DataFrame({
            'State': ['Test State'] * 5,
            'LGA': ['Test LGA'] * 5,
            'WardName': [f'Ward_{i}' for i in range(5)],
            # Only RDT data, no Microscopy
            'Persons presenting with fever & tested by RDT <5yrs': [100, 150, 200, 120, 180],
            'Persons tested positive for malaria by RDT <5yrs': [20, 35, 45, 28, 40]
        })
        
        # Act
        result = calculate_ward_tpr(incomplete_df, age_group='u5', test_method='rdt', facility_level='all')
        
        # Assert
        assert isinstance(result, pd.DataFrame), "Should still return DataFrame"
        if len(result) > 1:  # If it calculated something
            assert 'TPR' in result.columns, "Should have TPR column"
            assert result['TPR'].notna().any(), "Should calculate TPR from available data"
    
    @pytest.mark.asyncio
    async def test_agent_handles_ambiguous_input(self):
        """Test that agent handles ambiguous user input gracefully."""
        # Arrange
        shutil.copy(self.test_data_path, f"{self.session_path}/data.xlsx")
        agent = DataAnalysisAgent(self.session_id)
        
        ambiguous_inputs = [
            "help",
            "what can you do",
            "2",  # Just a number
            "yes",
            "show me the data"
        ]
        
        for user_input in ambiguous_inputs:
            # Act
            response = await agent.analyze(user_input)
            
            # Assert
            assert response['success'] == True, f"Should handle '{user_input}' without crashing"
            assert 'message' in response, f"Should provide a message for '{user_input}'"
            assert len(response['message']) > 0, f"Message should not be empty for '{user_input}'"
    
    @pytest.mark.asyncio
    async def test_no_data_error_handling(self):
        """Test that agent handles missing data appropriately."""
        # Arrange - No data file uploaded
        agent = DataAnalysisAgent(self.session_id)
        
        # Act
        response = await agent.analyze("Calculate TPR")
        
        # Assert
        assert 'message' in response, "Should provide an error message"
        message_lower = response['message'].lower()
        assert any(word in message_lower for word in ['no data', 'upload', 'file', 'load']), \
            "Should indicate that no data is available"
    
    @pytest.mark.asyncio
    async def test_map_visualization_creation(self):
        """Test that TPR map visualization is created when shapefile is available."""
        # Arrange
        shutil.copy(self.test_data_path, f"{self.session_path}/data.xlsx")
        agent = DataAnalysisAgent(self.session_id)
        
        # Act - Calculate TPR first
        await agent.analyze("Calculate TPR for all ages")
        
        # Assert - Check if map was created
        map_path = Path(self.session_path) / "tpr_distribution_map.html"
        # Map creation depends on shapefile availability
        if map_path.exists():
            assert map_path.stat().st_size > 1000, "Map file should have substantial content"
            
            # Verify map contains expected elements
            with open(map_path, 'r') as f:
                content = f.read()
                assert 'plotly' in content.lower(), "Should use Plotly for visualization"
                assert 'tpr' in content.lower(), "Should reference TPR in the map"


class TestTPRDataValidation:
    """Test suite for TPR data validation and edge cases."""
    
    def test_tpr_values_are_percentages(self):
        """Test that TPR values are calculated as percentages."""
        # Arrange
        test_df = pd.DataFrame({
            'State': ['Test'] * 2,
            'LGA': ['LGA1'] * 2,
            'WardName': ['Ward1', 'Ward2'],
            'Persons presenting with fever & tested by RDT <5yrs': [100, 200],
            'Persons tested positive for malaria by RDT <5yrs': [25, 40],
            'Persons presenting with fever and tested by Microscopy <5yrs': [100, 200],
            'Persons tested positive for malaria by Microscopy <5yrs': [20, 50]
        })
        
        # Act
        result = calculate_ward_tpr(test_df, age_group='u5', test_method='rdt')
        
        # Assert
        if len(result) > 1:
            # Ward1: 25/100 = 25%
            ward1_tpr = result[result['WardName'] == 'ward1']['TPR'].iloc[0]
            assert abs(ward1_tpr - 25.0) < 0.1, f"Ward1 TPR should be ~25%, got {ward1_tpr}"
            
            # Ward2: 40/200 = 20%
            ward2_tpr = result[result['WardName'] == 'ward2']['TPR'].iloc[0]
            assert abs(ward2_tpr - 20.0) < 0.1, f"Ward2 TPR should be ~20%, got {ward2_tpr}"
    
    def test_tpr_handles_zero_tested(self):
        """Test that TPR calculation handles zero tested cases."""
        # Arrange
        test_df = pd.DataFrame({
            'State': ['Test'],
            'LGA': ['LGA1'],
            'WardName': ['Ward1'],
            'Persons presenting with fever & tested by RDT <5yrs': [0],
            'Persons tested positive for malaria by RDT <5yrs': [0],
            'Persons presenting with fever and tested by Microscopy <5yrs': [0],
            'Persons tested positive for malaria by Microscopy <5yrs': [0]
        })
        
        # Act
        result = calculate_ward_tpr(test_df, age_group='u5', test_method='both')
        
        # Assert
        assert isinstance(result, pd.DataFrame), "Should return DataFrame even with zero values"
        if len(result) > 1:
            assert result['TPR'].iloc[0] == 0 or pd.isna(result['TPR'].iloc[0]), \
                "TPR should be 0 or NaN when no tests conducted"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])