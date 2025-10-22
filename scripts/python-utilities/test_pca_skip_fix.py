#!/usr/bin/env python
"""
Test script to verify PCA skip message fix
Tests that when PCA is skipped due to statistical tests,
users get a proper message instead of generic fallback.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

# Mock Flask app context
class MockApp:
    def __init__(self):
        self.services = MockServices()
        self.config = {'UPLOAD_FOLDER': 'instance/uploads'}

class MockServices:
    def __init__(self):
        self.interaction_logger = None

class MockFlask:
    @property
    def current_app(self):
        return MockApp()

# Mock the Flask module
sys.modules['flask'] = type(sys)('flask')
sys.modules['flask'].current_app = MockApp()
sys.modules['flask'].session = {}

# Now import the module we're testing
from app.tools.complete_analysis_tools import CompleteAnalysisTool

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_pca_skip_message():
    """Test that proper message is generated when PCA is skipped"""

    # Create the tool instance
    tool = CompleteAnalysisTool()

    # Mock the results as they would be when PCA is skipped
    composite_result = {
        'success': True,
        'data': {
            'wards_analyzed': 21,
            'top_vulnerable_wards': [
                {'WardName': 'Ward1', 'composite_score': 0.85},
                {'WardName': 'Ward2', 'composite_score': 0.82},
                {'WardName': 'Ward3', 'composite_score': 0.79},
                {'WardName': 'Ward4', 'composite_score': 0.76},
                {'WardName': 'Ward5', 'composite_score': 0.73}
            ],
            'variables_used': ['TPR', 'distance_to_waterbodies', 'rainfall', 'soil_wetness', 'urban_percentage']
        }
    }

    pca_result = {
        'success': False,
        'pca_skipped': True,
        'message': 'PCA not suitable for this dataset (KMO=0.496 < 0.5)',
        'data': {
            'kmo_value': 0.496,
            'bartlett_p_value': 0.123,
            'recommendation': 'Use composite analysis only'
        },
        'skipped_reason': {
            'kmo_value': 0.496,
            'bartlett_p_value': 0.123
        }
    }

    comparison_summary = {
        'summary': 'PCA analysis was not performed due to statistical test results',
        'pca_skipped': True,
        'reason': 'Data not suitable for PCA'
    }

    execution_time = 2.5
    session_id = 'test_session'

    # Mock the unified dataset loading - simulating when it's not available
    # This will trigger the fallback to _generate_summary_from_analysis_results
    import pandas as pd
    import geopandas as gpd

    # Create a mock GeoDataFrame with composite scores but no PCA scores
    data = {
        'WardName': ['Ward1', 'Ward2', 'Ward3', 'Ward4', 'Ward5'],
        'composite_score': [0.85, 0.82, 0.79, 0.76, 0.73],
        'detected_zone': ['north_east'] * 5,
        'geometry': [None] * 5  # Mock geometry
    }
    gdf = gpd.GeoDataFrame(data)

    # Temporarily patch the load_unified_dataset function
    original_load = None
    try:
        from app.data import unified_dataset_builder
        if hasattr(unified_dataset_builder, 'load_unified_dataset'):
            original_load = unified_dataset_builder.load_unified_dataset
            unified_dataset_builder.load_unified_dataset = lambda x: gdf
    except ImportError:
        pass

    try:
        # Call the method that generates the summary
        summary = tool._generate_comprehensive_summary(
            composite_result,
            pca_result,
            comparison_summary,
            execution_time,
            session_id
        )

        # Verify the summary contains expected elements
        print("\n" + "="*60)
        print("GENERATED SUMMARY:")
        print("="*60)
        print(summary)
        print("="*60)

        # Check that it's not the generic fallback
        assert "⚠️ *Detailed summary generation failed" not in summary, "Generic fallback message detected!"

        # Check for proper content
        assert "Analysis complete!" in summary, "Missing analysis complete message"
        assert "statistical tests" in summary.lower(), "Missing statistical test explanation"
        assert "ITN" in summary or "bed net" in summary, "Missing ITN planning guidance"
        assert "composite" in summary.lower(), "Missing composite score mention"

        # Check for the KMO value mention
        assert "0.496" in summary or "KMO" in summary, "Missing KMO test result"

        print("\n✅ TEST PASSED: Proper message generated when PCA is skipped!")
        print("Key elements found:")
        print("- Analysis complete message ✓")
        print("- Statistical test explanation ✓")
        print("- ITN planning guidance ✓")
        print("- Composite score results ✓")
        print("- KMO test results ✓")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original function if it was patched
        if original_load:
            unified_dataset_builder.load_unified_dataset = original_load

if __name__ == "__main__":
    print("Testing PCA Skip Message Fix...")
    print("-" * 60)

    success = test_pca_skip_message()

    if success:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n⚠️ Tests failed. Please check the implementation.")

    sys.exit(0 if success else 1)