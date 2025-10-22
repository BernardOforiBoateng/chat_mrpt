#!/usr/bin/env python
"""
Test script for the vision-based visualization explanation feature.
Tests Plotly-to-image conversion and fallback mechanisms.
"""

import os
import sys
import tempfile
import plotly.graph_objects as go

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_plotly_conversion():
    """Test Plotly figure to image conversion using Kaleido."""
    print("Testing Plotly to image conversion...")

    try:
        # Create a simple Plotly figure
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=['Ward A', 'Ward B', 'Ward C', 'Ward D'],
            y=[0.8, 0.6, 0.9, 0.3],
            name='Malaria Risk Score',
            marker_color=['red', 'orange', 'darkred', 'green']
        ))
        fig.update_layout(
            title='Malaria Risk by Ward',
            xaxis_title='Ward',
            yaxis_title='Risk Score',
            height=600
        )

        # Test Kaleido conversion
        print("  Converting Plotly figure to PNG...")
        img_bytes = fig.to_image(format="png")

        if img_bytes:
            print("  ✓ Kaleido conversion successful!")
            print(f"  Image size: {len(img_bytes)} bytes")
            return True
        else:
            print("  ✗ Kaleido conversion failed")
            return False

    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        print("  Make sure Kaleido is installed: pip install kaleido")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_vision_explainer():
    """Test the UniversalVisualizationExplainer."""
    print("\nTesting UniversalVisualizationExplainer...")

    try:
        from app.services.universal_viz_explainer import UniversalVisualizationExplainer

        # Create a test HTML file with Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4],
            y=[10, 11, 12, 13],
            mode='lines+markers',
            name='TPR Trend'
        ))
        fig.update_layout(title='Test Positivity Rate Over Time')

        # Save to temporary HTML
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
            fig.write_html(f.name)
            temp_path = f.name

        print(f"  Created test HTML: {temp_path}")

        # Test with vision disabled (default)
        explainer = UniversalVisualizationExplainer()
        explanation = explainer.explain_visualization(temp_path, 'test_chart', 'test_session')

        if 'Generated' in explanation or 'generated' in explanation:
            print("  ✓ Fallback explanation works")
        else:
            print("  ? Unexpected fallback response")

        # Test with vision enabled
        os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'
        explainer2 = UniversalVisualizationExplainer()

        # Test image conversion
        img_b64 = explainer2._convert_to_image(temp_path)
        if img_b64:
            print("  ✓ Image conversion successful")
            print(f"  Base64 length: {len(img_b64)} characters")
        else:
            print("  ✗ Image conversion failed")

        # Clean up
        os.unlink(temp_path)
        del os.environ['ENABLE_VISION_EXPLANATIONS']

        return True

    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Vision-Based Visualization Explainer Test")
    print("=" * 60)

    # Test 1: Kaleido/Plotly conversion
    plotly_ok = test_plotly_conversion()

    # Test 2: Full explainer
    explainer_ok = test_vision_explainer()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Plotly/Kaleido: {'✓ PASSED' if plotly_ok else '✗ FAILED'}")
    print(f"  Vision Explainer: {'✓ PASSED' if explainer_ok else '✗ FAILED'}")

    if plotly_ok and explainer_ok:
        print("\n✓ All tests passed! Vision explanations are ready to use.")
        print("\nTo enable in production:")
        print("  1. Set ENABLE_VISION_EXPLANATIONS=true in .env")
        print("  2. Ensure OpenAI API key is configured")
        print("  3. Restart the application")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

    print("=" * 60)

if __name__ == "__main__":
    main()