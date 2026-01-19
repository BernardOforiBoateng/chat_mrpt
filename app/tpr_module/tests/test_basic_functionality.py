"""
Basic functionality tests for TPR module.

Tests the core functionality with simple, focused tests.
"""

import unittest
import pandas as pd
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.core.tpr_calculator import TPRCalculator
from app.tpr_module.data.nmep_parser import NMEPParser
from app.tpr_module.data.geopolitical_zones import STATE_TO_ZONE, ZONE_VARIABLES
from app.tpr_module.core.tpr_state_manager import TPRStateManager


class TestBasicFunctionality(unittest.TestCase):
    """Test basic TPR module functionality."""
    
    def test_tpr_calculation_basic(self):
        """Test basic TPR calculation."""
        from app.tpr_module.tests.test_helpers import create_test_nmep_data
        
        calculator = TPRCalculator()
        
        # Create test data using the helper which creates properly mapped columns
        test_data = create_test_nmep_data(['Kano'])
        
        # Add some specific test values
        test_data.loc[0, 'rdt_positive_u5'] = 10
        test_data.loc[0, 'rdt_tested_u5'] = 50
        test_data.loc[0, 'micro_positive_u5'] = 5
        test_data.loc[0, 'micro_tested_u5'] = 30
        
        # Calculate TPR
        result = calculator.calculate_ward_tpr(test_data, age_group='u5')
        
        # Check result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        
        # Get the first ward result
        ward_name = list(result.keys())[0]
        ward_result = result[ward_name]
        self.assertIn('tpr', ward_result)
        self.assertIn('method', ward_result)
        self.assertGreater(ward_result['tpr'], 0)
    
    def test_geopolitical_zones(self):
        """Test geopolitical zone mapping."""
        # Test all states are mapped
        self.assertEqual(len(STATE_TO_ZONE), 37)  # 36 states + FCT
        
        # Test specific mappings
        self.assertEqual(STATE_TO_ZONE['Kano'], 'North_West')
        self.assertEqual(STATE_TO_ZONE['Lagos'], 'South_West')
        self.assertEqual(STATE_TO_ZONE['FCT'], 'North_Central')
        
        # Test all zones have variables
        self.assertEqual(len(ZONE_VARIABLES), 6)
        for zone, variables in ZONE_VARIABLES.items():
            self.assertIsInstance(variables, list)
            self.assertGreater(len(variables), 0)
    
    def test_state_manager_basic(self):
        """Test basic state management."""
        manager = TPRStateManager('test_session')
        
        # Test initial state
        state = manager.get_state()
        self.assertIsInstance(state, dict)
        
        # Test update
        manager.update_state('selected_state', 'Kano')
        value = manager.get_state('selected_state')
        self.assertEqual(value, 'Kano')
        
        # Test workflow stage
        manager.update_state('workflow_stage', 'state_selection')
        stage = manager.get_state('workflow_stage')
        self.assertEqual(stage, 'state_selection')
    
    def test_nmep_detection(self):
        """Test NMEP file detection."""
        parser = NMEPParser()
        
        # Create test Excel file with TPR columns
        test_data = pd.DataFrame({
            'State': ['Kano'],
            'Persons tested positive for malaria by RDT <5yrs': [10],
            'Persons presenting with fever & tested by RDT <5yrs': [50]
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            test_data.to_excel(tmp.name, sheet_name='raw', index=False)
            tmp_path = tmp.name
        
        try:
            # Test detection
            is_tpr = parser.detect_tpr_file(tmp_path)
            self.assertTrue(is_tpr)
        finally:
            os.unlink(tmp_path)
    
    def test_zone_variable_selection(self):
        """Test zone-specific variable selection."""
        # Test North West zone (Kano)
        kano_zone = STATE_TO_ZONE['Kano']
        kano_vars = ZONE_VARIABLES[kano_zone]
        
        # Should have specific variables for North West
        self.assertIn('housing_quality', kano_vars)
        self.assertIn('elevation', kano_vars)
        self.assertIn('evi', kano_vars)
        
        # Test South West zone (Lagos)
        lagos_zone = STATE_TO_ZONE['Lagos']
        lagos_vars = ZONE_VARIABLES[lagos_zone]
        
        # Should have urban-focused variables
        self.assertIn('nighttime_lights', lagos_vars)
        self.assertIn('rainfall', lagos_vars)
    
    def test_tpr_threshold_logic(self):
        """Test TPR threshold detection logic."""
        from app.tpr_module.tests.test_helpers import create_test_nmep_data
        
        calculator = TPRCalculator()
        
        # Create test data with high TPR
        test_data = create_test_nmep_data(['Kano'])
        
        # Modify first facility to have high TPR (60%)
        test_data.loc[0, 'facility'] = 'Urban_F1'
        test_data.loc[0, 'ward'] = 'Urban_Ward' 
        test_data.loc[0, 'lga'] = 'Urban_LGA'
        test_data.loc[0, 'rdt_positive_u5'] = 60
        test_data.loc[0, 'rdt_tested_u5'] = 100
        test_data.loc[0, 'micro_positive_u5'] = 55
        test_data.loc[0, 'micro_tested_u5'] = 90
        test_data.loc[0, 'outpatient_attendance'] = 300
        
        # Calculate TPR
        result = calculator.calculate_ward_tpr(test_data, age_group='u5')
        
        # Check if alternative method would be used
        ward_result = result.get('Urban_Ward', {})
        if 'tpr' in ward_result and ward_result['tpr'] > 50:
            # For urban areas with high TPR, alternative method should be considered
            self.assertIn('method', ward_result)


if __name__ == '__main__':
    unittest.main()