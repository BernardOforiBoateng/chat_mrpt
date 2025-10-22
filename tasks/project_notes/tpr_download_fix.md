# TPR Download Issue Fix

**Date**: 2025-09-29
**Issue**: TPR analysis file downloads failing with "Site wasn't available" error
**Solution**: Fix path validation in export_routes.py to allow both uploads and exports directories

## Problem Description

Users were unable to download TPR analysis results from the modal dialog:
- TPR Analysis Results (raw_data.csv) - Failed
- Ward Boundaries Shapefile (raw_shapefile.zip) - Failed
- TPR Dashboard (tpr_dashboard.html) - Failed

Browser showed "Site wasn't available" for all download attempts.

## Root Cause

In `app/web/routes/export_routes.py`, the download endpoint was incorrectly validating file paths:

```python
# Line 178 - INCORRECT
if not str(file_path.resolve()).startswith(str(export_base_dir.resolve())):
    abort(403, "Invalid file path")
```

The problem:
1. TPR files are stored in `instance/uploads/{session_id}/`
2. The code was only allowing files from `instance/exports/{session_id}/`
3. This caused a 403 Forbidden error for all TPR file downloads

## Solution

Modified the path validation to accept files from BOTH directories:

```python
# Lines 177-183 - FIXED
# Ensure path is within allowed directories (exports OR uploads)
resolved_path = str(file_path.resolve())
allowed_dirs = [str(export_base_dir.resolve()), str(uploads_dir.resolve())]

if not any(resolved_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
    logger.error(f"Path traversal attempt: {file_path}")
    abort(403, "Invalid file path")
```

## File Locations

TPR analysis files are stored in different locations:
- **Uploads directory** (`instance/uploads/{session_id}/`):
  - raw_data.csv - TPR analysis results
  - raw_shapefile.zip - Ward boundaries
  - tpr_dashboard.html - Interactive dashboard

- **Exports directory** (`instance/exports/{session_id}/`):
  - ITN distribution results
  - Risk analysis results
  - Other exported files

## Testing

After the fix:
1. Files from uploads directory can be downloaded ✅
2. Files from exports directory still work ✅
3. Path traversal protection maintained ✅
4. Session validation still enforced ✅

## Deployment

Deployed to both production instances:
- Instance 1: 3.21.167.170 ✅
- Instance 2: 18.220.103.20 ✅

Services restarted on both instances.

## Prevention

This issue occurred because:
1. Different features store files in different directories
2. The validation logic was too restrictive
3. No testing for TPR file downloads

Future considerations:
1. Consolidate file storage locations
2. Add unit tests for download endpoints
3. Validate against multiple allowed directories from the start