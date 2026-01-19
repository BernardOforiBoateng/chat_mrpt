#!/usr/bin/env python3
"""
Test Arena Integration with Real Session Data
Uses actual session data from Adamawa TPR analysis
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

# Import Arena components
from app.core.arena_trigger_detector import ConversationalArenaTrigger
from app.core.arena_data_context import ArenaDataContextManager
from app.core.arena_prompt_builder import ModelSpecificPromptBuilder
from app.core.enhanced_arena_manager import EnhancedArenaManager

# Use real session from Adamawa analysis
SESSION_ID = '8d9f54ce-6ddf-4dd2-8895-b1f646877ef5'
SESSION_PATH = f'/home/ec2-user/ChatMRPT/instance/uploads/{SESSION_ID}'

def test_trigger_detection():
    """Test trigger detection with real session context."""
    print("\n=== Testing Trigger Detection ===")
    
    trigger = ConversationalArenaTrigger(SESSION_ID)
    
    # Build context from real session
    context = {
        'analysis_complete': True,  # .analysis_complete file exists
        'tpr_workflow_complete': True,  # .tpr_complete file exists
        'csv_loaded': True,
        'shapefile_loaded': True,
        'statistics': {}
    }
    
    # Load real statistics from the data
    try:
        composite_df = pd.read_csv(os.path.join(SESSION_PATH, 'analysis_composite_scores.csv'))
        risk_dist = composite_df['risk_category'].value_counts().to_dict() if 'risk_category' in composite_df.columns else {}
        
        context['statistics']['risk_distribution'] = risk_dist
        print(f"Risk distribution: {risk_dist}")
        
        # Calculate TPR stats if available
        if 'test_positivity_rate' in composite_df.columns:
            tpr_mean = composite_df['test_positivity_rate'].mean()
            context['statistics']['tpr'] = {'mean': tpr_mean}
            print(f"TPR mean: {tpr_mean:.2f}%")
    except Exception as e:
        print(f"Error loading statistics: {e}")
    
    # Test various trigger phrases
    test_phrases = [
        "What does this mean?",
        "Explain these results",
        "Why is Adamawa showing high risk?",
        "What are the implications of these TPR values?",
        "Show me different perspectives",
        "What should we do next?"
    ]
    
    print("\nTesting trigger phrases:")
    for phrase in test_phrases:
        should_trigger, trigger_type, confidence = trigger.should_trigger(phrase, context)
        if should_trigger:
            print(f"✅ TRIGGERED: '{phrase[:30]}...' -> {trigger_type} (conf: {confidence:.2f})")
        else:
            print(f"❌ Not triggered: '{phrase[:30]}...'")
        
        # Reset cooldown for testing
        trigger.reset_cooldown()

def test_data_context_loading():
    """Test loading real session data context."""
    print("\n=== Testing Data Context Loading ===")
    
    # Mock Flask app context for testing
    from unittest.mock import Mock, patch
    
    with patch('app.core.arena_data_context.current_app') as mock_app:
        mock_app.instance_path = '/home/ec2-user/ChatMRPT/instance'
        
        manager = ArenaDataContextManager(SESSION_ID)
        context = manager.load_full_context()
        
        print("\nLoaded data files:")
        for file_type, data in context['data_files'].items():
            if isinstance(data, pd.DataFrame):
                print(f"  - {file_type}: {data.shape[0]} rows, {data.shape[1]} columns")
        
        print("\nAnalysis results:")
        for result_type, data in context['analysis_results'].items():
            if isinstance(data, pd.DataFrame):
                print(f"  - {result_type}: {data.shape[0]} rows")
        
        print("\nStatistics:")
        for stat_type, value in context['statistics'].items():
            if isinstance(value, dict):
                print(f"  - {stat_type}: {list(value.keys())}")
            else:
                print(f"  - {stat_type}: {value}")
        
        # Build prompt with real data
        prompt = manager.build_arena_prompt(
            "Explain the high risk areas in this analysis",
            "interpretation_request"
        )
        
        print(f"\nPrompt preview (first 500 chars):")
        print(prompt[:500] + "...")
        
        return context

def test_model_prompts(context):
    """Test model-specific prompt building with real data."""
    print("\n=== Testing Model-Specific Prompts ===")
    
    builder = ModelSpecificPromptBuilder()
    base_prompt = "Analyze the Adamawa TPR data and explain the risk patterns"
    
    models = ['phi3:mini', 'mistral:7b', 'qwen2.5:7b']
    
    for model in models:
        print(f"\n{model} prompt characteristics:")
        prompt = builder.build_prompt(model, base_prompt, context)
        
        # Check for model-specific elements
        if 'phi3' in model:
            if "The Analyst" in prompt:
                print("  ✅ Has Analyst role")
            if "PATTERN IDENTIFICATION" in prompt:
                print("  ✅ Has pattern identification focus")
            if "Step" in prompt:
                print("  ✅ Has step-by-step instructions")
                
        elif 'mistral' in model:
            if "The Statistician" in prompt:
                print("  ✅ Has Statistician role")
            if "STATISTICAL SIGNIFICANCE" in prompt:
                print("  ✅ Has statistical focus")
            if "Dataset size: n =" in prompt:
                print("  ✅ Has dataset statistics")
                
        elif 'qwen' in model:
            if "The Technician" in prompt:
                print("  ✅ Has Technician role")
            if "PRACTICAL INTERVENTIONS" in prompt:
                print("  ✅ Has implementation focus")
            if "Data Specifications" in prompt:
                print("  ✅ Has technical specifications")
        
        # Show temperature
        temp = builder.get_model_temperature(model)
        print(f"  Temperature: {temp}")

def test_integration():
    """Test the full integration with real data."""
    print("\n=== Testing Full Integration ===")
    
    # Check if analysis is complete
    if os.path.exists(os.path.join(SESSION_PATH, '.analysis_complete')):
        print("✅ Analysis is complete")
    else:
        print("❌ Analysis not complete")
        return
    
    # Load some actual data
    try:
        unified_df = pd.read_csv(os.path.join(SESSION_PATH, 'unified_dataset.csv'))
        print(f"\nUnified dataset: {unified_df.shape[0]} wards")
        
        # Show sample of high-risk wards
        if 'risk_category' in unified_df.columns:
            high_risk = unified_df[unified_df['risk_category'] == 'High']
            print(f"High-risk wards: {len(high_risk)}")
            
            if not high_risk.empty:
                print("\nSample high-risk wards:")
                for idx, row in high_risk.head(3).iterrows():
                    ward = row.get('ward', 'Unknown')
                    score = row.get('composite_score', 0)
                    print(f"  - {ward}: score={score:.3f}")
        
        # Check visualization files
        viz_path = os.path.join(SESSION_PATH, 'visualizations')
        if os.path.exists(viz_path):
            viz_files = os.listdir(viz_path)
            print(f"\nVisualizations created: {len(viz_files)}")
            for vf in viz_files[:3]:
                print(f"  - {vf}")
        
        # Check ITN distribution results
        itn_results_path = os.path.join(SESSION_PATH, 'itn_distribution_results.json')
        if os.path.exists(itn_results_path):
            with open(itn_results_path, 'r') as f:
                itn_data = json.load(f)
                total_nets = itn_data.get('summary', {}).get('total_nets_needed', 0)
                print(f"\nITN Distribution: {total_nets:,} nets needed")
    
    except Exception as e:
        print(f"Error loading data: {e}")

def main():
    """Run all tests with real session data."""
    print("="*60)
    print(f"ARENA INTEGRATION TEST WITH REAL SESSION DATA")
    print(f"Session ID: {SESSION_ID}")
    print("="*60)
    
    # Run tests
    test_trigger_detection()
    context = test_data_context_loading()
    
    if context:
        test_model_prompts(context)
    
    test_integration()
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)

if __name__ == "__main__":
    main()
