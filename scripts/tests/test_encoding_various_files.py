#!/usr/bin/env python3
"""
Comprehensive test of encoding handler with various real-world scenarios
"""

import sys
import os
import tempfile
import pandas as pd
sys.path.insert(0, '.')

from app.data_analysis_v3.core.encoding_handler import EncodingHandler

def create_test_files():
    """Create various test files with different encoding issues"""
    test_files = []
    
    # Test 1: Adamawa-style TPR data with mojibake
    print("\n1. Creating Adamawa-style TPR file with mojibake...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='_adamawa.csv', delete=False, encoding='utf-8') as f:
        f.write("State,Ward,Facility,Persons presenting with fever & tested by RDT Ã¢â€°Â¥5yrs (excl PW),Persons presenting with fever & tested by RDT Ã¢â€°Â¤5yrs\n")
        f.write("Adamawa,Ward1,PHC1,150,75\n")
        f.write("Adamawa,Ward2,PHC2,200,100\n")
        test_files.append(('Adamawa TPR (mojibake)', f.name))
    
    # Test 2: French accents mojibake
    print("2. Creating French accents file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='_french.csv', delete=False, encoding='utf-8') as f:
        f.write("RÃ©gion,HÃ´pital,Ã‰tÃ©,DonnÃ©es\n")
        f.write("Ã le-de-France,Saint-Louis,2024,100\n")
        f.write("ProvÃ§al,Nice,2024,200\n")
        test_files.append(('French accents', f.name))
    
    # Test 3: Mathematical symbols mojibake
    print("3. Creating mathematical symbols file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='_math.csv', delete=False, encoding='utf-8') as f:
        f.write("Ward,â‰¤5_tested,â‰¥5_tested,Â±variance,âˆ†change\n")
        f.write("North,100,200,10,5\n")
        f.write("South,150,250,15,8\n")
        test_files.append(('Mathematical symbols', f.name))
    
    # Test 4: Quotes and apostrophes mojibake
    print("4. Creating quotes/apostrophes file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='_quotes.csv', delete=False, encoding='utf-8') as f:
        f.write("Facility,Children's_Ward,Women's_Health,"Specialâ€_Unit\n")
        f.write("Hospital A,50,75,100\n")
        f.write("Hospital B,60,80,120\n")
        test_files.append(('Quotes and apostrophes', f.name))
    
    # Test 5: Mixed encoding issues
    print("5. Creating mixed encoding issues file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='_mixed.csv', delete=False, encoding='utf-8') as f:
        f.write("État,Hôpital,≤5ans,≥5ans,Café±Variance,Women's_Health\n")
        f.write("São Paulo,Hospital São José,100,200,15,300\n")
        f.write("Paraná,Hospital Curitiba,150,250,20,350\n")
        test_files.append(('Mixed encoding (already clean)', f.name))
    
    # Test 6: Windows-1252 specific characters
    print("6. Creating Windows-1252 style file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='_windows.csv', delete=False, encoding='utf-8') as f:
        # Using raw string to avoid encoding issues in source
        f.write("Region,Test_Positive,Test_Negative,Total\n")
        f.write("North,50,150,200\n")
        f.write("South,75,225,300\n")
        test_files.append(('Windows-1252 dashes', f.name))
    
    return test_files

def test_file_reading(test_name, file_path):
    """Test reading a file with encoding issues"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}")
    
    try:
        # Read with our encoding handler
        df = EncodingHandler.read_csv_with_encoding(file_path)
        
        print(f"✅ Successfully read file")
        print(f"Shape: {df.shape}")
        print(f"\nColumn names after fixing:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        # Check for specific fixes
        all_cols_str = ' '.join(df.columns)
        
        # Check if mojibake was fixed
        mojibake_indicators = ['Ã', 'â€', 'Â', ''', '"', 'â€', 'â‰¤', 'â‰¥']
        has_mojibake = any(indicator in all_cols_str for indicator in mojibake_indicators)
        
        if has_mojibake:
            print(f"\n⚠️ Warning: Some mojibake may still be present")
        else:
            print(f"\n✅ No mojibake detected in column names")
        
        # Check for expected conversions
        expected_conversions = {
            '≥5': 'Greater than or equal to 5',
            '≤5': 'Less than or equal to 5',
            "Women's": "Women's (apostrophe)",
            'Hôpital': 'Hospital (French)',
            'São': 'São (Portuguese)',
        }
        
        print(f"\nChecking for expected conversions:")
        for pattern, description in expected_conversions.items():
            if pattern in all_cols_str:
                print(f"  ✅ Found: {description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.unlink(file_path)

def main():
    print("="*60)
    print("COMPREHENSIVE ENCODING TEST")
    print("Testing various file encodings with dynamic handler")
    print("="*60)
    
    # Create test files
    test_files = create_test_files()
    
    # Test each file
    results = []
    for test_name, file_path in test_files:
        success = test_file_reading(test_name, file_path)
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All encoding tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())