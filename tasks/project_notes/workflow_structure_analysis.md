# ChatMRPT Workflow Structure Analysis

## Date: 2025-09-04
## Status: Investigation Complete

## Executive Summary
ChatMRPT has **four distinct workflows** that are NOT overlapping, but rather complementary systems designed for different use cases. Each workflow has its own entry point, processing logic, and transition mechanisms.

## The Four Workflows

### 1. Request Interpreter (Main Chat Workflow)
**Purpose**: General conversational interface for asking questions about malaria, data exploration after risk analysis
**Entry Point**: `/send_message` endpoint
**Location**: `app/core/request_interpreter.py`
**Key Features**:
- Handles general malaria questions (e.g., "What is malaria?")
- Uses OpenAI with function calling for tool-based responses
- Activated AFTER data has been uploaded and analyzed (CSV + Shapefile)
- Has access to tools for visualization, data querying, settlement mapping
- Uses Arena mode for knowledge questions (comparing multiple models)

**Activation Trigger**: 
- Default workflow for standard chat
- Active when user has uploaded CSV + Shapefile files
- Handles post-analysis interactions

### 2. Risk Analysis Workflow
**Purpose**: Core malaria risk assessment and ward vulnerability ranking
**Entry Point**: Triggered after CSV + Shapefile upload
**Location**: `app/analysis/pipeline.py`
**Key Features**:
- Performs composite scoring (mean-based and PCA-based)
- Ranks wards by vulnerability (High/Medium/Low)
- Creates vulnerability maps and visualizations
- Generates ITN distribution recommendations
- Works with ward-level demographic and health data

**Activation Trigger**:
- User uploads CSV file with demographic data
- User uploads Shapefile with ward boundaries
- System automatically runs analysis pipeline

### 3. Data Analysis Agent (Single File Workflow)
**Purpose**: General data exploration and analysis for ANY data file
**Entry Point**: `/api/data-analysis/upload` (Data Analysis tab)
**Location**: `app/data_analysis_v3/core/agent.py`
**Key Features**:
- Uses LangGraph with OpenAI gpt-4o
- Handles single file uploads (CSV/Excel/JSON)
- Interactive data exploration with natural language
- Automatic TPR detection for NMEP files
- Can transition to TPR workflow if TPR data detected

**Activation Trigger**:
- User switches to "Data Analysis" tab
- User uploads single data file
- System uses LangGraph agent for exploration

### 4. TPR Workflow (Test Positivity Rate)
**Purpose**: Process TPR data from NMEP Excel files for risk analysis
**Entry Point**: Detected within Data Analysis workflow
**Location**: `app/data_analysis_v3/core/tpr_workflow_handler.py`
**Key Features**:
- Handles NMEP (National Malaria Elimination Programme) Excel files
- Guides user through state/facility/age group selection
- Calculates TPR metrics
- Prepares data for risk analysis pipeline
- Transitions to Risk Analysis workflow when complete

**Activation Trigger**:
- Data Analysis Agent detects TPR data format
- User confirms they want to calculate TPR
- System guides through selection process

## Workflow Transitions

### Standard Flow (CSV + Shapefile):
```
1. User uploads CSV + Shapefile
   ↓
2. Risk Analysis Workflow runs automatically
   ↓
3. Request Interpreter becomes active for exploration
```

### Data Analysis Flow (Single File):
```
1. User switches to Data Analysis tab
   ↓
2. User uploads single file
   ↓
3. Data Analysis Agent explores data
   ↓
   [If TPR data detected]
   ↓
4. TPR Workflow guides selection
   ↓
5. Transitions to Risk Analysis Workflow
   ↓
6. Request Interpreter for final exploration
```

## Key Integration Points

### 1. Session Management
- Flask sessions track workflow state
- Session ID used across all workflows
- Files stored in `instance/uploads/{session_id}/`

### 2. Workflow State Files
- `.data_analysis_mode` - Indicates Data Analysis V3 active
- `.tpr_workflow_active` - TPR workflow in progress
- `.analysis_complete` - Risk analysis finished
- These files enable cross-worker state detection

### 3. OpenAI Integration
- **Request Interpreter**: Uses function calling for tools
- **Data Analysis Agent**: Uses LangGraph with gpt-4o
- **Risk Analysis**: Can use LLM for variable selection
- **TPR Workflow**: Uses LLM for data understanding

## Current Disconnects & Issues

### 1. ✅ Working
- Individual workflows function correctly
- Session management works
- File uploads successful
- Arena mode operational

### 2. ⚠️ Potential Issues

#### A. Workflow Transitions
**Issue**: Transitions between workflows may not always trigger correctly
**Location**: Various state managers
**Evidence**: Complex state checking logic across multiple files

#### B. OpenAI Tool Calling
**Issue**: Request Interpreter's function calling may not execute properly
**Location**: `app/core/request_interpreter.py` lines 115-120
**Fix Needed**: Proper tool execution and response formatting

#### C. Data Availability
**Issue**: Data may not be available across workers in multi-instance setup
**Location**: Session and file-based state management
**Fix Needed**: Ensure consistent data access across workers

#### D. Frontend Routing
**Issue**: Frontend may not correctly route to appropriate endpoints
**Location**: `frontend/src/services/api.ts`
**Fix Needed**: Ensure correct endpoint selection based on workflow

## Correct Architecture Understanding

The system is NOT overlapping but rather a **staged workflow system**:

1. **Entry Points**: Different tabs/upload methods trigger different workflows
2. **Processing**: Each workflow has specialized processing logic
3. **Transitions**: Clear handoffs between workflows
4. **Exit Points**: All workflows eventually enable Request Interpreter for exploration

## Priority Fixes

### 1. 🔴 Critical
- Fix OpenAI function calling in Request Interpreter
- Ensure workflow transitions work reliably
- Fix data availability across workers

### 2. 🟡 Important
- Streamline TPR → Risk Analysis transition
- Improve error handling in workflow transitions
- Add clear user feedback for workflow states

### 3. 🟢 Enhancement
- Add workflow status indicators in UI
- Improve state persistence
- Add workflow reset capability

## Testing Checklist

### Test Case 1: Standard Flow
1. Upload CSV + Shapefile
2. Verify risk analysis runs
3. Ask "What are the high risk wards?"
4. Verify Request Interpreter responds with data

### Test Case 2: Data Analysis → TPR Flow
1. Switch to Data Analysis tab
2. Upload NMEP Excel file
3. Verify TPR workflow starts
4. Complete TPR selections
5. Verify transition to risk analysis
6. Verify Request Interpreter active

### Test Case 3: Arena Mode
1. Ask "What is malaria?"
2. Verify Arena mode activates
3. Vote on responses
4. Verify tournament progression

## Conclusion

ChatMRPT has a well-designed multi-workflow architecture where:
- **Request Interpreter**: General chat and post-analysis exploration
- **Risk Analysis**: Core malaria vulnerability assessment
- **Data Analysis Agent**: Interactive single-file exploration
- **TPR Workflow**: NMEP data preparation for risk analysis

The workflows are complementary, not competing. The main issues are around workflow transitions and OpenAI integration, not architectural conflicts.