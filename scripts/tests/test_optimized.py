#!/usr/bin/env python3
"""
Test optimized version with 11MB file
"""
import sys
import os
import time

sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app.services.data_analysis_agent import SimpleDataAnalysisAgent

print("Creating 11MB test Excel file...")
import pandas as pd
import numpy as np

rows = 200000
data = {
    'State': np.random.choice(['Adamawa', 'Kwara', 'Osun'], rows),
    'LGA': [f'LGA_{i%50}' for i in range(rows)],
    'Ward': [f'Ward_{i%200}' for i in range(rows)],
    'TPR': np.random.uniform(5, 60, rows),
    'Cases': np.random.randint(10, 1000, rows),
}

df = pd.DataFrame(data)
test_file = '/tmp/test_11mb.xlsx'
df.to_excel(test_file, index=False)
file_size = os.path.getsize(test_file) / (1024 * 1024)
print(f"File size: {file_size:.2f}MB")

agent = SimpleDataAnalysisAgent()

# Test with optimized query
print("\nTesting with optimized query (should skip vLLM)...")
start = time.time()
result = agent.analyze(test_file, "print(df.shape)")
elapsed = time.time() - start

print(f"Time: {elapsed:.2f}s")
print(f"Success: {result.get('success')}")
print(f"Result: {result.get('message', '')[:200]}")

os.unlink(test_file)