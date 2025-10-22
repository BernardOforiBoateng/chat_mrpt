# TPR One-Tool Pattern Deployment Guide

## Files Changed
The following files have been updated with the one-tool pattern implementation:

1. **app/tpr_module/conversation.py**
   - Added `get_next_action()` method - ONE unified method where LLM decides everything
   - No predefined tools, just intelligence

2. **app/tpr_module/integration/llm_tpr_handler.py** 
   - Simplified to basic routing based on LLM's decision
   - Handles: execute, confirm, input, message action types

3. **app/tpr_module/prompts.py**
   - Fixed zone variables to use actual values from geopolitical_zones.py
   - Contains correct TPR calculation formulas

4. **app/tpr_module/sandbox.py**
   - Fixed builtins to work correctly
   - Properly captures execution results

## Manual Deployment Steps

### Option 1: Deploy via Terminal (Recommended)

```bash
# 1. Copy SSH key to temp location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# 2. SSH to staging server
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217

# 3. Once connected, navigate to project
cd /home/ec2-user/ChatMRPT

# 4. Pull the latest changes (if using git)
git pull origin main

# OR manually update the files by creating them:
# Create backup first
cp -r app/tpr_module app/tpr_module.backup

# 5. Restart the service
sudo systemctl restart chatmrpt

# 6. Check status
sudo systemctl status chatmrpt

# 7. Test health check
curl http://localhost:5000/ping
```

### Option 2: Copy Files Directly

If you can't use git, copy the files manually:

```bash
# From your local machine, copy the TPR module files
scp -i /tmp/chatmrpt-key2.pem -r app/tpr_module/ ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/

# Then SSH in and restart
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.117.115.217
sudo systemctl restart chatmrpt
```

## What Changed - One-Tool Pattern

### Before (Multi-Tool Approach):
- Multiple predefined tools (analyze_data, calculate_tpr, match_wards, etc.)
- Complex tool routing and validation
- Rigid structure with hardcoded parameters
- Would have resulted in 100+ tools

### After (One-Tool Pattern - Industry Standard):
- ONE execution environment (sandbox)
- LLM decides everything through `get_next_action()`
- Simple if/else routing in handler
- Maximum flexibility, no hardcoding

## How It Works

1. **User uploads TPR file**
   - LLM analyzes data structure dynamically
   - No hardcoded column names

2. **User asks question/request**
   - LLM's `get_next_action()` decides what to do:
     ```json
     {
       "thought": "reasoning about what to do",
       "action_type": "execute|confirm|input|message",
       "code": "pandas code to execute",
       "needs_confirmation": true/false,
       "needs_input": {...}
     }
     ```

3. **Handler routes based on action_type**
   - `execute`: Run code in sandbox
   - `confirm`: Ask user for confirmation
   - `input`: Request user input (ward matching, state selection)
   - `message`: Just display message

4. **Example Flow**:
   ```
   User: "Calculate TPR for Adamawa"
   LLM: Decides to filter data and calculate
   System: Executes code
   LLM: Detects ward mismatches
   System: Shows ward matching UI
   User: Confirms matches
   LLM: Generates map
   System: Displays visualization
   ```

## Testing the Deployment

### 1. Access Staging
- Direct: http://18.117.115.217:5000
- ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

### 2. Test TPR Workflow
1. Upload a TPR Excel/CSV file (use files from `www/` folder)
2. Ask "What columns are in my data?"
3. Request "Calculate TPR for all wards"
4. System should:
   - Detect columns dynamically
   - Calculate TPR using correct formula
   - Handle ward name mismatches interactively
   - Generate map automatically

### 3. Verify One-Tool Pattern
- Check logs: `sudo journalctl -u chatmrpt -f`
- Look for `get_next_action` calls
- Verify no hardcoded column names in errors

## Key Benefits

1. **Dynamic**: Works with any TPR format
2. **Intelligent**: LLM decides everything
3. **Interactive**: User confirms important decisions
4. **Flexible**: No rigid tool definitions
5. **Scalable**: One pattern for all operations

## Troubleshooting

If deployment fails:

1. **Check service logs**:
   ```bash
   sudo journalctl -u chatmrpt -n 100
   ```

2. **Check Python imports**:
   ```bash
   cd /home/ec2-user/ChatMRPT
   python -c "from app.tpr_module.conversation import TPRConversation; print('Import OK')"
   ```

3. **Test Ollama availability**:
   ```bash
   ollama list
   ```

4. **Restart workers**:
   ```bash
   sudo systemctl restart chatmrpt
   ps aux | grep gunicorn
   ```

## Files Location on Server

```
/home/ec2-user/ChatMRPT/
├── app/
│   └── tpr_module/
│       ├── conversation.py         # Core LLM logic with get_next_action()
│       ├── sandbox.py              # Code execution environment
│       ├── prompts.py              # LLM prompts with TPR formulas
│       └── integration/
│           └── llm_tpr_handler.py  # Simplified routing logic
```

## Success Criteria

✅ LLM handles entire TPR workflow with ONE method
✅ User interactions work (confirmations, selections)  
✅ Ward matching with fuzzy logic
✅ Map automatically generated
✅ No hardcoded tools or column names

## Next Steps After Deployment

1. Test with different TPR file formats
2. Verify Ollama is being used (check logs)
3. Test ward matching interaction
4. Verify map generation works
5. Check transition to risk analysis workflow