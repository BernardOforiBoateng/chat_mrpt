"""
Integration test for TPR module.

This script tests that the TPR module is properly integrated with ChatMRPT.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

def test_imports():
    """Test that all TPR module components can be imported."""
    print("Testing TPR module imports...")
    
    try:
        # Test core imports
        from app.tpr_module.data.nmep_parser import NMEPParser
        print("✓ NMEPParser imported successfully")
        
        from app.tpr_module.core.tpr_calculator import TPRCalculator
        print("✓ TPRCalculator imported successfully")
        
        from app.tpr_module.core.tpr_conversation_manager import TPRConversationManager
        print("✓ TPRConversationManager imported successfully")
        
        from app.tpr_module.services.raster_extractor import RasterExtractor
        print("✓ RasterExtractor imported successfully")
        
        from app.tpr_module.output.output_generator import OutputGenerator
        print("✓ OutputGenerator imported successfully")
        
        # Test integration imports
        from app.tpr_module.integration.upload_detector import TPRUploadDetector
        print("✓ TPRUploadDetector imported successfully")
        
        from app.tpr_module.integration.tpr_handler import TPRHandler
        print("✓ TPRHandler imported successfully")
        
        # Test route imports
        from app.web.routes.tpr_routes import tpr_bp
        print("✓ TPR routes imported successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False


def test_upload_detection():
    """Test that TPR upload detection works."""
    print("\nTesting TPR upload detection...")
    
    try:
        from app.tpr_module.integration.upload_detector import TPRUploadDetector
        
        detector = TPRUploadDetector()
        print("✓ TPRUploadDetector created successfully")
        
        # Test detection method exists
        assert hasattr(detector, 'detect_tpr_upload'), "detect_tpr_upload method missing"
        print("✓ Detection method exists")
        
        # Test with empty file (should return standard)
        upload_type, info = detector.detect_tpr_upload(None, None)
        assert upload_type == 'standard', f"Expected 'standard', got '{upload_type}'"
        print("✓ Empty file returns 'standard'")
        
        print("\n✅ Upload detection test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Upload detection test failed: {e}")
        return False


def test_geopolitical_zones():
    """Test that geopolitical zone data is available."""
    print("\nTesting geopolitical zone data...")
    
    try:
        from app.tpr_module.data.geopolitical_zones import STATE_TO_ZONE, ZONE_VARIABLES
        
        # Test that we have data
        assert len(STATE_TO_ZONE) == 37, f"Expected 37 states, got {len(STATE_TO_ZONE)}"
        print(f"✓ Found {len(STATE_TO_ZONE)} states in STATE_TO_ZONE")
        
        assert len(ZONE_VARIABLES) == 6, f"Expected 6 zones, got {len(ZONE_VARIABLES)}"
        print(f"✓ Found {len(ZONE_VARIABLES)} geopolitical zones")
        
        # Test specific states
        assert STATE_TO_ZONE.get('Lagos') == 'South_West'
        assert STATE_TO_ZONE.get('Kano') == 'North_West'
        print("✓ State to zone mapping correct")
        
        # Test zone variables
        assert 'rainfall' in ZONE_VARIABLES['North_Central']
        print("✓ Zone variables defined correctly")
        
        print("\n✅ Geopolitical zone test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Geopolitical zone test failed: {e}")
        return False


def test_raster_database():
    """Test that raster database is set up."""
    print("\nTesting raster database...")
    
    try:
        from app.tpr_module.services.raster_extractor import RasterExtractor
        
        extractor = RasterExtractor()
        print("✓ RasterExtractor created successfully")
        
        # Check raster base directory
        assert extractor.raster_base_dir.exists(), f"Raster directory not found: {extractor.raster_base_dir}"
        print(f"✓ Raster directory exists: {extractor.raster_base_dir}")
        
        # Get available variables
        available = extractor.get_available_variables()
        print(f"✓ Found {len(available)} variable types in raster database")
        
        if available:
            print("\nAvailable variables:")
            for var, info in list(available.items())[:5]:  # Show first 5
                print(f"  - {var}: {len(info['files'])} files")
        
        print("\n✅ Raster database test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Raster database test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("TPR MODULE INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Upload Detection Test", test_upload_detection),
        ("Geopolitical Zones Test", test_geopolitical_zones),
        ("Raster Database Test", test_raster_database)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! TPR module is properly integrated.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)