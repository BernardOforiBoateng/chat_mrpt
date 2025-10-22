#\!/bin/bash

echo "=== Deploying Risk Transition Fix ==="

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOSSH'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "1. Backing up risk_transition.py..."
cp app/tpr_module/integration/risk_transition.py app/tpr_module/integration/risk_transition.py.backup_path_fix

echo "2. Updating risk_transition.py..."
python3 << 'PYTHON'
import re

with open('app/tpr_module/integration/risk_transition.py', 'r') as f:
    content = f.read()

# Fix can_transition method
content = re.sub(
    r"try:\s*\n\s*# Check for required TPR output files.*?logger\.info\(f\"TPR outputs available for transition: \{self\.session_id\}\"\)\s*\n\s*return True",
    """try:
            # Look for actual TPR output files in session folder (not tpr_outputs subfolder)
            # Files are named {state}_plus.csv and {state}_state.zip
            import glob
            
            # Find the plus.csv and state.zip files
            csv_files = glob.glob(os.path.join(self.session_folder, '*_plus.csv'))
            shp_files = glob.glob(os.path.join(self.session_folder, '*_state.zip'))
            
            if not csv_files:
                logger.warning(f"No *_plus.csv files found in {self.session_folder}")
                return False
                
            if not shp_files:
                logger.warning(f"No *_state.zip files found in {self.session_folder}")
                return False
            
            # Store the found files for later use
            self._tpr_csv = csv_files[0]  # Use the first match
            self._tpr_shapefile = shp_files[0]
            
            logger.info(f"TPR outputs available for transition: {os.path.basename(self._tpr_csv)}, {os.path.basename(self._tpr_shapefile)}")
            return True""",
    content,
    flags=re.DOTALL
)

# Fix prepare_files_for_risk_analysis method
content = re.sub(
    r"try:\s*\n\s*# Source files from TPR\s*\n\s*tpr_main_csv = os\.path\.join\(self\.tpr_folder, 'main_analysis\.csv'\).*?logger\.info\(f\"Copied TPR shapefile to \{risk_shapefile\}\"\)",
    """try:
            # Check if files were found by can_transition
            if not hasattr(self, '_tpr_csv') or not hasattr(self, '_tpr_shapefile'):
                # If not found in attributes, find them again
                import glob
                csv_files = glob.glob(os.path.join(self.session_folder, '*_plus.csv'))
                shp_files = glob.glob(os.path.join(self.session_folder, '*_state.zip'))
                
                if not csv_files or not shp_files:
                    raise FileNotFoundError("TPR output files not found")
                
                self._tpr_csv = csv_files[0]
                self._tpr_shapefile = shp_files[0]
            
            # Target files for risk analysis (matching standard upload)
            risk_csv = os.path.join(self.session_folder, 'raw_data.csv')
            risk_shapefile = os.path.join(self.session_folder, 'raw_shapefile.zip')
            
            # Copy files (preserving TPR outputs)
            shutil.copy2(self._tpr_csv, risk_csv)
            logger.info(f"Copied {os.path.basename(self._tpr_csv)} to raw_data.csv")
            
            shutil.copy2(self._tpr_shapefile, risk_shapefile)
            logger.info(f"Copied {os.path.basename(self._tpr_shapefile)} to raw_shapefile.zip")""",
    content,
    flags=re.DOTALL
)

with open('app/tpr_module/integration/risk_transition.py', 'w') as f:
    f.write(content)

print("✓ Updated risk_transition.py")
PYTHON

echo ""
echo "3. Checking syntax..."
python3 -m py_compile app/tpr_module/integration/risk_transition.py && echo "✓ Syntax OK" || echo "✗ Syntax error"

echo ""
echo "4. Restarting service..."
sudo systemctl restart chatmrpt

sleep 3

echo ""
echo "5. Service status:"
sudo systemctl status chatmrpt  < /dev/null |  head -10

echo ""
echo "=== Deployment Complete! ==="
echo "Risk transition will now:"
echo "- Look for *_plus.csv and *_state.zip files"
echo "- Copy them to raw_data.csv and raw_shapefile.zip"
echo "- Allow permission system to take over"
EOSSH
