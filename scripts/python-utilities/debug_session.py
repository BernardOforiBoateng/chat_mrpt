#!/usr/bin/env python3
import os
import pickle
from datetime import datetime

# Check most recent session files
session_dir = 'instance/flask_session'
files = [(f, os.path.getmtime(os.path.join(session_dir, f))) for f in os.listdir(session_dir)]
files.sort(key=lambda x: x[1], reverse=True)

print('Most recent 5 session files:')
for f, mtime in files[:5]:
    print(f'  {f} - {datetime.fromtimestamp(mtime)}')
    
# Read the most recent session
if files:
    latest_file = files[0][0]
    print(f'\nReading latest session: {latest_file}')
    try:
        with open(os.path.join(session_dir, latest_file), 'rb') as f:
            data = pickle.load(f)
            print('\nSession data:')
            for k, v in data.items():
                if k != '_permanent':
                    print(f'  {k}: {v}')
            
            # Check specific analysis-related keys
            print('\nAnalysis-related keys:')
            print(f'  analysis_complete: {data.get("analysis_complete", "NOT SET")}')
            print(f'  csv_loaded: {data.get("csv_loaded", "NOT SET")}')
            print(f'  shapefile_loaded: {data.get("shapefile_loaded", "NOT SET")}')
            print(f'  session_id: {data.get("session_id", "NOT SET")}')
    except Exception as e:
        print(f'Error reading session: {e}')