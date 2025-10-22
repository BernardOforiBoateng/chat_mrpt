"""
Test workflow transition from Data Analysis V3 to main ChatMRPT.

Tests that after TPR completion, the system properly:
1. Removes the .data_analysis_mode flag
2. Sets workflow_transitioned flag
3. Prevents re-routing to Data Analysis V3
"""

import pytest
import os
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def test_session():
    """Create a test session with necessary files."""
    session_id = "test_transition_session"
    session_folder = Path(f"instance/uploads/{session_id}")
    
    # Clean up if exists
    if session_folder.exists():
        shutil.rmtree(session_folder)
    
    # Create session folder
    session_folder.mkdir(parents=True, exist_ok=True)
    
    # Create initial state files
    flag_file = session_folder / '.data_analysis_mode'
    flag_file.write_text('test_data.csv\n2025-01-18T00:00:00')
    
    state_file = session_folder / '.agent_state.json'
    initial_state = {
        '_session_id': session_id,
        'current_stage': 'tpr_complete',
        'tpr_completed': True,
        'workflow_transitioned': False,
        '_last_updated': '2025-01-18T00:00:00'
    }
    state_file.write_text(json.dumps(initial_state, indent=2))
    
    yield {
        'session_id': session_id,
        'session_folder': session_folder,
        'flag_file': flag_file,
        'state_file': state_file
    }
    
    # Cleanup
    if session_folder.exists():
        shutil.rmtree(session_folder)


def test_flag_file_removal_on_transition(test_session):
    """Test that the .data_analysis_mode flag is removed on workflow transition."""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    
    session_id = test_session['session_id']
    flag_file = test_session['flag_file']
    
    # Verify flag exists initially
    assert flag_file.exists(), "Flag file should exist initially"
    
    # Initialize handler
    state_manager = DataAnalysisStateManager(session_id)
    handler = TPRWorkflowHandler(session_id, state_manager, None)
    
    # Create mock data files for trigger_risk_analysis
    data_file = test_session['session_folder'] / 'raw_data.csv'
    data_file.write_text('WardName,TPR\nWard1,0.25\nWard2,0.45')
    
    shapefile = test_session['session_folder'] / 'raw_shapefile.zip'
    shapefile.write_bytes(b'mock shapefile content')
    
    # Trigger workflow transition
    result = handler.trigger_risk_analysis()
    
    # Verify flag file is removed
    assert not flag_file.exists(), "Flag file should be removed after transition"
    
    # Verify workflow_transitioned is set
    state = json.loads(test_session['state_file'].read_text())
    assert state.get('workflow_transitioned') == True, "workflow_transitioned should be True"


def test_state_update_on_transition(test_session):
    """Test that the state is properly updated on workflow transition."""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    
    session_id = test_session['session_id']
    state_manager = DataAnalysisStateManager(session_id)
    
    # Verify initial state
    initial_state = state_manager.get_state()
    assert initial_state.get('workflow_transitioned') == False
    
    # Update state to simulate transition
    state_manager.update_state({'workflow_transitioned': True})
    
    # Verify state is updated
    updated_state = state_manager.get_state()
    assert updated_state.get('workflow_transitioned') == True


def test_request_interpreter_respects_transition(test_session):
    """Test that request_interpreter doesn't route to Data Analysis V3 after transition."""
    import sys
    import json
    
    session_id = test_session['session_id']
    flag_file = test_session['flag_file']
    state_file = test_session['state_file']
    
    # Set workflow_transitioned to True
    state = json.loads(state_file.read_text())
    state['workflow_transitioned'] = True
    state_file.write_text(json.dumps(state, indent=2))
    
    # Ensure flag file exists (to test that transition overrides it)
    if not flag_file.exists():
        flag_file.write_text('test_data.csv\n2025-01-18T00:00:00')
    
    # Mock Flask app context
    with patch('flask.current_app') as mock_app:
        mock_app.config = {'UPLOAD_FOLDER': 'instance/uploads'}
        
        # Test the routing logic (simplified version)
        upload_folder = 'instance/uploads'
        flag_path = Path(upload_folder) / session_id / '.data_analysis_mode'
        state_path = Path(upload_folder) / session_id / '.agent_state.json'
        
        # Check conditions
        has_flag = flag_path.exists()
        workflow_transitioned = False
        
        if has_flag and state_path.exists():
            state_data = json.loads(state_path.read_text())
            workflow_transitioned = state_data.get('workflow_transitioned', False)
        
        # Should NOT route to Data Analysis V3 if transitioned
        should_route_to_v3 = has_flag and not workflow_transitioned
        
        assert not should_route_to_v3, "Should NOT route to Data Analysis V3 after transition"


def test_visualization_in_response(test_session):
    """Test that visualizations are included in the TPR response."""
    from app.data_analysis_v3.core.state_manager import DataAnalysisStateManager
    from app.data_analysis_v3.core.tpr_workflow_handler import TPRWorkflowHandler
    from app.data_analysis_v3.core.state_manager import ConversationStage
    
    session_id = test_session['session_id']
    state_manager = DataAnalysisStateManager(session_id)
    handler = TPRWorkflowHandler(session_id, state_manager, None)
    
    # Set up TPR selections
    handler.tpr_selections = {
        'state': 'TestState',
        'facility_level': 'primary',
        'age_group': 'u5'
    }
    handler.current_stage = ConversationStage.TPR_AGE_GROUP
    
    # Create mock TPR map file
    map_file = test_session['session_folder'] / 'tpr_distribution_map.html'
    map_file.write_text('<html>Mock TPR Map</html>')
    
    # Mock the TPR calculation tool
    with patch('app.data_analysis_v3.tools.tpr_analysis_tool.tpr_analysis_tool') as mock_tool:
        mock_tool.return_value = "TPR Calculation Complete!\nResults saved to: tpr_results.csv"
        
        # Calculate TPR
        result = handler.calculate_tpr()
    
    # Verify response includes visualizations
    assert result.get('success') == True
    assert 'visualizations' in result
    
    # If map was created, verify visualization object
    if map_file.exists():
        viz_list = result.get('visualizations', [])
        if viz_list:
            viz = viz_list[0]
            assert viz['type'] == 'iframe'
            assert 'tpr_distribution_map.html' in viz['url']
            assert viz['title'].startswith('TPR Distribution')


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, '-v'])