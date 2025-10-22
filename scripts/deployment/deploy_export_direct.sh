#!/bin/bash

echo "Deploying export_tools.py fix directly..."

# Create a Python script to fix the file in place
cat > fix_export_tools.py << 'EOF'
import re

# Read the file
with open('app/tools/export_tools.py', 'r') as f:
    content = f.read()

# Fix the f-string syntax error at line 1131
# Change {''.join([f""" to {"".join([f'''
old_pattern = r"\{''.join\(\[f\"\"\""
new_pattern = '{"".join([f\'\'\''

content = content.replace(old_pattern, new_pattern)

# Also fix the closing quotes
content = content.replace('""" for rec in recommendations[:3]])}', "''' for rec in recommendations[:3]])}")

# Write the fixed content back
with open('app/tools/export_tools.py', 'w') as f:
    f.write(content)

print("Fixed f-string syntax error in export_tools.py")
EOF

echo "Fix script created. Run this on the server:"
echo "1. cd /home/ubuntu/ChatMRPT"
echo "2. python3 fix_export_tools.py"
echo "3. sudo systemctl reload gunicorn"