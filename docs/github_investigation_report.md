# GitHub Investigation Report - Vulnerability Map Tools

## Key Findings:

### 1. Tool Classes in `visualization_maps_tools.py` (Both main branch and current):
- `CreateVulnerabilityMap` - For COMPOSITE method only
- `CreatePCAMap` - For PCA method only
- `CreateVulnerabilityMapComparison` - For SIDE-BY-SIDE comparison of both methods
- `CreateCompositeScoreMaps` - For composite score with model breakdowns
- `CreateUrbanExtentMap`
- `CreateDecisionTree`
- `CreateBoxPlot`
- `CreateInterventionMap`

### 2. Critical Difference Found:

**ON MAIN BRANCH (`app/tools/__init__.py`):**
```python
from .visualization_maps_tools import (
    CreateVulnerabilityMap,
    CreatePCAMap,
    CreateUrbanExtentMap,
    CreateDecisionTree,
    CreateCompositeScoreMaps,
    CreateBoxPlot,
    CreateInterventionMap
)
```
**NOTE:** `CreateVulnerabilityMapComparison` is NOT exported!

**CURRENT LOCAL (`app/tools/__init__.py`):**
```python
from .visualization_maps_tools import (
    CreateVulnerabilityMap,
    CreateVulnerabilityMapComparison,  # <-- I ADDED THIS TODAY (MISTAKE!)
    CreatePCAMap,
    CreateUrbanExtentMap,
    CreateDecisionTree,
    CreateCompositeScoreMaps,
    CreateBoxPlot,
    CreateInterventionMap
)
```

### 3. Tool Registration Names:
- `createvulnerabilitymap` - Composite only
- `createpcamap` - PCA only
- `create_vulnerability_map_comparison` - Side-by-side (overrides get_tool_name())
- `createcompositescoremaps` - Composite with breakdowns

### 4. The Problem:

1. I incorrectly added `CreateVulnerabilityMapComparison` to the exports in `__init__.py`
2. This may have broken the tool discovery or caused conflicts
3. The tool `CreateVulnerabilityMapComparison` exists in the file but was intentionally NOT exported
4. There is NO `CreateVulnerabilityMapSimple` tool - it never existed in the Git history

### 5. How It Should Work (based on main branch):

When user asks for "vulnerability map for composite score method":
- Should use `CreateCompositeScoreMaps` tool (registered as `createcompositescoremaps`)
- This creates composite score maps with individual model breakdowns

When user asks for generic "vulnerability map":
- Should use `CreateVulnerabilityMap` (for composite) or offer choices

The `CreateVulnerabilityMapComparison` tool exists but wasn't exported, possibly because it wasn't ready or had issues.

### 6. Current Error:
The error "Visualization file not found" occurs when:
- The tool is found and executed
- But the visualization file is not created properly
- This suggests the underlying `create_agent_composite_score_maps()` function may be failing

### 7. Git History Notes:
- Commit `824b047` tried to fix the comparison tool but only added it to `__all__` in the .py file, NOT to `__init__.py`
- The main branch has been stable without exporting `CreateVulnerabilityMapComparison`
- I mistakenly added the export today thinking it would help