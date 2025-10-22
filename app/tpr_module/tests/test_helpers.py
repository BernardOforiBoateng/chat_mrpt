"""
Test helpers for TPR module tests.

Provides utilities to set up test data and simulate real workflows.
"""

import pandas as pd
from typing import Dict, List, Any


def create_test_nmep_data(states: List[str] = None, mapped: bool = True) -> pd.DataFrame:
    """
    Create test NMEP data that matches the expected structure.
    
    Args:
        states: List of states to include (default: ['Kano', 'Lagos'])
        mapped: Whether to return column-mapped data (default: True)
        
    Returns:
        DataFrame with NMEP structure
    """
    if states is None:
        states = ['Kano', 'Lagos']
    
    # Create test data with proper column names
    data = []
    for state in states:
        for month in ['January 2024', 'February 2024']:
            for facility_num in range(3):
                data.append({
                    'State': f'ng {state}',  # NMEP format with prefix
                    'LGA': f'LGA{facility_num + 1}',
                    'Ward': f'Ward{facility_num + 1}',
                    'Health Faccility': f'{state}_Facility_{facility_num + 1}',
                    'level': 'Primary' if facility_num < 2 else 'Secondary',
                    'ownership': 'Public',
                    'periodname': month,
                    'periodcode': '202401' if 'January' in month else '202402',
                    # RDT data for under 5
                    'Persons presenting with fever & tested by RDT <5yrs': 50 + facility_num * 10,
                    'Persons tested positive for malaria by RDT <5yrs': 10 + facility_num * 2,
                    # Microscopy data for under 5
                    'Persons presenting with fever and tested by Microscopy <5yrs': 40 + facility_num * 5,
                    'Persons tested positive for malaria by Microscopy <5yrs': 8 + facility_num,
                    # Outpatient data
                    'Total Outpatient attendance': 200 + facility_num * 50
                })
    
    df = pd.DataFrame(data)
    
    if mapped:
        # Apply column mapping to match what the TPR calculator expects
        from app.tpr_module.data.column_mapper import ColumnMapper
        mapper = ColumnMapper()
        df = mapper.map_columns(df)
    
    return df


def create_test_metadata(states: List[str] = None) -> Dict[str, Any]:
    """
    Create test metadata that matches NMEP parser output.
    
    Args:
        states: List of states (default: ['Kano', 'Lagos'])
        
    Returns:
        Metadata dictionary
    """
    if states is None:
        states = ['Kano', 'Lagos']
    
    return {
        'states': states,
        'state_count': len(states),
        'time_range': 'January 2024 to February 2024',
        'months_covered': 2,
        'facility_levels': {
            'Primary': 4,
            'Secondary': 2
        },
        'total_facilities': 6,
        'total_records': 12,
        'year': 2024,
        'month': 'February'
    }


def setup_conversation_manager_for_test(conversation_manager, states: List[str] = None):
    """
    Set up conversation manager with test data to simulate post-upload state.
    
    Args:
        conversation_manager: TPRConversationManager instance
        states: List of states to include
    """
    metadata = create_test_metadata(states)
    
    # Simulate the file upload and parsing
    conversation_manager.parsed_data = {
        'states': metadata['states'],
        'metadata': metadata,
        'status': 'success',
        'data': create_test_nmep_data(states, mapped=False)  # Store unmapped for parser compatibility
    }
    
    # Mock the parser's get_state_data method
    def mock_get_state_data(state_name):
        """Return filtered test data for a state."""
        test_data = create_test_nmep_data(states, mapped=False)  # Use unmapped for parser
        # Clean state names in test data
        test_data['State_clean'] = test_data['State'].apply(
            lambda x: x.split(' ', 1)[1] if ' ' in x else x
        )
        return test_data[test_data['State_clean'] == state_name]
    
    # Replace the parser method
    conversation_manager.parser.get_state_data = mock_get_state_data
    conversation_manager.parser.data = create_test_nmep_data(states, mapped=False)
    
    # Mock the parser's summary method
    def mock_get_summary(metadata):
        states_str = ", ".join(metadata['states'])
        return f"""I've analyzed your NMEP TPR data:
- **States found**: {states_str} ({metadata['state_count']} states)
- **Time period**: {metadata['time_range']} ({metadata['months_covered']} months)
- **Total facilities**: {metadata['total_facilities']:,}

Which state would you like to analyze?"""
    
    conversation_manager.parser.get_summary_for_conversation = mock_get_summary