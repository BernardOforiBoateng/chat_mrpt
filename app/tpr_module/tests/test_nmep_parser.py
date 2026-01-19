"""
Unit tests for NMEP Parser.

Tests the parsing and detection of NMEP Excel files.
"""

import unittest
import pandas as pd
import tempfile
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.data.nmep_parser import NMEPParser


class TestNMEPParser(unittest.TestCase):
    """Test NMEP Excel file parsing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = NMEPParser()
        self.temp_files = []
    
    def tearDown(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def create_test_excel(self, data, sheet_name='raw'):
        """Create a temporary Excel file for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file.close()
        
        # Write data to Excel
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def test_detect_tpr_file_positive(self):
        """Test detection of valid TPR files."""
        # Create test data with TPR columns
        data = pd.DataFrame({
            'State': ['Kano', 'Lagos'],
            'LGA': ['LGA1', 'LGA2'],
            'Ward': ['Ward1', 'Ward2'],
            'Facility': ['Facility1', 'Facility2'],
            'Month': ['January', 'January'],
            'Year': [2024, 2024],
            'Persons tested positive for malaria by RDT': [10, 20],
            'Persons tested for malaria by RDT': [50, 100],
            'Persons tested positive for malaria by Microscopy': [8, 15],
            'Persons tested for malaria by Microscopy': [40, 80]
        })
        
        excel_file = self.create_test_excel(data)
        
        # Test detection
        is_tpr = self.parser.detect_tpr_file(excel_file)
        self.assertTrue(is_tpr)
    
    def test_detect_tpr_file_negative(self):
        """Test detection rejects non-TPR files."""
        # Create test data without TPR columns
        data = pd.DataFrame({
            'State': ['Kano', 'Lagos'],
            'Population': [1000, 2000],
            'Area': [500, 600]
        })
        
        excel_file = self.create_test_excel(data)
        
        # Test detection
        is_tpr = self.parser.detect_tpr_file(excel_file)
        self.assertFalse(is_tpr)
    
    def test_parse_file_success(self):
        """Test successful parsing of NMEP file."""
        # Create complete test data
        data = pd.DataFrame({
            'State': ['Kano', 'Kano', 'Lagos', 'Lagos'],
            'LGA': ['LGA1', 'LGA1', 'LGA2', 'LGA2'],
            'Ward': ['Ward1', 'Ward2', 'Ward3', 'Ward4'],
            'Facility': ['Facility1', 'Facility2', 'Facility3', 'Facility4'],
            'Level of Health Facility': ['Primary', 'Secondary', 'Primary', 'Tertiary'],
            'Month': ['January', 'January', 'January', 'January'],
            'Year': [2024, 2024, 2024, 2024],
            'Total number of all outpatient attendance': [200, 300, 400, 500],
            'Persons tested positive for malaria by RDT <5': [5, 10, 15, 20],
            'Persons tested for malaria by RDT <5': [25, 50, 75, 100],
            'Persons tested positive for malaria by RDT >=5': [10, 15, 20, 25],
            'Persons tested for malaria by RDT >=5': [50, 75, 100, 125],
            'Persons tested positive for malaria by Microscopy <5': [3, 8, 12, 18],
            'Persons tested for malaria by Microscopy <5': [20, 40, 60, 90],
            'Persons tested positive for malaria by Microscopy >=5': [7, 12, 18, 22],
            'Persons tested for malaria by Microscopy >=5': [40, 60, 90, 110]
        })
        
        excel_file = self.create_test_excel(data)
        
        # Parse file
        result = self.parser.parse_file(excel_file)
        
        # Check result structure
        self.assertEqual(result['status'], 'success')
        self.assertIn('data', result)
        self.assertIn('metadata', result)
        
        # Check data
        self.assertEqual(len(result['data']), 4)
        
        # Check metadata
        metadata = result['metadata']
        self.assertEqual(metadata['year'], 2024)
        self.assertEqual(metadata['month'], 'January')
        self.assertIn('Kano', metadata['states_available'])
        self.assertIn('Lagos', metadata['states_available'])
        self.assertEqual(metadata['total_rows'], 4)
    
    def test_extract_metadata(self):
        """Test metadata extraction from NMEP data."""
        data = pd.DataFrame({
            'State': ['Kano', 'Kano', 'Lagos', 'Kaduna'],
            'Month': ['January', 'January', 'January', 'February'],
            'Year': [2024, 2024, 2024, 2023],
            'Facility': ['F1', 'F2', 'F3', 'F4']
        })
        
        excel_file = self.create_test_excel(data)
        self.parser.data = pd.read_excel(excel_file, sheet_name='raw')
        
        metadata = self.parser._extract_metadata()
        
        # Should extract most common year/month
        self.assertEqual(metadata['year'], 2024)
        self.assertEqual(metadata['month'], 'January')
        
        # Should list all states
        self.assertEqual(len(metadata['states_available']), 3)
        self.assertIn('Kano', metadata['states_available'])
        self.assertIn('Lagos', metadata['states_available'])
        self.assertIn('Kaduna', metadata['states_available'])
        
        # Facility count
        self.assertEqual(metadata['facility_count'], 4)
    
    def test_clean_state_names(self):
        """Test state name cleaning."""
        # Test various state name formats
        test_cases = [
            ('KANO STATE', 'Kano'),
            ('lagos', 'Lagos'),
            ('  Kaduna  ', 'Kaduna'),
            ('FEDERAL CAPITAL TERRITORY', 'FCT'),
            ('F.C.T', 'FCT'),
            ('Akwa-Ibom', 'Akwa Ibom'),
            ('CROSS RIVER', 'Cross River')
        ]
        
        for input_name, expected in test_cases:
            cleaned = self.parser._clean_state_name(input_name)
            self.assertEqual(cleaned, expected, 
                           f"Failed to clean '{input_name}' to '{expected}', got '{cleaned}'")
    
    def test_parse_missing_columns(self):
        """Test parsing files with missing expected columns."""
        # Create data missing some TPR columns
        data = pd.DataFrame({
            'State': ['Kano'],
            'LGA': ['LGA1'],
            'Ward': ['Ward1'],
            'Facility': ['Facility1'],
            'Persons tested positive for malaria by RDT': [10],
            'Persons tested for malaria by RDT': [50]
            # Missing microscopy columns
        })
        
        excel_file = self.create_test_excel(data)
        result = self.parser.parse_file(excel_file)
        
        # Should still parse successfully but note missing columns
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['data']), 1)
    
    def test_parse_empty_file(self):
        """Test parsing empty Excel file."""
        data = pd.DataFrame()
        excel_file = self.create_test_excel(data)
        
        result = self.parser.parse_file(excel_file)
        
        # Should handle gracefully
        self.assertIn('status', result)
        if result['status'] == 'success':
            self.assertEqual(len(result['data']), 0)
    
    def test_parse_different_sheet_names(self):
        """Test parsing files with different sheet names."""
        data = pd.DataFrame({
            'State': ['Kano'],
            'Persons tested positive for malaria by RDT': [10],
            'Persons tested for malaria by RDT': [50]
        })
        
        # Try different sheet names
        for sheet_name in ['raw', 'data', 'Sheet1']:
            excel_file = self.create_test_excel(data, sheet_name=sheet_name)
            
            # Parser expects 'raw' sheet, so only that should work
            result = self.parser.parse_file(excel_file)
            
            if sheet_name == 'raw':
                self.assertEqual(result['status'], 'success')
            else:
                # Should fail or handle missing sheet
                self.assertIn('status', result)
    
    def test_data_type_handling(self):
        """Test handling of different data types."""
        data = pd.DataFrame({
            'State': ['Kano', 'Lagos', 'Kaduna'],
            'Month': ['January', 'February', 3],  # Mixed types
            'Year': [2024, '2024', 2024.0],  # Mixed numeric types
            'Persons tested positive for malaria by RDT': [10, '20', 30.5],
            'Persons tested for malaria by RDT': [50, '100', 150.0]
        })
        
        excel_file = self.create_test_excel(data)
        result = self.parser.parse_file(excel_file)
        
        # Should handle mixed types gracefully
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['data']), 3)
        
        # Check year extraction handles different formats
        metadata = result['metadata']
        self.assertEqual(metadata['year'], 2024)


class TestNMEPColumns(unittest.TestCase):
    """Test NMEP column name handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = NMEPParser()
    
    def test_column_name_mapping(self):
        """Test that all expected NMEP columns are mapped."""
        expected_columns = [
            'state',
            'lga', 
            'ward',
            'facility',
            'facility_level',
            'month',
            'year',
            'outpatient_attendance',
            'rdt_positive_under5',
            'rdt_tested_under5',
            'rdt_positive_over5',
            'rdt_tested_over5',
            'micro_positive_under5',
            'micro_tested_under5',
            'micro_positive_over5',
            'micro_tested_over5'
        ]
        
        for col in expected_columns:
            self.assertIn(col, self.parser.NMEP_COLUMNS,
                         f"Missing column mapping for: {col}")
    
    def test_tpr_marker_columns(self):
        """Test TPR file detection markers."""
        self.assertGreater(len(self.parser.TPR_MARKERS), 0,
                          "No TPR marker columns defined")
        
        # Should include key TPR indicators
        marker_text = ' '.join(self.parser.TPR_MARKERS).lower()
        self.assertIn('tested positive', marker_text)
        self.assertIn('malaria', marker_text)


if __name__ == '__main__':
    unittest.main()