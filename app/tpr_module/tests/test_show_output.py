"""
Show the actual output of TPR module without cleanup.
"""

import os
import sys
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.tpr_module.data.nmep_parser import NMEPParser
from app.tpr_module.data.column_mapper import ColumnMapper
from app.tpr_module.core.tpr_calculator import TPRCalculator
from app.tpr_module.output.output_generator import OutputGenerator

# Path to actual NMEP data file
nmep_file = "/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/NMEP Malaria Adamawa_Kwara_Osun_Test Postivity Rate_2022_2024.xlsx"

print("\n=== GENERATING TPR OUTPUT FILES ===\n")

# Parse NMEP file
parser = NMEPParser()
parse_result = parser.parse_file(nmep_file)
data = parse_result['data']
states = parse_result['states']

# Process first state
state_name = states[0]
print(f"Processing {state_name}...")

# Get state data
state_data = parser.get_state_data(state_name)

# Map columns
mapper = ColumnMapper()
mapped_data = mapper.map_columns(state_data)

# Calculate TPR
calculator = TPRCalculator()
tpr_results = calculator.calculate_ward_tpr(mapped_data, age_group='u5')

# Convert to DataFrame
tpr_df = calculator.export_results_to_dataframe()

# Generate outputs
output_dir = f"test_output_demo"
generator = OutputGenerator('test_demo', output_dir)

metadata = {
    'facility_level': 'All',
    'age_group': 'Under 5',
    'source_file': os.path.basename(nmep_file)
}

output_paths = generator.generate_outputs(tpr_df, state_name, metadata)

# Show the main CSV content
print("\n=== MAIN CSV CONTENT ===")
main_csv = output_paths.get('main_analysis')
if main_csv and os.path.exists(main_csv):
    df = pd.read_csv(main_csv)
    print(f"File: {main_csv}")
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumns: {list(df.columns)}")
    
    print("\n--- First 5 rows (selected columns) ---")
    display_cols = ['WardName', 'WardCode', 'LGA', 'LGACode', 'TPR', 'Urban']
    display_cols = [c for c in display_cols if c in df.columns]
    print(df[display_cols].head().to_string())
    
    print("\n--- Environmental variables sample ---")
    env_cols = ['WardName', 'TPR', 'housing_quality', 'evi', 'ndwi', 'soil_wetness']
    env_cols = [c for c in env_cols if c in df.columns]
    print(df[env_cols].head().to_string())
    
print("\n=== FILES GENERATED ===")
for file_type, path in output_paths.items():
    if path and os.path.exists(path):
        size = os.path.getsize(path) / 1024
        print(f"{file_type}: {os.path.basename(path)} ({size:.1f} KB)")

print("\n✅ Files are available in:", output_dir)