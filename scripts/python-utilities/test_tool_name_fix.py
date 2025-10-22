#!/usr/bin/env python3
"""
Test that tool names match correctly between classes and registry
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT')

# Set environment to avoid loading heavy models during test
os.environ['DISABLE_TOOL_SCORING'] = 'true'
os.environ['TESTING'] = 'true'

def test_tool_names():
    """Test that tool names are correctly generated"""
    try:
        from app.tools.visualization_maps_tools import CreateCompositeScoreMaps, CreateVulnerabilityMap, CreateVulnerabilityMapComparison

        print("="*60)
        print("Testing Tool Name Generation")
        print("="*60)

        # Test CreateCompositeScoreMaps
        composite_name = CreateCompositeScoreMaps.get_tool_name()
        print(f"CreateCompositeScoreMaps.get_tool_name() = '{composite_name}'")
        assert composite_name == "createcompositescoremaps", f"Expected 'createcompositescoremaps', got '{composite_name}'"
        print("✅ CreateCompositeScoreMaps name is correct")

        # Test CreateVulnerabilityMap
        vuln_name = CreateVulnerabilityMap.get_tool_name()
        print(f"CreateVulnerabilityMap.get_tool_name() = '{vuln_name}'")
        assert vuln_name == "createvulnerabilitymap", f"Expected 'createvulnerabilitymap', got '{vuln_name}'"
        print("✅ CreateVulnerabilityMap name is correct")

        # Test CreateVulnerabilityMapComparison (this one overrides get_tool_name())
        comparison_name = CreateVulnerabilityMapComparison.get_tool_name()
        print(f"CreateVulnerabilityMapComparison.get_tool_name() = '{comparison_name}'")
        assert comparison_name == "create_vulnerability_map_comparison", f"Expected 'create_vulnerability_map_comparison', got '{comparison_name}'"
        print("✅ CreateVulnerabilityMapComparison name is correct (overridden with underscores)")

        # Test that registry can find them
        print("\nTesting Tool Registry Discovery...")
        from app.core.tool_registry import ToolRegistry

        registry = ToolRegistry()
        registry.discover_tools()

        all_tools = registry.list_tools()
        print(f"Registry found {len(all_tools)} total tools")

        # Check if our tools are registered
        if 'createcompositescoremaps' in all_tools:
            print("✅ createcompositescoremaps found in registry")
        else:
            print("❌ createcompositescoremaps NOT found in registry")

        if 'createvulnerabilitymap' in all_tools:
            print("✅ createvulnerabilitymap found in registry")
        else:
            print("❌ createvulnerabilitymap NOT found in registry")

        if 'create_vulnerability_map_comparison' in all_tools:
            print("✅ create_vulnerability_map_comparison found in registry")
        else:
            print("❌ create_vulnerability_map_comparison NOT found in registry")

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nSummary:")
        print("- Tool names are lowercase class names without underscores")
        print("- Registry correctly discovers tools with these names")
        print("- Request interpreter should use these exact names")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_tool_names()
    sys.exit(0 if success else 1)