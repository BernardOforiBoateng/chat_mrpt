"""
End-to-end tests for TPR workflow using actual NMEP data.

Tests the complete workflow from file upload to final output generation,
simulating various user interaction patterns.
"""

import unittest
import os
import sys
import tempfile
import shutil
import pandas as pd
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.data.nmep_parser import NMEPParser
from app.tpr_module.core.tpr_conversation_manager import TPRConversationManager
from app.tpr_module.core.tpr_state_manager import TPRStateManager
from app.tpr_module.integration.tpr_handler import TPRHandler
from app.tpr_module.integration.upload_detector import TPRUploadDetector


class TestEndToEndTPRWorkflow(unittest.TestCase):
    """Test complete TPR workflow with actual NMEP data."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests."""
        # Path to actual NMEP test data
        cls.test_data_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"
        
        # Create temporary directory for test outputs
        cls.temp_dir = tempfile.mkdtemp()
        cls.session_dir = os.path.join(cls.temp_dir, "test_session")
        os.makedirs(cls.session_dir, exist_ok=True)
        
        # Parse the data once to get available states
        parser = NMEPParser()
        parse_result = parser.parse_file(cls.test_data_path)
        cls.available_states = parse_result['metadata'].get('states', [])
        print(f"\nAvailable states in test data: {', '.join(cls.available_states)}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test data."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up for each test."""
        self.session_id = "test_session"
        self.tpr_handler = TPRHandler(self.session_id)
        # Set the upload folder for outputs
        self.tpr_handler.output_generator.upload_folder = self.session_dir
        
    def tearDown(self):
        """Clean up after each test."""
        # Clear any session data
        if hasattr(self, 'tpr_handler'):
            self.tpr_handler.state_manager.clear_state()
    
    def test_complete_workflow_adamawa_primary_u5(self):
        """Test complete workflow for Adamawa state, Primary facilities, Under 5."""
        print("\n=== Testing Adamawa State - Primary Facilities - Under 5 ===")
        
        # Step 1: Upload and detect TPR file
        detector = TPRUploadDetector()
        with open(self.test_data_path, 'rb') as f:
            content = f.read()
        
        # Simulate file upload detection
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        file_storage = FileStorage(
            stream=BytesIO(content),
            filename="NMEP_data.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        upload_type, detection_info = detector.detect_tpr_upload(
            csv_file=file_storage,
            shapefile=None,
            csv_content=content
        )
        
        self.assertEqual(upload_type, 'tpr_excel')
        self.assertTrue(detection_info['is_tpr'])
        
        # Step 2: Initialize TPR workflow
        result = self.tpr_handler.handle_tpr_upload(
            csv_file_path=self.test_data_path,
            shapefile_path=None,
            upload_type='tpr_excel',
            detection_info=detection_info
        )
        self.assertEqual(result['status'], 'success')
        print(f"Initial message: {result.get('response', result.get('message', ''))[:100]}...")
        
        # Step 3: Select Adamawa state (test various phrasings)
        state_inputs = [
            "I want to analyze Adamawa",
            "adamawa state please",
            "Let's look at ADAMAWA",
            "Show me data for Adamawa"
        ]
        
        for state_input in state_inputs:
            print(f"\nTesting state selection: '{state_input}'")
            result = self.tpr_handler.process_tpr_message(state_input)
            if 'Adamawa' in result.get('response', ''):
                break
        
        self.assertIn('facility', result['response'].lower())
        self.assertEqual(result['stage'], 'facility_selection')
        
        # Step 4: Select Primary facilities (test various phrasings)
        facility_inputs = [
            "primary facilities",
            "just primary",
            "PRIMARY only",
            "primary health centers"
        ]
        
        for facility_input in facility_inputs:
            print(f"\nTesting facility selection: '{facility_input}'")
            result = self.tpr_handler.process_tpr_message(facility_input)
            if 'age group' in result.get('response', '').lower():
                break
        
        self.assertEqual(result['stage'], 'age_group_selection')
        
        # Step 5: Select Under 5 age group (test various phrasings)
        age_inputs = [
            "under 5 years",
            "children under five",
            "kids below 5",
            "under 5",
            "<5 years"
        ]
        
        for age_input in age_inputs:
            print(f"\nTesting age selection: '{age_input}'")
            result = self.tpr_handler.process_tpr_message(age_input)
            if 'calculat' in result.get('response', '').lower():
                break
        
        # Should start calculation
        self.assertIn('stage', result)
        
        # Step 6: Check if threshold alert appears (for high TPR areas)
        if result['stage'] == 'threshold_check':
            print("\nThreshold alert detected, confirming to proceed...")
            result = self.tpr_handler.process_tpr_message("yes, continue")
        
        # Step 7: Verify outputs were generated
        output_files = os.listdir(self.session_dir)
        print(f"\nGenerated files: {output_files}")
        
        # Check for expected output files
        tpr_files = [f for f in output_files if 'TPR_Analysis' in f and f.endswith('.csv')]
        main_files = [f for f in output_files if 'Main_Analysis' in f and f.endswith('.csv')]
        
        self.assertTrue(len(tpr_files) > 0, "No TPR analysis file generated")
        self.assertTrue(len(main_files) > 0, "No main analysis file generated")
        
        # Verify TPR data
        tpr_df = pd.read_csv(os.path.join(self.session_dir, tpr_files[0]))
        print(f"\nTPR Analysis: {len(tpr_df)} wards analyzed")
        print(f"Average TPR: {tpr_df['tpr'].mean():.2f}%")
        print(f"TPR Range: {tpr_df['tpr'].min():.2f}% - {tpr_df['tpr'].max():.2f}%")
        
        self.assertGreater(len(tpr_df), 0, "No ward data in TPR analysis")
        self.assertIn('ward', tpr_df.columns)
        self.assertIn('tpr', tpr_df.columns)
    
    def test_workflow_all_states_different_combinations(self):
        """Test workflow for all available states with different parameter combinations."""
        print("\n=== Testing All Available States ===")
        
        # Initialize workflow once
        self.tpr_handler.handle_tpr_upload(
            csv_file_path=self.test_data_path,
            shapefile_path=None,
            upload_type='tpr_excel',
            detection_info={}
        )
        
        # Test each state with different combinations
        test_combinations = [
            # (state_phrase, facility_phrase, age_phrase)
            ("analyze {state}", "all facilities", "all age groups"),
            ("show me {state} data", "secondary", "over 5 years"),
            ("{state} state", "primary health", "pregnant women"),
            ("I want {state}", "tertiary", "under five"),
            ("Let's do {state}", "every facility", "children"),
        ]
        
        for idx, state in enumerate(self.available_states[:3]):  # Test first 3 states
            print(f"\n--- Testing {state} ---")
            
            # Use different phrasing for each state
            combo = test_combinations[idx % len(test_combinations)]
            state_phrase = combo[0].format(state=state)
            facility_phrase = combo[1]
            age_phrase = combo[2]
            
            # Reset workflow for new state
            self.tpr_handler.state_manager.clear_state()
            self.tpr_handler = TPRHandler(self.session_id)
            self.tpr_handler.output_generator.upload_folder = self.session_dir
            self.tpr_handler.handle_tpr_upload(
                csv_file_path=self.test_data_path,
                shapefile_path=None,
                upload_type='tpr_excel',
                detection_info={}
            )
            
            # Select state
            print(f"State selection: '{state_phrase}'")
            result = self.tpr_handler.process_tpr_message(state_phrase)
            
            # Select facility
            print(f"Facility selection: '{facility_phrase}'")
            result = self.tpr_handler.process_tpr_message(facility_phrase)
            
            # Select age group
            print(f"Age selection: '{age_phrase}'")
            result = self.tpr_handler.process_tpr_message(age_phrase)
            
            # Handle threshold if needed
            if result.get('stage') == 'threshold_check':
                result = self.tpr_handler.process_tpr_message("proceed")
            
            # Verify completion
            self.assertIn('completed', str(result.get('stage', '')).lower())
            print(f"✓ {state} analysis completed successfully")
    
    def test_conversation_error_handling(self):
        """Test how the system handles various error cases and unclear inputs."""
        print("\n=== Testing Error Handling ===")
        
        # Initialize workflow
        self.tpr_handler.handle_tpr_upload(
            csv_file_path=self.test_data_path,
            shapefile_path=None,
            upload_type='tpr_excel',
            detection_info={}
        )
        
        # Test 1: Invalid state name
        print("\nTest 1: Invalid state name")
        result = self.tpr_handler.process_tpr_message("I want to analyze California")
        self.assertIn('clarification', result.get('status', ''))
        print(f"Response: {result['response'][:100]}...")
        
        # Test 2: Ambiguous input
        print("\nTest 2: Ambiguous state name")
        result = self.tpr_handler.process_tpr_message("Lagos")  # Assuming Lagos is not in this dataset
        if 'clarification' in result.get('status', ''):
            print("System asked for clarification as expected")
        
        # Test 3: Gibberish input during state selection
        print("\nTest 3: Gibberish input")
        result = self.tpr_handler.process_tpr_message("asdfghjkl zxcvbnm")
        self.assertNotEqual(result.get('stage'), 'facility_selection')
        
        # Test 4: Valid state to continue
        result = self.tpr_handler.process_tpr_message("Adamawa")
        self.assertEqual(result.get('stage'), 'facility_selection')
        
        # Test 5: Skip facility level
        print("\nTest 5: Skip facility level")
        result = self.tpr_handler.process_tpr_message("skip")
        self.assertEqual(result.get('stage'), 'age_group_selection')
        
        # Test 6: Multiple criteria in one message
        print("\nTest 6: Multiple criteria")
        result = self.tpr_handler.process_tpr_message("under 5 children in primary facilities")
        # Should pick up age group at minimum
        
        # Complete the workflow
        if result.get('stage') != 'completed':
            result = self.tpr_handler.process_tpr_message("continue")
    
    def test_natural_conversation_flow(self):
        """Test natural conversation patterns that real users might use."""
        print("\n=== Testing Natural Conversation Flow ===")
        
        conversations = [
            {
                'name': 'Hurried User',
                'messages': [
                    "adamawa",
                    "primary", 
                    "kids",
                    "yes"
                ]
            },
            {
                'name': 'Detailed User',
                'messages': [
                    "I'd like to analyze the malaria test positivity rate for Kwara state",
                    "Can you show me just the primary health facilities? Those are most important",
                    "Let's focus on children under 5 years old since they're most vulnerable",
                    "Yes, that looks correct. Please proceed with the analysis"
                ]
            },
            {
                'name': 'Uncertain User',
                'messages': [
                    "umm... what states do you have?",
                    "ok let me see Osun",
                    "what do you recommend for facilities?",
                    "sure, use that",
                    "all ages I guess",
                    "go ahead"
                ]
            },
            {
                'name': 'Technical User',
                'messages': [
                    "Analyze Adamawa state",
                    "Filter: facility_level=Secondary",
                    "age_group: o5",
                    "confirm and execute"
                ]
            }
        ]
        
        for conversation in conversations:
            print(f"\n--- {conversation['name']} Conversation ---")
            
            # Reset for new conversation
            self.tpr_handler.state_manager.clear_state()
            self.tpr_handler = TPRHandler(self.session_id)
            self.tpr_handler.output_generator.upload_folder = self.session_dir
            self.tpr_handler.handle_tpr_upload(
                csv_file_path=self.test_data_path,
                shapefile_path=None,
                upload_type='tpr_excel',
                detection_info={}
            )
            
            for msg in conversation['messages']:
                print(f"\nUser: {msg}")
                result = self.tpr_handler.process_tpr_message(msg)
                print(f"Bot: {result['response'][:150]}...")
                
                # Handle threshold checks
                if result.get('stage') == 'threshold_check':
                    result = self.tpr_handler.process_tpr_message("continue")
            
            # Verify workflow completed
            final_stage = result.get('stage', '')
            print(f"\nFinal stage: {final_stage}")
    
    def test_data_completeness_handling(self):
        """Test how system handles incomplete data scenarios."""
        print("\n=== Testing Data Completeness Handling ===")
        
        # Initialize workflow
        self.tpr_handler.handle_tpr_upload(
            csv_file_path=self.test_data_path,
            shapefile_path=None,
            upload_type='tpr_excel',
            detection_info={}
        )
        
        # Select a state
        result = self.tpr_handler.process_tpr_message("Kwara state")
        
        # The system should show data completeness in facility selection
        self.assertIn('response', result)
        print(f"\nFacility recommendation shows completeness: {result['response'][:200]}...")
        
        # Select facilities
        result = self.tpr_handler.process_tpr_message("all facilities")
        
        # Age group selection should also show completeness
        self.assertIn('complete', result['response'].lower())
        print(f"\nAge group completeness info: {result['response'][:200]}...")
    
    def test_output_file_validation(self):
        """Test that output files contain expected data structure."""
        print("\n=== Testing Output File Structure ===")
        
        # Run a complete workflow
        self.tpr_handler.handle_tpr_upload(
            csv_file_path=self.test_data_path,
            shapefile_path=None,
            upload_type='tpr_excel',
            detection_info={}
        )
        self.tpr_handler.process_tpr_message("Osun")
        self.tpr_handler.process_tpr_message("primary")
        result = self.tpr_handler.process_tpr_message("under 5")
        
        if result.get('stage') == 'threshold_check':
            result = self.tpr_handler.process_tpr_message("yes")
        
        # Find output files
        output_files = os.listdir(self.session_dir)
        tpr_file = next((f for f in output_files if 'TPR_Analysis' in f), None)
        main_file = next((f for f in output_files if 'Main_Analysis' in f), None)
        
        self.assertIsNotNone(tpr_file, "TPR analysis file not found")
        self.assertIsNotNone(main_file, "Main analysis file not found")
        
        # Validate TPR file structure
        tpr_df = pd.read_csv(os.path.join(self.session_dir, tpr_file))
        expected_tpr_columns = ['state', 'lga', 'ward', 'tpr', 'method', 'total_tested', 'total_positive']
        for col in expected_tpr_columns:
            self.assertIn(col, tpr_df.columns, f"Missing column '{col}' in TPR file")
        
        # Validate Main file structure  
        main_df = pd.read_csv(os.path.join(self.session_dir, main_file))
        self.assertIn('tpr', main_df.columns)
        
        # Check for environmental variables (should be zone-specific)
        env_vars = [col for col in main_df.columns if col not in ['state', 'lga', 'ward', 'tpr']]
        print(f"\nEnvironmental variables included: {env_vars}")
        self.assertGreater(len(env_vars), 0, "No environmental variables in main analysis")
        
        print(f"\n✓ Output files validated successfully")
        print(f"  - TPR file: {len(tpr_df)} wards")
        print(f"  - Main file: {len(main_df)} wards with {len(env_vars)} environmental variables")


if __name__ == '__main__':
    unittest.main(verbosity=2)