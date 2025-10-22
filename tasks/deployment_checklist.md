# Deployment Checklist - Agent/TPR Separation

## Files Changed ✅

### New Files
- ✅ `app/data_analysis_v3/core/agent.py` - Clean agent (317 lines)
- ✅ `app/data_analysis_v3/tpr/__init__.py` - TPR module init
- ✅ `app/data_analysis_v3/tpr/workflow_manager.py` - TPR workflow (copied from core/)
- ✅ `app/data_analysis_v3/tpr/data_analyzer.py` - TPR analyzer (copied from core/)

### Modified Files
- ✅ `app/web/routes/data_analysis_v3_routes.py` - Bridge implementation

### Backup Files (Safe to Delete After Testing)
- `app/data_analysis_v3/core/agent_old_with_tpr.py`
- `app/data_analysis_v3/core/agent.py.backup_20251001_013342`
- `app/data_analysis_v3/core/tpr_workflow_handler.py` (old location)
- `app/data_analysis_v3/core/tpr_data_analyzer.py` (old location)

## Imports Verified ✅

### Agent Imports
- ✅ `app/data_analysis_v3/__init__.py` → exports DataAnalysisAgent
- ✅ `app/web/routes/data_analysis_v3_routes.py` → imports from core.agent
- ✅ `app/web/routes/analysis_routes.py` → imports from core.agent

### TPR Imports
- ✅ `app/web/routes/data_analysis_v3_routes.py` → imports from tpr module
- ✅ `app/data_analysis_v3/tpr/workflow_manager.py` → uses relative imports to core/
- ✅ `app/data_analysis_v3/tpr/__init__.py` → exports TPRWorkflowHandler, TPRDataAnalyzer

## Architecture ✅

```
User Query
    ↓
data_analysis_v3_routes.py (THE BRIDGE)
    ↓
┌───────────────┴────────────────┐
│                                │
TPR Workflow Active?         No Workflow
    ↓                             ↓
Keyword?                    Pure Agent
│      │                         ↓
Yes    No                   GPT-4o responds
│      │
│      └─→ Agent with context
│           (gentle reminder)
│
└─→ Workflow advances
    (primary → age selection)
```

## Testing Plan

### 1. Pure Agent (No Workflow)
- Upload data
- Ask: "Show me summary"
- Ask: "What columns do I have?"
- Ask: "help"

Expected: Agent responds naturally

### 2. TPR Workflow - Keywords
- Start TPR workflow
- Say: "primary"
- Say: "u5"

Expected: Workflow advances through stages

### 3. TPR Workflow - Deviations (THE KEY TEST)
- Start TPR workflow
- At facility selection, ask: "What's the difference between primary and secondary?"

Expected: Agent explains AND adds gentle reminder about continuing workflow

### 4. TPR Workflow - Complete Deviation
- Start TPR workflow
- At facility selection, say: "Actually, cluster my wards first"

Expected: Agent does clustering AND reminds about workflow

## Deployment Commands

```bash
# Copy files to production instances
scp -i /tmp/chatmrpt-key2.pem -r app/data_analysis_v3/core/agent.py ec2-user@3.21.167.170:~/ChatMRPT/app/data_analysis_v3/core/
scp -i /tmp/chatmrpt-key2.pem -r app/data_analysis_v3/tpr/ ec2-user@3.21.167.170:~/ChatMRPT/app/data_analysis_v3/
scp -i /tmp/chatmrpt-key2.pem app/web/routes/data_analysis_v3_routes.py ec2-user@3.21.167.170:~/ChatMRPT/app/web/routes/

# Repeat for instance 2
scp -i /tmp/chatmrpt-key2.pem -r app/data_analysis_v3/core/agent.py ec2-user@18.220.103.20:~/ChatMRPT/app/data_analysis_v3/core/
scp -i /tmp/chatmrpt-key2.pem -r app/data_analysis_v3/tpr/ ec2-user@18.220.103.20:~/ChatMRPT/app/data_analysis_v3/
scp -i /tmp/chatmrpt-key2.pem app/web/routes/data_analysis_v3_routes.py ec2-user@18.220.103.20:~/ChatMRPT/app/web/routes/

# Restart services
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo systemctl restart chatmrpt'
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 'sudo systemctl restart chatmrpt'
```

## Expected Improvements

### Before (Test Scores)
- Average: 32.5/100
- Edge cases: 25-30/100
- Help queries: 25/100
- Export requests: 25/100
- Hardcoded: "Data has been prepared..."

### After (Expected)
- Average: 60-80/100
- Edge cases: 50-70/100
- Help queries: 60-80/100
- Export requests: 60-80/100
- Natural GPT-4o responses

## Rollback Plan

If issues occur:
```bash
# Restore old agent
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'cd ChatMRPT/app/data_analysis_v3/core && cp agent_old_with_tpr.py agent.py && sudo systemctl restart chatmrpt'
```

## Status: READY TO DEPLOY ✅
