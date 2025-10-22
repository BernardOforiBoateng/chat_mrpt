# TPR Data Analysis - Complete User Interaction Flow

## Staging URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com

## Step-by-Step User Journey

### 1. User Opens ChatMRPT Website
```
User navigates to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
```

### 2. User Clicks on "Data Analysis" Tab
- The Data Analysis V3 interface loads
- Chat panel appears on the right
- Upload area visible on the left

### 3. User Uploads TPR Data File
**File Example**: `NMEP TPR and LLIN 2024_16072025.xlsx` (Adamawa state data)

User clicks "Choose File" and selects the TPR Excel file, then clicks "Upload"

### 4. System Automatically Detects TPR Data
**System Response:**
```
I've detected that you've uploaded Test Positivity Rate (TPR) data for Adamawa state. 
This dataset contains malaria testing data across different facilities and wards.

Your data includes:
- 21 LGAs 
- 224 wards
- Test results for different age groups
- Multiple facility types

What would you like to do with this data?
1. Analyze the overall trends and patterns
2. Calculate TPR by ward
3. Prepare data for risk analysis
```

### 5. User Requests TPR Calculation
**User types:** "Calculate the TPR for all wards"

### 6. System Starts Interactive Selection Process

**System Response:**
```
I'll calculate the Test Positivity Rate for all wards. To ensure accurate calculations, 
I need to know your preferences:

Which age group would you like to analyze?
- Under 5 years
- Over 5 years  
- All ages (combined)
- Pregnant women

Please type your selection:
```

### 7. User Selects Age Group
**User types:** "All ages"

**System Response:**
```
Great! Using all age groups for the analysis.

Now, which test method should I use for the TPR calculation?
- RDT only (Rapid Diagnostic Test)
- Microscopy only
- Both methods combined

Please type your selection:
```

### 8. User Selects Test Method
**User types:** "Both"

**System Response:**
```
Perfect! I'll use both RDT and Microscopy results.

Finally, which facility levels should I include?
- All facilities
- Primary facilities only
- Secondary facilities only
- Tertiary facilities only

Please type your selection:
```

### 9. User Selects Facility Level
**User types:** "All facilities"

### 10. System Performs TPR Calculation

**System Response:**
```
Calculating Test Positivity Rate for Adamawa state...

✅ TPR Calculation Complete!

Summary:
- Analyzed 224 wards across 21 LGAs
- Used: All age groups, Both test methods, All facility levels
- State average TPR: 48.3%

Key Findings:
• Highest TPR: Michika ward (78.5%)
• Lowest TPR: Yola South Central (12.3%)
• 45 wards show TPR above 60% (high transmission)
• 23 wards show TPR below 30% (low transmission)

Files generated:
- adamawa_tpr_results.csv (detailed ward-level TPR)
- adamawa_tpr_summary.csv (LGA summaries)

Would you like to:
1. Visualize these results on a map?
2. Export the detailed analysis?
3. Proceed to risk analysis?
```

### 11. User Proceeds to Risk Analysis
**User types:** "Let's proceed to risk analysis"

### 12. System Prepares Data for Risk Analysis

**System Response:**
```
Preparing your TPR data for comprehensive risk analysis...

I'm now extracting environmental and demographic variables for Adamawa state 
(North-East geopolitical zone).

Extracting zone-specific variables:
• Elevation data
• Proximity to water bodies
• Vegetation index (NDVI)
• Land surface temperature
• Rainfall patterns

✅ Data preparation complete!

Your data is now ready for risk analysis with:
- 224 wards with calculated TPR values
- 5 environmental variables specific to North-East zone
- Ward identifiers (WardCode, WardName, StateCode) for accurate mapping

Would you like to proceed with the risk analysis to identify priority areas for intervention?
```

### 13. User Confirms Risk Analysis
**User types:** "Yes"

### 14. System Transitions to Risk Analysis

**System Response:**
```
Starting comprehensive malaria risk analysis for Adamawa state...

Analyzing multiple risk factors:
• Disease burden (TPR: 48.3% average)
• Environmental suitability for vectors
• Population vulnerability
• Access to healthcare

[Progress bar animation]

✅ Risk Analysis Complete!

High-Risk Areas Identified:
1. Michika LGA - Risk Score: 8.9/10
   - Very high TPR (78.5%)
   - High rainfall, near water bodies
   - Limited healthcare access
   
2. Madagali LGA - Risk Score: 8.4/10
   - High TPR (65.2%)
   - Favorable vector breeding conditions
   - High population density

3. Mubi North LGA - Risk Score: 8.1/10
   - Elevated TPR (61.8%)
   - Multiple environmental risk factors

Recommendations:
• Priority 1: Deploy LLIN distribution in Michika (15,000 nets needed)
• Priority 2: Establish RDT testing centers in Madagali
• Priority 3: Seasonal chemoprevention in Mubi North

Would you like to:
- View the interactive risk map?
- Download the full report?
- Explore specific ward details?
```

### 15. User Requests Interactive Map
**User types:** "Show me the interactive risk map"

**System Response:**
```
Generating interactive risk map...

✅ Map created successfully!

[Interactive map displays showing Adamawa state with color-coded risk levels]

Map Features:
• Click any ward for detailed information
• Toggle between TPR, risk score, and intervention layers
• Export options available in top-right corner

The map is now displayed in your browser. You can interact with it to explore:
- Ward-level TPR values
- Environmental risk factors
- Recommended interventions
- Population data

Is there anything specific you'd like to explore on the map?
```

## Complete HTTP Request/Response Flow

### Backend API Calls Made:

1. **File Upload**
   ```
   POST /api/data-analysis-v3/upload
   Body: FormData with Excel file
   Response: {
     "success": true,
     "session_id": "abc123",
     "file_type": "tpr_data",
     "message": "TPR data detected"
   }
   ```

2. **Chat Messages** (WebSocket or polling)
   ```
   POST /api/data-analysis-v3/chat
   Body: {
     "message": "Calculate the TPR for all wards",
     "session_id": "abc123"
   }
   Response: Streaming responses with agent interactions
   ```

3. **Risk Analysis Transition**
   ```
   POST /api/data-analysis-v3/analyze
   Body: {
     "action": "risk_analysis",
     "session_id": "abc123",
     "data_ready": true
   }
   ```

4. **Map Generation**
   ```
   GET /api/visualizations/risk-map?session_id=abc123
   Response: HTML with interactive Folium map
   ```

## Key Features Demonstrated:

1. **Automatic Detection**: System recognizes TPR data without user specification
2. **Interactive Flow**: Step-by-step selections for accurate analysis
3. **Flexibility**: Works with available columns, handles missing data
4. **Zone-Specific**: Uses North-East specific variables for Adamawa
5. **Seamless Transition**: Natural flow from TPR to risk analysis
6. **Rich Outputs**: CSV files, summaries, and interactive visualizations
7. **Context Preservation**: Maintains session throughout the workflow

## Error Handling:

If any step fails, the system gracefully handles it:
- Missing columns: Uses available data with notification
- Network issues: Retries with exponential backoff
- Invalid selections: Provides helpful guidance
- Data quality issues: Shows warnings but continues with valid data

## Session Persistence:

All data is stored in session-specific directories:
```
/instance/uploads/{session_id}/
├── raw_data.xlsx           # Original upload
├── adamawa_tpr_results.csv # TPR calculations
├── adamawa_risk_scores.csv # Risk analysis results
└── risk_map_*.html         # Interactive visualizations
```

This ensures multi-user support and data isolation across the 6 Gunicorn workers.