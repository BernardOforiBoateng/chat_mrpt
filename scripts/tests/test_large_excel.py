#!/usr/bin/env python3
"""
Test processing a large Excel file directly
"""
import sys
import os
import time

# Add the app directory to path
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

from app.services.data_analysis_agent import SimpleDataAnalysisAgent

# Create test Excel file (similar size to user's file)
print("Creating large test Excel file...")
import pandas as pd
import numpy as np

# Create a large dataset similar to malaria data
rows = 50000  # Approximate rows for 11MB file
data = {
    'State': np.random.choice(['Adamawa', 'Kwara', 'Osun'], rows),
    'LGA': [f'LGA_{i%50}' for i in range(rows)],
    'Ward': [f'Ward_{i%200}' for i in range(rows)],
    'Month': np.random.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'], rows),
    'Year': np.random.choice([2022, 2023, 2024], rows),
    'Tests_Conducted': np.random.randint(100, 5000, rows),
    'Positive_Cases': np.random.randint(10, 1000, rows),
    'TPR': np.random.uniform(5, 60, rows),
    'Population': np.random.randint(5000, 50000, rows),
    'Under5_Cases': np.random.randint(5, 500, rows),
    'Pregnant_Cases': np.random.randint(1, 100, rows),
}

df = pd.DataFrame(data)

# Save as Excel
test_file = '/tmp/large_test_malaria.xlsx'
df.to_excel(test_file, index=False)
file_size = os.path.getsize(test_file) / (1024 * 1024)
print(f"Created test file: {test_file} ({file_size:.2f}MB)")

# Test the agent
print("\nTesting agent with large file...")
agent = SimpleDataAnalysisAgent()

# Simple query
query = "Show the shape of the data and column names"

print(f"Query: {query}")
print("Starting analysis...")
start = time.time()

result = agent.analyze(test_file, query)

elapsed = time.time() - start
print(f"\nAnalysis completed in {elapsed:.2f} seconds")
print(f"Success: {result.get('success')}")
print(f"Message: {result.get('message', 'No message')[:500]}")

# Clean up
os.unlink(test_file)
print("\nTest complete")