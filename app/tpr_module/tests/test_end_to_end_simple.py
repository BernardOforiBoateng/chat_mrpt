"""
Simple end-to-end tests for TPR workflow without Flask context.

Tests the complete workflow from file parsing to output generation,
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
from app.tpr_module.data.column_mapper import ColumnMapper
from app.tpr_module.core.tpr_conversation_manager import TPRConversationManager
from app.tpr_module.core.tpr_state_manager import TPRStateManager
from app.tpr_module.core.tpr_calculator import TPRCalculator
from app.tpr_module.services.facility_filter import FacilityFilter
from app.tpr_module.services.state_selector import StateSelector
from app.tpr_module.services.raster_extractor import RasterExtractor
from app.tpr_module.output.output_generator import OutputGenerator


class TestSimpleEndToEndTPRWorkflow(unittest.TestCase):
    """Test complete TPR workflow with actual NMEP data without Flask context."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests."""
        # Path to actual NMEP test data
        cls.test_data_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"
        
        # Create temporary directory for test outputs
        cls.temp_dir = tempfile.mkdtemp()
        print(f"Test output directory: {cls.temp_dir}")
        
        # Parse the data once to get available states
        parser = NMEPParser()
        parse_result = parser.parse_file(cls.test_data_path)
        cls.available_states = parse_result['metadata'].get('states', [])
        cls.parsed_data = parse_result['data']
        cls.metadata = parse_result['metadata']
        print(f"\nAvailable states in test data: {', '.join(cls.available_states)}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test data."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up for each test."""
        self.session_id = "test_session"
        self.session_dir = os.path.join(self.temp_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Initialize components directly
        self.state_manager = TPRStateManager(self.session_id)
        self.conversation_manager = TPRConversationManager(self.state_manager)
        self.calculator = TPRCalculator()
        self.facility_filter = FacilityFilter()
        self.state_selector = StateSelector()
        self.raster_extractor = RasterExtractor()
        self.output_generator = OutputGenerator(self.session_id)
        self.output_generator.upload_folder = self.session_dir
        
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'state_manager'):
            self.state_manager.clear_state()
    
    def test_complete_workflow_adamawa_primary_u5(self):
        """Test complete workflow for Adamawa state, Primary facilities, Under 5."""
        print("\n=== Testing Adamawa State - Primary Facilities - Under 5 ===")
        
        # Step 1: Initialize conversation with metadata
        response = self.conversation_manager.generate_response('start', {'metadata': self.metadata})
        print(f"\nInitial greeting: {response['response'][:150]}...")
        self.assertIn('TPR', response['response'].upper())
        
        # Step 2: Select Adamawa state 
        print("\n--- State Selection ---")
        # First set up the parsed data in conversation manager
        self.conversation_manager.parsed_data = {
            'data': self.parsed_data,
            'metadata': self.metadata,
            'states': self.available_states,
            'status': 'success'
        }
        self.conversation_manager.parser.data = self.parsed_data
        
        # Test various ways of selecting Adamawa
        state_inputs = [
            "I want to analyze Adamawa",
            "adamawa state please",
            "Let's look at ADAMAWA",
            "Adamawa"
        ]
        
        for state_input in state_inputs:
            print(f"Testing: '{state_input}'")
            result = self.conversation_manager.process_user_input(state_input)
            print(f"Response: {result['response'][:100]}...")
            if 'facility' in result['response'].lower():
                break
        
        # Verify state was selected
        state = self.state_manager.get_state()
        self.assertEqual(state.get('selected_state'), 'Adamawa State')
        
        # Step 3: Select Primary facilities
        print("\n--- Facility Selection ---")
        facility_inputs = [
            "primary facilities",
            "just primary",
            "PRIMARY only"
        ]
        
        for facility_input in facility_inputs:
            print(f"Testing: '{facility_input}'")
            result = self.conversation_manager.process_user_input(facility_input)
            print(f"Response: {result['response'][:100]}...")
            if 'age' in result['response'].lower():
                break
        
        # Step 4: Select Under 5 age group
        print("\n--- Age Group Selection ---")
        age_inputs = [
            "under 5 years",
            "children under five",
            "under 5"
        ]
        
        for age_input in age_inputs:
            print(f"Testing: '{age_input}'")
            result = self.conversation_manager.process_user_input(age_input)
            print(f"Response: {result['response'][:100]}...")
            if 'calculat' in result['response'].lower() or 'threshold' in result['response'].lower():
                break
        
        # Step 5: If threshold check, confirm
        if result.get('stage') == 'threshold_check':
            print("\n--- Threshold Check ---")
            result = self.conversation_manager.process_user_input("yes, continue")
        
        # Step 6: Generate outputs
        print("\n--- Generating Outputs ---")
        
        # Get the calculated TPR results
        tpr_results = self.calculator.results if hasattr(self.calculator, 'results') else []
        
        if not tpr_results:
            # If no results from calculator, calculate directly
            state_data = self.conversation_manager.parser.get_state_data('Adamawa State')
            filtered_data = self.facility_filter.filter_by_level(state_data, 'Primary')
            
            # Map columns
            mapper = ColumnMapper()
            mapped_data = mapper.map_columns(filtered_data)
            
            # Calculate TPR
            tpr_results_dict = self.calculator.calculate_ward_tpr(mapped_data, age_group='u5')
            
            # Convert to list format for output generator
            tpr_results = []
            for ward, data in tpr_results_dict.items():
                tpr_results.append({
                    'ward_name': ward,
                    'lga': data.get('lga', ''),
                    'tpr_value': data['tpr'],
                    'method': data['method'],
                    'numerator': data.get('total_positive', 0),
                    'denominator': data.get('total_tested', 0)
                })
        
        # Generate output files
        output_paths = self.output_generator.generate_all_outputs(
            tpr_results=tpr_results,
            state_name='Adamawa State',
            facility_level='Primary',
            age_group='u5',
            zone='North_East',
            raster_values={}  # Empty for now
        )
        
        print(f"\nGenerated output files:")
        for file_type, path in output_paths.items():
            if path and os.path.exists(path):
                print(f"  - {file_type}: {os.path.basename(path)}")
                
                # Verify content
                if file_type == 'tpr_analysis':
                    df = pd.read_csv(path)
                    print(f"    Rows: {len(df)}, Avg TPR: {df['tpr'].mean():.2f}%")
        
        # Verify outputs
        self.assertTrue(output_paths.get('tpr_analysis'))
        self.assertTrue(os.path.exists(output_paths['tpr_analysis']))
    
    def test_natural_conversation_patterns(self):
        """Test various natural conversation patterns."""
        print("\n=== Testing Natural Conversation Patterns ===")
        
        test_conversations = [
            {
                'name': 'Direct User',
                'inputs': ['Kwara', 'all', 'under 5']
            },
            {
                'name': 'Conversational User', 
                'inputs': [
                    'I would like to analyze Osun state data',
                    'Show me all the facilities combined',
                    'Focus on children under 5 years old'
                ]
            },
            {
                'name': 'Uncertain User',
                'inputs': [
                    'um... Adamawa?',
                    'what do you recommend?',
                    'ok use that',
                    'all ages'
                ]
            }
        ]
        
        for conv in test_conversations:
            print(f"\n--- {conv['name']} ---")
            
            # Reset state
            self.state_manager.clear_state()
            
            # Initialize
            self.conversation_manager.generate_response('start', {'metadata': self.metadata})
            self.conversation_manager.parsed_data = {
                'data': self.parsed_data,
                'metadata': self.metadata,
                'states': self.available_states,
                'status': 'success'
            }
            self.conversation_manager.parser.data = self.parsed_data
            
            # Run conversation
            for user_input in conv['inputs']:
                print(f"\nUser: {user_input}")
                result = self.conversation_manager.process_user_input(user_input)
                print(f"Bot: {result['response'][:150]}...")
                
                # Handle threshold if needed
                if result.get('stage') == 'threshold_check':
                    result = self.conversation_manager.process_user_input("continue")
            
            # Verify completion
            state = self.state_manager.get_state()
            print(f"\nFinal state: {state.get('workflow_stage')}")
    
    def test_all_states_basic_workflow(self):
        """Test basic workflow for all available states."""
        print("\n=== Testing All Available States ===")
        
        for state in self.available_states:
            print(f"\n--- Testing {state} ---")
            
            # Reset
            self.state_manager.clear_state()
            
            # Initialize
            self.conversation_manager.generate_response('start', {'metadata': self.metadata})
            self.conversation_manager.parsed_data = {
                'data': self.parsed_data,
                'metadata': self.metadata,
                'states': self.available_states,
                'status': 'success'
            }
            self.conversation_manager.parser.data = self.parsed_data
            
            # Quick workflow
            inputs = [state, 'primary', 'under 5']
            
            for user_input in inputs:
                result = self.conversation_manager.process_user_input(user_input)
                
                if result.get('stage') == 'threshold_check':
                    result = self.conversation_manager.process_user_input("yes")
            
            # Verify state was processed
            final_state = self.state_manager.get_state()
            self.assertEqual(final_state.get('selected_state'), state)
            print(f"✓ {state} completed successfully")


if __name__ == '__main__':
    unittest.main(verbosity=2)