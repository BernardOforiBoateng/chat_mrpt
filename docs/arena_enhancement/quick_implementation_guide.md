# Quick Implementation Guide
## Arena Mode Extension - Getting Started

---

## Immediate Next Steps

### Step 1: Create Context Extraction Module
```python
# app/core/arena_analysis_context.py

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ArenaAnalysisContext:
    """
    Extracts and formats analysis context for Arena model interpretation.
    """
    
    @staticmethod
    def extract_tpr_context(tpr_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from TPR analysis results."""
        try:
            context = {
                'analysis_type': 'test_positivity_rate',
                'summary': {
                    'overall_tpr': tpr_results.get('overall_tpr', 0),
                    'total_tests': tpr_results.get('total_tests', 0),
                    'positive_tests': tpr_results.get('positive_tests', 0),
                    'data_completeness': tpr_results.get('completeness', 0)
                },
                'geographic_breakdown': [],
                'temporal_trends': [],
                'data_quality_flags': []
            }
            
            # Add top 5 states/regions
            if 'by_state' in tpr_results:
                for state in tpr_results['by_state'][:5]:
                    context['geographic_breakdown'].append({
                        'name': state['name'],
                        'tpr': state['tpr'],
                        'tests': state['total_tests']
                    })
            
            # Add data quality indicators
            if tpr_results.get('completeness', 100) < 50:
                context['data_quality_flags'].append('Low data completeness')
            if tpr_results.get('outliers'):
                context['data_quality_flags'].append(f"{len(tpr_results['outliers'])} outliers detected")
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting TPR context: {e}")
            return {}
    
    @staticmethod
    def extract_risk_analysis_context(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from composite risk analysis."""
        try:
            context = {
                'analysis_type': 'composite_risk_scoring',
                'summary': {
                    'total_wards': len(analysis_results.get('ward_scores', [])),
                    'high_risk_count': 0,
                    'medium_risk_count': 0,
                    'low_risk_count': 0,
                    'scoring_method': analysis_results.get('method', 'unknown')
                },
                'top_risk_areas': [],
                'key_indicators': [],
                'recommendations': []
            }
            
            # Categorize risk levels
            for ward in analysis_results.get('ward_scores', []):
                score = ward.get('composite_score', 0)
                if score > 0.7:
                    context['summary']['high_risk_count'] += 1
                elif score > 0.4:
                    context['summary']['medium_risk_count'] += 1
                else:
                    context['summary']['low_risk_count'] += 1
            
            # Get top 10 high-risk areas
            sorted_wards = sorted(
                analysis_results.get('ward_scores', []),
                key=lambda x: x.get('composite_score', 0),
                reverse=True
            )
            
            for ward in sorted_wards[:10]:
                context['top_risk_areas'].append({
                    'name': ward.get('ward_name', 'Unknown'),
                    'score': ward.get('composite_score', 0),
                    'population': ward.get('population', 0)
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error extracting risk analysis context: {e}")
            return {}
    
    @staticmethod
    def build_interpretation_prompt(context: Dict[str, Any], task_type: str = 'interpret') -> str:
        """Build a comprehensive prompt for Arena models."""
        
        base_prompt = f"""
Analysis Type: {context.get('analysis_type', 'Unknown')}
Timestamp: {datetime.now().isoformat()}

Analysis Summary:
{json.dumps(context.get('summary', {}), indent=2)}
        """
        
        if task_type == 'interpret':
            base_prompt += """

As a malaria epidemiologist, provide:
1. Your interpretation of these results
2. Key insights for public health action  
3. Any concerns about the data or methodology
4. Three specific recommendations

Be concise but comprehensive.
            """
            
        elif task_type == 'explain':
            base_prompt += """

Explain these results to a non-technical audience:
1. What do these numbers mean in simple terms?
2. Why are these findings important?
3. What actions should be taken?

Use clear, accessible language.
            """
            
        elif task_type == 'validate':
            base_prompt += """

Critically evaluate this analysis:
1. Are the results statistically valid?
2. What are potential biases or limitations?
3. What additional analysis would strengthen conclusions?
4. Rate confidence level (Low/Medium/High) and explain why.
            """
            
        return base_prompt
```

### Step 2: Modify Analysis Pipeline to Trigger Arena
```python
# In app/analysis/pipeline.py, add after analysis completion:

from app.core.arena_analysis_context import ArenaAnalysisContext
from app.web.routes.arena_routes import trigger_arena_interpretation

def run_full_analysis_pipeline(...):
    # ... existing pipeline code ...
    
    # After analysis completes successfully
    if results and results.get('success'):
        # Check if user has Arena mode enabled
        if session_state.get('arena_interpretation_enabled', False):
            # Extract context for Arena
            context = ArenaAnalysisContext.extract_risk_analysis_context(results)
            
            # Trigger Arena interpretation in background
            trigger_arena_interpretation.delay(
                session_id=session_id,
                context=context,
                task_type='interpret'
            )
            
            # Add flag to results
            results['arena_interpretation_available'] = True
    
    return results
```

### Step 3: Add Frontend Trigger Button
```javascript
// app/static/js/arena_analysis.js

class ArenaAnalysisIntegration {
    constructor() {
        this.init();
    }
    
    init() {
        // Listen for analysis completion
        document.addEventListener('analysisComplete', (event) => {
            if (event.detail.arena_interpretation_available) {
                this.showArenaButton(event.detail.session_id);
            }
        });
    }
    
    showArenaButton(sessionId) {
        const container = document.getElementById('analysis-results');
        if (!container) return;
        
        const button = document.createElement('button');
        button.className = 'btn btn-primary arena-interpret-btn';
        button.innerHTML = `
            <span class="icon">🤖</span>
            <span>Get AI Interpretations (5 Models)</span>
        `;
        button.onclick = () => this.launchArenaInterpretation(sessionId);
        
        // Insert after results summary
        const summary = container.querySelector('.results-summary');
        if (summary) {
            summary.insertAdjacentElement('afterend', button);
        }
    }
    
    async launchArenaInterpretation(sessionId) {
        try {
            const response = await fetch('/api/arena/interpret-analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ session_id: sessionId })
            });
            
            const data = await response.json();
            if (data.battle_id) {
                // Redirect to Arena comparison page
                window.location.href = `/arena/battle/${data.battle_id}?type=interpretation`;
            }
        } catch (error) {
            console.error('Failed to launch Arena interpretation:', error);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new ArenaAnalysisIntegration();
});
```

### Step 4: Create New Arena Route
```python
# Add to app/web/routes/arena_routes.py

@arena_bp.route('/api/arena/interpret-analysis', methods=['POST'])
async def interpret_analysis():
    """Launch Arena interpretation of analysis results."""
    data = request.json
    session_id = data.get('session_id')
    
    # Get analysis results from session
    analysis_results = get_session_analysis_results(session_id)
    if not analysis_results:
        return jsonify({'error': 'No analysis results found'}), 404
    
    # Extract context based on analysis type
    context_extractor = ArenaAnalysisContext()
    
    if 'tpr' in analysis_results:
        context = context_extractor.extract_tpr_context(analysis_results)
    elif 'composite_scores' in analysis_results:
        context = context_extractor.extract_risk_analysis_context(analysis_results)
    else:
        context = {'summary': analysis_results}
    
    # Build interpretation prompt
    prompt = context_extractor.build_interpretation_prompt(
        context, 
        task_type='interpret'
    )
    
    # Create Arena battle with all 5 models
    arena_manager = current_app.arena_manager
    battle_id = str(uuid.uuid4())
    
    # Store battle with context
    battle = ProgressiveBattleSession(
        session_id=battle_id,
        user_message=prompt,
        all_models=['gpt-4o-mini', 'llama3.1:8b', 'mistral:7b', 'phi3:mini', 'gemma2:9b'],
        metadata={'type': 'analysis_interpretation', 'context': context}
    )
    
    await arena_manager.store_battle(battle)
    
    # Generate all responses in parallel
    responses = await arena_manager.generate_all_responses(battle_id)
    
    return jsonify({
        'battle_id': battle_id,
        'redirect_url': f'/arena/battle/{battle_id}?type=interpretation'
    })
```

---

## Testing the Enhancement

### Test Script
```python
# test_arena_interpretation.py

import asyncio
from app.core.arena_analysis_context import ArenaAnalysisContext

def test_context_extraction():
    # Mock TPR results
    tpr_results = {
        'overall_tpr': 70.5,
        'total_tests': 100000,
        'positive_tests': 70500,
        'completeness': 85.2,
        'by_state': [
            {'name': 'Kano', 'tpr': 75.3, 'total_tests': 15000},
            {'name': 'Lagos', 'tpr': 68.2, 'total_tests': 20000},
            {'name': 'Kaduna', 'tpr': 72.1, 'total_tests': 10000}
        ]
    }
    
    # Extract context
    context = ArenaAnalysisContext.extract_tpr_context(tpr_results)
    print("Extracted Context:")
    print(json.dumps(context, indent=2))
    
    # Build prompt
    prompt = ArenaAnalysisContext.build_interpretation_prompt(context, 'interpret')
    print("\nGenerated Prompt:")
    print(prompt)
    
    return context, prompt

async def test_arena_interpretation():
    context, prompt = test_context_extraction()
    
    # Simulate Arena battle
    print("\nSimulating Arena responses...")
    
    # This would normally call actual models
    print("Model A (GPT-4): [Interpretation would appear here]")
    print("Model B (Llama): [Interpretation would appear here]")
    print("Model C (Mistral): [Interpretation would appear here]")
    print("Model D (Phi): [Interpretation would appear here]")
    print("Model E (Gemma): [Interpretation would appear here]")

if __name__ == "__main__":
    asyncio.run(test_arena_interpretation())
```

---

## Configuration Options

```python
# config/arena_config.py

ARENA_INTERPRETATION_CONFIG = {
    'enabled': True,
    'auto_trigger': False,  # Automatically trigger after analysis
    'models': [
        'gpt-4o-mini',
        'llama3.1:8b', 
        'mistral:7b',
        'phi3:mini',
        'gemma2:9b'
    ],
    'task_types': [
        'interpret',  # Technical interpretation
        'explain',    # Layman explanation  
        'validate',   # Critical evaluation
        'recommend'   # Action recommendations
    ],
    'context_limits': {
        'max_summary_size': 2000,  # Characters
        'max_data_points': 100,     # For charts/tables
        'max_geographic_units': 20  # For maps
    },
    'ui_options': {
        'show_button_after_analysis': True,
        'allow_task_selection': True,
        'show_model_names': False,  # Hide until voting
        'enable_progressive_battles': True
    }
}
```

---

## Deployment Checklist

### Pre-deployment:
- [ ] Create ArenaAnalysisContext class
- [ ] Add context extraction methods
- [ ] Update arena_routes.py with new endpoint
- [ ] Add frontend integration script
- [ ] Test with sample data

### Deployment:
- [ ] Deploy backend changes to staging
- [ ] Deploy frontend changes
- [ ] Test full workflow on staging
- [ ] Monitor performance metrics
- [ ] Deploy to production

### Post-deployment:
- [ ] Monitor user engagement
- [ ] Collect feedback on interpretations
- [ ] Fine-tune prompts based on results
- [ ] Document lessons learned

---

## Quick Wins

### 1. Start with TPR Interpretation
- Simplest analysis type
- Clear metrics to interpret
- High user value

### 2. Add "Explain to Manager" Button
- Single task type initially
- Clear use case
- Easy to implement

### 3. Show Top 3 Interpretations
- Reduce cognitive load
- Faster to implement
- Can expand later

---

This guide provides the essential code and steps to begin implementing Arena interpretation features. Start with Step 1 and test each component before moving to the next.