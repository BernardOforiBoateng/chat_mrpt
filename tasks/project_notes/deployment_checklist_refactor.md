# Deployment Checklist - RequestInterpreter Refactor

Date: 2025-09-24
Status: **READY FOR DEPLOYMENT** ✅

## Pre-Deployment Validation ✅

### Code Changes Summary
- ✅ Added 5 new service modules:
  - `app/core/data_repository.py` - Centralized file I/O
  - `app/core/session_context_service.py` - Session context management
  - `app/core/prompt_builder.py` - System prompt construction
  - `app/core/tool_runner.py` - Tool registry and execution
  - `app/core/llm_orchestrator.py` - LLM interaction orchestration

- ✅ Modified 1 file:
  - `app/core/request_interpreter.py` - Integrated new services, removed legacy prompt code

### Testing Results
- ✅ All new modules import successfully
- ✅ Services instantiate without errors
- ✅ 40 tools load from registry
- ✅ System prompts generate correctly (4123 chars)
- ✅ Session context builds properly with data files
- ✅ Backward compatibility maintained
- ✅ No regressions found

### Fixed Issues
- ✅ Indentation error in `request_interpreter.py:304` (fixed)

## Deployment Options

### Option 1: Deploy to Production + Test (RECOMMENDED)
```bash
# Deploy to both production instances
./deployment/deploy_to_production.sh

# SSH to test on production
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170
cd ChatMRPT
source chatmrpt_venv_new/bin/activate
python -c "from app.core import data_repository, session_context_service, prompt_builder, tool_runner, llm_orchestrator; print('✅ All modules loaded')"
sudo systemctl restart chatmrpt
```

### Option 2: Deploy to One Instance First
```bash
# Deploy to Instance 1 only
scp -i ~/.ssh/chatmrpt-key.pem app/core/*.py ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/core/
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170 'sudo systemctl restart chatmrpt'

# Test on Instance 1
# If successful, deploy to Instance 2
```

## Deployment Steps

### 1. Backup Current Production
```bash
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170
tar -czf ChatMRPT_pre_refactor_backup_$(date +%Y%m%d_%H%M%S).tar.gz ChatMRPT/ \
  --exclude="ChatMRPT/instance/uploads/*" \
  --exclude="ChatMRPT/chatmrpt_venv*" \
  --exclude="*.pyc"
```

### 2. Deploy Files
Files to deploy:
- `app/core/data_repository.py` (NEW)
- `app/core/session_context_service.py` (NEW)
- `app/core/prompt_builder.py` (NEW)
- `app/core/tool_runner.py` (NEW)
- `app/core/llm_orchestrator.py` (NEW)
- `app/core/request_interpreter.py` (MODIFIED)

### 3. Post-Deployment Verification
```bash
# On each production instance
cd /home/ec2-user/ChatMRPT
source chatmrpt_venv_new/bin/activate

# Test imports
python -c "
from app.core.data_repository import DataRepository
from app.core.session_context_service import SessionContextService
from app.core.prompt_builder import PromptBuilder
from app.core.tool_runner import ToolRunner
from app.core.llm_orchestrator import LLMOrchestrator
from app.core.request_interpreter import RequestInterpreter
print('✅ All imports successful')
"

# Check service status
sudo systemctl status chatmrpt

# Check logs for errors
sudo journalctl -u chatmrpt -n 50

# Test the application
curl -I http://localhost:5000/ping
```

### 4. CloudFront Cache Invalidation (if needed)
```bash
aws cloudfront create-invalidation --distribution-id E37HZ8B0X8HQXJ --paths "/*"
```

## Rollback Plan

If issues occur:
```bash
# Restore from backup
ssh -i /tmp/chatmrpt-key2.pem ec2-user@[INSTANCE_IP]
cd /home/ec2-user
tar -xzf ChatMRPT_pre_refactor_backup_[TIMESTAMP].tar.gz
sudo systemctl restart chatmrpt
```

## Post-Deployment Monitoring

1. Check application logs for errors:
   ```bash
   sudo journalctl -u chatmrpt -f
   ```

2. Test key functionality:
   - Upload a CSV file
   - Run a data query
   - Generate a visualization
   - Check that prompts are being built correctly

3. Monitor for 15-30 minutes for any issues

## Risk Assessment

- **Risk Level**: LOW
- **Reasons**:
  - Backward compatibility maintained
  - Fallback mechanisms in place
  - Tested locally with success
  - Easy rollback available

## Notes

- Legacy tool wrappers remain as fallbacks (not removed)
- Old prompt building code already removed
- Services use slightly different names internally:
  - `data_repo` (not `data_repository`)
  - `context_service` (not `session_context_service`)

## Decision Required

**Deploy Now?** The refactoring is tested and ready. The changes are backward compatible with fallback mechanisms.

**Recommendation**: Deploy to production with the standard deployment script, then verify on both instances.