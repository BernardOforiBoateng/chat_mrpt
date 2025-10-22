"""
Test to see what raw output the executor generates
"""

import pandas as pd
import sys
from io import StringIO
from app.data_analysis_v3.core.executor import SecureExecutor

# Load the test data
df = pd.read_csv('www/adamawa_tpr_cleaned.csv')
print(f"Loaded data with shape: {df.shape}")
print(f"Columns: {list(df.columns)[:5]}...")

# Create executor
executor = SecureExecutor('test_session')

# Test code that should list top 10
test_code = """
# Get top 10 health facilities
if 'healthfacility' in df.columns:
    top_10 = df['healthfacility'].value_counts().head(10)
    print("Top 10 health facilities by record count:")
    for i, (facility, count) in enumerate(top_10.items(), 1):
        print(f"{i}. {facility}: {count} records")
else:
    print("Column 'healthfacility' not found")
    print(f"Available columns: {list(df.columns)}")
"""

# Execute
output, state = executor.execute(test_code, {'df': df})

print("\n" + "="*60)
print("RAW OUTPUT FROM EXECUTOR:")
print("="*60)
print(output)
print("="*60)
print(f"Output length: {len(output)} chars")

# Now test with sanitized columns
df.columns = [col.lower().replace(' ', '_') for col in df.columns]
output2, state2 = executor.execute(test_code, {'df': df})

print("\n" + "="*60)
print("OUTPUT WITH SANITIZED COLUMNS:")
print("="*60)
print(output2)
print("="*60)
