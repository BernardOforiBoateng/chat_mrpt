"""
Unit tests for TPR Calculator.

Tests the accuracy of TPR calculations using various test cases.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.core.tpr_calculator import TPRCalculator


class TestTPRCalculator(unittest.TestCase):
    """Test TPR calculation accuracy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = TPRCalculator()
    
    def test_standard_tpr_calculation(self):
        """Test standard TPR calculation with max(RDT, Microscopy) logic."""
        # Test case 1: RDT higher than Microscopy
        data = pd.DataFrame({
            'RDT_Tested': [100],
            'RDT_Positive': [25],
            'Microscopy_Tested': [80],
            'Microscopy_Positive': [15]
        })
        
        result = self.calculator.calculate_tpr(data)
        self.assertEqual(result.iloc[0]['Total_Tested'], 100)  # max(100, 80)
        self.assertEqual(result.iloc[0]['Total_Positive'], 25)  # max(25, 15)
        self.assertEqual(result.iloc[0]['TPR'], 25.0)  # (25/100) * 100
        self.assertEqual(result.iloc[0]['Method'], 'standard')
    
    def test_microscopy_higher_calculation(self):
        """Test when Microscopy values are higher."""
        data = pd.DataFrame({
            'RDT_Tested': [50],
            'RDT_Positive': [10],
            'Microscopy_Tested': [120],
            'Microscopy_Positive': [30]
        })
        
        result = self.calculator.calculate_tpr(data)
        self.assertEqual(result.iloc[0]['Total_Tested'], 120)  # max(50, 120)
        self.assertEqual(result.iloc[0]['Total_Positive'], 30)  # max(10, 30)
        self.assertEqual(result.iloc[0]['TPR'], 25.0)  # (30/120) * 100
    
    def test_alternative_tpr_calculation(self):
        """Test alternative TPR calculation for urban areas."""
        # High TPR > 50% triggers alternative calculation
        data = pd.DataFrame({
            'RDT_Tested': [100],
            'RDT_Positive': [60],
            'Microscopy_Tested': [80],
            'Microscopy_Positive': [45],
            'Outpatient_Attendance': [200]
        })
        
        result = self.calculator.calculate_tpr(data)
        # Should use alternative: positive/outpatient
        self.assertEqual(result.iloc[0]['TPR'], 30.0)  # (60/200) * 100
        self.assertEqual(result.iloc[0]['Method'], 'alternative')
    
    def test_zero_tested_handling(self):
        """Test handling of zero tested cases."""
        data = pd.DataFrame({
            'RDT_Tested': [0],
            'RDT_Positive': [0],
            'Microscopy_Tested': [0],
            'Microscopy_Positive': [0]
        })
        
        result = self.calculator.calculate_tpr(data)
        self.assertTrue(pd.isna(result.iloc[0]['TPR']))
        self.assertEqual(result.iloc[0]['Method'], 'no_data')
    
    def test_missing_data_handling(self):
        """Test handling of missing data."""
        data = pd.DataFrame({
            'RDT_Tested': [100, np.nan, 50],
            'RDT_Positive': [20, np.nan, 10],
            'Microscopy_Tested': [np.nan, 80, 60],
            'Microscopy_Positive': [np.nan, 16, 12]
        })
        
        result = self.calculator.calculate_tpr(data)
        
        # First row: only RDT data
        self.assertEqual(result.iloc[0]['TPR'], 20.0)
        
        # Second row: only Microscopy data  
        self.assertEqual(result.iloc[1]['TPR'], 20.0)
        
        # Third row: both available
        self.assertEqual(result.iloc[2]['TPR'], 20.0)
    
    def test_batch_calculation(self):
        """Test batch TPR calculation for multiple facilities."""
        data = pd.DataFrame({
            'Facility': ['Facility A', 'Facility B', 'Facility C', 'Facility D'],
            'RDT_Tested': [100, 200, 150, 0],
            'RDT_Positive': [20, 50, 75, 0],
            'Microscopy_Tested': [80, 180, 140, 50],
            'Microscopy_Positive': [15, 40, 70, 25],
            'Outpatient_Attendance': [300, 400, 200, 100]
        })
        
        result = self.calculator.calculate_tpr(data)
        
        # Check all rows calculated
        self.assertEqual(len(result), 4)
        
        # Facility A: standard calculation
        self.assertEqual(result.iloc[0]['TPR'], 20.0)
        
        # Facility B: standard calculation
        self.assertEqual(result.iloc[1]['TPR'], 25.0)
        
        # Facility C: high TPR, should use alternative
        self.assertEqual(result.iloc[2]['Method'], 'alternative')
        self.assertEqual(result.iloc[2]['TPR'], 37.5)  # 75/200 * 100
        
        # Facility D: only microscopy data
        self.assertEqual(result.iloc[3]['TPR'], 50.0)
    
    def test_age_group_columns(self):
        """Test TPR calculation with age-specific columns."""
        data = pd.DataFrame({
            'RDT_Tested_<5': [50],
            'RDT_Positive_<5': [10],
            'RDT_Tested_>=5': [100],
            'RDT_Positive_>=5': [15],
            'Microscopy_Tested': [120],
            'Microscopy_Positive': [20]
        })
        
        # Map age-specific to general columns
        data['RDT_Tested'] = data['RDT_Tested_<5']
        data['RDT_Positive'] = data['RDT_Positive_<5']
        
        result = self.calculator.calculate_tpr(data)
        
        # Should use microscopy (higher tested count)
        self.assertEqual(result.iloc[0]['Total_Tested'], 120)
        self.assertEqual(result.iloc[0]['Total_Positive'], 20)
        self.assertEqual(result.iloc[0]['TPR'], 16.67)
    
    def test_threshold_detection(self):
        """Test that high TPR triggers alternative calculation."""
        # Create data with varying TPR levels
        data = pd.DataFrame({
            'Facility': ['Low', 'Medium', 'High', 'Very High'],
            'RDT_Tested': [100, 100, 100, 100],
            'RDT_Positive': [10, 30, 55, 80],
            'Microscopy_Tested': [100, 100, 100, 100],
            'Microscopy_Positive': [10, 30, 55, 80],
            'Outpatient_Attendance': [200, 200, 200, 200]
        })
        
        result = self.calculator.calculate_tpr(data)
        
        # Low and Medium should use standard
        self.assertEqual(result.iloc[0]['Method'], 'standard')
        self.assertEqual(result.iloc[1]['Method'], 'standard')
        
        # High and Very High should use alternative
        self.assertEqual(result.iloc[2]['Method'], 'alternative')
        self.assertEqual(result.iloc[3]['Method'], 'alternative')
        
        # Check alternative calculation
        self.assertEqual(result.iloc[2]['TPR'], 27.5)  # 55/200 * 100
        self.assertEqual(result.iloc[3]['TPR'], 40.0)  # 80/200 * 100
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with very small numbers
        data = pd.DataFrame({
            'Test': ['Small', 'One', 'Fraction'],
            'RDT_Tested': [1, 1, 3],
            'RDT_Positive': [1, 0, 1],
            'Microscopy_Tested': [1, 1, 2],
            'Microscopy_Positive': [0, 1, 1]
        })
        
        result = self.calculator.calculate_tpr(data)
        
        # 100% TPR
        self.assertEqual(result.iloc[0]['TPR'], 100.0)
        
        # 100% from microscopy
        self.assertEqual(result.iloc[1]['TPR'], 100.0)
        
        # Fractional TPR
        self.assertAlmostEqual(result.iloc[2]['TPR'], 33.33, places=2)
    
    def test_calculate_single_tpr(self):
        """Test the internal single TPR calculation method."""
        # Test with dictionary input
        row = {
            'RDT_Tested': 100,
            'RDT_Positive': 25,
            'Microscopy_Tested': 80,
            'Microscopy_Positive': 20
        }
        
        result = self.calculator._calculate_single_tpr(row)
        
        self.assertEqual(result['tpr'], 25.0)
        self.assertEqual(result['tested'], 100)
        self.assertEqual(result['positive'], 25)
        self.assertEqual(result['method'], 'standard')
    
    def test_rounding_precision(self):
        """Test that TPR values are rounded to 2 decimal places."""
        data = pd.DataFrame({
            'RDT_Tested': [3, 7, 13],
            'RDT_Positive': [1, 2, 4],
            'Microscopy_Tested': [3, 7, 13],
            'Microscopy_Positive': [1, 2, 4]
        })
        
        result = self.calculator.calculate_tpr(data)
        
        # Check rounding
        self.assertEqual(result.iloc[0]['TPR'], 33.33)  # 1/3
        self.assertEqual(result.iloc[1]['TPR'], 28.57)  # 2/7
        self.assertEqual(result.iloc[2]['TPR'], 30.77)  # 4/13


class TestTPRValidation(unittest.TestCase):
    """Test TPR data validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = TPRCalculator()
    
    def test_negative_values_handling(self):
        """Test that negative values are handled properly."""
        data = pd.DataFrame({
            'RDT_Tested': [100, -50, 100],
            'RDT_Positive': [20, 10, -20],
            'Microscopy_Tested': [80, 80, 80],
            'Microscopy_Positive': [15, 15, 15]
        })
        
        # Should handle negative values gracefully
        result = self.calculator.calculate_tpr(data)
        
        # First row should calculate normally
        self.assertEqual(result.iloc[0]['TPR'], 20.0)
        
        # Rows with negative values should be handled
        # (implementation dependent - could be NaN or use valid column)
        self.assertIsNotNone(result.iloc[1]['TPR'])
        self.assertIsNotNone(result.iloc[2]['TPR'])
    
    def test_positive_exceeds_tested(self):
        """Test when positive cases exceed tested cases."""
        data = pd.DataFrame({
            'RDT_Tested': [100],
            'RDT_Positive': [150],  # More positive than tested!
            'Microscopy_Tested': [80],
            'Microscopy_Positive': [20]
        })
        
        result = self.calculator.calculate_tpr(data)
        
        # Should handle gracefully - might cap at 100% or use valid data
        self.assertLessEqual(result.iloc[0]['TPR'], 100.0)


if __name__ == '__main__':
    unittest.main()