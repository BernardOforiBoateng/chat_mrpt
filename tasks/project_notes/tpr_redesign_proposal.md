# TPR Redesign Proposal - Based on Production Analysis

## Date: 2025-08-12

## Problem Analysis

### Current Issues (from Browser Console):
1. **Repetitive Questions**: System asks age group, then test method, then goes BACK to age group
2. **Confusing Flow**: "I've detected TPR data" appears multiple times
3. **Wrong Data Count**: Says "10,452 rows" when it's actually 224 wards
4. **No Clear Path**: User doesn't know what to do after upload

### How Production Worked (from deleted files):
The production `TPRConversationManager` had:
- **Flexible stages** not rigid steps
- **Natural language understanding** 
- **Clear conversation flow** with state management
- **Comprehensive summaries** with actual data counts

## Proposed Solution: User-Choice Driven Approach

### 1. **Remove Automatic TPR Detection**
Instead of forcing TPR detection, present OPTIONS to the user.

### 2. **On Data Upload, Show This:**

```
📊 I've successfully loaded your data from Adamawa State!

**Data Summary:**
- 224 wards across 21 LGAs
- 512 health facilities
- Test data: RDT and Microscopy available
- Age groups: Under 5, Over 5, Pregnant women
- Time period: January 2024 - July 2024

**What would you like to do?**

1️⃣ **Explore & Analyze** 
   Examine patterns, create visualizations, understand your data
   
2️⃣ **Calculate Test Positivity Rate (TPR)** 
   I'll guide you through selecting age groups, test methods, and facility levels
   
3️⃣ **Quick Overview** 
   Show summary statistics and data quality

Just type what you'd like to do, or say "1", "2", or "3"

💡 Tip: You can always switch between options. Start exploring and calculate TPR later!
```

### 3. **Smart Keyword Triggers**

```python
def detect_user_intent(user_message: str) -> str:
    """Detect what the user wants to do."""
    
    message_lower = user_message.lower()
    
    # TPR-related keywords
    if any(word in message_lower for word in ['tpr', 'test positivity', 'positivity rate', 'calculate tpr']):
        return 'start_tpr_flow'
    
    # Analysis keywords
    if any(word in message_lower for word in ['analyze', 'explore', 'pattern', 'trend', 'visualize']):
        return 'data_analysis'
    
    # Option numbers
    if '2' in message_lower or 'option 2' in message_lower:
        return 'start_tpr_flow'
    
    if '1' in message_lower or 'option 1' in message_lower:
        return 'data_analysis'
    
    return 'clarify'
```

### 4. **TPR Flow (When User Chooses It)**

When user selects TPR calculation:

```
Great! Let's calculate the Test Positivity Rate for your data.

I'll need a few quick selections to ensure accurate calculations:

**1. Which age group?**
• All ages (recommended for overall picture)
• Under 5 years
• Over 5 years (excluding pregnant women)
• Pregnant women

Type your choice or number (1-4):
```

Then after age group selection:

```
Perfect! You selected "Under 5 years".

**2. Which test method?**
• Both RDT and Microscopy (uses maximum TPR)
• RDT only
• Microscopy only

Type your choice or number (1-3):
```

Then after test method:

```
Great! Using RDT only for Under 5 years.

**3. Which facilities to include?**
• All facilities (recommended)
• Primary health centers only
• Secondary facilities only
• Tertiary facilities only

Type your choice or number (1-4):
```

### 5. **Key Implementation Changes**

#### A. Update `agent.py`:
```python
def _create_data_summary(self, state: DataAnalysisState) -> str:
    """Create a user-choice driven summary."""
    
    # Don't automatically detect TPR
    # Instead, present options
    
    if state.get("input_data"):
        # Get accurate data stats
        df = pd.read_excel(data_path)  # Read FULL data
        
        return f"""📊 I've successfully loaded your data from {state_name}!

**Data Summary:**
- {n_wards} wards across {n_lgas} LGAs
- {n_facilities} health facilities
- {len(df):,} total records
- {len(df.columns)} data columns

**What would you like to do?**

1️⃣ **Explore & Analyze** - Examine patterns and create visualizations
2️⃣ **Calculate Test Positivity Rate (TPR)** - Guided TPR calculation
3️⃣ **Quick Overview** - Summary statistics

Just type what you'd like to do!"""
```

#### B. Create Simple Intent Router:
```python
def route_user_intent(self, user_message: str) -> str:
    """Route based on user intent, not forced detection."""
    
    # Check for TPR intent
    if 'tpr' in user_message.lower() or 'test positivity' in user_message.lower():
        return self._start_tpr_flow()
    
    # Check for analysis intent
    if 'explore' in user_message.lower() or 'analyze' in user_message.lower():
        return self._start_analysis_flow()
    
    # Default to asking what they want
    return self._show_options()
```

## Benefits of This Approach

1. **User Control**: User decides their path, not forced
2. **Flexibility**: Can explore first, then calculate TPR
3. **Clear Options**: No confusion about what's available
4. **Natural Flow**: Matches how users think
5. **Always Available**: Can trigger TPR anytime with keywords

## Implementation Priority

1. **IMMEDIATE**: Fix the data summary to show options (not forced TPR)
2. **HIGH**: Add intent detection for flexible routing
3. **HIGH**: Fix the TPR flow to remember selections (not repeat)
4. **MEDIUM**: Add ability to switch between modes

## Success Metrics

- User uploads data → Sees clear options
- User says "calculate TPR" → Smooth guided flow
- User says "explore" → Goes to analysis
- No repeated questions
- Correct data counts shown