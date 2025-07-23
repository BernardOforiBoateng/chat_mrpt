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

## Follow-up Fixes (July 22, 2025 - Part 2)

### Issue 1: Ward Ranking Data Overload
**Problem**: The ward ranking explanation was dumping all raw data (rankings, scores, all variable values) before providing interpretation, creating information overload.

**Solution**: Modified `conversational_data_access.py` to:
- Hide raw data in HTML comments for LLM processing
- Provide clear instruction for interpretation-only output
- Keep data available for analysis but not visible to users

### Issue 2: Settlement Map Visual Quality
**Problem**: The carto-positron style looked poor and the maps weren't visually appealing.

**Solution**: Enhanced `settlement_validation_tools.py` with:
- Changed base style to "white-bg" with custom tile layers
- Added Carto light theme tiles as default background
- Included map style switcher buttons (Street Map/Satellite)
- Increased settlement fill opacity from 0.25 to 0.5
- Increased border width from 0.8 to 2 pixels
- Improved ward boundary and label styling
- Better color contrast for all map elements

**Key Improvements**:
- Users can now switch between street and satellite views
- Settlement types are more visible while maintaining transparency
- Professional appearance without CSP violations
- Enhanced readability with better typography and colors

## Advanced Ward Ranking Implementation (July 22, 2025 - Part 3)

### Multi-Metric Statistical Comparisons
**Problem**: Users needed more context when asking "why is X ward ranked where it is?" - percentiles alone weren't sufficient.

**Solution**: Implemented comprehensive statistical comparisons showing:
1. **Rank Position**: "ranked 3/66" - immediate understanding
2. **Percentile**: "75th percentile" - relative position
3. **Median Comparison**: "2.5x median" or "+3.2 from median" - magnitude sense
4. **Extreme Value Detection**: "⚠️ extreme" flag when z-score > 2

**Implementation Details**:
- Completely dynamic - works with any dataset variables
- No hardcoded variable names or thresholds
- Calculates z-scores to identify statistical outliers
- Handles edge cases (zero median, missing values)
- Clean output format: "variable: value (ranked X/Y | Zth percentile | Ax median)"

**Benefits**:
- Users get multiple perspectives on each variable
- Easy to spot outliers and concerning values
- Context helps explain why wards are ranked where they are
- Works with any malaria dataset without modification

## 2025-01-23: TPR Environmental Data Extraction Dynamic Fix

### Problem Identified
The TPR module was failing to generate environmental data files because:
1. Hardcoded expectation of 2023 annual raster files that don't exist
2. Actual data consists of monthly files from various years (2015-2024)
3. Bug where `append()` was called on a set instead of `add()`
4. No mechanism to average multiple temporal files

### Solution Implemented
Created a dynamic raster extraction system that:
1. **Discovers all available files** - `_discover_all_files_for_variable()` finds all .tif files for a variable regardless of year
2. **Computes temporal averages** - `_compute_temporal_average()` averages across multiple raster files
3. **Truly dynamic extraction** - `_extract_with_averaging()` automatically:
   - Finds ALL available years of data
   - Averages across ALL years (not just one)
   - Uses annual files when available, falls back to representative monthly files
   - The year parameter from NMEP metadata is only used for logging context
4. **Handles monthly data** - Uses last available month as representative for each year
5. **Variable name mapping** - Maps 'temp' → 'temperature' and 'distance_to_waterbodies' → 'distance_to_water'

### Technical Details
- Added methods to RasterExtractor for dynamic file discovery and averaging
- Removed hardcoded VARIABLE_TO_RASTER mapping from geopolitical_zones.py
- Fixed set.append() bug (changed to set.add())
- Added import re for regex pattern matching
- System now works with any available data instead of expecting specific years

### Key Learnings
1. **Never hardcode temporal expectations** - Environmental data availability varies by year
2. **Build flexible averaging systems** - Better to average available data than fail completely
3. **Log extensively** - Added detailed logging of what files are found and used
4. **Handle edge cases** - System now handles monthly files, missing years, and partial data

### Files Modified
1. `app/tpr_module/services/raster_extractor.py` - Added dynamic averaging methods
2. `app/tpr_module/data/geopolitical_zones.py` - Removed hardcoded mappings

### Next Steps
- Test the system with real TPR data
- Deploy to AWS
- Monitor logs to ensure averaging is working correctly

## 2025-01-23: TPR Analysis Workflow Report Implementation

### Requirements
User requested a comprehensive TPR analysis report that:
- Documents the entire workflow (steps taken, parameters used)
- Includes environmental variables extracted
- Contains the TPR distribution map
- Can be shared with supervisors and colleagues
- Professional format suitable for presentations

### Solution Implemented
Created a comprehensive HTML report generator that includes:

1. **Executive Summary** - Key metrics in visual metric boxes
2. **Analysis Workflow** - Step-by-step documentation of what was done
3. **TPR Statistics** - Detailed statistical breakdown
4. **High Risk Wards** - Table of top 10 highest TPR wards
5. **Environmental Variables** - List of extracted variables with coverage
6. **Recommendations** - Based on threshold analysis
7. **Embedded Map** - TPR distribution map embedded directly in report
8. **Methodology Notes** - Technical details for transparency

### Technical Implementation
1. Created `TPRReportGenerator` class in `app/tpr_module/output/tpr_report_generator.py`
2. Integrated into `OutputGenerator.generate_outputs()` method
3. Report searches multiple locations for TPR map and embeds it
4. Uses Jinja2 templating for clean HTML generation
5. Includes Plotly.js for interactive map display
6. Professional styling with print-friendly CSS

### Key Features
- **Self-contained HTML** - Single file with all content
- **Interactive map** - Embedded Plotly visualization
- **Professional design** - Clean layout with ChatMRPT branding
- **Comprehensive data** - All relevant metrics and analysis details
- **Shareable format** - Ready for email or presentation

### Files Modified
1. `app/tpr_module/output/tpr_report_generator.py` - New report generator
2. `app/tpr_module/output/output_generator.py` - Integration into pipeline

### Benefits
- Users can share analysis results with stakeholders
- Complete documentation of analysis process
- Professional presentation format
- All information in one place
- No need to explain separate files

## TPR Workflow Consistency Fixes (January 2025)

### Problem Discovery
User reported inconsistent TPR workflow behavior on AWS:
- Sometimes getting "I've paused TPR analysis" messages unexpectedly
- State names like "Adamawa State" triggering wrong responses
- Download links disappearing after generation
- Workflow lost on browser refresh
- Frustration about demo reliability

### Root Cause Analysis

1. **Multi-Worker Session Issues**
   - Gunicorn runs 4 worker processes
   - Flask sessions not properly persisted without `session.modified = True`
   - Worker A sets data, Worker B doesn't see it
   - Download links particularly affected

2. **Intent Classification Flaws**
   - LLM sometimes misinterprets state names as questions
   - Fallback classifier too simplistic
   - Single-word inputs not handled well
   - "Adamawa" → "What do you want to know?" → User confusion

3. **Page Refresh Design Flaw**
   - `core_routes.py` always reset TPR state on index load
   - Intended to prevent stale sessions
   - But breaks active TPR workflows on refresh
   - Users lose progress mid-analysis

### Solution Design Process

**Key Constraint**: Must not break existing malaria risk analysis workflow

Designed three-phase approach:
1. **Low Risk**: Session persistence fixes only
2. **Medium Risk**: Intent classification improvements  
3. **Higher Risk**: Smart session state management

### Implementation Details

#### Phase 1: Session Persistence
Added `session.modified = True` in 5 locations:
- After activating TPR workflow
- After storing download links (critical fix)
- After completing analysis
- After cancelling workflow
- After user exits workflow

**Learning**: Flask's session interface doesn't automatically detect dictionary modifications. Must explicitly flag.

#### Phase 2: Intent Classification
Enhanced fallback classifier with:
- State name variation matching (with/without "State")
- Single/two-word default to TPR continuation
- Explicit exit only with "stop TPR"
- Better logging for debugging

Updated LLM prompt with explicit rules and examples.

**Learning**: Being overly clever with intent detection causes more problems than defaulting to expected behavior.

#### Phase 3: Smart Session Management
Changed from always resetting to conditional reset:
- Check `request.referrer` - None means new session
- Preserve state on internal navigation
- Still reset for truly new sessions

**Learning**: Browser refresh has referrer, new tabs don't. Perfect for our use case.

### What Worked
- Session persistence fixes immediately solved download issues
- Enhanced intent classification eliminated false exits
- Smart session management preserved workflow on refresh
- Extensive logging helped debug in production
- Phased approach minimized risk

### What Didn't Work Initially
- First attempt broke normal risk analysis by being too aggressive
- Had to revert and redesign more carefully
- Learned importance of testing BOTH workflows

### Deployment Strategy
- Created comprehensive deployment script
- Includes Gunicorn restart with proper settings
- Added log monitoring commands
- Clear testing checklist

### Performance Impact
- Minimal - only added logging and session flags
- No new database queries
- No additional API calls
- Session cookie slightly larger with modified flag

### Future Considerations
- Redis session backend remains as option if issues persist
- Could add session timeout handling (4+ hours)
- Might enhance with workflow state visualization

### Key Takeaways
1. Multi-worker environments need explicit session management
2. Default to expected behavior in ambiguous cases
3. Test all workflows, not just the one being fixed
4. Phased deployment reduces risk
5. Logging is critical for production debugging

### Issue Resolution: "I understand you're asking about" Messages (January 23, 2025)

**Problem**: Even after deploying all session and routing fixes, users still getting "I understand you're asking about: 'Adamawa State'" messages instead of proper TPR workflow continuation.

**Root Cause Discovery**:
1. Initially thought it was a routing issue in TPR workflow router
2. Checked request interpreter - not the source
3. Found the message was coming from TPR conversation manager itself
4. The issue was in `_handle_general_query` method returning this generic message

**Deeper Analysis**:
- The conversation manager's `_handle_state_selection` method had poor state name matching
- Only did simple substring matching: `state.lower() in user_input.lower()`
- This failed for exact matches like "Adamawa State" → "Adamawa State"
- When state selection failed, it went to `_handle_general_query` instead of clarification

**Solution Implemented**:
Enhanced state matching in `_handle_state_selection` with multiple patterns:
- Exact match (case insensitive)
- State name without "State" suffix
- User input contains state name
- State name contains user input
- Bidirectional substring matching

**Key Learning**: Sometimes the issue is not where you expect. The "I understand you're asking about" message seemed like a routing problem but was actually a matching logic issue within the correct handler.

**Deployment**: Fix deployed to AWS at 3:30 AM UTC on January 23, 2025

### Critical Discovery: Redis Missing on AWS (January 23, 2025)

**Problem**: TPR workflow completely inconsistent on AWS - state/facility/age selections randomly fail with generic responses.

**Investigation Process**:
1. SSH'd into AWS EC2 instance to check logs
2. Examined session folders and Flask session files
3. Analyzed TPR workflow router and conversation manager code
4. Discovered intent classification was working correctly
5. Found the real issue: no Redis installed on AWS server

**Root Cause**:
- Application configured to use Redis for session management in multi-worker environments
- Redis not installed/running on AWS: `which redis-server` returns nothing
- App falls back to filesystem sessions: `SESSION_TYPE = 'filesystem'`
- Multiple Gunicorn workers (4) behind ALB cannot share filesystem sessions
- Worker A sets `tpr_workflow_active=True`, Worker B doesn't see it
- TPR state lost between requests → generic responses

**Why It Works Locally**:
- Local development uses single process/worker
- Filesystem sessions work fine with single worker
- No session state sharing issues

**Solution Options**:
1. **Install Redis** (recommended): 
   - `sudo amazon-linux-extras install redis6`
   - Enables proper session sharing across workers
2. **Single Worker** (quick fix): 
   - Set `workers = 1` in gunicorn.conf.py
   - Reduces concurrency but ensures consistency
3. **Sticky Sessions on ALB**: 
   - Configure AWS ALB session affinity
   - Routes same user to same worker
4. **Database Sessions**: 
   - Use SQLAlchemy session backend
   - More overhead than Redis

**Key Learning**: Multi-worker production environments REQUIRE shared session storage. Filesystem sessions are development-only.

**Next Steps**: Install and configure Redis on AWS for proper production deployment.

### HTML Report Not Showing in Downloads (January 23, 2025)

**Problem**: After successful TPR analysis, only 3 files appeared in the download UI instead of 4. The HTML report was missing despite being generated and sent by the backend.

**Root Cause**: Type mismatch between backend and frontend:
- Backend sends HTML report with type 'TPR Analysis Report'
- Frontend JavaScript `typeMap` expected 'Summary Report'
- The `getKeyFromType()` function returned null for 'TPR Analysis Report', filtering it out

**Solution**: Added 'TPR Analysis Report' to the typeMap in tpr-download-manager.js:
```javascript
const typeMap = {
    'TPR Analysis Data': 'tpr_analysis',
    'Complete Analysis': 'main_analysis',
    'Shapefile': 'shapefile',
    'Summary Report': 'summary',
    'TPR Analysis Report': 'summary'  // Added mapping for HTML report
};
```

**Key Learning**: Always verify that frontend type mappings match backend output exactly. Even small string differences can cause features to silently fail.