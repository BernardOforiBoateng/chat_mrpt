# ChatMRPT Backup and Restore Instructions
Created: 2024-09-23

## Current Backup Details

### AWS Backups
**Instance 1 (3.21.167.170)**
- File: `/home/ec2-user/ChatMRPT_code_only_backup_20250923_161022.tar.gz`
- Size: 351MB
- Contains: Code only (app/, run.py, gunicorn_config.py, requirements.txt)

**Instance 2 (18.220.103.20)**
- File: `/home/ec2-user/ChatMRPT_code_only_backup_20250923_161113.tar.gz`
- Size: 190MB
- Contains: Code only (app/, run.py, gunicorn_config.py, requirements.txt)

### GitHub Backup
- Commit: `db34a2f`
- Branch: `feature/enhance-model-capabilities`
- Tag: `backup-before-major-changes-20250923`
- Message: "Backup: Add hardcoded state name fixes for TPR maps"

## What's Included in This Backup

### Code Changes
1. **TPR State Name Fixes**
   - Enhanced state name normalization
   - 5-level matching strategy with hardcoded fallbacks
   - Fixed Akwa-Ibom vs Akwa Ibom naming issues
   - Hardcoded fixes for Ebonyi, Kebbi, Plateau, Nasarawa

### Files Modified
- `/app/core/tpr_utils.py`
- `/app/data_analysis_v3/tools/tpr_analysis_tool.py`

## How to Restore

### Method 1: Restore from AWS Backup

**On Instance 1:**
```bash
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170
cd /home/ec2-user

# Stop the service
sudo systemctl stop chatmrpt

# Backup current state (optional)
mv ChatMRPT ChatMRPT.old

# Extract backup
tar -xzf ChatMRPT_code_only_backup_20250923_161022.tar.gz -C /home/ec2-user/ChatMRPT/

# Restart service
sudo systemctl start chatmrpt
```

**On Instance 2:**
```bash
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20
cd /home/ec2-user

# Stop the service
sudo systemctl stop chatmrpt

# Backup current state (optional)
mv ChatMRPT ChatMRPT.old

# Extract backup
tar -xzf ChatMRPT_code_only_backup_20250923_161113.tar.gz -C /home/ec2-user/ChatMRPT/

# Restart service
sudo systemctl start chatmrpt
```

### Method 2: Restore from Git

**Local Machine:**
```bash
# Checkout the backup tag
git checkout backup-before-major-changes-20250923

# Or checkout the specific commit
git checkout db34a2f
```

**Deploy to AWS:**
```bash
# Deploy specific files
scp -i ~/.ssh/chatmrpt-key.pem app/core/tpr_utils.py ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/core/
scp -i ~/.ssh/chatmrpt-key.pem app/data_analysis_v3/tools/tpr_analysis_tool.py ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/

# Restart services
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 "sudo systemctl restart chatmrpt"
```

### Method 3: Quick Rollback (Emergency)

If something goes wrong immediately after deployment:

```bash
# On each instance
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@[INSTANCE_IP]

# Quick restore from backup
cd /home/ec2-user
tar -xzf ChatMRPT_code_only_backup_20250923_*.tar.gz -C ChatMRPT/ --overwrite
sudo systemctl restart chatmrpt
```

## Important Notes

1. **Data Folders Not Included**: The backups exclude:
   - `/www/` - Shapefiles and data
   - `/instance/` - User uploads and sessions
   - `/kano_settlement_data/` - Large geospatial data
   - Virtual environments and cache files

2. **State at Backup Time**:
   - TPR map fixes implemented for problem states
   - Both production instances running stable
   - All recent deployments successful

3. **Testing After Restore**:
   - Test TPR maps for: Adamawa, Akwa Ibom, Ebonyi, Kebbi, Plateau, Nasarawa
   - Verify service status: `sudo systemctl status chatmrpt`
   - Check logs: `sudo journalctl -u chatmrpt -f`

## Contact for Issues
If restore fails, check:
1. Service logs: `/home/ec2-user/ChatMRPT/instance/app.log`
2. System logs: `sudo journalctl -u chatmrpt -n 100`
3. Git history: `git log --oneline -10`