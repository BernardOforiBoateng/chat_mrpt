# TPR Integration Checklist - What's Next

## Date: 2025-01-06

## 🔍 Current State Analysis

### ✅ What We Have Ready

1. **Core TPR Logic**
   - ✅ Correct TPR calculation formulas (`tpr_calculator.py`)
   - ✅ Geopolitical zone variables (`geopolitical_zones.py`)
   - ✅ Shapefile extraction and matching (`shapefile_extractor.py`)
   - ✅ Visualization service (`tpr_visualization_service.py`)

2. **New Interactive System**
   - ✅ Interactive conversation handler (`interactive_conversation.py`)
   - ✅ Interactive prompts (`interactive_prompts.py`)
   - ✅ Fuzzy ward matching with verification
   - ✅ Sandboxed execution (`sandbox.py`)

3. **Existing Infrastructure**
   - ✅ TPR routes (`/api/tpr/*`)
   - ✅ TPR handler (`tpr_handler.py`)
   - ✅ State management (`tpr_state_manager.py`)
   - ✅ Output generation (`output_generator.py`)

### 🔄 What Needs Integration

#### 1. **Connect Interactive System to Existing Routes** 🔴 HIGH PRIORITY
```python
# Current: tpr_routes.py uses old TPRHandler
# Need: Connect to new InteractiveTPRConversation

# Modify tpr_handler.py to use new system:
class TPRHandler:
    def __init__(self, session_id):
        # OLD: self.conversation_manager = TPRConversationManager(...)
        # NEW: self.conversation = InteractiveTPRConversation(...)
```

#### 2. **Variable Distribution Visualization** 🔴 HIGH PRIORITY
```python
# Current: tpr_visualization_service.py has create_tpr_distribution_map()
# Need: Add interactive variable distribution plots

def create_variable_distribution_plots(self, 
                                      tpr_df: pd.DataFrame,
                                      variables: List[str]) -> List[str]:
    """
    Create interactive distribution plots for environmental variables.
    - Histogram for each variable
    - Box plots by TPR risk category
    - Correlation matrix
    """
```

#### 3. **Visualization Endpoint Integration** 🔴 HIGH PRIORITY
```python
# Add to tpr_routes.py:
@tpr_bp.route('/visualizations', methods=['POST'])
def create_visualizations():
    """
    Generate TPR map and variable distributions.
    """
    # Get TPR results
    # Create distribution map
    # Create variable plots
    # Return paths
```

#### 4. **Geopolitical Zone Variable Extraction** 🟡 MEDIUM PRIORITY
```python
# Connect raster_extractor.py to interactive flow
def extract_variables_interactive(self, ward_data, state_name):
    # Get zone for state
    zone = get_zone_for_state(state_name)
    
    # Get available variables
    available = self.check_available_rasters(zone)
    
    # Ask user which to extract
    selected = self.llm.ask_user_variables(available)
    
    # Extract selected
    return self.extract_selected(ward_data, selected)
```

#### 5. **Shapefile Matching Integration** 🟡 MEDIUM PRIORITY
```python
# Connect shapefile_extractor.py to interactive flow
def match_wards_with_verification(self, tpr_data, shapefile):
    # Use InteractiveTPRConversation.match_wards_interactive()
    matches, unmatched = self.conversation.match_wards_interactive(
        tpr_data, shapefile_wards
    )
    
    # Get user verification for unmatched
    for ward in unmatched:
        user_choice = self.conversation.get_user_match(ward)
        # Apply user choice
```

#### 6. **Complete Pipeline Flow** 🟢 LOWER PRIORITY
```python
# Create unified flow:
1. Upload file → InteractiveTPRConversation.start_analysis()
2. User dialogue → process_user_response() loop
3. Calculate TPR → calculate_tpr() with user method
4. Match wards → match_wards_interactive()
5. Extract variables → extract_variables_interactive()
6. Create visualizations → create_tpr_distribution_map() + create_variable_distribution_plots()
7. Generate outputs → output_generator.generate_outputs()
```

## 📋 Implementation Tasks

### Task 1: Modify TPR Handler (1-2 hours)
```python
# app/tpr_module/integration/tpr_handler.py

class TPRHandler:
    def __init__(self, session_id: str):
        # Use new interactive conversation
        self.conversation = InteractiveTPRConversation(
            llm_adapter=self._get_llm_client(),
            sandbox=create_tpr_sandbox()
        )
        
    def process_tpr_message(self, user_message: str):
        # Route to interactive conversation
        stage = self.conversation.context.get('stage')
        return self.conversation.process_user_response(
            user_message, stage
        )
```

### Task 2: Add Variable Distribution Plots (2-3 hours)
```python
# app/tpr_module/services/tpr_visualization_service.py

def create_variable_distribution_plots(self, 
                                      tpr_df: pd.DataFrame,
                                      zone_variables: Dict[str, float]) -> List[str]:
    """
    Create interactive plots for environmental variables.
    """
    plots = []
    
    # 1. Histogram for each variable
    for var_name, values in zone_variables.items():
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=values,
            name=var_name,
            nbinsx=30
        ))
        # Save and add to plots
    
    # 2. Box plot by risk category
    tpr_df['risk_category'] = pd.cut(
        tpr_df['TPR'],
        bins=[0, 20, 40, 60, 100],
        labels=['Low', 'Medium', 'High', 'Very High']
    )
    
    for var_name in zone_variables:
        fig = go.Figure()
        for category in ['Low', 'Medium', 'High', 'Very High']:
            subset = tpr_df[tpr_df['risk_category'] == category]
            fig.add_trace(go.Box(
                y=subset[var_name],
                name=category
            ))
        # Save and add to plots
    
    # 3. Correlation heatmap
    corr_matrix = tpr_df[list(zone_variables.keys()) + ['TPR']].corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu'
    ))
    # Save and add to plots
    
    return plots
```

### Task 3: Create Visualization Endpoint (1 hour)
```python
# app/web/routes/tpr_routes.py

@tpr_bp.route('/visualizations', methods=['POST'])
@validate_session
@handle_errors
def create_tpr_visualizations():
    """
    Create TPR distribution map and variable plots.
    """
    session_id = session.get('session_id')
    data = request.get_json()
    
    # Get TPR results from session
    tpr_handler = get_tpr_handler(session_id)
    tpr_results = tpr_handler.get_tpr_results()
    
    # Initialize visualization service
    viz_service = TPRVisualizationService(session_id)
    
    # Create distribution map
    map_path = viz_service.create_tpr_distribution_map(
        tpr_results['data'],
        tpr_results['state_name'],
        title=data.get('title')
    )
    
    # Create variable distribution plots
    if tpr_results.get('zone_variables'):
        plot_paths = viz_service.create_variable_distribution_plots(
            tpr_results['data'],
            tpr_results['zone_variables']
        )
    else:
        plot_paths = []
    
    return jsonify({
        'status': 'success',
        'map_url': map_path,
        'plot_urls': plot_paths,
        'message': f'Created {len(plot_paths) + 1} visualizations'
    })
```

### Task 4: Connect Variable Extraction (1-2 hours)
```python
# Modify interactive_conversation.py to include variable extraction

async def extract_environmental_variables(self, state_name: str) -> Dict[str, Any]:
    """
    Extract zone-specific environmental variables with user input.
    """
    from ..data.geopolitical_zones import get_zone_for_state, get_variables_for_zone
    from ..services.raster_extractor import RasterExtractor
    
    # Get zone and variables
    zone = get_zone_for_state(state_name)
    zone_vars = get_variables_for_zone(zone)
    
    # Check what's available
    extractor = RasterExtractor()
    available = extractor.check_available_variables(zone_vars)
    
    # Ask user
    response = {
        'stage': 'variable_extraction',
        'zone': zone,
        'recommended_variables': zone_vars,
        'available': available['found'],
        'missing': available['missing'],
        'question': 'Which environmental variables should I extract?',
        'options': [
            {'id': 'all_available', 'label': f'Extract all available ({len(available["found"])} variables)'},
            {'id': 'skip', 'label': 'Skip environmental variables'},
            {'id': 'select', 'label': 'Let me select specific variables'}
        ]
    }
    
    return response
```

### Task 5: Test Complete Flow (2-3 hours)
```python
# Create test script: test_complete_tpr_flow.py

def test_complete_interactive_flow():
    """
    Test the complete TPR flow with all integrations.
    """
    # 1. Upload file
    response = client.post('/api/tpr/upload', files={'file': test_file})
    assert response.status_code == 200
    
    # 2. Process conversation
    response = client.post('/api/tpr/process', json={'message': '1'})  # Select age group
    assert 'data_quality' in response.json()['stage']
    
    # 3. Handle quality issues
    response = client.post('/api/tpr/process', json={'message': 'exclude'})
    assert 'calculation_method' in response.json()['stage']
    
    # 4. Select calculation method
    response = client.post('/api/tpr/process', json={'message': 'standard'})
    assert 'ward_matching' in response.json()['stage']
    
    # 5. Verify ward matches
    response = client.post('/api/tpr/process', json={'message': 'a'})  # Accept match
    assert 'variable_extraction' in response.json()['stage']
    
    # 6. Extract variables
    response = client.post('/api/tpr/process', json={'message': 'all_available'})
    assert 'results_review' in response.json()['stage']
    
    # 7. Create visualizations
    response = client.post('/api/tpr/visualizations')
    assert response.json()['map_url'] is not None
    assert len(response.json()['plot_urls']) > 0
    
    # 8. Export results
    response = client.get('/api/tpr/download-links')
    assert len(response.json()['files']) > 0
```

## 🎯 Priority Order

1. **HIGH**: Modify TPR Handler to use interactive conversation
2. **HIGH**: Add variable distribution visualization functions
3. **HIGH**: Create visualization endpoint
4. **MEDIUM**: Connect variable extraction with user dialogue
5. **MEDIUM**: Integrate shapefile matching
6. **LOW**: Complete end-to-end testing

## 📋 Before Testing Checklist

- [ ] TPR Handler uses InteractiveTPRConversation
- [ ] Variable distribution plots implemented
- [ ] Visualization endpoint created
- [ ] Zone variable extraction connected
- [ ] Ward matching integrated
- [ ] All endpoints return expected formats
- [ ] Error handling in place
- [ ] Session state preserved across requests
- [ ] Sandbox execution working
- [ ] LLM adapter connected

## 🚀 Next Immediate Steps

1. **Step 1**: Modify `tpr_handler.py` to use `InteractiveTPRConversation`
2. **Step 2**: Add `create_variable_distribution_plots()` to visualization service
3. **Step 3**: Create `/api/tpr/visualizations` endpoint
4. **Step 4**: Test with sample data
5. **Step 5**: Deploy to staging

## 💡 Key Integration Points

```python
# The main integration flow:
Upload → InteractiveTPRConversation → TPR Calculation → Ward Matching → 
Variable Extraction → Visualization Generation → Output Export

# Each step should:
1. Use the interactive conversation for user dialogue
2. Preserve state across requests
3. Handle errors gracefully
4. Provide clear feedback to user
```