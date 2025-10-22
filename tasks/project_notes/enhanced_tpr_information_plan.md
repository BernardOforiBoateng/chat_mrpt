# Enhanced TPR Information Display Plan

## Date: 2025-08-13

## Overview
The production TPR module provided rich contextual information at each decision point, helping users make informed choices. The current Data Analysis V3 just lists options without context. We need to enhance it to provide detailed statistics and insights.

## What Production TPR Provided

### 1. Initial Data Summary (After Upload)
```
I've analyzed your NMEP TPR data file. Here's what I found:

**Geographic Coverage:**
- 3 states: Adamawa, Kwara, Osun
- 2,456 health facilities

**Time Period:**
- 6 months of data from Jan 2024 - Jun 2024

**Data Quality Overview:**
- Total tests performed: 45,678
- Test types: RDT (78%), Microscopy (22%)
- Missing data: 12% of facilities

**State-Level Statistics:**
State        | Facilities | Tests  | Avg TPR
-------------|------------|--------|---------
Adamawa      | 834        | 15,234 | 24.5%
Kwara        | 785        | 14,567 | 18.3%
Osun         | 837        | 15,877 | 21.2%

Which state would you like to analyze?
```

### 2. Age Group Selection (With Context)
```
**Age Group Analysis Options:**

1. **All Age Groups Combined** (Recommended)
   - 45,678 total tests across all ages
   - Most comprehensive view of malaria burden
   - Best for overall planning

2. **Under 5 Years**
   - 18,234 tests (39.9% of total)
   - Highest risk group (TPR: 32.4%)
   - Critical for child health interventions

3. **Over 5 Years**
   - 22,456 tests (49.1% of total)
   - Lower TPR (18.7%) but larger population
   - Important for community-wide strategies

4. **Pregnant Women**
   - 4,988 tests (10.9% of total)
   - Special vulnerable group (TPR: 28.1%)
   - Essential for maternal health programs

Which age group would you like to focus on?
```

### 3. Test Method Selection (With Statistics)
```
**Test Method Options for Under 5 Years:**

1. **RDT Only**
   - 14,234 tests available (78% of U5 tests)
   - Faster results, widely deployed
   - Coverage: 95% of facilities

2. **Microscopy Only**
   - 4,000 tests available (22% of U5 tests)
   - Gold standard, more accurate
   - Coverage: 45% of facilities (mainly secondary/tertiary)

3. **Combined (RDT + Microscopy)**
   - All 18,234 tests included
   - Most comprehensive analysis
   - Shows testing capacity variations

Which test method would you like to analyze?
```

### 4. Facility Level Selection (With Distribution)
```
**Facility Level Analysis for Adamawa State:**

1. **All Facilities** (Recommended)
   - 834 total facilities
   - Complete geographic coverage
   - Mix of urban (23%) and rural (77%)

2. **Primary Health Centers**
   - 687 facilities (82.4% of total)
   - Rural focus, community-level care
   - Average TPR: 26.3%

3. **Secondary Facilities**
   - 125 facilities (15.0% of total)
   - General hospitals, comprehensive care
   - Average TPR: 21.8%

4. **Tertiary Facilities**
   - 22 facilities (2.6% of total)
   - Teaching hospitals, specialized care
   - Average TPR: 18.5%

Which facility level would you like to analyze?
```

### 5. TPR Calculation Results (Rich Summary)
```
✅ **TPR Calculation Complete!**

**Analysis Summary for Adamawa State (Under 5, All Facilities):**

📊 **Overall Results:**
- Calculated TPR for 226 wards
- Average TPR: 32.4%
- Median TPR: 28.7%
- Standard Deviation: 12.3%

📈 **TPR Distribution:**
- Very Low (0-10%): 15 wards (6.6%)
- Low (10-20%): 38 wards (16.8%)
- Moderate (20-30%): 89 wards (39.4%)
- High (30-40%): 52 wards (23.0%)
- Very High (>40%): 32 wards (14.2%)

🏥 **Testing Coverage:**
- Wards with >100 tests: 145 (64.2%)
- Wards with 50-100 tests: 56 (24.8%)
- Wards with <50 tests: 25 (11.0%)

⚠️ **Data Quality:**
- High Quality (≥80% complete): 178 wards
- Medium Quality (50-79%): 35 wards
- Low Quality (<50%): 13 wards

🎯 **High-Risk Areas Identified:**
Top 5 Wards by TPR:
1. Gombi Ward A: 56.3% (245 tests)
2. Michika Central: 52.1% (189 tests)
3. Madagali North: 48.9% (312 tests)
4. Hong Urban: 47.2% (156 tests)
5. Mubi South: 45.8% (278 tests)

Would you like to proceed with risk analysis for intervention planning?
```

## Current Data Analysis V3 Display

### Current (Minimal Information)
```
Which age group should I focus on for the TPR calculation?

1. **All age groups combined** (default)
2. **Under 5 years**
3. **Over 5 years**
4. **Pregnant women**

Please let me know which option you'd prefer!
```

## Implementation Plan

### 1. Create Data Analyzer Component
```python
class TPRDataAnalyzer:
    """Analyze uploaded data to provide rich context."""
    
    def analyze_for_options(self, df: pd.DataFrame, option_type: str):
        """Generate statistics for each option type."""
        if option_type == 'age_group':
            return self._analyze_age_groups(df)
        elif option_type == 'test_method':
            return self._analyze_test_methods(df)
        elif option_type == 'facility_level':
            return self._analyze_facility_levels(df)
    
    def _analyze_age_groups(self, df):
        """Get statistics for each age group."""
        stats = {}
        
        # Under 5
        u5_cols = [col for col in df.columns if '<5' in col or 'u5' in col.lower()]
        if u5_cols:
            u5_tests = df[u5_cols].sum().sum()
            u5_positive = df[[c for c in u5_cols if 'positive' in c.lower()]].sum().sum()
            stats['under_5'] = {
                'tests': u5_tests,
                'percentage': (u5_tests / total_tests) * 100,
                'tpr': (u5_positive / u5_tests) * 100 if u5_tests > 0 else 0,
                'description': 'Highest risk group for severe malaria'
            }
        
        # Similar for other age groups...
        return stats
```

### 2. Enhance Message Generation
```python
def _generate_age_group_options(self, df):
    """Generate rich age group selection message."""
    analyzer = TPRDataAnalyzer()
    stats = analyzer.analyze_age_groups(df)
    
    message = "**Age Group Analysis Options:**\n\n"
    
    for idx, (group, data) in enumerate(stats.items(), 1):
        message += f"{idx}. **{group.replace('_', ' ').title()}**\n"
        message += f"   - {data['tests']:,} tests ({data['percentage']:.1f}% of total)\n"
        message += f"   - Average TPR: {data['tpr']:.1f}%\n"
        message += f"   - {data['description']}\n\n"
    
    message += "Which age group would you like to focus on?"
    return message
```

### 3. Add Summary Statistics
```python
def _generate_initial_summary(self, df):
    """Generate comprehensive initial data summary."""
    summary = DataProfiler.profile_dataset(df)
    
    # Add TPR-specific analysis
    tpr_stats = self._analyze_tpr_potential(df)
    
    message = "📊 **NMEP TPR Data Analysis Complete!**\n\n"
    
    # Geographic coverage
    if 'State' in df.columns:
        states = df['State'].unique()
        message += f"**Geographic Coverage:**\n"
        message += f"- {len(states)} states: {', '.join(states[:5])}\n"
        
    # Add facility counts
    if 'HealthFacility' in df.columns:
        message += f"- {df['HealthFacility'].nunique():,} health facilities\n"
    
    # Time period
    if any('month' in col.lower() for col in df.columns):
        message += f"\n**Time Period:**\n"
        # Extract and show time range
    
    # Data quality
    message += f"\n**Data Quality Overview:**\n"
    message += f"- Completeness: {100 - (df.isnull().sum().sum() / df.size * 100):.1f}%\n"
    
    # Test statistics
    test_cols = [c for c in df.columns if 'test' in c.lower()]
    if test_cols:
        total_tests = df[test_cols].sum().sum()
        message += f"- Total tests recorded: {total_tests:,}\n"
    
    return message
```

### 4. Add Distribution Analysis
```python
def _calculate_tpr_distribution(self, tpr_results):
    """Calculate TPR distribution for summary."""
    ranges = {
        'Very Low (0-10%)': 0,
        'Low (10-20%)': 0,
        'Moderate (20-30%)': 0,
        'High (30-40%)': 0,
        'Very High (>40%)': 0
    }
    
    for result in tpr_results:
        tpr = result['tpr_value']
        if tpr < 10:
            ranges['Very Low (0-10%)'] += 1
        elif tpr < 20:
            ranges['Low (10-20%)'] += 1
        # etc...
    
    return ranges
```

### 5. Add Ward Ranking
```python
def _get_high_risk_wards(self, tpr_results, top_n=5):
    """Identify highest risk wards."""
    sorted_wards = sorted(tpr_results, key=lambda x: x['tpr_value'], reverse=True)
    
    high_risk = []
    for ward in sorted_wards[:top_n]:
        high_risk.append({
            'name': ward['ward_name'],
            'tpr': ward['tpr_value'],
            'tests': ward['total_tests']
        })
    
    return high_risk
```

## Benefits of Enhanced Information

### For Users
1. **Informed Decisions**: Know exactly what each option means
2. **Context Awareness**: Understand data distribution before choosing
3. **Quality Indicators**: See data completeness and reliability
4. **Actionable Insights**: Get specific ward/facility recommendations

### For Analysis
1. **Better Targeting**: Focus on high-impact areas
2. **Data Quality**: Identify and handle low-quality data appropriately
3. **Comparison**: See how selections compare to overall data
4. **Validation**: Verify selections make sense given the data

## Integration with State Management

This enhanced information display will work perfectly with the state management plan:

1. **First Message**: Show comprehensive data summary
2. **Store Analysis**: Cache the analyzed statistics in state
3. **Progressive Disclosure**: Show relevant stats at each stage
4. **No Recalculation**: Reuse cached analysis for performance

## Success Metrics

- Users make selections faster (less confusion)
- Fewer "back" commands (users confident in choices)
- Higher completion rate for TPR workflow
- Better quality analysis (appropriate selections for data)

## Priority

**HIGH** - This directly improves user experience and decision quality. Should be implemented alongside state management for maximum impact.