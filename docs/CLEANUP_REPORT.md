# ChatMRPT Codebase Cleanup Report

## Summary
The codebase contains a massive amount of legacy/unused code that's causing confusion. We're now using:
- **Frontend**: React (NOT Flask templates)
- **LLM Backend**: Ollama (NOT vLLM)
- **Arena**: Should be using a single, clean implementation

## Files/Directories to Remove

### 1. vLLM Related (19 files) - NO LONGER USED
```
.env.vllm
configure_vllm_backend.sh
deploy_vllm_config_to_staging.sh
fix_vllm_security_group.sh
fix_vllm_tool_calling.sh
launch_gpu_instance_for_vllm.sh
setup_vllm_*.sh (7 files)
test_vllm_*.py (2 files)
vllm_arena_server.py
vllm_qwen3_integration_complete.md
tasks/project_notes/data_analysis_vllm_fix.md
tasks/project_notes/vllm_setup_notes.md
```

### 2. Old Flask Frontend - NO LONGER USED
```
app/templates/               # Entire directory - using React now
app/static/archived_old_frontend/  # Archived old code
app/static/css/              # Old CSS - React has its own
app/static/js/               # Old JS - React has its own
```

### 3. Duplicate Arena Implementations
Keep only `app/core/arena_manager.py`, remove:
```
app/core/arena_manager_memory_backup.py
app/core/arena_manager_redis.py
app/core/arena_manager_redis_fixed.py
arena_manager_update.py
```

### 4. Excessive Scripts in Root (359 total!)
- **149 deployment scripts** (deploy_*.sh)
- **144 test files** in root (test_*.py, test_*.sh, test_*.html)
- **66 check/fix scripts** (check_*.sh, fix_*.sh)

These should be:
- Moved to appropriate directories (deployment/, tests/, scripts/)
- Or deleted if obsolete

### 5. Old Model References
Current .env shows mixed references:
- vLLM settings (lines 37-38, 58-59) - REMOVE
- Old arena models that don't exist (line 60) - UPDATE

### 6. Unused AWS/Deployment Files
```
Procfile
render.yaml
docker-compose.yml
apt-packages
aws_files/  # May contain sensitive data
backups*/   # Multiple backup directories
```

## What We Should Keep

### Current Stack
1. **Frontend**: `frontend/` directory (React app)
2. **Backend**: Flask API in `app/` (but remove templates)
3. **Ollama Integration**: 
   - `app/core/ollama_adapter.py`
   - `app/core/ollama_manager.py`
4. **Arena**: Single clean implementation
5. **Core App**: Essential Flask routes and services

### Proper Structure
```
ChatMRPT/
├── frontend/           # React app
├── app/               # Flask backend (API only)
│   ├── core/          # Core logic
│   ├── web/routes/    # API routes
│   └── services/      # Business logic
├── tests/             # All test files
├── scripts/           # Utility scripts
├── deployment/        # Deployment configs
└── docs/              # Documentation
```

## Recommended Actions

1. **Create backup** before cleanup:
   ```bash
   tar -czf chatmrpt_backup_$(date +%Y%m%d).tar.gz .
   ```

2. **Move to organized structure**:
   - Create `scripts/deployment/`, `scripts/checks/`, `scripts/fixes/`
   - Move test files to `tests/`
   - Archive or delete old implementations

3. **Update configurations**:
   - Remove vLLM references from .env
   - Update arena model configurations
   - Clean up Flask static serving (React handles this)

4. **Focus on Ollama**:
   - Ensure Ollama models are correctly configured
   - Remove all vLLM references
   - Simplify model naming

## Estimated Cleanup Impact
- **Files to remove/reorganize**: ~500+ files
- **Code reduction**: ~40-50% of current codebase
- **Clarity improvement**: Significant - clear separation of concerns
- **Maintenance**: Much easier with organized structure

## Next Steps
1. Backup everything
2. Create proper directory structure
3. Move files to appropriate locations
4. Delete confirmed unused code
5. Update all imports and references
6. Test that core functionality still works