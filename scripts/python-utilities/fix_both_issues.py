#!/usr/bin/env python3
"""
Fix both critical issues:
1. Over 5 Years group missing due to encoding not being applied
2. Formatting with line breaks not working
"""

print("="*60)
print("FIXING BOTH CRITICAL ISSUES")
print("="*60)

print("\n1. Updating agent.py to use EncodingHandler for data loading...")

# First, let's create the fix for agent.py
agent_fix = """
# At line 141-143, replace:
# df_full = pd.read_csv(data_path)  # Read FULL data
# df_full = pd.read_excel(data_path)  # Read FULL data

# With:
from .encoding_handler import EncodingHandler
if data_path.endswith('.csv'):
    df_full = EncodingHandler.read_csv_with_encoding(data_path)
else:
    df_full = EncodingHandler.read_excel_with_encoding(data_path)
"""

print("Fix for agent.py:")
print(agent_fix)

print("\n2. Creating JavaScript fix for line break formatting...")

js_fix = """
// In parseMarkdownContent function, after handling bold text but before returning
// Add this to ensure line breaks within list items are preserved:

// Step X: Fix line breaks in list items
text = text.replace(/•\\s*/g, '\\n• ');  // Ensure bullets start on new lines
text = text.replace(/(\\d+\\.\\s+[^\\n]+)(•)/g, '$1\\n$2');  // Add line break before bullets in numbered items
"""

print("Fix for message-handler.js:")
print(js_fix)

print("\n3. Testing the fixes locally...")

# Test that encoding handler works with the actual file
import sys
import pandas as pd
sys.path.insert(0, '.')

from app.data_analysis_v3.core.encoding_handler import EncodingHandler

file_path = 'www/tpr_data_by_state/ad_Adamawa_State_TPR_LLIN_2024.xlsx'
print(f"\nTesting with: {file_path}")

# Read with encoding handler
df = EncodingHandler.read_excel_with_encoding(file_path, nrows=5)

print("\nColumns after encoding fix:")
over_5_cols = []
for col in df.columns:
    if any(pattern in str(col).lower() for pattern in ['≥5', 'gte_5', 'gte5', 'over_5', 'over5', '>5']):
        over_5_cols.append(col)
        print(f"  ✓ {col}")

if len(over_5_cols) >= 4:
    print(f"\n✅ Found {len(over_5_cols)} Over 5 columns - encoding fix works!")
else:
    print(f"\n❌ Only found {len(over_5_cols)} Over 5 columns - need to check patterns")

print("\n" + "="*60)
print("FILES TO UPDATE:")
print("="*60)
print("1. app/data_analysis_v3/core/agent.py - Use EncodingHandler")
print("2. app/static/js/modules/chat/core/message-handler.js - Fix line breaks")
print("3. Deploy both fixes to staging")