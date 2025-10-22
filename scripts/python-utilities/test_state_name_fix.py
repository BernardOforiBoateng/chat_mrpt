#!/usr/bin/env python3
"""
Test script to verify state name normalization fixes.
"""

import sys
import os
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app.data_analysis_v3.tools.tpr_analysis_tool import normalize_state_name
from app.core.tpr_utils import extract_state_from_data
import pandas as pd

def test_normalization():
    """Test state name normalization."""
    print("Testing State Name Normalization")
    print("=" * 50)

    test_cases = [
        ("Akwa-Ibom State", "Akwa Ibom"),
        ("Akwa Ibom State", "Akwa Ibom"),
        ("akwa-ibom state", "Akwa Ibom"),
        ("AKWA-IBOM STATE", "Akwa Ibom"),
        ("Benue State", "Benue"),
        ("benue state", "Benue"),
        ("Nasarawa State", "Nasarawa"),
        ("Plateau State", "Plateau"),
        ("Kebbi State", "Kebbi"),
        ("Ebonyi State", "Ebonyi"),
        ("Cross River State", "Cross River"),
        ("Cross-River State", "Cross River"),
        ("Federal Capital Territory", "Federal Capital Territory"),
        ("FCT", "Federal Capital Territory"),
    ]

    for input_name, expected in test_cases:
        result = normalize_state_name(input_name)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{input_name}' -> '{result}' (expected: '{expected}')")

    print("\nTesting extract_state_from_data")
    print("=" * 50)

    # Test with different data formats
    test_data_cases = [
        (pd.DataFrame({"State": ["Akwa-Ibom State"]}), "Akwa Ibom"),
        (pd.DataFrame({"State": ["eb Ebonyi State"]}), "Ebonyi"),
        (pd.DataFrame({"State": ["bn Benue State"]}), "Benue"),
        (pd.DataFrame({"State": ["ns Nasarawa State"]}), "Nasarawa"),
        (pd.DataFrame({"State": ["pl Plateau State"]}), "Plateau"),
        (pd.DataFrame({"State": ["kb Kebbi State"]}), "Kebbi"),
    ]

    for df, expected in test_data_cases:
        result = extract_state_from_data(df)
        status = "✓" if result == expected else "✗"
        state_value = df['State'].iloc[0]
        print(f"{status} DataFrame with '{state_value}' -> '{result}' (expected: '{expected}')")

if __name__ == "__main__":
    test_normalization()
    print("\n✅ Test script completed!")