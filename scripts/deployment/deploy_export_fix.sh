#!/bin/bash

# Simple deployment script for export_tools.py fix

echo "Deploying export_tools.py fix to staging server..."

# Copy file using Python
python3 << 'EOF'
import subprocess
import os

# Read the file content
with open('app/tools/export_tools.py', 'r') as f:
    content = f.read()

# Write to a temporary script that will be executed on the server
deploy_script = '''#!/bin/bash
cd /home/ubuntu/ChatMRPT
cp app/tools/export_tools.py app/tools/export_tools.py.backup
cat > app/tools/export_tools.py << 'FILEEND'
{}
FILEEND

# Reload gunicorn
sudo systemctl reload gunicorn

echo "Deployment complete!"
'''.format(content.replace("'", "'\\''"))

# Write the deployment script
with open('deploy_temp.sh', 'w') as f:
    f.write(deploy_script)

# Make it executable
os.chmod('deploy_temp.sh', 0o755)

print("Deployment script created. Please run it on the staging server.")
print("You can access the staging server at: 18.117.115.217")
EOF

echo "Fix prepared. The f-string syntax error has been fixed."
echo "Changed line 1131 from: {''.join([f\"\"\" to: {\"\".join([f'''"
echo "This resolves the unmatched bracket error."