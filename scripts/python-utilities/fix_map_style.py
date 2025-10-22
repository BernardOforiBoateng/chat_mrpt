#!/usr/bin/env python3
"""Fix map visualization style to use open-street-map instead of carto-positron"""

import os
import re

files_to_fix = [
    "app/services/agents/visualizations/composite_visualizations.py",
    "app/services/agents/visualizations/pca_visualizations.py",
    "app/tpr_module/services/tpr_visualization_service.py"
]

for filepath in files_to_fix:
    if os.path.exists(filepath):
        print(f"Fixing {filepath}...")
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace carto-positron with open-street-map
        original_count = content.count('style="carto-positron"')
        content = content.replace('style="carto-positron"', 'style="open-street-map"')
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"  - Replaced {original_count} occurrences")
    else:
        print(f"File not found: {filepath}")

print("\nDone! Maps should now render properly.")