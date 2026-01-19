# ChatMRPT Architecture Migration Guide

## Overview

This guide documents the migration from the complex, over-engineered architecture to a simplified py-sidebot-inspired design.

## Migration Status

### ✅ Completed
1. **System Prompts** - Updated to focus on user intent
2. **Visualization Loading** - Uses lazy loading with `get_unified_dataset()`
3. **UnifiedDataState** - Single source of truth for data
4. **Direct Tools** - Simple async functions following py-sidebot pattern
5. **SimpleRequestInterpreter** - Clean implementation without complex routing
6. **Analysis State Handler** - Manages post-analysis transitions

### 🔄 In Progress
- Testing end-to-end implementation
- Gradual migration of existing tools

### 📋 TODO
- Full migration of all tools to new framework
- Remove legacy code paths

## How to Enable the New Architecture

### Option 1: Environment Variable
```bash
export USE_SIMPLE_INTERPRETER=true
python run.py
```

### Option 2: Flask Configuration
```python
# In app/config/development.py or production.py
USE_SIMPLE_INTERPRETER = True
```

### Option 3: Runtime Migration
```python
from app.core.interpreter_migration import migrate_to_simple_interpreter
from app.services.container import get_service_container

container = get_service_container()
migrate_to_simple_interpreter(container)
```

## Architecture Changes

### Before (Complex)
```
User Message
    ↓
RequestInterpreter (complex routing)
    ↓
Pattern Matching & Intent Detection
    ↓
Tool Selection Logic
    ↓
Parameter Extraction
    ↓
Multiple Data Loading Paths
    ↓
Tool Execution
```

### After (Simple - py-sidebot inspired)
```
User Message
    ↓
SimpleRequestInterpreter
    ↓
LLM with All Tools Available
    ↓
Direct Tool Execution
    ↓
UnifiedDataState (single source)
```

## Key Components

### 1. UnifiedDataState
Located in `app/core/unified_data_state.py`

Provides single source of truth:
- `current_data` - Returns unified data if available, otherwise raw data
- `get_stage()` - Returns 'no_data', 'pre_analysis', or 'post_analysis'
- Lazy loading with caching
- Automatic state detection

### 2. Direct Tools
Located in `app/core/direct_tools.py`

Simple async functions:
```python
async def execute_sql_query(query: str, session_id: str) -> str:
    # Direct execution on UnifiedDataState
    
async def execute_python_code(code: str, session_id: str) -> str:
    # Direct pandas/numpy execution
```

### 3. SimpleRequestInterpreter
Located in `app/core/simple_request_interpreter.py`

Key features:
- No complex routing logic
- All tools registered as simple functions
- LLM handles tool selection
- Clean, maintainable code

## Testing the Migration

### 1. Basic Functionality Test
```python
# Test UnifiedDataState
from app.core.unified_data_state import get_data_state

data_state = get_data_state(session_id)
print(f"Stage: {data_state.get_stage()}")
print(f"Data shape: {data_state.current_data.shape if data_state.current_data else 'No data'}")
```

### 2. SQL Query Test
After analysis completes, test SQL generation:
- User: "Show me the top 10 highest risk wards"
- Expected: Should return actual data, not column names

### 3. Visualization Test
After analysis completes:
- User: "Create vulnerability map"
- Expected: Should successfully create map without "no data" errors

## Rollback Plan

If issues arise, disable the new architecture:
```bash
unset USE_SIMPLE_INTERPRETER
# or
export USE_SIMPLE_INTERPRETER=false
```

The system will automatically fall back to the legacy RequestInterpreter.

## Benefits of Migration

1. **Simpler Code** - Easier to understand and maintain
2. **Better Performance** - Single data source, no repeated loading
3. **Correct Behavior** - SQL queries return data, visualizations work
4. **Extensibility** - Easy to add new tools
5. **Reliability** - Fewer moving parts, less to break

## Next Steps

1. **Monitor** - Watch logs for any issues with the new architecture
2. **Feedback** - Collect user feedback on improved SQL/visualization behavior
3. **Optimize** - Further simplify based on usage patterns
4. **Clean Up** - Remove legacy code once migration is stable