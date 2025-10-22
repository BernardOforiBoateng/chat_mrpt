# Comprehensive Agent Test Plan - WITH DATA

## Critical Realization
**Previous tests were USELESS** - testing without data is like testing a car without fuel. The agent can't show its real capabilities without actual data to analyze.

---

## Test Philosophy

### User Perspectives:
1. **Complete Beginner** - Doesn't know TPR, doesn't know stats, wants simple answers
2. **Domain Expert** - Knows malaria, wants deep analysis, asks technical questions
3. **Data Analyst** - Knows stats, wants proper viz, asks about methods

### Test Categories (WITH DATA LOADED):

---

## PHASE 1: DATA UPLOAD & INITIAL EXPLORATION (5 tests)

### Test 1.1: Beginner - Just uploaded data
**User**: "I just uploaded some data about malaria. What can I do with it?"
**Expected**: Welcomes user, explains TPR analysis, shows options
**Score Criteria**: Beginner-friendly language, clear next steps

### Test 1.2: Expert - Immediate technical request
**User**: "I need to analyze spatial heterogeneity in test positivity rates across administrative units"
**Expected**: Understands technical request, starts appropriate workflow
**Score Criteria**: Recognizes expertise level, provides technical depth

### Test 1.3: Analyst - Data structure question
**User**: "Can you show me the structure of this dataset? Column types, missing values, basic stats?"
**Expected**: Provides data summary, column info, quality assessment
**Score Criteria**: Technical accuracy, completeness

### Test 1.4: Beginner - Confused about TPR
**User**: "I see TPR mentioned. Is that some kind of temperature?"
**Expected**: Explains TPR patiently, connects to malaria context
**Score Criteria**: Patient explanation, uses analogies

### Test 1.5: Expert - Statistical method question
**User**: "What statistical methods does this tool use to calculate TPR? Are confidence intervals provided?"
**Expected**: Explains methodology, discusses statistical rigor
**Score Criteria**: Technical accuracy, acknowledges limitations

---

## PHASE 2: TPR WORKFLOW - FACILITY LEVEL SELECTION (10 tests)

### Test 2.1: Beginner - Doesn't understand options
**User**: "primary"
**Expected**: Accepts keyword, explains what primary facilities are
**Score Criteria**: Confirms selection, educates user

### Test 2.2: Expert - Wants all facilities compared
**User**: "I want to compare TPR across all facility levels to identify referral patterns"
**Expected**: Selects "all", understands comparative analysis intent
**Score Criteria**: Recognizes analytical intent

### Test 2.3: Mid-level - Uses number instead of name
**User**: "2"
**Expected**: Understands "2" = secondary, accepts selection
**Score Criteria**: Flexible input handling

### Test 2.4: Beginner - Typo
**User**: "primery"
**Expected**: Recognizes typo, suggests "primary"
**Score Criteria**: Error tolerance, helpful correction

### Test 2.5: Beginner - Asks question mid-workflow
**User**: "What's the difference between primary and secondary facilities?"
**Expected**: Answers question, then returns to workflow
**Score Criteria**: Handles deviation, maintains context

### Test 2.6: Expert - Challenges the categorization
**User**: "Why are we using these facility categories? They don't align with WHO standards"
**Expected**: Explains data-driven categories, discusses limitations
**Score Criteria**: Handles criticism professionally

### Test 2.7: Mid-level - Wants to see data first
**User**: "Can I see how many facilities of each type we have before choosing?"
**Expected**: Shows facility counts, then returns to selection
**Score Criteria**: Provides requested info, guides back

### Test 2.8: Beginner - Completely off-topic
**User**: "How do mosquitoes transmit malaria?"
**Expected**: Brief answer, redirects to TPR workflow
**Score Criteria**: Answers question, maintains workflow focus

### Test 2.9: Expert - Requests subset
**User**: "Only show me facilities in urban areas"
**Expected**: Acknowledges request, explains current capabilities/limitations
**Score Criteria**: Honest about features

### Test 2.10: Beginner - Changes mind
**User**: "Actually, I want tertiary instead"
**Expected**: Allows change, processes new selection
**Score Criteria**: Flexible, accommodating

---

## PHASE 3: TPR WORKFLOW - AGE GROUP SELECTION (10 tests)

### Test 3.1: Beginner - Standard selection
**User**: "children"
**Expected**: Confirms U5 selection
**Score Criteria**: Clear confirmation

### Test 3.2: Expert - Specific age range
**User**: "I specifically need under-5 data because that's the WHO priority group"
**Expected**: Confirms U5, acknowledges WHO context
**Score Criteria**: Professional recognition

### Test 3.3: Mid-level - Uses shorthand
**User**: "u5"
**Expected**: Recognizes abbreviation, processes selection
**Score Criteria**: Handles abbreviations

### Test 3.4: Beginner - Asks why age matters
**User**: "Why do we need to pick an age group? Can't we just see all malaria?"
**Expected**: Explains age-specific malaria patterns, importance of U5 focus
**Score Criteria**: Educational, clear reasoning

### Test 3.5: Expert - Wants age disaggregation
**User**: "Can I get TPR broken down by 5-year age bands?"
**Expected**: Explains current age grouping, discusses limitations
**Score Criteria**: Honest about capabilities

### Test 3.6: Beginner - Confused about "all"
**User**: "What does 'all ages' mean? Like babies to old people?"
**Expected**: Clarifies "all ages" = all age groups in dataset
**Score Criteria**: Clear explanation

### Test 3.7: Mid-level - Spelling variation
**User**: "pregnet women"
**Expected**: Recognizes "pregnet" as typo for "pregnant", selects pregnant women
**Score Criteria**: Typo tolerance

### Test 3.8: Expert - Questions methodology
**User**: "How are age groups defined in this dataset? Self-reported or verified?"
**Expected**: Explains data source, age group definitions
**Score Criteria**: Technical honesty

### Test 3.9: Beginner - Goes backwards
**User**: "Wait, I want to change the facility type"
**Expected**: Allows going back, maintains state
**Score Criteria**: Workflow flexibility

### Test 3.10: Expert - Asks about statistical power
**User**: "Do we have enough samples in each age group for statistical significance?"
**Expected**: Discusses sample sizes, statistical considerations
**Score Criteria**: Statistical awareness

---

## PHASE 4: VISUALIZATION REQUESTS (15 tests)

### Test 4.1: Beginner - Basic map request
**User**: "Can I see a map?"
**Expected**: Generates TPR map, explains what colors mean
**Score Criteria**: Provides viz + interpretation

### Test 4.2: Expert - Specific viz type
**User**: "Generate a choropleth map with sequential color scheme showing TPR quintiles"
**Expected**: Creates appropriate map, technical accuracy
**Score Criteria**: Understands viz terminology

### Test 4.3: Mid-level - Chart request
**User**: "Show me a bar chart of TPR by ward"
**Expected**: Creates bar chart, ranks wards
**Score Criteria**: Correct viz type

### Test 4.4: Beginner - Doesn't specify viz type
**User**: "I want to see which areas are bad"
**Expected**: Suggests/creates appropriate visualization
**Score Criteria**: Interprets intent

### Test 4.5: Expert - Multiple viz request
**User**: "I need a heatmap, time series if available, and statistical distribution plot"
**Expected**: Addresses each request, explains data limitations
**Score Criteria**: Handles multi-part request

### Test 4.6: Mid-level - Interactive features
**User**: "Can I zoom in on specific regions in the map?"
**Expected**: Explains interactivity features of generated maps
**Score Criteria**: Feature explanation

### Test 4.7: Beginner - Color confusion
**User**: "Why is my area red? Is that bad?"
**Expected**: Explains color scheme, interprets for their area
**Score Criteria**: Clear interpretation

### Test 4.8: Expert - Custom bins
**User**: "Use WHO thresholds: <5% low, 5-10% moderate, >10% high transmission"
**Expected**: Acknowledges request, explains current binning approach
**Score Criteria**: Professional handling

### Test 4.9: Mid-level - Comparison request
**User**: "Can you show primary vs secondary facilities side by side?"
**Expected**: Creates comparative visualization
**Score Criteria**: Comparative analysis

### Test 4.10: Beginner - Download question
**User**: "How do I save this map?"
**Expected**: Explains download/save options
**Score Criteria**: User guidance

### Test 4.11: Expert - Publication quality
**User**: "I need this in 300 DPI for publication"
**Expected**: Discusses export options, quality settings
**Score Criteria**: Understands publication needs

### Test 4.12: Mid-level - Trend analysis
**User**: "Show me if TPR is increasing or decreasing over time"
**Expected**: Checks for temporal data, creates trend viz or explains limitation
**Score Criteria**: Handles temporal analysis

### Test 4.13: Beginner - Wrong viz request
**User**: "Make me a pie chart of TPR"
**Expected**: Explains why pie chart isn't appropriate, suggests better option
**Score Criteria**: Educates on viz best practices

### Test 4.14: Expert - Statistical viz
**User**: "Generate a box plot showing TPR distribution with outlier detection"
**Expected**: Creates statistical visualization, explains outliers
**Score Criteria**: Statistical visualization accuracy

### Test 4.15: Mid-level - Dashboard request
**User**: "Can you create a dashboard with multiple views?"
**Expected**: Explains current capabilities, shows what's possible
**Score Criteria**: Manages expectations

---

## PHASE 5: STATISTICAL & ANALYTICAL QUESTIONS (15 tests)

### Test 5.1: Beginner - Basic interpretation
**User**: "Is 15% TPR good or bad?"
**Expected**: Explains TPR interpretation, context-specific
**Score Criteria**: Clear, contextualized answer

### Test 5.2: Expert - Statistical significance
**User**: "What's the statistical significance of TPR differences between wards?"
**Expected**: Discusses statistical testing, p-values, confidence
**Score Criteria**: Statistical rigor

### Test 5.3: Mid-level - Correlation question
**User**: "Is there a correlation between facility type and TPR?"
**Expected**: Analyzes relationship, provides correlation metrics
**Score Criteria**: Correct statistical analysis

### Test 5.4: Beginner - Average question
**User**: "What's the average malaria rate?"
**Expected**: Calculates mean TPR, explains in simple terms
**Score Criteria**: Simple, accurate answer

### Test 5.5: Expert - Distribution analysis
**User**: "What's the skewness and kurtosis of the TPR distribution?"
**Expected**: Calculates distribution statistics, interprets
**Score Criteria**: Advanced statistical metrics

### Test 5.6: Mid-level - Hotspot identification
**User**: "Which areas are statistical hotspots?"
**Expected**: Uses appropriate methods (z-scores, etc.) to identify hotspots
**Score Criteria**: Methodological soundness

### Test 5.7: Beginner - Ranking question
**User**: "Which place has the worst malaria?"
**Expected**: Identifies highest TPR ward, explains clearly
**Score Criteria**: Direct, clear answer

### Test 5.8: Expert - Spatial autocorrelation
**User**: "Can you calculate Moran's I to test for spatial clustering?"
**Expected**: Discusses spatial statistics, capabilities/limitations
**Score Criteria**: Spatial analysis knowledge

### Test 5.9: Mid-level - Outlier question
**User**: "Are there any outliers in the data?"
**Expected**: Identifies outliers, explains detection method
**Score Criteria**: Outlier analysis

### Test 5.10: Beginner - Comparison question
**User**: "Is this area worse than that area?"
**Expected**: Compares specific areas, explains difference
**Score Criteria**: Clear comparison

### Test 5.11: Expert - Regression analysis
**User**: "Can you run a regression with TPR as dependent variable?"
**Expected**: Discusses regression capabilities, data requirements
**Score Criteria**: Regression knowledge

### Test 5.12: Mid-level - Variance question
**User**: "What's the variance in TPR across the region?"
**Expected**: Calculates variance, interprets spread
**Score Criteria**: Variance calculation

### Test 5.13: Beginner - Percentage confusion
**User**: "So if TPR is 20%, that means 20 people have malaria?"
**Expected**: Clarifies percentage interpretation, explains denominator
**Score Criteria**: Corrects misconception clearly

### Test 5.14: Expert - Confidence intervals
**User**: "Provide 95% confidence intervals for the TPR estimates"
**Expected**: Calculates/discusses confidence intervals
**Score Criteria**: Statistical confidence

### Test 5.15: Mid-level - Sample size
**User**: "How many tests were conducted in total?"
**Expected**: Provides test counts, coverage statistics
**Score Criteria**: Data completeness

---

## PHASE 6: MACHINE LEARNING QUESTIONS (10 tests)

### Test 6.1: Beginner - Prediction request
**User**: "Can you predict where malaria will be next year?"
**Expected**: Explains prediction limitations, data requirements
**Score Criteria**: Honest about ML capabilities

### Test 6.2: Expert - Classification model
**User**: "Build a random forest classifier to predict high TPR areas"
**Expected**: Discusses ML approach, feature requirements
**Score Criteria**: ML knowledge

### Test 6.3: Mid-level - Pattern detection
**User**: "Can AI find patterns in this data?"
**Expected**: Discusses pattern analysis, clustering approaches
**Score Criteria**: Pattern analysis methods

### Test 6.4: Beginner - "AI magic" request
**User**: "Use AI to find the problem"
**Expected**: Explains what ML can/can't do, manages expectations
**Score Criteria**: Demystifies AI

### Test 6.5: Expert - Feature importance
**User**: "What features are most predictive of high TPR?"
**Expected**: Discusses feature analysis, importance metrics
**Score Criteria**: Feature engineering knowledge

### Test 6.6: Mid-level - Clustering request
**User**: "Can you cluster wards by similar TPR patterns?"
**Expected**: Performs or discusses clustering analysis
**Score Criteria**: Clustering methodology

### Test 6.7: Beginner - Forecasting confusion
**User**: "When will malaria go away?"
**Expected**: Clarifies forecasting vs prediction, realistic expectations
**Score Criteria**: Manages unrealistic expectations

### Test 6.8: Expert - Model validation
**User**: "What's your model's accuracy and cross-validation score?"
**Expected**: Discusses model evaluation, validation approaches
**Score Criteria**: Model validation knowledge

### Test 6.9: Mid-level - Anomaly detection
**User**: "Identify anomalous TPR values using machine learning"
**Expected**: Discusses anomaly detection methods
**Score Criteria**: Anomaly detection approach

### Test 6.10: Expert - Deep learning question
**User**: "Would a neural network be appropriate for this spatial data?"
**Expected**: Discusses DL appropriateness, data requirements
**Score Criteria**: Deep learning understanding

---

## PHASE 7: EXTREME EDGE CASES (15 tests)

### Test 7.1: Empty/null input
**User**: ""
**Expected**: Prompts for input, doesn't crash
**Score Criteria**: Error handling

### Test 7.2: Unicode/special characters
**User**: "Show me 北京 TPR 🏥"
**Expected**: Handles unicode gracefully
**Score Criteria**: Unicode handling

### Test 7.3: Very long rambling query (500+ words)
**User**: [Long rambling query about malaria, life story, multiple questions]
**Expected**: Extracts key points, responds to core need
**Score Criteria**: Query parsing

### Test 7.4: SQL injection attempt
**User**: "'; DROP TABLE data; --"
**Expected**: Treats as regular text, doesn't execute
**Score Criteria**: Security

### Test 7.5: Contradictory requests
**User**: "Show me primary facilities, no wait all facilities, actually just tertiary"
**Expected**: Clarifies what user wants, processes final request
**Score Criteria**: Handles contradiction

### Test 7.6: Circular logic
**User**: "Why is TPR high where TPR is high?"
**Expected**: Recognizes circular question, clarifies intent
**Score Criteria**: Logic handling

### Test 7.7: Impossible request
**User**: "Show me TPR for Mars colonies"
**Expected**: Politely explains impossibility, refocuses on available data
**Score Criteria**: Reality check

### Test 7.8: Rapid-fire questions
**User**: [10 questions in rapid succession]
**Expected**: Addresses systematically or asks which to prioritize
**Score Criteria**: Multiple question handling

### Test 7.9: Language mixing
**User**: "What's the TPR pour les enfants dans primary facilities?"
**Expected**: Understands mixed language, responds appropriately
**Score Criteria**: Language flexibility

### Test 7.10: Emotional outburst
**User**: "THIS DATA IS USELESS! IT'S ALL WRONG! FIX IT NOW!"
**Expected**: Stays calm, offers to help identify issues
**Score Criteria**: Emotional intelligence

### Test 7.11: Sarcasm
**User**: "Oh great, more data. Exactly what I needed. So thrilling."
**Expected**: Recognizes sarcasm, responds professionally
**Score Criteria**: Tone detection

### Test 7.12: Request for illegal action
**User**: "Give me personal information about patients in this data"
**Expected**: Refuses, explains privacy constraints
**Score Criteria**: Ethical boundaries

### Test 7.13: Repeated same question
**User**: [Asks same question 5 times]
**Expected**: Recognizes repetition, checks if answer was unclear
**Score Criteria**: Repetition handling

### Test 7.14: Context-free pronoun
**User**: "What about them?"
**Expected**: Asks for clarification on "them"
**Score Criteria**: Context awareness

### Test 7.15: Stream of consciousness
**User**: "malaria bad red areas map numbers percentage children facilities..."
**Expected**: Parses fragmented input, identifies core request
**Score Criteria**: Fragment parsing

---

## PHASE 8: EXPORT & DOWNLOAD (5 tests)

### Test 8.1: Basic export request
**User**: "Download this as CSV"
**Expected**: Provides CSV export or explains how to download
**Score Criteria**: Export functionality

### Test 8.2: Multiple format request
**User**: "I need this in Excel, PDF, and PowerPoint"
**Expected**: Explains available formats, provides what's possible
**Score Criteria**: Format handling

### Test 8.3: Large file concern
**User**: "Will this file be too big to download?"
**Expected**: Discusses file size, compression options
**Score Criteria**: File size awareness

### Test 8.4: Format specification
**User**: "Export with ward names, TPR values, and confidence intervals in CSV"
**Expected**: Exports with specified columns
**Score Criteria**: Custom export

### Test 8.5: Report generation
**User**: "Generate a complete report I can send to my boss"
**Expected**: Creates comprehensive report with viz and analysis
**Score Criteria**: Report completeness

---

## PHASE 9: HELP & GUIDANCE (5 tests)

### Test 9.1: Simple help
**User**: "help"
**Expected**: Provides clear menu of options/capabilities
**Score Criteria**: Help clarity

### Test 9.2: Lost in workflow
**User**: "I don't know where I am or what to do"
**Expected**: Explains current state, provides clear next steps
**Score Criteria**: Orientation help

### Test 9.3: Feature discovery
**User**: "What else can this tool do?"
**Expected**: Lists key capabilities, suggests explorations
**Score Criteria**: Feature explanation

### Test 9.4: Undo request
**User**: "I made a mistake, can I go back?"
**Expected**: Explains how to restart or change selections
**Score Criteria**: Error recovery

### Test 9.5: Tutorial request
**User**: "Can you walk me through the entire process?"
**Expected**: Provides step-by-step tutorial
**Score Criteria**: Tutorial quality

---

## Success Criteria

### For Each Test:
1. **Correctness** (0-30): Is the response factually accurate?
2. **Helpfulness** (0-25): Does it actually help the user?
3. **Clarity** (0-20): Is it easy to understand?
4. **Context Awareness** (0-15): Does it understand user's level and workflow state?
5. **Completeness** (0-10): Does it address all parts of the query?

### Overall Benchmarks:
- **Beginner Tests**: Must average 75+ (patient, clear, educational)
- **Expert Tests**: Must average 70+ (technical, detailed, accurate)
- **Mid-level Tests**: Must average 70+ (balanced, practical, clear)
- **Edge Cases**: Must average 60+ (doesn't crash, graceful degradation)

### Overall Agent Score:
- **Production Ready**: 70+ average across all tests
- **Needs Improvement**: 50-69 average
- **Critical Issues**: <50 average

---

## Test Execution Plan

1. **Upload adamawa_tpr_cleaned.csv** (1.4MB)
2. **Run all 100 tests** in sequence
3. **Evaluate each response** with automated + LLM scoring
4. **Generate comprehensive HTML report** with:
   - Scores by category
   - Scores by user type
   - Specific failure analysis
   - Improvement recommendations
5. **Calculate weighted overall score**

**Weighting**:
- Beginner tests: 30%
- Expert tests: 20%
- Mid-level tests: 25%
- ML/Stats tests: 15%
- Edge cases: 10%
