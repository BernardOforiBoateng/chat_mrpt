#!/usr/bin/env python3
"""
Test with 11MB Excel file to reproduce the issue
"""
import sys
import os
import time

sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app.services.data_analysis_agent import SimpleDataAnalysisAgent

print("Creating 11MB test Excel file...")
import pandas as pd
import numpy as np

# Create dataset to approximate 11MB
rows = 200000  # More rows for 11MB
data = {
    'State': np.random.choice(['Adamawa', 'Kwara', 'Osun'], rows),
    'LGA': [f'LGA_{i%50}' for i in range(rows)],
    'Ward': [f'Ward_{i%200}' for i in range(rows)],
    'Month': np.random.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rows),
    'Year': np.random.choice([2022, 2023, 2024], rows),
    'Tests_Conducted': np.random.randint(100, 5000, rows),
    'Positive_Cases': np.random.randint(10, 1000, rows),
    'TPR': np.random.uniform(5, 60, rows),
    'Population': np.random.randint(5000, 50000, rows),
    'Under5_Cases': np.random.randint(5, 500, rows),
    'Pregnant_Cases': np.random.randint(1, 100, rows),
    'Deaths': np.random.randint(0, 50, rows),
    'ITN_Distributed': np.random.randint(0, 1000, rows),
}

df = pd.DataFrame(data)

test_file = '/tmp/large_11mb_malaria.xlsx'
df.to_excel(test_file, index=False)
file_size = os.path.getsize(test_file) / (1024 * 1024)
print(f"Created test file: {test_file} ({file_size:.2f}MB)")

# Test with simple query
print("\nTesting with simple query...")
agent = SimpleDataAnalysisAgent()

query = "print(df.shape)"
print(f"Query: {query}")
print("Starting analysis...")
start = time.time()

try:
    result = agent.analyze(test_file, query)
    elapsed = time.time() - start
    print(f"\nAnalysis completed in {elapsed:.2f} seconds")
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message', 'No message')[:500]}")
except Exception as e:
    elapsed = time.time() - start
    print(f"\nAnalysis FAILED after {elapsed:.2f} seconds")
    print(f"Error: {e}")

# Clean up
try:
    os.unlink(test_file)
except:
    pass
    
print("\nTest complete")