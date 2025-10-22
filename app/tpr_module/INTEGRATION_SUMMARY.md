# TPR Module Integration Summary

## Overview
The TPR (Test Positivity Rate) module has been successfully integrated into ChatMRPT. This document summarizes the integration points and how the module works within the main application.

## Key Integration Points

### 1. Upload Detection (`app/web/routes/upload_routes.py`)
- **TPRUploadDetector** automatically detects NMEP Excel files during upload
- New upload types added: `tpr_excel` and `tpr_shapefile`
- Detection happens seamlessly without breaking existing CSV/shapefile uploads
- Integration is done via minimal modification to existing UploadTypeDetector class

### 2. Workflow Routing
When a TPR file is detected:
1. Upload handler routes to `handle_tpr_path()` function
2. TPRHandler is initialized for the session
3. Session flags are set: `tpr_workflow_active = True`
4. User receives initial TPR-specific response

### 3. Conversational Flow (`app/core/request_interpreter.py`)
- Special workflow handling checks for `tpr_workflow_active` flag
- All messages are routed to TPRHandler when TPR workflow is active
- Natural language processing handles state selection and parameter configuration
- No rigid patterns - uses LLM for flexible intent recognition

### 4. API Endpoints (`app/web/routes/tpr_routes.py`)
New endpoints added under `/api/tpr/`:
- `POST /process` - Process conversational messages
- `GET /status` - Get current workflow status
- `GET /download/<file_type>` - Download output files
- `GET /states` - Get available states
- `POST /validate-state` - Validate state selection
- `POST /cancel` - Cancel active workflow

### 5. Session Management
TPR workflow uses session flags:
- `tpr_workflow_active`: Indicates active TPR workflow
- `tpr_session_id`: Links to TPR handler instance
- `upload_type`: Set to `tpr_excel` or `tpr_shapefile`

## Workflow Summary

1. **Upload**: User uploads NMEP Excel file (with optional shapefile)
2. **Detection**: System detects TPR file and routes to TPR workflow
3. **Conversation**: Natural language interface guides user through:
   - State selection
   - Facility level filtering (optional)
   - Age group selection (optional)
4. **Processing**: TPR pipeline runs:
   - Calculates TPR using max(RDT, Microscopy) logic
   - Aggregates to ward level
   - Extracts zone-specific environmental variables
   - Generates three output files
5. **Completion**: Files are ready for download, workflow ends

## Key Features

### Natural Language Processing
- No rigid command patterns
- Flexible understanding of user intent
- Educational responses explain TPR methodology

### Zone-Aware Processing
- Automatically selects environmental variables based on state's geopolitical zone
- Six zones with tailored variable sets
- Ensures relevant factors for regional malaria assessment

### Three-File Output
1. **TPR Analysis CSV**: Detailed TPR calculations per ward
2. **Main Analysis CSV**: TPR + environmental variables
3. **Shapefile**: Geographic boundaries with all data

### Performance
- Raster database eliminates Google Earth Engine dependency
- Local processing for faster results
- Parallel extraction of environmental variables

## Configuration

### Enable/Disable TPR Module
The module can be disabled by setting in Flask config:
```python
ENABLE_TPR_MODULE = False
```

### Raster Database Location
Default: `app/tpr_module/raster_database/`
- Organized by variable type (vegetation/, rainfall/, etc.)
- Consistent naming: `{variable}_{year}_{temporal}.tif`

## Error Handling
- Graceful fallback if TPR module unavailable
- Clear error messages for missing dependencies
- Session cleanup on workflow cancellation

## Testing
Run integration tests:
```bash
python app/tpr_module/tests/test_integration.py
```

## Next Steps
1. Add comprehensive unit tests for each component
2. Create user documentation with screenshots
3. Performance optimization for large state datasets
4. Add support for historical TPR trend analysis