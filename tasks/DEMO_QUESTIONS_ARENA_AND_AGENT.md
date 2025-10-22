# Demo Questions: Arena + AI Agent Prowess

**Date:** 2025-10-06
**Purpose:** Questions for 15-minute sales demo
**Data:** Adamawa State - 226 wards, 21 LGAs, TPR + environmental data

---

## PART 1: ARENA QUESTIONS (3 Questions)

### Arena Question 1: Test Positivity Rate Interpretation

**Question:**
> "A ward reports a Test Positivity Rate (TPR) of 85% based on 500 RDT tests conducted in one month. What does this indicate about malaria transmission in this ward, and what actions should be prioritized?"

**Why this question:**
- Tests understanding of TPR as a surveillance metric
- Requires knowledge of WHO TPR thresholds (>5% indicates high transmission)
- Links data to action (intervention prioritization)
- Real-world decision-making scenario

**Expected concepts in good answers:**
- High TPR (85%) indicates very high malaria transmission
- Suggests most fevers are malaria-related
- May indicate high parasite reservoir in community
- Prioritize: ITN distribution, IRS, case management
- Consider: Testing volume (500 may be low for ward population)

---

### Arena Question 2: Environmental Risk Factors

**Question:**
> "Two wards have similar populations and healthcare access. Ward A is located 500m from a river with high rainfall (>1500mm/year), while Ward B is 5km from water sources with moderate rainfall (800mm/year). Which environmental factors make Ward A potentially higher risk for malaria, and why?"

**Why this question:**
- Tests understanding of mosquito breeding habitats
- Links environmental factors to malaria ecology
- Requires knowledge of Anopheles mosquito behavior
- Spatial thinking about malaria risk

**Expected concepts in good answers:**
- Proximity to water bodies = mosquito breeding sites
- Higher rainfall = more standing water = more breeding
- Ward A has both factors (close to water + high rainfall)
- Anopheles mosquitoes fly 1-2km from breeding sites
- Temperature and humidity also matter (related to rainfall)
- Ward A likely has higher vector density

---

### Arena Question 3: ITN Distribution Strategy

**Question:**
> "A state has 100,000 ITNs to distribute across 200 wards. Should nets be distributed equally (500 per ward) or based on malaria risk rankings? Explain the trade-offs of each approach and when you would choose one over the other."

**Why this question:**
- Tests understanding of resource allocation strategies
- Requires knowledge of equity vs efficiency
- Real-world policy decision
- Multiple valid approaches (assesses reasoning quality)

**Expected concepts in good answers:**
- **Equal distribution:**
  - Pros: Equitable, politically acceptable, simple logistics
  - Cons: Inefficient, low-risk areas get same as high-risk
- **Risk-based distribution:**
  - Pros: Maximizes impact, evidence-based, targets burden
  - Cons: May leave some wards without nets, complex logistics
- **Hybrid approach:**
  - Minimum baseline for all + extra for high-risk
- Decision depends on: political context, total nets available, risk variation

---

## PART 2: AI AGENT PROWESS QUESTIONS (10 Questions)

### Category A: Statistical Analysis (3 questions)

#### Q1: Basic Descriptive Statistics
**Question to Agent:**
> "What is the mean, median, and standard deviation of TPR across all wards? Which LGA has the highest average TPR?"

**Why impressive:**
- Shows instant statistical calculation
- Multi-part question (4 answers in one)
- Demonstrates data aggregation

**Expected Answer:**
- Mean TPR: 71.38%
- Median TPR: 72.98%
- Standard deviation: 11.03%
- Highest LGA: Maiha with 82.52% mean TPR

---

#### Q2: Testing Volume Analysis
**Question to Agent:**
> "How many total tests were conducted across all wards? What percentage tested positive? Which ward had the highest testing volume?"

**Why impressive:**
- Shows summation and percentage calculation
- Demonstrates data filtering/sorting
- Multiple metrics in one query

**Expected Answer:**
- Total tests: 906,495
- Overall positivity rate: 72.5% (657,227 positive / 906,495 tested)
- Highest testing volume: [Ward name] with 14,516 tests

---

#### Q3: Outlier Identification
**Question to Agent:**
> "Which wards are statistical outliers in TPR - meaning wards with TPR more than 2 standard deviations from the mean? List them with their TPR values."

**Why impressive:**
- Shows statistical concept application (Z-scores)
- Demonstrates filtering logic
- Identifies unusual patterns

**Expected Answer:**
- Mean ± 2 SD range: 49.32% to 93.44%
- Outliers (high): Humbutudi (91.52%), Rumde (91.42%), Girei 2 (89.97%)
- Outliers (low): Hyambula (36.23%), Kwaja (36.42%), Duhu (47.00%)

---

### Category B: Data Exploration (3 questions)

#### Q4: Geographic Patterns
**Question to Agent:**
> "Show me the 5 LGAs with highest TPR and the 5 with lowest TPR. Include the number of wards in each."

**Why impressive:**
- Shows grouping and aggregation
- Demonstrates ranking logic
- Clear comparative output

**Expected Answer:**
**Highest:**
1. Maiha: 82.52% (10 wards)
2. Shelleng: 81.53% (10 wards)
3. Lamurde: 77.36% (10 wards)
4. Mayo-Belwa: 76.79% (12 wards)
5. Girei: 76.44% (10 wards)

**Lowest:**
1. Madagali: [X]% ([X] wards)
2. Mubi South: [X]% ([X] wards)
... [etc]

---

#### Q5: Environmental Variable Ranges
**Question to Agent:**
> "What's the range of urban percentage across wards? How many wards are considered highly urban (>50% urban)?"

**Why impressive:**
- Shows data filtering
- Demonstrates counting with conditions
- Real-world categorization

**Expected Answer:**
- Urban percentage range: 10.3% to 59.3%
- Mean urban: 33.9%
- Wards >50% urban: [Count] wards
- [Optional: List names if agent provides]

---

#### Q6: Testing Coverage Analysis
**Question to Agent:**
> "Which 5 wards had the lowest testing volume? Is there a relationship between testing volume and urban percentage?"

**Why impressive:**
- Multi-part exploratory question
- Shows sorting capability
- Introduces correlation concept

**Expected Answer:**
- 5 lowest testing volumes: [List wards with counts]
- Relationship: [May need to calculate correlation or show scatter]
- Could mention: Rural areas might have lower testing access

---

### Category C: Correlations & Relationships (2 questions)

#### Q7: Environmental Correlations with TPR
**Question to Agent:**
> "Calculate the correlation between TPR and each environmental variable (rainfall, distance to water, soil wetness, urban percentage). Which has the strongest relationship with TPR?"

**Why impressive:**
- Shows statistical correlation analysis
- Demonstrates multi-variable comparison
- Interprets findings

**Expected Answer:**
- Rainfall: +0.302 (moderate positive)
- Distance to water: +0.033 (very weak positive)
- Urban percentage: +0.011 (negligible)
- Soil wetness: -0.148 (weak negative)
- **Strongest:** Rainfall (0.302) - higher rainfall associated with higher TPR

---

#### Q8: Testing Volume vs TPR
**Question to Agent:**
> "Is there a correlation between testing volume and TPR? Do wards with more tests tend to have higher or lower TPR?"

**Why impressive:**
- Tests a non-obvious hypothesis
- Shows agent can calculate new correlations
- Practical question (sampling bias check)

**Expected Answer:**
- Correlation: [Calculate TPR vs Total_Tested]
- Interpretation: Weak/no correlation suggests TPR is not driven by testing volume
- This is GOOD - means TPR reflects true burden, not just testing availability

---

### Category D: Visualizations (2 questions)

#### Q9: TPR Distribution Histogram
**Question to Agent:**
> "Create a histogram showing the distribution of TPR across all wards. Include bins of 10% width (30-40%, 40-50%, etc.)."

**Why impressive:**
- Shows visualization capability
- Demonstrates data binning
- Visual output is engaging

**Expected Output:**
- Histogram with bins: 30-40, 40-50, 50-60, 60-70, 70-80, 80-90, 90-100
- Most wards likely in 60-80% range
- Shows skew toward higher TPR values

---

#### Q10: Scatter Plot - Rainfall vs TPR
**Question to Agent:**
> "Create a scatter plot showing the relationship between rainfall and TPR. Color-code points by LGA if possible."

**Why impressive:**
- Shows complex visualization
- Demonstrates relationship visually
- Color coding adds sophistication

**Expected Output:**
- Scatter plot with TPR on Y-axis, rainfall on X-axis
- Positive trend visible (upward slope)
- Points clustered by LGA (if colored)
- Shows variability within trend

---

## DEMO EXECUTION STRATEGY

### For Arena (Tab 5):
1. **Pick 1 question to show** (recommend Q1 - TPR Interpretation)
2. Show Model A and Model B responses side-by-side
3. Don't vote - just say "participants will vote and explain their choice"
4. Mention: "This helps us assess your conceptual understanding"
5. Keep it to 1 minute max

### For AI Agent (Tab 6 - Optional):
1. **Pre-run 4-5 questions** before demo (have tabs ready)
2. **Show in this order** (if time permits):
   - Q1 (Basic stats) - 15 seconds
   - Q4 (Geographic patterns) - 20 seconds
   - Q7 (Correlations) - 20 seconds
   - Q9 or Q10 (Visualization) - 30 seconds
3. **Don't wait for responses live** - switch between pre-loaded tabs
4. Total time: 1-2 minutes

### Quick Demo Script for Agent:

> "ChatMRPT can also answer your data questions instantly. For example:
>
> [TAB: Q1] 'What's the mean TPR?' - **71.38%**, done.
>
> [TAB: Q4] 'Which LGAs have highest TPR?' - **Maiha, Shelleng, Lamurde** - ranked instantly.
>
> [TAB: Q7] 'What environmental factors correlate with TPR?' - **Rainfall has the strongest relationship at +0.30**.
>
> [TAB: Q9] 'Show me a histogram of TPR distribution' - **Visual output, generated in seconds**.
>
> So if you have questions during the breakout, just ask ChatMRPT. It's like having a data analyst on demand."

---

## PRE-DEMO PREPARATION CHECKLIST

### Arena:
- [ ] Select 1 question to demonstrate (recommend Q1)
- [ ] Have Model A and Model B responses ready
- [ ] Practice quick explanation (30 seconds)

### AI Agent:
- [ ] Run Q1, Q4, Q7, Q9 or Q10 in ChatMRPT
- [ ] Keep 4-5 tabs open with responses
- [ ] Bookmark each tab or note the URLs
- [ ] Practice quick transitions (5 seconds between tabs)
- [ ] Have backup screenshots in case tabs fail

### Testing:
- [ ] Test all questions work on the Adamawa dataset
- [ ] Verify visualizations display correctly
- [ ] Check correlations calculate properly
- [ ] Ensure responses are accurate
- [ ] Time the Tab 6 sequence (should be <2 minutes)

---

## BACKUP QUESTIONS (If some don't work)

### Statistical Backups:
- "What's the total number of positive cases across all wards?"
- "Which ward has the highest TPR? What's the value?"
- "What percentage of wards have TPR above 70%?"

### Exploration Backups:
- "List the top 3 wards by testing volume"
- "How many LGAs are in the dataset?"
- "What's the range of soil wetness values?"

### Visualization Backups:
- "Create a bar chart of mean TPR by LGA"
- "Show a box plot of TPR distribution"

---

**Status:** Questions ready for demo preparation
**Next Step:** Pre-run these questions in ChatMRPT and save the tabs
**Time to prepare:** 30-45 minutes to run all questions and organize tabs
