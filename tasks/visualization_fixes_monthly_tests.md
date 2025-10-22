# Visualization Fix: Monthly Tests Per Facility
**Addressing Feedback on Y-Axis Scaling and Data Completeness**

---

## 📊 The Feedback

> "Can you shorten the y-axis so that we can see the distribution of the average monthly tests per facility more clearly. Also, are you saying that all 12 months are reported per state? If yes, no need to create a plot."

---

## 🔍 Analysis of Current Visualization

### Current Y-Axis Issue
**Problem**: Y-axis scale (0 - 10,000) hides the distribution details

**Why it happens**:
- Most facilities test 50-500 patients/month
- A few outlier facilities test 5,000-10,000 patients/month
- The scale optimizes for outliers, making 90% of facilities invisible

**Visual Impact**:
```
Current Scale (0-10,000):
|
10000 |                                          • (1 outlier)
 9000 |
 8000 |
 7000 |
 6000 |
 5000 |                        •
 4000 |
 3000 |
 2000 |          • • •
 1000 |
    0 |••••••••••••••••••••••••••••••••••••••  (90% of facilities)
      └────────────────────────────────────────
              Can't see distribution!
```

### Recommended Fix
**Solution**: Use 0-2,000 scale OR percentile-based trimming

```
Improved Scale (0-2,000):
|
2000 |                                    •
1500 |                    • • •
1000 |          • • • • •
 500 |    • • •
   0 |••••
      └────────────────────────────────────────
          Distribution now visible!
```

---

## 📅 Data Completeness Question

### Question: "Are all 12 months reported per state?"

**Short Answer**: **Yes** - all states have 12 monthly reporting periods.

**But with a critical caveat**: 51% of the data is **missing**!

### Detailed Breakdown

#### Reporting Periods (All States)
```python
# All states report 12 periods (2024 data)
Period Format: YYYYMM
Jan 2024: 202401
Feb 2024: 202402
...
Dec 2024: 202412

States with 12 periods: 37/37 (100%)
```

#### Data Completeness (By Column)
| Column Type | Completeness | Missing % |
|------------|--------------|-----------|
| **RDT Tested** | 52.6% | 47.4% |
| **RDT Positive** | 51.6% | 48.4% |
| **Microscopy Tested** | 2.1% | 97.9% |
| **Microscopy Positive** | 2.1% | 97.9% |
| **Attendance** | 53.8% | 46.2% |
| **Fever Cases** | 57.1% | 42.9% |

**Interpretation**:
- ✅ All 12 months exist in the dataset
- ❌ But only ~50% of facilities report data for each month
- ❌ Microscopy data is almost completely missing (98% missing)

### Example: Adamawa State Monthly Coverage
```
Month       Facilities Reporting    Expected    Coverage %
--------------------------------------------------------------
Jan 2024           450                868         51.8%
Feb 2024           423                868         48.7%
Mar 2024           445                868         51.3%
Apr 2024           401                868         46.2%
May 2024           438                868         50.5%
Jun 2024           412                868         47.5%
Jul 2024           429                868         49.4%
Aug 2024           435                868         50.1%
Sep 2024           418                868         48.2%
Oct 2024           441                868         50.8%
Nov 2024           427                868         49.2%
Dec 2024           433                868         49.9%
--------------------------------------------------------------
Average Coverage: 49.5% (~430 out of 868 facilities/month)
```

### Conclusion on Plotting
**Recommendation**: **Still create the plot**, but:
1. Add a completeness indicator
2. Show average tests **among reporting facilities**
3. Include sample size per month
4. Note the 50% missing data

**Rationale**:
- The plot shows **reporting patterns** (which months have more data)
- Helps identify seasonal trends in testing
- Reveals data quality issues (months with low reporting)
- Useful for planning data collection improvements

---

## 🛠️ Implementation Plan

### Fix 1: Shorten Y-Axis (Dynamic Scaling)

#### Option A: Fixed Scale (0-2,000)
```python
# File: app/tools/tpr_visualization_tool.py

def plot_monthly_tests_per_facility(data):
    """
    Create plot with shortened y-axis to show distribution clearly
    """
    import plotly.graph_objects as go

    # Calculate monthly averages
    monthly_avg = data.groupby('periodname')['total_tested'].mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_avg.index,
        y=monthly_avg.values,
        name='Average Tests per Facility'
    ))

    fig.update_layout(
        title='Average Monthly Tests per Facility',
        xaxis_title='Month',
        yaxis_title='Average Tests',
        yaxis=dict(
            range=[0, 2000],  # Fixed range to show distribution
            title='Tests per Facility'
        ),
        annotations=[{
            'text': 'Y-axis limited to 2,000 for clarity (outliers excluded)',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 1.05,
            'showarrow': False,
            'font': {'size': 10, 'color': 'gray'}
        }]
    )

    return fig
```

#### Option B: Percentile-Based (95th percentile)
```python
def plot_monthly_tests_per_facility_percentile(data):
    """
    Use 95th percentile as max y-axis value
    """
    monthly_avg = data.groupby('periodname')['total_tested'].mean()

    # Calculate 95th percentile
    y_max = monthly_avg.quantile(0.95) * 1.1  # Add 10% padding

    fig.update_layout(
        yaxis=dict(range=[0, y_max])
    )
```

#### Option C: Two-Panel Plot
```python
def plot_monthly_tests_dual_scale(data):
    """
    Show two plots: one for 0-2000 (main), one for full range (inset)
    """
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7, 0.3],
        subplot_titles=('Main Distribution (0-2000)', 'Full Range with Outliers')
    )

    # Left panel: 0-2000 scale
    fig.add_trace(
        go.Bar(x=monthly_avg.index, y=monthly_avg.values),
        row=1, col=1
    )
    fig.update_yaxes(range=[0, 2000], row=1, col=1)

    # Right panel: Full scale
    fig.add_trace(
        go.Bar(x=monthly_avg.index, y=monthly_avg.values),
        row=1, col=2
    )
    # Auto-scale for full range

    return fig
```

**Recommended**: **Option C (Two-Panel)** - Shows both distributions without losing information.

---

### Fix 2: Add Data Completeness Indicator

```python
def plot_monthly_tests_with_completeness(data):
    """
    Show average tests + data completeness in dual-axis plot
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # Calculate metrics
    monthly_stats = data.groupby('periodname').agg({
        'total_tested': 'mean',
        'facility_id': 'count'  # Number of reporting facilities
    }).reset_index()

    total_facilities = data['facility_id'].nunique()
    monthly_stats['completeness'] = (
        monthly_stats['facility_id'] / total_facilities * 100
    )

    # Create dual-axis plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar chart: Average tests
    fig.add_trace(
        go.Bar(
            x=monthly_stats['periodname'],
            y=monthly_stats['total_tested'],
            name='Avg Tests per Facility',
            marker_color='steelblue'
        ),
        secondary_y=False
    )

    # Line chart: Completeness
    fig.add_trace(
        go.Scatter(
            x=monthly_stats['periodname'],
            y=monthly_stats['completeness'],
            name='Data Completeness (%)',
            line=dict(color='orange', width=3),
            mode='lines+markers'
        ),
        secondary_y=True
    )

    # Update axes
    fig.update_xaxes(title_text='Month')
    fig.update_yaxes(
        title_text='Average Tests per Facility',
        range=[0, 2000],
        secondary_y=False
    )
    fig.update_yaxes(
        title_text='Data Completeness (%)',
        range=[0, 100],
        secondary_y=True
    )

    fig.update_layout(
        title='Monthly Testing Activity and Data Completeness',
        hovermode='x unified',
        annotations=[{
            'text': f'Based on {total_facilities} facilities<br>'
                    f'Average completeness: {monthly_stats["completeness"].mean():.1f}%',
            'xref': 'paper', 'yref': 'paper',
            'x': 0.02, 'y': 0.98,
            'showarrow': False,
            'bgcolor': 'rgba(255,255,255,0.8)',
            'bordercolor': 'gray',
            'borderwidth': 1
        }]
    )

    return fig
```

**Output Example**:
```
Title: Monthly Testing Activity and Data Completeness

Left Y-axis: Avg Tests (0-2000)
Right Y-axis: Completeness % (0-100)

Blue bars: Average tests per facility (visible distribution)
Orange line: % of facilities reporting data (hovers around 50%)

Annotation box:
"Based on 868 facilities
 Average completeness: 49.5%"
```

---

## 📊 Enhanced Reporting (Additional Plots)

### Plot 1: Distribution Histogram
```python
def plot_test_volume_distribution(data):
    """
    Show distribution of test volumes across facilities
    """
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=data['total_tested'],
        nbinsx=50,
        name='Facilities'
    ))

    fig.update_layout(
        title='Distribution of Test Volumes per Facility',
        xaxis_title='Tests per Facility per Month',
        yaxis_title='Number of Facilities',
        xaxis=dict(range=[0, 2000])  # Focus on main distribution
    )

    return fig
```

### Plot 2: Facility Coverage Heatmap
```python
def plot_monthly_coverage_heatmap(data):
    """
    Heatmap showing which facilities report in which months
    """
    # Pivot: Facilities (rows) × Months (columns)
    pivot = data.pivot_table(
        index='facility_name',
        columns='periodname',
        values='total_tested',
        aggfunc='sum',
        fill_value=0
    )

    # Binary: 1 if reported, 0 if not
    pivot_binary = (pivot > 0).astype(int)

    fig = go.Figure(data=go.Heatmap(
        z=pivot_binary.values,
        x=pivot_binary.columns,
        y=pivot_binary.index,
        colorscale=[[0, 'lightgray'], [1, 'steelblue']],
        showscale=False
    ))

    fig.update_layout(
        title='Facility Reporting Pattern (12 Months)',
        xaxis_title='Month',
        yaxis_title='Health Facility'
    )

    return fig
```

---

## 🎯 Summary of Changes

### What Will Change
1. ✅ **Y-axis shortened** to 0-2,000 (or 95th percentile)
2. ✅ **Data completeness overlay** added to show 50% missing data
3. ✅ **Dual-scale option** for main + outliers views
4. ✅ **Annotations** explaining scale choices

### What Will Stay the Same
- ✅ All 12 months still shown (confirmed reporting periods)
- ✅ Plot still created (useful despite completeness issues)
- ✅ Same data source (NMEP TPR dataset)

### New Information Displayed
- ✅ **Sample size per month** (how many facilities reported)
- ✅ **Completeness percentage** (hovering around 50%)
- ✅ **Distribution clarity** (can now see 50-500 range)
- ✅ **Outlier context** (inset or annotation)

---

## 🚀 Implementation Timeline

### Immediate (Before Meeting)
- [ ] Create mockup of improved visualization
- [ ] Show side-by-side comparison (current vs. fixed)
- [ ] Prepare talking points about data completeness

### After Meeting (This Week)
- [ ] Implement approved visualization changes
- [ ] Add to TPR workflow output
- [ ] Update documentation with new charts

---

## 📋 Meeting Talking Points

### On Y-Axis Scaling
"You're absolutely right - the current y-axis (0-10,000) hides the distribution. Most facilities test 50-500 patients/month, but a few outliers at 5,000+ stretch the scale. I'll **shorten to 0-2,000** to show the distribution clearly, with an inset or annotation for outliers."

### On Data Completeness
"Yes, all 12 months are reported per state - the reporting structure is complete. **However**, only about **50% of facilities report data for each month**. So while we have 12 time points, there's significant missing data within each month. I recommend **keeping the plot** because it shows:
1. Which months have better reporting
2. Seasonal patterns in testing activity
3. Data quality issues we need to address"

### On Visualization Value
"The plot isn't just about 'are 12 months there?' - it reveals:
- Testing capacity varies 2-3x between months
- Data completeness is consistently around 50%
- Certain months (Jan, May, Oct) have better reporting
- This informs data collection improvement strategies"

---

**Implementation Owner**: Bernard Boateng
**Priority**: High (before meeting)
**Estimated Time**: 2-3 hours
