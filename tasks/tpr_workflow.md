TYPICAL TPR WORKFLOW
User Action: Uploads NMEP TPR Excel File
  ---
  Step 1: Data Summary & Overview
  ChatMRPT Response:
  "I've analyzed your NMEP TPR data file. Here's what I found:
  Geographic Coverage:
  - Three states: Adamawa, Kwara, Osun
  - Dozens of LGAs across all states
  - Hundreds of wards total
  - Thousands of health facilities
  Time Period:
  - Three years of monthly data from 2022 to 2024
  State-Level Breakdown:
  - Adamawa State: Multiple LGAs, hundreds of wards, many facilities
  - Kwara State: Multiple LGAs, hundreds of wards, many facilities
  - Osun State: Multiple LGAs, hundreds of wards, many facilities
  Data Quality by State:
  - Adamawa: RDT data mostly complete, Microscopy data sparse
  - Kwara: RDT data mostly complete, Microscopy data sparse
  - Osun: RDT data mostly complete, Microscopy data sparse
  Which state would you like to analyze?
  1. Adamawa State
  2. Kwara State
  3. Osun State
  Please select one state to proceed with TPR analysis."
  User: "Adamawa State"
  ---
  Step 2: State-Specific Data Summary
  ChatMRPT Response:
  "Perfect! I'll focus on Adamawa State for TPR analysis.
  Adamawa State Overview:
  - Geographic: Multiple LGAs covering hundreds of wards
  - Facilities: Nearly a thousand health facilities
  - Time Coverage: Three years of monthly data
  Facility Distribution in Adamawa:
  - Primary Health Facilities: Vast majority of facilities
  - Secondary Health Facilities: Small portion
  - Tertiary Health Facilities: Very few
  Data Quality in Adamawa:
  - Thousands of facility-month records available
  - RDT Testing Data: Good availability across most records
  - Microscopy Testing Data: Limited availability
  - Outpatient Attendance: Good availability
  Ward Distribution:
  - Most wards have multiple facilities
  - Some wards have single facilities
  - Few wards have many facilities
  Would you like to proceed with TPR calculation for Adamawa State?"
  User: "Yes, proceed"
  ---
  Step 3: Health Facility Level Selection
  ChatMRPT Response:
  "For TPR analysis in Adamawa State, I recommend focusing on Primary Health Facilities because:
  - They represent the vast majority of your Adamawa data
  - Secondary facilities handle complicated cases that aren't representative of ward-level transmission
  - Primary facilities better reflect community-level malaria burden in Adamawa
  Current Selection for Adamawa:
  - Primary facilities: Most facilities across all wards
  - Good distribution: Multiple primary facilities per ward on average
  - Coverage: Some wards have single facilities, others have many
  Do you want to:
  1. Use Primary Health Facilities only (recommended)
  2. Include Secondary facilities
  3. Include all facility types
  Your choice?"
  User: "Use Primary Health Facilities only"
  ---
  Step 4: Age Group Selection
  ChatMRPT Response:
  "I can calculate TPR for different age groups in Adamawa State. Here's the data availability:
  Under 5 years in Adamawa:
  - RDT Testing: Good data availability
  - Microscopy Testing: Limited data availability
  - Recommended - best data coverage
  Over 5 years (excluding pregnant women) in Adamawa:
  - RDT Testing: Good data availability
  - Microscopy Testing: Limited data availability
  Pregnant Women in Adamawa:
  - RDT Testing: Moderate data availability
  - Microscopy Testing: Very limited data availability
  - Limited data - significant gaps
  Which would you like to calculate for Adamawa:
  1. Under 5 TPR (recommended)
  2. Over 5 TPR
  3. Pregnant Women TPR
  4. All three separately
  5. Combined overall TPR
  Your choice?"
  User: "Start with Under 5 TPR"
  ---
  Step 5: Column Selection & Data Quality
  ChatMRPT Response:
  "For Under 5 TPR calculation in Adamawa State, I need to identify the best numerator and denominator columns:
  NUMERATOR (Tested Positive in Adamawa):
  - RDT Positive Under 5: Good data availability
  - Microscopy Positive Under 5: Limited data availability
  DENOMINATOR (Tested Population in Adamawa):
  - RDT Tested Under 5: Good data availability
  - Microscopy Tested Under 5: Limited data availability
  My Logic: For each facility in Adamawa, I'll compare RDT vs Microscopy values and use the greater value. If only one has data, I'll use the available value.
  Missing Data Analysis by Ward in Adamawa:
  - Most wards have complete data from all facilities
  - Some wards have partial facility reporting
  - Few wards have no TPR data available
  Should I proceed with this column selection approach for Adamawa State?"
  User: "Yes, proceed"
  ---
  Step 6: Initial TPR Calculation
  ChatMRPT Response:
  "I've calculated Under 5 TPR for each facility in Adamawa State using the column comparison logic, then aggregated to ward level:
  Calculation Process for Adamawa:
  1. Facility Level: For each facility-month, compared RDT vs Microscopy (used greater value)
  2. Ward Level: Summed all facility numerators and denominators per ward
  3. Final TPR: (Total Positive Cases / Total Tested Cases) × 100
  Results Summary for Adamawa:
  - Most wards with valid TPR calculations
  - Few wards with insufficient data
  - TPR Range: Low single digits to high values
  - Average TPR: Moderate level
  :bar_chart: [INTERACTIVE MAP: Adamawa Under 5 TPR - Initial Calculation]
  Map shows color-coded wards:
  - Dark red: Several wards with very high TPR
  - Orange: Many wards with high TPR
  - Yellow: Many wards with moderate TPR
  - Light green: Some wards with low TPR
  - Dark green: Few wards with very low TPR
  - Gray: Few wards with no data
  :warning: Threshold Alert for Adamawa:
  I found several wards with TPR above 50%:
  - Multiple LGAs affected with very high values
  - Urban areas showing unrealistic transmission levels
  Question: These high values in Adamawa's urban areas (highlighted in dark red on the map) might not represent true transmission. Do these patterns match your local knowledge of malaria burden in
  Adamawa? If not, I can recalculate using outpatient attendance as denominator."
  User: "The values seem too high for urban areas in Adamawa. Please recalculate."
  ---
  Step 7: Alternative Calculation
  ChatMRPT Response:
  "I'll now recalculate TPR for Adamawa State using Outpatient Attendance as the denominator for a broader population base:
  New Calculation for Adamawa:
  - NUMERATOR: Same (Positive malaria cases from RDT/Microscopy comparison)
  - DENOMINATOR: Total outpatient attendance (all patients, not just fever cases)
  - New Formula: TPR = (Positive Cases / Outpatient Attendance) × 100
  Revised Results for Adamawa:
  - TPR Range: Low single digits to moderate teens
  - Average TPR: Low single digits
  - Wards with very high TPR: None (problem resolved!)
  :map_distribution: [SIDE-BY-SIDE COMPARISON MAPS for Adamawa]
  Map 1: Fever-Tested Denominator
  Shows the original calculation with problematic high values
  - Several wards in dark red (unrealistically high)
  - Values reaching unrealistic levels
  Map 2: Outpatient Denominator
  Shows the revised calculation with realistic values
  - All wards now showing reasonable levels
  - Color scale: Gradual progression from low to moderate
  - More realistic geographic distribution
  The second approach gives more realistic values for Adamawa's urban areas. Which calculation would you prefer to use for Adamawa?"
  User: "Use the outpatient attendance approach"