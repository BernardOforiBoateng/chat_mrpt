# TPR User Interaction Flow - What Users See

## Complete User Journey

### 1. **User Uploads File**
```
User: *uploads "NMEP TPR and LLIN 2024.xlsx"*
```

### 2. **System Detects TPR File**
```
ChatMRPT: "I've analyzed your NMEP TPR data file. Here's what I found:

**Geographic Coverage:**
- 7 states: Adamawa, Bauchi, Borno, Gombe, Taraba, Yobe, Plateau
- 186 LGAs across all states  
- 2,257 wards total
- 8,542 health facilities

**Time Period:**
- 3 months of data from January 2024 - March 2024

**State-Level Breakdown:**
- **Adamawa**: 21 LGAs, 226 wards, 1,245 facilities
- **Bauchi**: 20 LGAs, 323 wards, 1,456 facilities
- **Borno**: 27 LGAs, 312 wards, 987 facilities
..."
```

### 3. **State Selection**
```
ChatMRPT: "Which state would you like to analyze? I can help you with:
- Adamawa
- Bauchi  
- Borno
- Gombe
- Taraba
- Yobe
- Plateau"

User: "Let's analyze Adamawa"

ChatMRPT: "Great! I'll analyze Adamawa State. Here's an overview:

**Adamawa State TPR Overview:**
- 21 Local Government Areas
- 226 Wards
- 1,245 Health Facilities

Ready to proceed with the analysis?"
```

### 4. **Facility Level Selection**
```
User: "Yes, proceed"

ChatMRPT: "What type of health facilities would you like to include?
- All facilities (recommended for comprehensive analysis)
- Primary facilities only
- Secondary facilities only
- Tertiary facilities only"

User: "All facilities"
```

### 5. **Age Group Selection**
```
ChatMRPT: "Which age group analysis would you like?
- All ages combined (default)
- Under 5 years
- 5 years and above
- Pregnant women"

User: "All ages"
```

### 6. **Processing & Results**
```
ChatMRPT: "Processing TPR analysis for Adamawa State...

✅ Analysis Complete!

**Summary Results:**
- Wards analyzed: 226
- Mean TPR: 42.3%
- High TPR wards (>50%): 87 wards
- Very high TPR wards (>70%): 23 wards

**Key Findings:**
1. Highest TPR areas: Michika (78.5%), Madagali (72.3%), Hong (68.9%)
2. Lowest TPR areas: Yola North (12.4%), Yola South (15.6%)

**Generated Files:**
📊 TPR Map: [View Interactive Map]
📈 Facility Rankings: [Download Excel]
📄 Full Report: [Download PDF]

Would you like to explore alternative TPR calculations or analyze a different state?"
```

### 7. **Alternative Calculations (Optional)**
```
User: "What alternative calculations are available?"

ChatMRPT: "I can calculate TPR using different methods:

1. **Facility-reported fevers** (current method)
2. **Expected malaria cases** (based on OPD attendance)
3. **Custom threshold** (you specify the formula)

Which would you like to try?"
```

## Key User Experience Elements

### 1. **Progressive Disclosure**
- Don't overwhelm with all options at once
- Guide through logical steps
- Show relevant information at each stage

### 2. **Clear Feedback**
- Always acknowledge what was detected
- Show data quality indicators
- Explain what's happening during processing

### 3. **Flexible Navigation**
```
User: "Actually, can we look at just Under 5 data for Bauchi instead?"

ChatMRPT: "Of course! Let me restart the analysis for Bauchi State, 
focusing on Under 5 years age group..."
```

### 4. **Error Handling**
```
Scenario: Missing data for some wards

ChatMRPT: "⚠️ Note: 12 wards in Adamawa have incomplete data:
- Furore Ward: Missing RDT data
- Kwapre Ward: No facility reports
...
These wards will be excluded from the analysis. Continue?"
```

### 5. **Technical → User-Friendly Mapping**

**Backend sees:**
```
orgunitlevel2: "ad Adamawa State"
orgunitlevel3: "ad1501 Demsa"  
orgunitlevel4: "ad150101 Bille"
```

**User sees:**
```
State: Adamawa
LGA: Demsa
Ward: Bille
```

## The Critical Frontend Mapping Points

### 1. **Column Name Display**
```python
# Backend column: 'orgunitlevel2'
# Frontend shows: "State"

# Backend column: 'rdt_tested_u5'
# Frontend shows: "RDT Tests (Under 5)"
```

### 2. **Value Cleaning**
```python
# Backend value: "ad Adamawa State"
# Frontend shows: "Adamawa State"

# Backend value: "ad1501 Demsa"
# Frontend shows: "Demsa"
```

### 3. **Error Messages**
```python
# Backend error: "Column 'State' not found"
# Frontend shows: "Unable to identify location columns in your file. 
                 Please ensure your file contains State, LGA, and Ward information."
```

## Conversational Flow State Machine

```
UPLOAD → DETECTION → STATE_SELECTION → FACILITY_SELECTION → AGE_GROUP → 
PROCESSING → RESULTS → [ALTERNATIVE_CALC or NEW_STATE or COMPLETE]
```

Each stage has:
- **Entry message**: What to show when entering
- **Options**: Valid user choices
- **Validation**: Check user input
- **Exit**: Transition to next stage
- **Error handling**: What if something goes wrong

## Key Insight for Implementation

The frontend conversation flow is **already well-designed** in `tpr_conversation_manager.py`. We just need to ensure:

1. **Detection works** with any file format
2. **Column names map** correctly in backend
3. **Display names** are user-friendly in frontend
4. **Values are cleaned** (remove prefixes) before display

The conversation flow itself doesn't need to change!