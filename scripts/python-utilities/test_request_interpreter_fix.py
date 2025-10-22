#!/usr/bin/env python3
"""
Test that the request interpreter properly uses Pydantic tools for vulnerability maps
"""

import sys
import os
import logging

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

# Set environment to avoid loading heavy models during test
os.environ['DISABLE_TOOL_SCORING'] = 'true'
os.environ['TESTING'] = 'true'

def test_request_interpreter():
    """Test that request interpreter uses correct tools for vulnerability maps"""
    try:
        from app.core.request_interpreter import RequestInterpreter
        from unittest.mock import Mock, patch, MagicMock

        # Create mock services
        llm_manager = Mock()
        data_service = Mock()
        analysis_service = Mock()
        visualization_service = Mock()

        # Create request interpreter
        interpreter = RequestInterpreter(
            llm_manager=llm_manager,
            data_service=data_service,
            analysis_service=analysis_service,
            visualization_service=visualization_service
        )

        print("\n" + "="*60)
        print("Testing Request Interpreter Vulnerability Map Handling")
        print("="*60)

        # Test 1: Composite-only request should use CreateCompositeScoreMaps
        print("\n1. Testing composite-only vulnerability map request...")

        with patch('app.core.tool_registry.get_tool_registry') as mock_registry:
            mock_tool_registry = Mock()
            mock_registry.return_value = mock_tool_registry

            # Mock successful tool execution
            mock_tool_registry.execute_tool.return_value = {
                'status': 'success',
                'message': 'Composite score map created',
                'data': {
                    'file_path': '/test/path/map.html',
                    'web_path': '/serve_viz/test/map.html'
                }
            }

            # Call the method with composite method
            result = interpreter._create_vulnerability_map(
                session_id='test_session',
                method='composite'
            )

            # Check that the correct tool was called
            mock_tool_registry.execute_tool.assert_called_with(
                'create_composite_score_maps',
                session_id='test_session'
            )

            # Check the result
            assert result['status'] == 'success'
            assert 'create_composite_score_maps' in result['tools_used']
            print("✅ Composite-only request correctly uses CreateCompositeScoreMaps tool")

        # Test 2: PCA request should use CreateVulnerabilityMap
        print("\n2. Testing PCA vulnerability map request...")

        with patch('app.core.tool_registry.get_tool_registry') as mock_registry:
            mock_tool_registry = Mock()
            mock_registry.return_value = mock_tool_registry

            # Mock successful tool execution
            mock_tool_registry.execute_tool.return_value = {
                'status': 'success',
                'message': 'PCA vulnerability map created',
                'data': {
                    'file_path': '/test/path/pca_map.html',
                    'web_path': '/serve_viz/test/pca_map.html'
                }
            }

            # Call the method with PCA method
            result = interpreter._create_vulnerability_map(
                session_id='test_session',
                method='pca'
            )

            # Check that the correct tool was called
            mock_tool_registry.execute_tool.assert_called_with(
                'create_vulnerability_map',
                session_id='test_session',
                method='pca'
            )

            # Check the result
            assert result['status'] == 'success'
            assert 'create_vulnerability_map' in result['tools_used']
            print("✅ PCA request correctly uses CreateVulnerabilityMap tool")

        # Test 3: No method specified should use comparison tool
        print("\n3. Testing vulnerability map comparison (no method specified)...")

        with patch('app.core.tool_registry.get_tool_registry') as mock_registry:
            mock_tool_registry = Mock()
            mock_registry.return_value = mock_tool_registry

            # Mock successful tool execution
            mock_tool_registry.execute_tool.return_value = {
                'status': 'success',
                'message': 'Side-by-side comparison created',
                'data': {
                    'file_path': '/test/path/comparison.html',
                    'web_path': '/serve_viz/test/comparison.html'
                }
            }

            # Call the method without method parameter
            result = interpreter._create_vulnerability_map(
                session_id='test_session',
                method=None
            )

            # Check that the comparison tool was called
            mock_tool_registry.execute_tool.assert_called_with(
                'create_vulnerability_map_comparison',
                session_id='test_session',
                include_statistics=True
            )

            # Check the result
            assert result['status'] == 'success'
            assert 'create_vulnerability_map_comparison' in result['tools_used']
            print("✅ No method specified correctly uses comparison tool")

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSummary:")
        print("- Composite requests now use CreateCompositeScoreMaps tool")
        print("- PCA requests use CreateVulnerabilityMap tool")
        print("- Comparison requests use CreateVulnerabilityMapComparison tool")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_request_interpreter()
    sys.exit(0 if success else 1)