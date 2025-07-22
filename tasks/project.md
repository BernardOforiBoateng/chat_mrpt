# ChatMRPT Development Notes

## Overview
This document captures the journey of implementing the Test Positivity Rate (TPR) module for ChatMRPT, a malaria risk analysis platform. It contains technical decisions, challenges faced, solutions implemented, and lessons learned.

## Project Context
ChatMRPT is an epidemiological tool for malaria risk assessment. The TPR module extends its capabilities to analyze Test Positivity Rates from National Malaria Elimination Programme (NMEP) data, requiring specialized workflows and conversational interfaces.

## Architecture Decisions

### 1. Module Structure
We organized the TPR module as a self-contained component:
```
app/tpr_module/
├── core/           # Business logic (calculator, conversation manager)
├── data/           # Data handling (parser, mapper, validator)
├── services/       # Service layer (filters, selectors, extractors)
├── output/         # Output generation
├── integration/    # ChatMRPT integration layer
└── raster_database/# Environmental data storage
```

**Why this structure?**
- Clear separation of concerns
- Easy to test individual components
- Can be extracted as standalone package if needed
- Follows ChatMRPT's existing patterns

### 2. Conversational Flow Design
Instead of rigid step-by-step wizards, we implemented a flexible conversational interface that understands context and user intent.

**Key Components:**
- `TPRConversationManager`: Orchestrates the flow
- `TPRWorkflowRouter`: Routes messages intelligently
- Intent extraction: Uses LLM for natural language understanding

**Benefits:**
- Users can ask questions mid-workflow
- System provides helpful recommendations
- Errors are handled gracefully with context

### 3. Data Pipeline Architecture
```
Excel File → Parser → Column Mapper → Validator → Calculator → Output Generator
```

Each stage is independent and testable. The column mapper was crucial for handling heterogeneous data formats from different states.

## Major Challenges & Solutions

### 1. Ward Name Cleaning Timing
**Problem**: Ward names had prefixes (AD, KW, OS) that needed removal, but cleaning happened after TPR calculation, causing mismatches.

**Solution**: Clean ward names during parsing, before any analysis:
```python
def _clean_ward_name(self, ward_raw: str) -> str:
    # Remove state prefix and 'Ward' suffix
    # 'AD Karewa Ward' → 'Karewa'
```

### 2. Column Name Heterogeneity
**Problem**: Different states used different column names for the same data.

**Solution**: Created a comprehensive column mapper:
```python
COLUMN_MAPPINGS = {
    'rdt_tested_u5': [
        'Persons presenting with fever & tested by RDT <5yrs',
        'RDT Tested Under 5',
        # ... many variations
    ]
}
```

### 3. Session State Management
**Problem**: Web requests are stateless, but TPR workflow is stateful.

**Solution**: 
- Store state in session with unique IDs
- Restore state at the beginning of each request
- Clear TPR state on index page load to prevent bleeding

### 4. Identifier Population
**Problem**: Output files needed ward_code and lga_code from shapefiles, but merges were failing.

**Solution**: Simplified merge logic:
```python
# Merge on cleaned ward names
tpr_data = tpr_data.merge(
    ward_boundaries[['WardName', 'ward_code', 'lga_code']], 
    on='WardName'
)
```

### 5. File Upload UX
**Problem**: TPR uploads were clearing chat history, disrupting conversation flow.

**Solution**: Removed `clearChat()` from TPR uploads to maintain consistency with regular uploads.

## Key Technical Insights

### 1. Testing Best Practices
- **Never modify tests to pass**: Fix the code, not the test
- **Test data matters**: Bad test data leads to bad assumptions
- **Integration tests reveal architectural issues**: Our comprehensive workflow test exposed many edge cases

### 2. Data Quality
- **Clean early, clean once**: Data cleaning should happen at parse time
- **Validate assumptions**: What works for one state may not for another
- **Preserve originals**: Keep raw data for debugging

### 3. User Experience
- **Consistency matters**: TPR uploads should behave like regular uploads
- **Context is king**: Show users where they are in the workflow
- **Recommendations help**: Don't just ask questions, provide guidance

### 4. Session Management
- **Stateless is hard**: Web apps need careful state restoration
- **Isolation is critical**: Each session must be completely independent
- **Clear boundaries**: Know when to reset state (page loads, not uploads)

## Implementation Highlights

### 1. Natural Language Processing
```python
def _understand_user_intent(self, user_input: str) -> Dict[str, Any]:
    # Use LLM to understand intent
    # Fallback to keyword matching if needed
```

### 2. Dynamic Column Detection
```python
# Instead of hardcoding column names
level_col = 'facility_level' if 'facility_level' in data.columns else 'level'
```

### 3. Flexible Routing
```python
# Route based on workflow stage, not rigid steps
if workflow_stage == 'state_selection':
    return self._handle_state_selection()
elif workflow_stage == 'facility_selection':
    return self._show_facility_selection()
```

## Critical Bug Fixes

### Session Persistence Bug (Jul 18, 2025)
**The Problem**: TPR state was persisting across different user sessions, causing data to bleed between users.

**Root Cause**: TPR state wasn't being cleared when users navigated away or started new sessions.

**The Fix**: Always reset TPR state on index page load:
```python
@core_bp.route('/')
def index():
    # ALWAYS reset TPR state on index load
    if 'tpr_workflow_active' in session:
        session.pop('tpr_workflow_active', None)
```

**Lesson Learned**: In multi-user web applications, aggressive state clearing is safer than selective clearing.

### Conversation Continuity Fix (Jul 18, 2025)
**The Problem**: TPR uploads were clearing the entire chat conversation when files were uploaded. Users would start with greetings, then upload TPR data, and lose their entire conversation history.

**Root Cause**: `window.chatManager.clearChat()` was being called in the TPR upload handler, but regular uploads don't clear the chat.

**The Fix**: Removed the clearChat() call from TPR uploads to maintain conversation continuity:
```javascript
// REMOVED: window.chatManager.clearChat();
// Now TPR uploads behave like regular uploads - they ADD to the conversation
```

**Lesson Learned**: Maintain consistency in UX patterns. If regular uploads preserve conversation, so should TPR uploads.

### Critical Data Restoration Fix (Jul 18, 2025)

**The Problem**: "No data loaded. Call parse_file() first." error when selecting a state after TPR upload.

**Root Cause**: The conversation manager has its own parser instance that wasn't getting the parsed data restored. Data was being restored to the handler's parser but not the conversation manager's parser.

**The Fix**: 
1. Restore data to BOTH parsers in `_restore_parsed_data()`:
```python
# Restore to handler's parser
self.nmep_parser.data = state['nmep_data']
# CRITICAL: Also restore to conversation manager's parser!
self.conversation_manager.parser.data = state['nmep_data']
```

2. Call `_restore_parsed_data()` before processing each message to handle request statelessness:
```python
def process_tpr_message(self, user_message: str):
    # CRITICAL: Restore parsed data before processing message
    self._restore_parsed_data()
```

**Lesson Learned**: In stateless web applications, always restore state at the beginning of each request handler, not just during initialization.

### Geographic Coverage Fix (Jul 19, 2025)

**The Problem**: TPR data summary was showing generic values like "Multiple LGAs, hundreds of wards" instead of actual counts.

**Root Cause**: The NMEP parser's `get_summary_for_conversation` method wasn't receiving the actual data, only metadata.

**The Fix**:
1. Pass data along with metadata when generating initial response
2. Calculate LGA and ward counts in metadata extraction
3. Update conversation manager to restore data to parser

**Lesson Learned**: Always ensure data is available where it's needed, especially in multi-component systems.

### Facility Filter Column Fix (Jul 19, 2025)

**The Problem**: "No 'level' column found in data" error preventing facility filtering.

**Root Cause**: 
1. Column mapping changes 'level' to 'facility_level'
2. Data values are "Primary Health Facility" not just "Primary"
3. Old hardcoded checks remained after fixes

**The Fix**:
1. Dynamic column detection: `level_col = 'facility_level' if 'facility_level' in data.columns else 'level'`
2. Facility level mappings to handle variations:
```python
FACILITY_LEVEL_MAPPINGS = {
    'Primary': ['Primary', 'Primary Health Facility', 'PHC'],
    'Secondary': ['Secondary', 'Secondary Health Facility', 'General Hospital'],
    'Tertiary': ['Tertiary', 'Tertiary Health Facility', 'Teaching Hospital']
}
```

**Lesson Learned**: When fixing bugs, search for ALL occurrences of the problematic pattern, not just the obvious ones.

### Data Quality Percentages Fix (Jul 20, 2025)

**The Problem**: Data quality was showing generic terms like "Limited availability" instead of actual percentages.

**Root Cause**: The code was converting percentages to descriptive terms rather than showing the raw numbers.

**The Fix**: 
1. Show actual percentages in state overview:
```python
# Instead of: "RDT data mostly complete"
summary += f"RDT data {rdt_tested_complete:.1f}% complete"
```

2. Show detailed breakdowns:
```python
f"**RDT Testing Data**: {rdt_tested_complete:.1f}% complete ({rdt_positive_complete:.1f}% have positive results)"
```

**Lesson Learned**: Users prefer precise data over vague descriptions. Always show the numbers when available.

### 'level' KeyError Fix (Jul 20, 2025)

**The Problem**: KeyError: 'level' when selecting Primary facilities after successful filtering.

**Root Cause**: The `calculate_data_completeness` method was using hardcoded column names:
```python
data = state_data[state_data[self.NMEP_COLUMNS['level']] == facility_level].copy()
```

**The Fix**: Dynamic column detection with facility level mapping:
```python
level_col = 'facility_level' if 'facility_level' in state_data.columns else 'level'
# Also handle full facility level names
facility_level_mappings = {
    'Primary': ['Primary', 'Primary Health Facility', 'PHC'],
    # ...
}
level_variants = facility_level_mappings.get(facility_level, [facility_level])
data = state_data[state_data[level_col].isin(level_variants)].copy()
```

**Lesson Learned**: Always use dynamic column detection after data transformations. Never assume column names remain constant.

### "Grouper for 'lga' not 1-dimensional" Error Fix (Jul 20, 2025)

**The Problem**: Error "Grouper for 'lga' not 1-dimensional" when selecting any age group for TPR calculation.

**Root Cause**: The data was being column-mapped twice:
1. First in `nmep_parser.parse_file()` at line 114
2. Again in `conversation_manager._handle_age_group_selection()` at line 566

This created duplicate 'lga' columns because:
- The mapper tries to rename 'LGA' to 'lga'
- But 'lga' already exists from the first mapping
- pandas.rename() creates a duplicate column instead of overwriting

**The Fix**: Removed the redundant column mapping in conversation manager:
```python
# Removed these lines:
# mapper = ColumnMapper()
# mapped_data = mapper.map_columns(filtered_data)

# Now passes filtered_data directly to TPR calculator
tpr_results = self.calculator.calculate_ward_tpr(
    filtered_data,  # Already mapped in nmep_parser
    age_group=age_group
)
```

**Lesson Learned**: Be careful with data transformations in multi-stage pipelines. Always trace data flow to avoid duplicate operations.

### Enhanced Age Group Selection Display (Jul 20, 2025)

**The Problem**: Age group selection was showing only overall percentages, not the detailed RDT/Microscopy breakdown requested by the user.

**User Request**: 
- Show RDT and Microscopy data availability separately
- Add recommendation for Under 5 years
- Follow the format in TPR workflow.md

**The Fix**: Rewrote the age group selection display to match the workflow specification:
```python
# Now shows detailed breakdown:
message += f"**Under 5 years in {self.selected_state}:**\n"
message += f"- RDT Testing: {completeness_u5['by_test_type']['rdt_tested']:.1f}% data available\n"
message += f"- Microscopy Testing: {completeness_u5['by_test_type']['micro_tested']:.1f}% data available\n"
message += "- **Recommended** - best data coverage\n\n"
```

**Lesson Learned**: Always refer to workflow documentation for expected UI/UX patterns. Users expect consistency with documented workflows.

### Missing Outpatient Columns Investigation (Jul 20, 2025)

**The Problem**: Outpatient attendance showing as "0.0% complete" because columns are missing.

**The Investigation**: Added debug logging to identify available outpatient columns:
```python
outpatient_cols = [col for col in self.data.columns if 'outpatient' in col.lower() or 'opd' in col.lower()]
if outpatient_cols:
    logger.info(f"Found outpatient columns: {outpatient_cols}")
else:
    logger.warning("No outpatient columns found in data")
```

**Status**: The data might genuinely be missing outpatient columns, which is why the column mapper reports them as missing. This is a data quality issue, not a code bug.

### The Bigger Picture

TPR demonstrates how to extend a complex system without disrupting its core:
- **Separate concerns**: TPR handles NMEP specifics, ChatMRPT handles analysis
- **Clear boundaries**: Only interact through well-defined interfaces
- **User-centric**: Hide complexity behind conversational UI
- **Future-proof**: Can evolve independently as requirements change

## TPR Bug Fixes and Enhancements (Jul 20, 2025)

### Ward Count Discrepancy Fix (229 vs 226)

**The Problem**: Adamawa state was showing 229 wards instead of the correct 226. The user was adamant: "I know it is 226, so anything other than that means something is wrong."

**Root Cause**: Three ward names (Ribadu, Nassarawo, Yelwa) appeared in multiple LGAs with different WardCodes, causing duplicates when aggregating only by WardName.

**The Fix**: Modified both aggregation and merging to use WardCode when available:
```python
# In tpr_pipeline.py:
if 'WardCode' in facility_data.columns and facility_data['WardCode'].notna().any():
    groupby_cols = ['WardCode']
    first_cols = {'LGA': 'first', 'Ward': 'first', 'State': 'first'}

# In output_generator.py:
merged = tpr_data.merge(
    state_gdf[merge_cols],
    left_on=['WardName', 'LGA'],
    right_on=['WardName', 'LGAName'],
    how='left'
)
```

### Environmental Variable Extraction Fix

**The Problem**: All environmental variables (especially EVI) were returning empty/null values.

**Root Cause**: The `_find_most_recent_year` function was looking at all files in the directory, not just files for the specific variable.

**The Fix**: Changed to search only for variable-specific files:
```python
def _find_most_recent_year(self, var_dir: Path, variable: str) -> Optional[int]:
    for file in var_dir.glob(f"{variable}*.tif"):  # Only look for variable-specific files
```

### Download UI Complete Redesign

**The Problem**: 
- Massive white space in download tab
- Hardcoded "Adamawa_state.zip" filename
- Download button only downloading shapefile

**The Solution**: Complete redesign per user request:
- Removed individual download buttons
- Created single "Download All Files" button
- Minimized white space
- Fixed download endpoints to use proper API routes

### Seamless TPR to Risk Analysis Gateway

**Implementation**: Created a transition system that simulates standard upload without user intervention:

1. **Backend Infrastructure** (`risk_transition.py`):
   - Copies TPR outputs to standard upload locations
   - Sets session flags to mimic completed upload
   - Preserves TPR context while enabling risk analysis

2. **API Endpoint** (`/api/tpr/transition-to-risk`):
   - Validates TPR completion
   - Executes file transition
   - Updates session state

3. **Frontend Integration**:
   - Added "Continue to Malaria Risk Analysis" button in completion message
   - JavaScript function handles transition smoothly
   - Automatically switches to analysis tab

**Benefits**:
- Zero re-upload required
- Seamless workflow continuation
- Context preservation
- Time savings for users

### Key Lessons Learned

1. **Data Integrity**: Always validate ward counts against known values
2. **File Patterns**: Be specific when searching for files (e.g., "evi*.tif" not "*")
3. **User Experience**: Less is more - remove unnecessary UI elements
4. **Workflow Integration**: Plan transitions between modules from the start

## Conclusion

The TPR module successfully extends ChatMRPT's capabilities to handle Test Positivity Rate analysis with a user-friendly conversational interface. The implementation follows established patterns while introducing innovative approaches like natural language processing for user interactions. 

The journey revealed critical insights about session management, routing architecture, and the importance of true modularity. Despite challenges with data cleaning, identifier population, and session persistence, the final solution is robust and maintainable.

Most importantly, the seamless gateway from TPR to risk analysis demonstrates thoughtful integration - users can now flow from one analysis to another without friction, making the entire malaria intervention planning process more efficient.

The experience reinforced important software engineering principles: test integrity, data quality at the source, clear architectural boundaries, and the value of understanding not just what to build, but why. The module is ready for production use with proper session isolation ensuring it remains a helpful addition rather than an intrusive requirement.

## Post-Deployment Issues and Fixes (July 22, 2025)

### Issue 1: Ward Ranking Explanations Lacking Detail
**Problem**: When users asked "why is X ward ranked where it is?", the system only showed rankings without the actual variable values, making it impossible to understand the underlying factors.

**Root Cause**: The SQL query results were formatted correctly but not interpreted with epidemiological context. The system displayed raw data without explaining what the values meant.

**Solution**: Enhanced `conversational_data_access.py` to detect ranking explanation queries and format them specially:
- Separate sections for rankings and risk factor values  
- Clear labeling of each metric
- Added prompt for epidemiological interpretation
- Structured output that guides the LLM to provide meaningful explanations

### Issue 2: Settlement Map CSP Errors
**Problem**: Browser console showed repeated Content Security Policy violations when loading settlement maps, trying to fetch fonts from `fonts.openmaptiles.org`.

**Root Cause**: The "open-street-map" style in Plotly attempts to load external font resources, which violates the application's CSP.

**Solution**: Changed map style from "open-street-map" to "carto-positron":
- Carto styles don't require external font resources
- Maintains clean, professional appearance
- Eliminates all CSP violations
- Maps load faster without external dependencies

### Issue 3: ITN Distribution Re-running Analysis
**Problem**: ITN planning tool was triggering a complete re-run of risk analysis instead of using existing results, causing unnecessary delays and computation.

**Root Cause**: The `_check_analysis_complete` method only checked data_handler attributes which weren't being set with the new unified data state system.

**Solution**: Enhanced the check to use multiple indicators:
1. Primary: Check Flask session for `analysis_complete` flag
2. Secondary: Check data_handler attributes (legacy support)
3. Tertiary: Check current dataset for analysis columns
- This multi-layered approach ensures compatibility across different execution contexts

### Key Takeaways
1. **Dynamic Over Hardcoded**: The hardcoded column issue reinforced the importance of dynamic, data-driven approaches
2. **CSP Awareness**: When using third-party visualization libraries, always consider CSP implications
3. **State Management**: Session flags should be the primary source of truth, with fallbacks for compatibility
4. **User-Centric Fixes**: Focus on what users need (explanations, not just data) rather than technical correctness alone