# TPR Implementation Audit - What We Actually Have

## Date: August 13, 2025

## Current Architecture Discovery

### Two Parallel TPR Systems Exist!

#### System 1: Direct Workflow (What We've Been Working On)
**Location**: `app/data_analysis_v3/core/agent.py`
**Method**: Direct method calls in agent

**Flow**:
1. User says "guide me through TPR"
2. `_start_tpr_workflow()` → State selection
3. `_handle_state_selection()` → Facility selection  
4. `_handle_facility_selection()` → Age group selection
5. `_handle_age_group_selection()` → Calls `_calculate_tpr()`
6. `_calculate_tpr()` → Calls `calculate_ward_tpr()` from `app/core/tpr_utils.py`

**What it does**:
- ✅ Guides through 3-step selection
- ✅ Calculates TPR values
- ✅ Returns basic results

**What it DOESN'T do**:
- ❌ Generate TPR maps
- ❌ Create raw_data.csv for risk analysis
- ❌ Create raw_shapefile.zip
- ❌ Extract environmental variables
- ❌ Prepare for risk analysis pipeline

#### System 2: Tool-Based System (Available but NOT Used in Workflow)
**Location**: `app/data_analysis_v3/tools/tpr_analysis_tool.py`  
**Method**: LangChain tool that agent CAN call

**Available Actions**:
1. `analyze` - Basic data exploration
2. `calculate_tpr` - Calculate TPR + CREATE MAP
3. `prepare_for_risk` - Create files for risk analysis

**What it CAN do**:
- ✅ Everything System 1 does
- ✅ Generate interactive TPR maps (Plotly)
- ✅ Create raw_data.csv with environmental variables
- ✅ Create raw_shapefile.zip
- ✅ Extract zone-specific environmental data
- ✅ Set flags for risk analysis readiness

**Current Integration**:
- Tool is added to agent.tools when TPR data detected
- Tool is bound to LLM for potential use
- BUT the guided workflow never calls it!

### The Problem

We have two systems:
1. **Guided workflow** (what user experiences) - uses direct methods, no maps
2. **Tool system** (sitting idle) - has all features but not integrated into workflow

When user follows the guided TPR workflow:
```
User: "Guide me through TPR"
Agent: Uses System 1 (direct methods)
Result: TPR calculated but NO map, NO risk prep
```

If user manually calls the tool:
```
User: "Use analyze_tpr_data tool with action='calculate_tpr'"
Agent: Uses System 2 (tool)
Result: TPR calculated WITH map
```

### What Actually Happens Now

Current flow when user uploads TPR data and asks for guidance:
1. Data uploaded → TPR detected → Tool added to agent.tools
2. User: "Guide me through TPR"
3. Agent starts guided workflow (System 1)
4. Selections made: State → Facility → Age
5. `_calculate_tpr()` runs → Basic TPR calculation
6. Results shown: Average TPR percentage
7. **NO MAP GENERATED**
8. **NO RISK ANALYSIS PREP**

### The Fix Needed

**Option 1: Integrate Tool into Workflow**
Modify `_calculate_tpr()` to call the tool instead:
```python
def _calculate_tpr(self):
    # Instead of direct calculation, use the tool
    from ..tools.tpr_analysis_tool import analyze_tpr_data
    
    options = {
        'age_group': self.tpr_selections['age_group'],
        'facility_level': self.tpr_selections['facility_level'],
        'test_method': 'both'
    }
    
    result = analyze_tpr_data(
        action="calculate_tpr",
        options=json.dumps(options),
        graph_state=self.graph_state
    )
```

**Option 2: Add Map/Risk Features to Direct Method**
Enhance `_calculate_tpr()` to:
1. Call `create_tpr_map()` after calculation
2. Call risk preparation logic
3. Save necessary files

### Files Involved

**System 1 (Direct)**:
- `app/data_analysis_v3/core/agent.py` - Main workflow
- `app/core/tpr_utils.py` - TPR calculation
- `app/data_analysis_v3/core/state_manager.py` - State persistence
- `app/data_analysis_v3/core/tpr_data_analyzer.py` - Statistics

**System 2 (Tool)**:
- `app/data_analysis_v3/tools/tpr_analysis_tool.py` - Full featured tool
- Has map generation
- Has risk preparation
- Has environmental extraction

### Summary

We've been fixing the guided workflow (System 1) but it doesn't use the full-featured tool (System 2) that has maps and risk prep. The tool is available but sits unused during the guided workflow.

**Current Status**:
- Guided workflow works but is feature-limited
- Full-featured tool exists but isn't called
- User gets TPR calculation but no visualization or risk prep