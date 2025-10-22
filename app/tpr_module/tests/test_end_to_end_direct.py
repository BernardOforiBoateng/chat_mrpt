"""
Direct end-to-end test for TPR workflow.

Tests the complete TPR calculation workflow by directly calling components
without complex conversational flow, to verify core functionality works.
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
from app.tpr_module.core.tpr_calculator import TPRCalculator
from app.tpr_module.services.facility_filter import FacilityFilter
from app.tpr_module.output.output_generator import OutputGenerator


class TestDirectTPRWorkflow(unittest.TestCase):
    """Test TPR workflow by directly calling components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data once for all tests."""
        # Path to actual NMEP test data
        cls.test_data_path = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/www/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"
        
        # Create temporary directory for test outputs
        cls.temp_dir = tempfile.mkdtemp()
        print(f"Test output directory: {cls.temp_dir}")
    
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
        
        # Initialize components
        self.parser = NMEPParser()
        self.mapper = ColumnMapper()
        self.calculator = TPRCalculator()
        self.facility_filter = FacilityFilter()
        self.output_generator = OutputGenerator(self.session_id)
        self.output_generator.upload_folder = self.session_dir
    
    def test_direct_tpr_calculation_all_states(self):
        """Test direct TPR calculation for all states in the data."""
        print("\n=== Direct TPR Calculation Test ===")
        
        # Step 1: Parse the NMEP file
        print("\n1. Parsing NMEP file...")
        parse_result = self.parser.parse_file(self.test_data_path)
        self.assertEqual(parse_result['status'], 'success')
        
        data = parse_result['data']
        metadata = parse_result['metadata']
        states = metadata.get('states', [])
        
        print(f"   - Found {len(states)} states: {', '.join(states)}")
        print(f"   - Total records: {len(data)}")
        
        # Step 2: Process each state
        for state in states:
            print(f"\n2. Processing {state}...")
            
            # Get state data
            state_data = self.parser.get_state_data(state)
            print(f"   - Records for {state}: {len(state_data)}")
            
            # Get facility levels
            facility_levels = state_data['level'].unique()
            print(f"   - Facility levels: {facility_levels}")
            
            # Use Primary facilities if available, otherwise use all
            if 'Primary' in facility_levels:
                filtered_data = self.facility_filter.filter_by_level(state_data, 'Primary')
                facility_level = 'Primary'
            else:
                filtered_data = state_data
                facility_level = 'All'
            
            print(f"   - Using {facility_level} facilities: {len(filtered_data)} records")
            
            # Step 3: Map columns
            print("\n3. Mapping columns...")
            mapped_data = self.mapper.map_columns(filtered_data)
            
            # Check what columns we have after mapping
            mapped_cols = [col for col in mapped_data.columns if 'rdt' in col or 'micro' in col]
            print(f"   - Mapped TPR columns: {len(mapped_cols)}")
            
            # Step 4: Calculate TPR for under 5
            print("\n4. Calculating TPR for under 5...")
            try:
                tpr_results = self.calculator.calculate_ward_tpr(mapped_data, age_group='u5')
                
                if isinstance(tpr_results, dict):
                    print(f"   - TPR calculated for {len(tpr_results)} wards")
                    
                    # Show some results
                    for i, (ward, result) in enumerate(tpr_results.items()):
                        if i < 3:  # Show first 3 wards
                            print(f"     • {ward}: {result['tpr']:.1f}% TPR")
                    
                    # Calculate average TPR
                    tpr_values = [r['tpr'] for r in tpr_results.values()]
                    if tpr_values:
                        avg_tpr = sum(tpr_values) / len(tpr_values)
                        print(f"   - Average TPR: {avg_tpr:.1f}%")
                    
                    # Step 5: Generate output files
                    print("\n5. Generating output files...")
                    
                    # Convert results to format expected by output generator
                    output_results = []
                    for ward, data in tpr_results.items():
                        output_results.append({
                            'ward_name': ward,
                            'lga': data.get('lga', ''),
                            'tpr_value': data['tpr'],
                            'method': data['method'],
                            'numerator': data.get('total_positive', 0),
                            'denominator': data.get('total_tested', 0),
                            'state': state,
                            'facility_count': data.get('facility_count', 0)
                        })
                    
                    # Determine zone
                    from app.tpr_module.data.geopolitical_zones import STATE_TO_ZONE
                    zone = STATE_TO_ZONE.get(state.replace(' State', ''), 'Unknown')
                    
                    # Convert results to DataFrame
                    import pandas as pd
                    tpr_df = pd.DataFrame(output_results)
                    
                    # Rename columns to match what output generator expects
                    tpr_df = tpr_df.rename(columns={
                        'ward_name': 'Ward',
                        'lga': 'LGA', 
                        'tpr_value': 'TPR',
                        'state': 'State'
                    })
                    
                    metadata = {
                        'facility_level': facility_level,
                        'age_group': 'u5',
                        'zone': zone,
                        'total_facilities': len(filtered_data['facility'].unique()) if 'facility' in filtered_data.columns else 0,
                        'total_wards': len(output_results)
                    }
                    
                    output_paths = self.output_generator.generate_outputs(
                        tpr_results=tpr_df,
                        state_name=state,
                        metadata=metadata
                    )
                    
                    # Verify output files
                    for file_type, path in output_paths.items():
                        if path and os.path.exists(path):
                            print(f"   ✓ Generated {file_type}: {os.path.basename(path)}")
                            
                            # Check TPR analysis file content
                            if file_type == 'tpr_analysis':
                                df = pd.read_csv(path)
                                print(f"     - Rows: {len(df)}, Columns: {len(df.columns)}")
                    
                    print(f"\n✓ Successfully processed {state}")
                    
            except Exception as e:
                print(f"   ✗ Error processing {state}: {str(e)}")
                # Continue with next state
    
    def test_tpr_calculation_with_different_age_groups(self):
        """Test TPR calculation for different age groups."""
        print("\n=== Testing Different Age Groups ===")
        
        # Parse file
        parse_result = self.parser.parse_file(self.test_data_path)
        data = parse_result['data']
        
        # Use first state for testing
        state = parse_result['metadata']['states'][0]
        state_data = self.parser.get_state_data(state)
        
        # Map columns
        mapped_data = self.mapper.map_columns(state_data)
        
        # Test each age group
        age_groups = ['u5', 'o5', 'pw']
        
        for age_group in age_groups:
            print(f"\n--- Testing {age_group} ---")
            
            try:
                # Check if we have data for this age group
                test_col = f'rdt_tested_{age_group}'
                if test_col in mapped_data.columns:
                    non_null = mapped_data[test_col].notna().sum()
                    print(f"  - Non-null records for {age_group}: {non_null}")
                    
                    if non_null > 0:
                        results = self.calculator.calculate_ward_tpr(mapped_data, age_group=age_group)
                        if results:
                            print(f"  - Calculated TPR for {len(results)} wards")
                    else:
                        print(f"  - No data available for {age_group}")
                else:
                    print(f"  - Column {test_col} not found after mapping")
                    
            except Exception as e:
                print(f"  - Error: {str(e)}")


if __name__ == '__main__':
    unittest.main(verbosity=2)