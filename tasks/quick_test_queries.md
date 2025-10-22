# Quick Test Queries - Copy & Paste
**Dataset**: Adamawa Ward Data (226 wards)
**Use**: Copy these exact queries to test agent capabilities

---

## ✅ Known Working (Baseline)
```
What is the correlation between TPR and rainfall? Also show correlation with soil_wetness and distance_to_waterbodies.
```

---

## 🔬 Statistical Tests (scipy.stats)

### ANOVA Test
```
Perform an ANOVA test to see if TPR differs significantly across different LGAs. Show me the F-statistic and p-value.
```

### T-Test
```
Is there a significant difference in TPR between wards with urban_percentage > 30% vs <= 30%? Use independent t-test.
```

### Normality Test
```
Check normality of TPR distribution using Shapiro-Wilk test. If not normal, suggest appropriate non-parametric alternative.
```

---

## 🤖 Machine Learning (sklearn)

### Clustering
```
Cluster the wards into 3 groups based on TPR, rainfall, and soil_wetness. Show me which wards are in each cluster.
```

### PCA
```
Perform PCA on environmental variables (rainfall, soil_wetness, distance_to_waterbodies, urban_percentage) and show variance explained by each component.
```

### Regression
```
Build a linear regression model to predict TPR from rainfall and soil_wetness. What are the coefficients and R-squared value?
```

---

## 📊 Visualizations

### Scatter Plot
```
Create a scatter plot of TPR vs rainfall, colored by LGA.
```

### Box Plot
```
Make a box plot showing TPR distribution for each LGA.
```

### Heatmap
```
Create a correlation heatmap for all numeric variables.
```

---

## 🔍 Data Queries

### Filtering
```
Show me the top 10 wards by TPR that have rainfall > 27700000.
```

### Aggregation
```
Which LGA has the highest average TPR? Show all LGAs ranked by average TPR.
```

### Complex Query
```
Find all wards where distance_to_waterbodies is 0 (adjacent to water). How many are there and what's their average TPR?
```

---

## 🧩 Complex Multi-Step

### Group Comparison
```
Compare wards with high urban percentage (>40%) vs low (<40%): show their average TPR, average distance to water, and perform t-test on TPR difference. Then create side-by-side box plots.
```

### Environmental Pattern Analysis
```
Find the 5 wards with highest TPR. For these wards, calculate their average environmental conditions (rainfall, soil_wetness, distance_to_waterbodies, urban_percentage) and compare to overall dataset averages.
```

### Cluster Characterization
```
Cluster wards into 3 groups using KMeans on (TPR, rainfall, soil_wetness). Then for each cluster, calculate: (1) average urban_percentage, (2) average distance to water, (3) count of wards, (4) list of top 3 wards by TPR. Present as a summary table.
```

---

## 🎯 Quick Diagnostic Tests

### Test 1: Does scipy.stats work?
```
Perform ANOVA to test if TPR differs across LGAs
```
**Expected**: F-statistic, p-value, interpretation
**Failure Mode**: "Code contains potentially dangerous operations"

### Test 2: Does sklearn work?
```
Run KMeans clustering with 3 clusters on TPR, rainfall, soil_wetness
```
**Expected**: Cluster assignments, centroids
**Failure Mode**: Routes to wrong operation or "ModuleNotFoundError"

### Test 3: Do visualizations work?
```
Create correlation heatmap for numeric variables
```
**Expected**: Interactive Plotly heatmap saved to visualizations/
**Failure Mode**: Generic response without actual chart

### Test 4: Does complex reasoning work?
```
Compare high TPR wards (>75%) vs low TPR wards (<=75%) on all environmental variables. Use t-test for each variable and create a summary table.
```
**Expected**: Multiple t-tests, comprehensive table, interpretation
**Failure Mode**: Partial answer or single variable only

---

## 📝 Testing Checklist

After each query, verify:
- [ ] Response includes actual analysis (not just acknowledgment)
- [ ] Statistical values are present (not placeholder text)
- [ ] Visualizations are created (check visualizations folder)
- [ ] Epidemiological interpretation provided
- [ ] No error messages about "dangerous operations"
- [ ] Tool used is `analyze_data_with_python` (check logs)

---

## 🚨 Red Flags

If you see these, Tool #19 is NOT working correctly:
- ❌ "Code contains potentially dangerous operations"
- ❌ "I'll check the data structure first..." (stalling behavior)
- ❌ Only correlation works, everything else fails
- ❌ Tool called: `execute_data_query` instead of `analyze_data_with_python`
- ❌ Generic responses without actual calculations
- ❌ "ModuleNotFoundError: No module named 'scipy'"

---

## ✅ Success Indicators

If you see these, Tool #19 IS working:
- ✅ Actual F-statistics, t-statistics, p-values shown
- ✅ Cluster assignments with ward names
- ✅ PCA variance explained percentages
- ✅ Regression coefficients and R² values
- ✅ Interactive visualizations saved and displayed
- ✅ Statistical significance interpretations
- ✅ Tool called: `analyze_data_with_python` (in logs)
- ✅ Multi-step reasoning executed correctly

---

**Dataset Location**: `/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/docs/raw_data.csv`
**Full Test Suite**: See `agent_test_questions.md` for comprehensive tests
**Summary**: See `agent_testing_summary.md` for context and background
