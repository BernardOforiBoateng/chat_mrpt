# Critical TPR Integration Fixes Needed

## Problems Identified from Browser Console

### 1. **CRITICAL BUG: Only Reading 5 Rows**
**Location**: `app/data_analysis_v3/core/agent.py` lines 116-118
```python
# CURRENT BAD CODE:
df = pd.read_csv(data_path, nrows=5)  # Just peek
df = pd.read_excel(data_path, nrows=5)
```

**Problem**: This is causing the agent to only see 5 rows and report "dataset has 5 rows"
**Fix**: Need to read full data for TPR detection, then use head() for display only

### 2. **Poor Initial TPR Detection Response**
**Current Response**: Generic "You've uploaded TPR data..." 
**Needed Response** (from production):
```
I've detected that you've uploaded Test Positivity Rate (TPR) data for Adamawa State.

📊 **Data Summary:**
- **State**: Adamawa
- **Total LGAs**: 21
- **Total Wards**: 224  
- **Total Health Facilities**: 512
- **Time Period**: January 2024 - July 2024

📋 **Available Metrics:**
- RDT Testing Data (Under 5, Over 5, Pregnant Women)
- Microscopy Testing Data (Under 5, Over 5, Pregnant Women)
- Persons presenting with fever
- Confirmed malaria cases

🎯 **What I can do with this data:**
1. **Calculate Test Positivity Rate (TPR)** - I'll guide you through selecting age groups and test methods
2. **Analyze trends** - Explore patterns across wards and LGAs
3. **Prepare for risk analysis** - Extract environmental variables and format for comprehensive analysis

Would you like me to calculate the TPR for your wards? I'll walk you through the options step by step.
```

### 3. **Missing Proactive Guidance**
Users don't know to type "Calculate TPR" - system should offer it immediately

### 4. **Data Exploration Tools Issues**
When asked for summary, the tools are not providing proper statistics about the full dataset

## Required Fixes

### Fix 1: Update TPR Detection (agent.py)
```python
# In _check_tpr_data method
def _check_tpr_data(self, file_path: str) -> Optional[Dict[str, Any]]:
    try:
        # Read FULL data for detection
        if file_path.endswith('.csv'):
            df_full = pd.read_csv(file_path)
        else:
            df_full = pd.read_excel(file_path)
        
        # Check if TPR using full data
        from app.core.tpr_utils import is_tpr_data
        if is_tpr_data(df_full):
            # Generate comprehensive summary
            summary = self._generate_tpr_summary(df_full)
            return {
                'is_tpr': True,
                'summary': summary,
                'row_count': len(df_full),
                'ward_count': df_full['WardName'].nunique() if 'WardName' in df_full.columns else 0,
                'lga_count': df_full['LGA'].nunique() if 'LGA' in df_full.columns else 0
            }
    except Exception as e:
        logger.error(f"Error checking TPR data: {e}")
    return None
```

### Fix 2: Create TPR Summary Generator
```python
def _generate_tpr_summary(self, df: pd.DataFrame) -> str:
    """Generate comprehensive TPR data summary"""
    state = df['State'].iloc[0] if 'State' in df.columns else 'Unknown'
    n_lgas = df['LGA'].nunique() if 'LGA' in df.columns else 0
    n_wards = df['WardName'].nunique() if 'WardName' in df.columns else 0
    n_facilities = df['HealthFacility'].nunique() if 'HealthFacility' in df.columns else 0
    
    # Check available test columns
    has_rdt = any('RDT' in col for col in df.columns)
    has_microscopy = any('Microscopy' in col for col in df.columns)
    
    return f"""I've detected that you've uploaded Test Positivity Rate (TPR) data for {state}.

📊 **Data Summary:**
- **State**: {state}
- **Total LGAs**: {n_lgas}
- **Total Wards**: {n_wards}
- **Total Health Facilities**: {n_facilities}
- **Total Records**: {len(df):,}

📋 **Available Test Data:**
{self._list_available_metrics(df)}

🎯 **What I can do with this data:**
1. **Calculate Test Positivity Rate (TPR)** - I'll guide you through selecting:
   • Age groups (Under 5, Over 5, All ages, Pregnant women)
   • Test methods (RDT, Microscopy, or Both)
   • Facility levels (All, Primary, Secondary, Tertiary)

2. **Analyze patterns** - Identify high-risk wards and transmission hotspots

3. **Prepare for risk analysis** - Extract environmental variables and integrate with other data

**Ready to calculate TPR?** Just say "Calculate TPR" and I'll walk you through the options step by step.
Or type "analyze" to explore the data in other ways."""
```

### Fix 3: Update System Prompt
Add clear examples of TPR interaction in the system prompt to guide the LLM

### Fix 4: Data Analysis Tools
Ensure tools work with full dataset, not just head(5)

## Implementation Priority
1. **URGENT**: Fix the nrows=5 bug - this breaks everything
2. **HIGH**: Improve TPR detection response with full summary
3. **HIGH**: Add proactive guidance
4. **MEDIUM**: Update tools to work with full data

## User Experience Goals
- User uploads TPR data → Gets comprehensive summary immediately
- System proactively offers TPR calculation with clear next steps
- Interactive flow is clearly explained upfront
- No confusion about what to do next