# Production vs Staging Architecture Discovery

## Date: January 18, 2025

## Major Discovery

Production and staging are running **completely different codebases** for TPR handling:
- **Production:** Uses the original `tpr_module` system
- **Staging:** Uses the new `data_analysis_v3` system

This explains why the workflow transition works flawlessly in production but fails in staging.

## Investigation Process

### 1. Initial Hypothesis
Initially thought production had a better implementation of the same system. Expected to find:
- Better logic in request_interpreter.py
- Fixed workflow_transitioned checks
- Better state management

### 2. SSH Investigation
Connected through staging to production:
```bash
ssh -i /tmp/chatmrpt-key.pem ec2-user@3.21.167.170
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52
```

### 3. The Surprise Discovery
When checking production's app directory:
```bash
ls -la /home/ec2-user/ChatMRPT/app/
```
Found:
- ✅ `tpr_module` directory exists
- ❌ `data_analysis_v3` directory DOES NOT exist
- ❌ `simple_instance_check.py` DOES NOT exist

This was completely unexpected!

## Key Architectural Differences

### Production's TPR Module
```
/app/tpr_module/
├── core/
│   ├── tpr_calculator.py
│   ├── tpr_state_manager.py
│   └── tpr_pipeline.py
├── integration/
│   ├── risk_transition.py
│   ├── tpr_handler.py
│   └── tpr_workflow_router.py  ← Smart router
└── output/
    └── tpr_report_generator.py
```

**Transition Method:**
1. TPR completes → stage = 'complete'
2. User says "yes" → router detects confirmation
3. Returns `__DATA_UPLOADED__` trigger
4. request_interpreter shows exploration menu
5. Clean transition!

### Staging's Data Analysis V3
```
/app/data_analysis_v3/
├── core/
│   ├── agent.py
│   ├── state_manager.py
│   └── tpr_workflow_handler.py
└── tools/
    └── [30+ analysis tools]
```

**Transition Method (Broken):**
1. TPR completes → workflow_transitioned = true
2. Removes .data_analysis_mode flag
3. Logic bug: only checks transition if flag exists
4. simple_instance_check syncs and recreates flag
5. Transition fails!

## The Multi-Instance Sync Problem

### Production
- No `simple_instance_check.py`
- Each instance handles its own sessions
- No cross-instance state sync
- No race conditions

### Staging
- Has `simple_instance_check.py`
- Actively syncs sessions between instances
- Copies flags and state files
- Creates race conditions

The sync was added to staging to handle multi-instance Data Analysis V3, but it's causing the transition to fail.

## Code Snippets

### Production's Clean Trigger (tpr_workflow_router.py)
```python
if enhanced_session_data['tpr_stage'] == 'complete':
    confirmation_words = {'yes', 'y', 'ok', 'okay', 'sure', 'proceed'}
    if any(word in user_message.lower() for word in confirmation_words):
        return {
            'status': 'tpr_to_main_transition',
            'response': '__DATA_UPLOADED__',
            'trigger_exploration': True
        }
```

### Staging's Buggy Check (request_interpreter.py)
```python
# BUG: Only checks if flag exists
if session_id and has_data_analysis_flag:
    # Check workflow_transitioned
    # But flag is already removed!
```

## Lessons Learned

1. **Don't assume environments are similar** - Production and staging can diverge significantly
2. **Simpler is often better** - Production's trigger-based approach is more robust
3. **Multi-instance sync is complex** - Introduces race conditions and state conflicts
4. **Check the basics first** - Should have checked if modules exist before diving into code
5. **Version control matters** - Need better tracking of what's deployed where

## Why This Happened

Looking at git status, the tpr_module files are marked with 'D' (deleted) in staging:
```
D app/tpr_module/__init__.py
D app/tpr_module/core/__init__.py
D app/tpr_module/core/tpr_calculator.py
[... all tpr_module files deleted ...]
```

This suggests someone migrated staging to the new Data Analysis V3 system but production was never updated. This created a divergence where:
- Production runs the stable, working tpr_module
- Staging runs the newer but buggy data_analysis_v3

## Impact

This discovery changes everything:
1. The "fix" isn't to patch staging's bugs
2. The real question is: should production migrate to V3 or should staging revert?
3. Need to understand why the migration happened and if V3's features are worth the complexity

## Next Steps

Options:
1. **Revert staging** to use tpr_module like production
2. **Fix V3's bugs** and keep staging on the new system
3. **Hybrid approach** - use V3's features with production's transition method

The team needs to decide the strategic direction before proceeding with fixes.