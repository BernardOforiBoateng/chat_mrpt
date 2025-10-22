"""
Test TPR upload detection integration.

Tests that TPR files are properly detected during upload.
"""

import unittest
import tempfile
import os
import sys
import pandas as pd
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.integration.upload_detector import TPRUploadDetector


class MockFileStorage:
    """Mock Flask FileStorage object for testing."""
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content
        self.stream = BytesIO(content)
    
    def read(self):
        return self.content
    
    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self.content)
    
    def seek(self, pos):
        self.stream.seek(pos)


class TestUploadIntegration(unittest.TestCase):
    """Test TPR upload detection integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = TPRUploadDetector()
        self.temp_files = []
    
    def tearDown(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def create_tpr_excel_content(self):
        """Create a valid TPR Excel file content."""
        # Create TPR data
        data = pd.DataFrame({
            'State': ['Kano', 'Kano'],
            'LGA': ['LGA1', 'LGA2'],
            'Ward': ['Ward1', 'Ward2'],
            'Health Faccility': ['Facility1', 'Facility2'],
            'level': ['Primary', 'Primary'],
            'ownership': ['Public', 'Public'],
            'periodname': ['January 2024', 'January 2024'],
            'periodcode': ['202401', '202401'],
            'Persons tested positive for malaria by RDT <5yrs': [10, 20],
            'Persons presenting with fever & tested by RDT <5yrs': [50, 100],
            'Persons tested positive for malaria by Microscopy <5yrs': [8, 15],
            'Persons presenting with fever and tested by Microscopy <5yrs': [40, 80]
        })
        
        # Write to bytes
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name='raw', index=False)
        
        return output.getvalue()
    
    def create_regular_csv_content(self):
        """Create regular CSV content."""
        data = pd.DataFrame({
            'ward_name': ['Ward1', 'Ward2'],
            'population': [1000, 2000],
            'cases': [10, 20]
        })
        
        return data.to_csv(index=False).encode('utf-8')
    
    def test_detect_tpr_excel(self):
        """Test detection of TPR Excel file."""
        # Create mock TPR file
        content = self.create_tpr_excel_content()
        mock_file = MockFileStorage('test_tpr.xlsx', content)
        
        # Test detection
        upload_type, detection_info = self.detector.detect_tpr_upload(
            csv_file=mock_file,
            shapefile=None,
            csv_content=content
        )
        
        # Should detect as TPR
        self.assertEqual(upload_type, 'tpr_excel')
        self.assertTrue(detection_info['is_tpr'])
        self.assertEqual(detection_info['file_type'], 'nmep_excel')
    
    def test_detect_regular_csv(self):
        """Test that regular CSV is not detected as TPR."""
        # Create regular CSV
        content = self.create_regular_csv_content()
        mock_file = MockFileStorage('regular_data.csv', content)
        
        # Test detection
        upload_type, detection_info = self.detector.detect_tpr_upload(
            csv_file=mock_file,
            shapefile=None,
            csv_content=content
        )
        
        # Should be standard
        self.assertEqual(upload_type, 'standard')
        self.assertFalse(detection_info['is_tpr'])
    
    def test_detect_tpr_with_shapefile(self):
        """Test detection of TPR Excel with shapefile."""
        # Create mock files
        tpr_content = self.create_tpr_excel_content()
        mock_tpr = MockFileStorage('test_tpr.xlsx', tpr_content)
        mock_shapefile = MockFileStorage('boundaries.zip', b'dummy shapefile content')
        
        # Test detection
        upload_type, detection_info = self.detector.detect_tpr_upload(
            csv_file=mock_tpr,
            shapefile=mock_shapefile,
            csv_content=tpr_content
        )
        
        # Should detect as TPR with shapefile
        self.assertEqual(upload_type, 'tpr_shapefile')
        self.assertTrue(detection_info['is_tpr'])
        self.assertTrue(detection_info['has_shapefile'])
    
    def test_empty_file_handling(self):
        """Test handling of empty or missing files."""
        # Test with no file
        upload_type, detection_info = self.detector.detect_tpr_upload(
            csv_file=None,
            shapefile=None
        )
        
        self.assertEqual(upload_type, 'standard')
        self.assertFalse(detection_info['is_tpr'])
    
    def test_should_use_tpr_workflow(self):
        """Test workflow routing decision."""
        # TPR types should use TPR workflow
        self.assertTrue(self.detector.should_use_tpr_workflow('tpr_excel'))
        self.assertTrue(self.detector.should_use_tpr_workflow('tpr_shapefile'))
        
        # Standard types should not
        self.assertFalse(self.detector.should_use_tpr_workflow('standard'))
        self.assertFalse(self.detector.should_use_tpr_workflow('csv_only'))
        self.assertFalse(self.detector.should_use_tpr_workflow('csv_shapefile'))
    
    def test_prepare_tpr_session(self):
        """Test TPR session preparation."""
        detection_info = {
            'is_tpr': True,
            'metadata': {
                'year': 2024,
                'month': 'January',
                'states_available': ['Kano', 'Lagos']
            },
            'validation': {
                'is_valid': True
            }
        }
        
        result = self.detector.prepare_tpr_session('test_session', detection_info)
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('session_data', result)
        
        session_data = result['session_data']
        self.assertEqual(session_data['workflow_type'], 'tpr')
        self.assertTrue(session_data['tpr_detected'])
        self.assertEqual(session_data['next_step'], 'state_selection')
        self.assertEqual(session_data['available_states'], ['Kano', 'Lagos'])


if __name__ == '__main__':
    unittest.main()