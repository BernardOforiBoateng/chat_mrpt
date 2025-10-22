# Current TPR Implementation Files to Review/Delete

## Overview
The current TPR implementation is scattered across the codebase and needs to be replaced with a modular approach that creates standard CSV + Shapefile outputs for the main upload flow.

## Core TPR Files (To be replaced/deleted)

### 1. Main TPR Processing
- **`app/data/tpr_parser.py`** - Current TPR parser that extracts from Excel
- **`app/services/tpr_data_extractor.py`** - Creates convergence files and manages state selection

### 2. GEE Variable Extraction (Shared services - keep but decouple)
- **`app/services/variable_extractor_real.py`** - Extracts variables from Google Earth Engine
- **`app/services/robust_earth_engine_client.py`** - Earth Engine authentication

### 3. Shapefile Services (Shared - keep)
- **`app/services/shapefile_fetcher.py`** - Fetches Nigerian administrative boundaries

### 4. Web Routes (TPR-specific routes to remove)
- **`app/web/routes/upload_routes.py`** - Contains `/api/tpr/*` routes:
  - `/api/tpr/detect-states`
  - `/api/tpr/process`

### 5. Frontend (TPR-specific functions to remove)
- **`app/static/js/modules/upload/file-uploader.js`** - Contains TPR upload functions:
  - `uploadTprFile()`
  - `handleStateSelection()`
  - `processSelectedState()`
  - `handleTprUploadSuccess()`
  - `handleTprUploadError()`
  - `setTprUploadStatus()`

## Files Mentioning TPR (Need updates)
- `app/core/request_interpreter.py` - Remove TPR routing
- `app/templates/index.html` - Remove TPR upload UI
- `app/core/variable_matcher.py` - Remove TPR-specific matching
- `app/analysis/region_aware_selection.py` - Remove TPR handling
- `app/analysis/pipeline_stages/data_preparation.py` - Remove TPR processing

## Current Implementation Problems
1. **Too integrated** - TPR logic mixed into main codebase
2. **State selection in UI** - Forces user to select state in upload modal
3. **Creates convergence files** - Goes straight to analysis format instead of standard CSV
4. **Triple parsing issue** - Parser called multiple times
5. **No interactive journey** - Just processes data without user guidance

## New Modular Approach Goals
1. **Completely separate module** - `app/tpr_module/` independent of main code
2. **Interactive conversation** - Step-by-step guidance through TPR calculation
3. **Standard outputs** - Creates regular CSV + Shapefile that main upload can handle
4. **No UI changes** - Uses existing chat interface for interaction
5. **Joins at upload** - Final output feeds into normal upload flow

## Key Differences in New Approach
- **Old**: Excel → Parser → State Selection → Convergence Files → Analysis
- **New**: Excel → Interactive Journey → TPR Calculations → Standard CSV + Shapefile → Normal Upload

This separation ensures the TPR module can be developed, tested, and modified without affecting the core ChatMRPT functionality.