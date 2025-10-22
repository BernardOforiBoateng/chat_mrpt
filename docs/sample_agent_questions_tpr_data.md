# Sample Questions for Data Analysis Agent Testing
## Based on Adamawa TPR Dataset

These questions are designed to test the **flexible data exploration** agent (Option 2), NOT the guided TPR workflow. They should demonstrate the agent's ability to analyze patterns, create visualizations, and answer complex questions about the data.

## Dataset Overview
- **File**: adamawa_tpr_cleaned.csv
- **Content**: Malaria testing data from Adamawa State health facilities
- **Time Period**: Monthly data for 2024 (periodname shows 2025 but periodcode shows 2024)
- **Key Metrics**: Tests performed (RDT & Microscopy), positive results, LLIN distribution
- **Demographics**: Children <5 years, Adults ≥5 years, Pregnant Women

---

## 📊 Trend Analysis Questions

1. **"Show me monthly variations in test positivity rates across all facilities"**
   - Tests general trend analysis without triggering TPR workflow
   - Should create time series visualization

2. **"What are the seasonal patterns in malaria cases for children under 5?"**
   - Analyzes temporal patterns for specific age group
   - Should identify peak months

3. **"Compare the monthly trends between RDT and microscopy testing methods"**
   - Comparative analysis of testing methods over time

---

## 🏥 Facility-Level Analysis Questions

4. **"Which health facilities have the highest test positivity?"**
   - Ranking analysis across facilities
   - Should identify high-burden locations

5. **"How does test positivity vary between primary, secondary, and tertiary facilities?"**
   - Facility level comparison
   - Tests grouping and aggregation

6. **"Show me the top 10 facilities by testing volume"**
   - Volume-based ranking
   - Tests sorting and filtering capabilities

---

## 👥 Demographic Analysis Questions

7. **"Compare malaria positivity rates between children, adults, and pregnant women"**
   - Cross-demographic comparison
   - Should show age/group disparities

8. **"What percentage of pregnant women who tested positive received LLIN?"**
   - Coverage analysis
   - Tests calculation of intervention rates

9. **"Analyze the distribution of cases by age group across different LGAs"**
   - Geographic-demographic analysis
   - Tests multi-dimensional grouping

---

## 📍 Geographic Analysis Questions

10. **"Which LGAs have the highest malaria burden?"**
    - Geographic ranking
    - Should aggregate by LGA

11. **"Create a heatmap of test positivity by ward"**
    - Spatial visualization request
    - Tests mapping capabilities

12. **"Compare malaria rates between Yola North and Yola South"**
    - Specific geographic comparison

---

## 📈 Statistical Analysis Questions

13. **"What's the correlation between testing volume and positivity rate?"**
    - Statistical relationship analysis
    - Should calculate correlation coefficient

14. **"Calculate the mean, median, and standard deviation of monthly positivity rates"**
    - Descriptive statistics
    - Tests statistical summary capabilities

15. **"Identify any outliers in the testing data"**
    - Anomaly detection
    - Tests statistical analysis

---

## 🎯 Intervention Analysis Questions

16. **"How effective is LLIN distribution in reducing positivity rates?"**
    - Impact analysis
    - Tests causal inference capabilities

17. **"Which wards need more LLIN distribution based on current coverage?"**
    - Gap analysis
    - Tests prioritization logic

18. **"Compare LLIN coverage between high and low burden areas"**
    - Coverage equity analysis

---

## 📊 Data Quality Questions

19. **"Which facilities have missing data and for which months?"**
    - Data completeness analysis
    - Tests NA/missing value handling

20. **"What percentage of records have complete testing data?"**
    - Data quality metrics
    - Tests completeness assessment

---

## 🔍 Complex Analytical Questions

21. **"Create a dashboard showing key malaria indicators for Adamawa"**
    - Multi-metric visualization
    - Tests comprehensive analysis

22. **"What factors are most associated with high test positivity?"**
    - Factor analysis
    - Tests advanced analytics

23. **"Predict which wards are likely to have increased cases next month"**
    - Predictive analysis
    - Tests forecasting capabilities

24. **"Segment health facilities into risk categories based on their data"**
    - Clustering/segmentation
    - Tests classification logic

25. **"Generate a summary report of malaria trends and recommendations"**
    - Comprehensive reporting
    - Tests synthesis capabilities

---

## Expected Behavior

### ✅ These queries should:
- Be handled by the **flexible data exploration agent** (Option 2)
- Generate visualizations where appropriate
- Provide data-driven insights
- NOT trigger the guided TPR workflow

### ❌ These queries should NOT:
- Start the step-by-step TPR calculation process
- Ask for facility level selection
- Request age group selection
- Follow the guided workflow pattern

---

## Testing Notes

When testing on staging:
1. Upload `adamawa_tpr_cleaned.csv`
2. You should see 2 options (not 4)
3. Select option 2 or just type the question directly
4. The agent should analyze the data without going through TPR workflow steps

These questions test that the routing fix is working correctly and that general analysis queries are properly handled by the flexible agent.