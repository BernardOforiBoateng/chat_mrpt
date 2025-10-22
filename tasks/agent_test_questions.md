# DataExplorationAgent Test Questions
**Dataset**: Adamawa State Ward-Level Malaria Data (226 wards)
**Purpose**: Verify agent capabilities for statistical analysis, ML, and visualizations

---

## Dataset Overview
- **226 wards** from Adamawa State, North-East Nigeria
- **21 LGAs** (Local Government Areas)
- **Variables**: 14 columns (7 text, 7 numeric)
- **No missing values**

### Numeric Variables Ranges:
| Variable | Min | Max | Mean | Median | Std |
|----------|-----|-----|------|--------|-----|
| TPR | 36.23% | 91.52% | 71.38% | 72.98% | 11.03 |
| Total_Tested | 65 | 14,516 | 4,011 | 3,039 | 3,025 |
| Total_Positive | 48 | 12,288 | 2,908 | 2,209 | 2,300 |
| distance_to_waterbodies | 0m | 10,000m | 2,898m | 2,828m | 2,092 |
| rainfall | 27,404,240 | 27,805,604 | 27,651,077 | 27,656,524 | 105,127 |
| soil_wetness | 0.53 | 0.92 | 0.69 | 0.71 | 0.10 |
| urban_percentage | 10.25% | 59.34% | 33.89% | 34.72% | 14.66 |

### Extreme Values:
- **Highest TPR**: Humbutudi (Maiha) - 91.52%
- **Lowest TPR**: Hyambula (Madagali) - 36.23%
- **Largest test volume**: Lamurde (Lamurde) - 13,030 tests

---

## Test Suite

### 1. CORRELATION ANALYSIS (scipy.stats.pearsonr)
**Expected**: Should work (already confirmed working)

**Q1.1**: "What is the correlation between TPR and rainfall? Also show correlation with soil_wetness and distance_to_waterbodies."

**Expected Output**:
- Correlation matrix or heatmap
- Pearson r values and p-values
- Interpretation of strength and significance

**Q1.2**: "Create a correlation heatmap for all numeric variables"

**Expected Output**:
- Plotly/seaborn heatmap
- All 7 numeric variables
- Color-coded correlation coefficients

---

### 2. ANOVA TEST (scipy.stats.f_oneway)
**Expected**: Should now work (was failing before)

**Q2.1**: "Perform an ANOVA test to see if TPR differs significantly across different LGAs. Show me the F-statistic and p-value."

**Expected Output**:
- F-statistic value
- p-value
- Interpretation (reject/fail to reject null hypothesis at α=0.05)
- Conclusion about TPR differences across LGAs

**Q2.2**: "Is there a significant difference in TPR across urban categories? Group wards into 'High Urban' (>40%) and 'Low Urban' (<=40%) and run ANOVA."

**Expected Output**:
- Group creation logic
- F-statistic and p-value
- Statistical conclusion

---

### 3. T-TEST (scipy.stats.ttest_ind)
**Expected**: Should now work (requires scipy.stats)

**Q3.1**: "Is there a significant difference in TPR between wards with urban_percentage > 30% vs <= 30%? Use independent t-test."

**Expected Output**:
- Group 1 stats (n, mean, std)
- Group 2 stats (n, mean, std)
- t-statistic and p-value
- Interpretation with confidence interval

**Q3.2**: "Compare rainfall between high TPR wards (>75%) and low TPR wards (<=75%) using t-test"

**Expected Output**:
- Descriptive stats for both groups
- t-test results
- Conclusion about rainfall difference

---

### 4. CLUSTERING (sklearn.cluster.KMeans)
**Expected**: Should now work (was failing before - routing to wrong operation)

**Q4.1**: "Cluster the wards into 3 groups based on TPR, rainfall, and soil_wetness. Show me which wards are in each cluster."

**Expected Output**:
- Cluster assignments for all 226 wards
- Cluster centers (centroids)
- Ward names per cluster
- Optional: visualization (scatter plot with cluster colors)

**Q4.2**: "Perform hierarchical clustering on environmental variables (rainfall, soil_wetness, distance_to_waterbodies, urban_percentage) with 4 clusters. Show dendrogram."

**Expected Output**:
- Dendrogram visualization
- Cluster assignments
- Interpretation of hierarchical structure

---

### 5. PCA (sklearn.decomposition.PCA)
**Expected**: Should now work (was failing before - routing to wrong operation)

**Q5.1**: "Perform PCA on all numeric variables. Show variance explained by each component and create a scree plot."

**Expected Output**:
- Variance explained per component (%)
- Cumulative variance explained
- Scree plot
- Loadings interpretation

**Q5.2**: "Run PCA on environmental variables (rainfall, soil_wetness, distance_to_waterbodies, urban_percentage) and show the first 2 components as a biplot"

**Expected Output**:
- PCA biplot with ward points
- Variable loadings as arrows
- Variance explained by PC1 and PC2

---

### 6. LINEAR REGRESSION (sklearn.linear_model.LinearRegression)
**Expected**: Should now work (was failing before)

**Q6.1**: "Build a linear regression model to predict TPR from rainfall and soil_wetness. What are the coefficients and R-squared value?"

**Expected Output**:
- Coefficients for rainfall and soil_wetness
- Intercept
- R² value
- Model equation (TPR = β0 + β1*rainfall + β2*soil_wetness)
- Interpretation of coefficients

**Q6.2**: "Create a multiple regression model predicting TPR using all environmental variables (distance_to_waterbodies, rainfall, soil_wetness, urban_percentage). Show feature importance."

**Expected Output**:
- All coefficients
- R² and adjusted R²
- Feature importance ranking
- Model performance metrics (RMSE, MAE)

---

### 7. DATA QUERIES & FILTERING
**Expected**: Should work (pandas operations)

**Q7.1**: "Show me the top 10 wards by TPR that have rainfall > 27,700,000"

**Expected Output**:
- Ward list with WardName, LGA, TPR, rainfall
- Filtered to meet both conditions
- Sorted by TPR descending

**Q7.2**: "Which LGA has the highest average TPR? Show all LGAs ranked by average TPR."

**Expected Output**:
- LGA rankings with avg TPR
- Number of wards per LGA
- Optional: bar chart

**Q7.3**: "Find all wards where distance_to_waterbodies is 0 (adjacent to water). How many are there and what's their average TPR?"

**Expected Output**:
- Count of wards with distance = 0
- List of ward names
- Average TPR for this group
- Comparison to overall average TPR

---

### 8. VISUALIZATIONS
**Expected**: Should create Plotly/matplotlib charts

**Q8.1**: "Create a scatter plot of TPR vs rainfall, colored by LGA"

**Expected Output**:
- Interactive Plotly scatter plot
- Different colors per LGA
- Trend line optional
- Saved to visualizations folder

**Q8.2**: "Make a box plot showing TPR distribution for each LGA"

**Expected Output**:
- Box plot with 21 boxes (one per LGA)
- Shows quartiles, median, outliers
- LGAs on x-axis, TPR on y-axis

**Q8.3**: "Create a histogram of soil_wetness with 20 bins"

**Expected Output**:
- Histogram with distribution
- 20 bins as requested
- Labels and title

---

### 9. COMPLEX MULTI-STEP ANALYSES
**Expected**: Agent should chain multiple operations

**Q9.1**: "Compare wards with high urban percentage (>40%) vs low (<40%): show their average TPR, average distance to water, and perform t-test on TPR difference. Then create side-by-side box plots."

**Expected Output**:
- Descriptive stats for both groups
- T-test results
- Box plot visualization
- Comprehensive interpretation

**Q9.2**: "Find the 5 wards with highest TPR. For these wards, calculate their average environmental conditions (rainfall, soil_wetness, distance_to_waterbodies, urban_percentage) and compare to overall dataset averages."

**Expected Output**:
- Top 5 wards identified
- Environmental variable averages for top 5
- Overall dataset averages
- Comparison table showing differences
- Interpretation of environmental patterns

**Q9.3**: "Cluster wards into 3 groups using KMeans on (TPR, rainfall, soil_wetness). Then for each cluster, calculate: (1) average urban_percentage, (2) average distance to water, (3) count of wards, (4) list of top 3 wards by TPR. Present as a summary table."

**Expected Output**:
- Cluster assignments
- Summary table with all requested metrics
- Top 3 wards per cluster
- Cluster characterization

---

### 10. STATISTICAL TESTING EDGE CASES
**Expected**: Proper error handling and assumptions checking

**Q10.1**: "Check normality of TPR distribution using Shapiro-Wilk test. If not normal, suggest appropriate non-parametric alternative."

**Expected Output**:
- Shapiro-Wilk test statistic and p-value
- Conclusion about normality
- Alternative test suggestion (e.g., Mann-Whitney U, Kruskal-Wallis)
- Optional: Q-Q plot or histogram

**Q10.2**: "Test for homogeneity of variance in TPR across LGAs using Levene's test"

**Expected Output**:
- Levene's test statistic and p-value
- Interpretation
- Implications for ANOVA assumptions

---

## Success Criteria

### Tool #19 (analyze_data_with_python) should successfully:

1. ✅ **Execute scipy.stats functions**:
   - pearsonr, f_oneway, ttest_ind, shapiro, levene

2. ✅ **Execute sklearn functions**:
   - KMeans, PCA, LinearRegression, StandardScaler

3. ✅ **Create visualizations**:
   - Plotly scatter, box, histogram, heatmap
   - Matplotlib when needed

4. ✅ **Handle complex queries**:
   - Multi-step reasoning
   - Chained operations
   - Data transformations

5. ✅ **Provide interpretations**:
   - Statistical significance
   - Clinical/epidemiological meaning
   - Actionable insights

### Error Indicators:

❌ "Code contains potentially dangerous operations" → Security filter blocking legitimate operations
❌ Routes to execute_data_query instead of analyze_data_with_python → Tool conflict
❌ "ModuleNotFoundError: No module named 'scipy'" → Missing dependency
❌ Generic response without actual analysis → Tool not being called
❌ Only correlation works, others fail → Hardcoded chart type detection

---

## Testing Protocol

1. **Sequential Testing**: Start with Q1.1, proceed in order
2. **Failure Documentation**: Note exact error message and line number
3. **Tool Inspection**: Check which tool was called in logs
4. **Output Verification**: Confirm statistical values are reasonable
5. **Visualization Check**: Verify charts are created and displayed

---

## Expected Tools Used (from logs)

Each question should trigger:
1. `analyze_data_with_python` tool call (RequestInterpreter)
2. DataExplorationAgent.analyze_sync() execution
3. LangGraph workflow: agent → Python tool → agent
4. SecureExecutor with scipy, sklearn, plotly available
5. Result formatting with insights

**File Output**: Look for new files in `instance/uploads/{session_id}/visualizations/`
