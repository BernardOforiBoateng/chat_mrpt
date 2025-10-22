# Debug Logging Implementation for Risk Analysis Flow

## Summary
Comprehensive debug logging has been added to the risk analysis flow to track all requests and responses, helping identify where visualizations fail after TPR transition.

## Files Modified

### 1. `/app/core/request_interpreter.py`
- Added debug logging at the start of `process_message()` to track:
  - Session ID
  - User message
  - Session data keys
  - Additional kwargs
- Added debug logging in `_llm_with_tools()` to track:
  - Available tools
  - Session context state
- Added debug logging for tool execution to track:
  - Tool name and parameters
  - Success/failure status
  - Error details if failed

### 2. `/app/tools/complete_analysis_tools.py`
- Added debug logging at the start of `_execute()` to track:
  - Session ID
  - Variables being used (composite and PCA)
  - Files present BEFORE analysis
- Added debug logging at completion to track:
  - Files created AFTER analysis
  - Specifically checks for `unified_dataset.csv` creation
  - Lists all HTML visualization files created

### 3. `/app/tools/visualization_maps_tools.py`
- Added debug logging in `CreateVulnerabilityMap.execute()` to track:
  - Session ID
  - Risk categories and classification method
  - Checks for `unified_dataset.csv` existence
  - Checks for `raw_data.csv` as potential fallback

### 4. `/app/tools/variable_distribution.py`
- Added debug logging in `execute()` to track:
  - Variable name being visualized
  - Session ID
  - File existence checks (raw_data.csv, unified_dataset.csv, raw_shapefile.zip)
- Added debug logging in `_load_data()` to track:
  - CSV loading success/failure
  - Data shape and columns
  - Whether the requested variable exists in the data
  - Case-insensitive matching attempts

## Debug Log Markers

All debug logs are prefixed with `🔍 DEBUG:` for easy filtering.

### Key Debug Points:
1. **Request Entry**: `🔍 DEBUG REQUEST INTERPRETER: Processing request`
2. **Tool Selection**: `🔍 DEBUG LLM_WITH_TOOLS: Starting tool selection`
3. **Tool Execution**: `🔍 DEBUG: Executing tool {tool_name} with params: {params}`
4. **Analysis Start**: `🔍 DEBUG COMPLETE ANALYSIS: Starting execution`
5. **File Checks**: `🔍 DEBUG: Files in session BEFORE/AFTER analysis`
6. **Unified Dataset**: `🔍 DEBUG: UNIFIED DATASET CREATED/NOT CREATED`
7. **Variable Distribution**: `🔍 DEBUG VARIABLE DISTRIBUTION: Starting for variable`
8. **Vulnerability Map**: `🔍 DEBUG VULNERABILITY MAP: Starting`

## Deployment

Debug logging has been deployed to both production instances:
- Instance 1: 3.21.167.170
- Instance 2: 18.220.103.20

## How to Monitor

### View Debug Logs on AWS:
```bash
# Connect to production instance
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@3.21.167.170

# View live debug logs
sudo journalctl -u chatmrpt -f | grep "🔍 DEBUG"

# View recent debug logs
sudo journalctl -u chatmrpt --since "10 minutes ago" | grep "🔍 DEBUG"
```

### Test the Debug Logging:
```bash
# Run the test script
chmod +x test_debug_logs.sh
./test_debug_logs.sh
```

## Expected Insights

The debug logging will reveal:

1. **Request Flow**: Exact messages being sent and how they're interpreted
2. **Tool Selection**: Which tools are being selected for each request
3. **File State**: What files exist before and after each operation
4. **Unified Dataset Issue**: Whether `unified_dataset.csv` is being created during risk analysis
5. **Visualization Failures**: Exact error messages when visualizations fail
6. **Variable Matching**: Whether variables like "evi" are found in the data
7. **Fallback Opportunities**: Where we could add fallbacks to `raw_data.csv`

## Next Steps

After analyzing the debug logs, we can:
1. Identify the exact point of failure
2. Implement appropriate fallbacks
3. Fix the unified dataset creation issue
4. Ensure visualizations work after TPR transition

## Test Session

Using session ID: `847e36e9-ad20-4641-afd5-bda1b5c8225a`
This session has TPR data and should show the visualization failures.