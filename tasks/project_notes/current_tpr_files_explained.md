# Current TPR Module Files - Complete List with Status

## 🟢 ACTIVELY USED FILES (New Interactive System)

### Integration Layer
- **`integration/interactive_tpr_handler.py`** ✅ NEW - Main handler with fuzzy ward matching
- **`integration/__init__.py`** ✅ ACTIVE - Factory that creates handlers (supports both old/new)

### Interactive Components  
- **`interactive_conversation.py`** ✅ NEW - Manages user dialogue for ward matching
- **`interactive_prompts.py`** ✅ NEW - User-friendly prompts and messages

### Output Generation
- **`output/output_generator.py`** ✅ MODIFIED - Generates 3 output files (uses WardName_Matched column)
- **`output/tpr_report_generator.py`** ✅ ACTIVE - Creates HTML reports

## 🟡 SHARED/FOUNDATION FILES (Used by Both Systems)

### Core Calculations
- **`core/tpr_calculator.py`** ✅ SHARED - TPR formulas (math is correct, both use it)
- **`core/tpr_state_manager.py`** ✅ SHARED - Manages session state
- **`core/tpr_pipeline.py`** ✅ SHARED - Pipeline orchestration

### Data Processing
- **`data/nmep_parser.py`** ✅ SHARED - Parses NMEP Excel files
- **`data/geopolitical_zones.py`** ✅ SHARED - Zone variables mapping
- **`data/data_validator.py`** ✅ SHARED - Validates data quality

### Services
- **`services/shapefile_extractor.py`** ✅ SHARED - Extracts shapefile data
- **`services/state_selector.py`** ✅ SHARED - Handles state selection
- **`services/raster_extractor.py`** ✅ SHARED - Extracts environmental variables
- **`services/facility_filter.py`** ✅ SHARED - Filters by facility level
- **`services/threshold_detector.py`** ✅ SHARED - Detects urban thresholds
- **`services/tpr_visualization_service.py`** ✅ SHARED - Creates TPR maps

### Integration Support
- **`integration/upload_detector.py`** ✅ SHARED - Detects TPR uploads
- **`integration/tpr_workflow_router.py`** ✅ SHARED - Routes workflows
- **`integration/risk_transition.py`** ✅ SHARED - Transitions to risk analysis

## 🔴 OLD/LEGACY FILES (Fallback Only)

### Original Implementation (Still Used if USE_INTERACTIVE_TPR=false)
- **`integration/tpr_handler.py`** ⚠️ OLD - Original rigid handler (fallback)
- **`core/tpr_conversation_manager.py`** ⚠️ OLD - Original conversation manager (rigid)
- **`data/column_mapper.py`** ⚠️ OLD - Rigid column mapping (bypassed by new system)

## ❌ UNUSED FILES (Never Implemented)

### Failed First Attempt (Can be deleted)
- **`conversation.py`** ❌ UNUSED - ReAct pattern attempt (never used)
- **`prompts.py`** ❌ UNUSED - Chain-of-thought prompts (never used)
- **`sandbox.py`** ❌ UNUSED - Code sandbox (never used)

## 📁 OTHER FILES

### Module Setup
- **`__init__.py`** - Module initialization files
- **`services/__init__.py`** - Services initialization
- **`output/__init__.py`** - Output initialization
- **`data/__init__.py`** - Data initialization
- **`integration/__init__.py`** - Integration initialization

### Tests
- **`tests/*.py`** - Various test files (may need updating for new system)

### Utilities
- **`raster_database/compute_annual_averages.py`** - Raster data processing

## Summary Count

- **🟢 Active (New System)**: 5 files
- **🟡 Shared/Foundation**: 15 files  
- **🔴 Legacy (Fallback)**: 3 files
- **❌ Unused**: 3 files
- **📁 Other**: 21 files (tests, init files)

**Total**: 47 Python files in TPR module

## What Happens When USE_INTERACTIVE_TPR=true

```
1. integration/__init__.py checks environment variable
2. Creates InteractiveTPRHandler (NEW)
3. Uses interactive_conversation.py for ward matching
4. Fuzzy matches ward names with user verification
5. Passes matched names to output_generator.py
6. Generates files with properly matched ward names
```

## What Happens When USE_INTERACTIVE_TPR=false

```
1. integration/__init__.py checks environment variable
2. Creates TPRHandler (OLD)
3. Uses tpr_conversation_manager.py (rigid)
4. Drops unmatched wards
5. Generates files with data loss
```