#!/usr/bin/env python3
"""
Unit Test for DataHandler Initialization Fix

Tests that DataHandler can be properly initialized with session_folder
and that the trigger_risk_analysis method correctly passes this argument.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestDataHandlerInitializationFix(unittest.TestCase):
    """Test the DataHandler initialization fix in trigger_risk_analysis"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_session_id = "test_session_123"
        self.temp_dir = tempfile.mkdtemp()
        self.session_folder = os.path.join(self.temp_dir, "instance", "uploads", self.test_session_id)
        os.makedirs(self.session_folder, exist_ok=True)
        
        # Create required files for risk analysis
        with open(os.path.join(self.session_folder, "raw_data.csv"), "w") as f:
            f.write("WardName,Value\nWard1,100\n")
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_datahandler_requires_session_folder(self):
        """Test that DataHandler requires session_folder argument"""
        from app.data import DataHandler
        
        # This should raise TypeError without session_folder
        with self.assertRaises(TypeError) as context:
            DataHandler()
        
        self.assertIn("missing 1 required positional argument", str(context.exception))
        self.assertIn("session_folder", str(context.exception))
    
    def test_datahandler_accepts_session_folder(self):
        """Test that DataHandler can be initialized with session_folder"""
        from app.data import DataHandler
        
        # This should work with session_folder
        data_handler = DataHandler(self.session_folder)
        
        self.assertIsNotNone(data_handler)
        self.assertEqual(data_handler.session_folder, self.session_folder)
    
    @patch('app.analysis.engine.AnalysisEngine')
    @patch('app.data.DataHandler')
    def test_trigger_risk_analysis_passes_session_folder(self, mock_data_handler_class, mock_analysis_engine_class):
        """Test that trigger_risk_analysis correctly passes session_folder to DataHandler"""
        from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
        from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
        
        # Setup mocks
        mock_data_handler = MagicMock()
        mock_data_handler_class.return_value = mock_data_handler
        
        mock_analysis_engine = MagicMock()
        mock_analysis_engine.run_composite_analysis.return_value = {
            'status': 'success',
            'visualizations_created': []
        }
        mock_analysis_engine_class.return_value = mock_analysis_engine
        
        # Create state manager mock
        state_manager = MagicMock(spec=DataAnalysisStateManager)
        
        # Create TPRDataAnalyzer mock (no arguments in constructor)
        tpr_analyzer = MagicMock()
        
        # Create workflow handler
        handler = TPRWorkflowHandler(self.test_session_id, state_manager, tpr_analyzer)
        
        # Override session_folder path for test
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Call trigger_risk_analysis
            result = handler.trigger_risk_analysis()
        
        # Verify DataHandler was called with session_folder
        expected_session_folder = f"instance/uploads/{self.test_session_id}"
        mock_data_handler_class.assert_called_once_with(expected_session_folder)
        
        # Verify AnalysisEngine was created with the data_handler
        mock_analysis_engine_class.assert_called_once_with(mock_data_handler)
        
        # Verify run_composite_analysis was called with correct parameters
        mock_analysis_engine.run_composite_analysis.assert_called_once_with(
            session_id=self.test_session_id,
            variables=None
        )
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertTrue(result.get('success'))
        self.assertIn('message', result)
    
    def test_trigger_risk_analysis_handles_missing_files(self):
        """Test that trigger_risk_analysis handles missing raw_data.csv gracefully"""
        from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
        from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
        
        # Remove the raw_data.csv file
        raw_data_path = os.path.join(self.session_folder, "raw_data.csv")
        if os.path.exists(raw_data_path):
            os.remove(raw_data_path)
        
        # Create mocks
        state_manager = MagicMock(spec=DataAnalysisStateManager)
        tpr_analyzer = MagicMock()
        
        # Create workflow handler
        handler = TPRWorkflowHandler(self.test_session_id, state_manager, tpr_analyzer)
        
        # Call trigger_risk_analysis
        result = handler.trigger_risk_analysis()
        
        # Should return error
        self.assertIsNotNone(result)
        self.assertFalse(result.get('success'))
        self.assertIn("TPR data file not found", result.get('message', ''))


class TestIntegrationDataHandler(unittest.TestCase):
    """Integration test for DataHandler with real components"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_session_id = "test_integration"
        self.session_folder = f"instance/uploads/{self.test_session_id}"
        os.makedirs(self.session_folder, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.session_folder):
            shutil.rmtree(self.session_folder)
    
    def test_datahandler_initialization_in_context(self):
        """Test DataHandler initialization in actual context"""
        from app.models.data_handler import DataHandler
        from app.analysis.engine import AnalysisEngine
        
        # Initialize DataHandler with session folder
        data_handler = DataHandler(self.session_folder)
        
        # Should be initialized properly
        self.assertIsNotNone(data_handler)
        self.assertEqual(data_handler.session_folder, self.session_folder)
        
        # Should be able to create AnalysisEngine with it
        analysis_engine = AnalysisEngine(data_handler)
        self.assertIsNotNone(analysis_engine)
        self.assertEqual(analysis_engine.data_handler, data_handler)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)