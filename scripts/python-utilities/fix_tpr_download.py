#!/usr/bin/env python3
"""Fix TPR download manager to include HTML report mapping."""

import re

# Read the file
with open('app/static/js/modules/data/tpr-download-manager.js', 'r') as f:
    content = f.read()

# Check if fix already applied
if "'TPR Analysis Report': 'summary'" in content:
    print("Fix already applied!")
    exit(0)

# Find the typeMap and add the new mapping
pattern = r"('Summary Report': 'summary')"
replacement = r"\1,\n            'TPR Analysis Report': 'summary'  // Added mapping for HTML report"

new_content = re.sub(pattern, replacement, content)

# Write the updated file
with open('app/static/js/modules/data/tpr-download-manager.js', 'w') as f:
    f.write(new_content)

print("Fix applied successfully!")
print("Added mapping: 'TPR Analysis Report': 'summary'")