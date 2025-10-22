# Statistical Tests User Guide
**ChatMRPT Data Analysis**

## How to Request Statistical Tests

ChatMRPT now supports comprehensive statistical analysis through natural language requests. You can ask questions in plain English, and the system will generate and execute the appropriate statistical tests.

## Supported Statistical Tests

### Correlation Analysis

**What it does:** Measures the strength and direction of relationship between two variables.

**Example Requests:**
- "What is the correlation between TPR and rainfall?"
- "Show me the correlation between soil wetness and distance to waterbodies"
- "Calculate Pearson correlation for TPR and rainfall"
- "Perform correlation analysis for all environmental variables"

**Use cases:**
- Identifying which environmental factors are most related to malaria TPR
- Understanding relationships between risk factors
- Finding redundant variables (highly correlated)

---

### ANOVA (Analysis of Variance)

**What it does:** Tests if there are significant differences in means across multiple groups.

**Example Requests:**
- "Is there a significant difference in TPR across facility levels?"
- "Perform ANOVA test for TPR by state"
- "Test if rainfall differs significantly across urban categories"
- "Check if there are significant differences in composite scores by LGA"

**Use cases:**
- Comparing malaria rates across different facility types (Primary/Secondary/Tertiary)
- Testing if environmental factors differ by geographic region
- Validating that risk scores differ significantly across vulnerability categories

---

### t-Tests (Two-Sample Comparison)

**What it does:** Tests if there are significant differences in means between two groups.

**Example Requests:**
- "Is there a significant difference in TPR between urban and rural wards?"
- "Compare average rainfall between high-risk and low-risk wards"
- "Test if composite scores differ between northern and southern LGAs"

**Use cases:**
- Comparing malaria burden between urban vs rural areas
- Testing if environmental factors differ between high and low risk areas
- Validating geographic differences in risk factors

---

### Non-Parametric Tests

**What they do:** Alternative tests that don't assume normal distribution (good for skewed data).

**Example Requests:**
- "Perform Mann-Whitney U test for TPR between urban and rural"
- "Run Kruskal-Wallis test for rainfall across states"
- "Test if there's a significant difference in ranks of composite scores by region"

**Use cases:**
- When data is not normally distributed
- When dealing with ordinal data (rankings)
- When sample sizes are small

---

### Chi-Square Tests

**What it does:** Tests independence between categorical variables.

**Example Requests:**
- "Is there a relationship between urban category and high/low TPR?"
- "Test if facility level and vulnerability category are independent"
- "Perform chi-square test for state and risk category"

**Use cases:**
- Testing if malaria risk is associated with urban/rural classification
- Checking if certain facility types are more common in high-risk areas
- Validating geographic patterns in categorical risk classifications

---

### Normality Tests

**What they do:** Test if data follows a normal distribution (important for choosing parametric vs non-parametric tests).

**Example Requests:**
- "Test if TPR is normally distributed"
- "Check normality of rainfall data"
- "Perform Shapiro-Wilk test for composite scores"

**Use cases:**
- Validating assumptions before running parametric tests
- Deciding between ANOVA vs Kruskal-Wallis
- Checking if data transformations are needed

---

### Regression Analysis

**What it does:** Models the relationship between independent variables and dependent variable.

**Example Requests:**
- "What is the relationship between rainfall and TPR?"
- "Run linear regression for TPR predicted by environmental factors"
- "Show me regression statistics for soil wetness vs TPR"

**Use cases:**
- Predicting malaria TPR from environmental variables
- Quantifying the effect size of risk factors
- Building explanatory models for malaria transmission

---

## Tips for Better Results

### 1. Be Specific About Variables
✅ **Good:** "Correlation between TPR and soil_wetness"
❌ **Vague:** "Show me some correlations"

### 2. Specify the Test (Optional)
✅ **Good:** "Perform Pearson correlation for TPR and rainfall"
✅ **Also Good:** "What's the relationship between TPR and rainfall?" (system will choose appropriate test)

### 3. Ask for Interpretation
- "What does a correlation of 0.7 mean?"
- "Is a p-value of 0.03 significant?"
- "Explain the ANOVA results"

### 4. Combine with Visualizations
- "Show correlation between TPR and rainfall, and create a scatter plot"
- "Perform ANOVA for facility levels and plot the distributions"

### 5. Request Multiple Tests
- "Test which environmental variables (rainfall, soil_wetness, distance_to_waterbodies) are most correlated with TPR"
- "Compare TPR across all facility levels and states using ANOVA"

---

## Understanding Statistical Output

### Correlation Coefficient (r)
- **Range:** -1 to +1
- **Interpretation:**
  - r = 0: No linear relationship
  - r = 0.3: Weak correlation
  - r = 0.5: Moderate correlation
  - r = 0.7: Strong correlation
  - r = 1.0: Perfect correlation
  - Negative values indicate inverse relationship

### p-value
- **Common threshold:** p < 0.05 (5% significance level)
- **Interpretation:**
  - p < 0.05: Statistically significant (reject null hypothesis)
  - p ≥ 0.05: Not statistically significant (cannot reject null hypothesis)
  - Lower p-values indicate stronger evidence

### F-statistic (ANOVA)
- **Higher values** indicate larger differences between group means
- **Must look at p-value** to determine if differences are significant

### t-statistic (t-tests)
- **Larger absolute values** indicate larger differences between groups
- **Must look at p-value** to determine if difference is significant

---

## Common Analysis Workflows

### Workflow 1: Variable Selection for Risk Model
```
1. "Show correlation matrix for all environmental variables"
2. "Which variables are most correlated with TPR?"
3. "Test if the top 3 variables differ significantly across risk categories"
```

### Workflow 2: Validating Geographic Differences
```
1. "Test if TPR differs significantly across states using ANOVA"
2. "Compare average TPR between northern and southern states"
3. "Check if these differences are also present for environmental factors"
```

### Workflow 3: Understanding Risk Factors
```
1. "What is the correlation between each environmental variable and TPR?"
2. "Plot the strongest correlations as scatter plots"
3. "Test if high-correlation variables also differ across high/low risk wards"
```

### Workflow 4: Validating Analysis Results
```
1. "Test if composite scores are normally distributed"
2. "Perform ANOVA to check if composite scores differ across vulnerability categories"
3. "Compare composite scores and PCA scores to see if they rank wards similarly"
```

---

## Technical Details

All statistical tests use **scipy.stats** library, which provides:
- Accurate statistical computations
- Standard test implementations
- Reliable p-value calculations
- Support for various data types and distributions

The system automatically:
- Loads your data
- Selects appropriate columns
- Handles missing values
- Formats results for readability
- Provides test statistics and p-values

---

## Need Help?

If you're unsure which test to use, just ask:
- "How can I test if TPR differs by state?"
- "What statistical test should I use to compare urban and rural wards?"
- "How do I check if two variables are related?"

The system will recommend appropriate tests and explain why.

---

## Example Session

**User:** "I want to understand which environmental variables affect TPR the most"

**ChatMRPT:** "Let me analyze the correlations between TPR and all environmental variables in your dataset."

*[Runs correlation analysis]*

**Result:**
```
Correlation with TPR:
- rainfall: r=0.45, p=0.001 (moderate, significant)
- soil_wetness: r=-0.15, p=0.234 (weak, not significant)
- distance_to_waterbodies: r=-0.38, p=0.003 (moderate, significant)
```

**ChatMRPT:** "Based on these results, rainfall and distance to waterbodies show moderate, statistically significant correlations with TPR. Would you like me to perform regression analysis or create visualizations?"

---

**Last Updated:** 2025-10-05
**Status:** Active - All statistical tests fully supported
