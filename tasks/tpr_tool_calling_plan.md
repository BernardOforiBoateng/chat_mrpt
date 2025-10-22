# TPR System: Tool-Calling Pattern Implementation Plan

## Current State Assessment

### ✅ What We Have:
1. **Core LLM Infrastructure**
   - `conversation.py` - ReAct pattern with full DataFrame access
   - `prompts.py` - Comprehensive prompts with correct TPR formulas
   - `sandbox.py` - Safe code execution environment
   - `llm_tpr_handler.py` - Basic LLM handler (needs enhancement)

2. **What Works:**
   - LLM can analyze data dynamically
   - Sandbox executes generated code safely
   - TPR calculation with correct formulas
   - Basic ward matching logic

### ❌ What's Missing:
1. **Tool-Calling Pattern** - LLM suggests actions but doesn't control execution
2. **User Confirmation Points** - No mechanism for ward matching verification
3. **TPR Map Generation** - Not integrated after calculation
4. **State Management** - No tracking of conversation flow
5. **Progress Feedback** - No updates during long operations

---

## Implementation Plan: Tool-Calling Pattern with User Confirmation

### Phase 1: Restructure to Tool-Calling Pattern ⏰ (2 hours)

#### 1.1 Create Tool Definitions
- [ ] Create `app/tpr_module/tools.py`:
  ```python
  TOOLS = [
      {
          "name": "analyze_data",
          "description": "Explore TPR data structure",
          "parameters": {...},
          "needs_confirmation": False
      },
      {
          "name": "calculate_tpr", 
          "description": "Calculate TPR with NMEP formula",
          "parameters": {...},
          "needs_confirmation": True  # User confirms before calculation
      },
      {
          "name": "match_wards",
          "description": "Match ward names with shapefile",
          "parameters": {...},
          "needs_confirmation": "partial"  # Only ambiguous matches
      }
  ]
  ```

#### 1.2 Enhance LLM Conversation for Tool Calling
- [ ] Modify `conversation.py`:
  ```python
  def suggest_tool_call(self, user_message, context):
      """LLM suggests tool call, doesn't execute"""
      prompt = f"""
      Context: {context}
      User: {user_message}
      
      Suggest appropriate tool call:
      1. Analyze current state
      2. Determine needed action
      3. Return tool call JSON
      """
      return self.llm.get_tool_suggestion(prompt)
  ```

#### 1.3 Update Handler with Tool Execution Control
- [ ] Enhance `llm_tpr_handler.py`:
  ```python
  def process_message(self, user_message):
      # LLM suggests tool
      tool_call = self.conversation.suggest_tool_call(user_message, self.state)
      
      # Check if needs confirmation
      if tool_call.needs_confirmation:
          return {
              'type': 'confirmation_needed',
              'tool': tool_call,
              'message': f"I need to {tool_call.description}. Proceed?"
          }
      
      # Execute tool
      result = self.execute_tool(tool_call)
      return self.conversation.process_result(result)
  ```

### Phase 2: Interactive Ward Matching ⏰ (1.5 hours)

#### 2.1 Implement Ward Matching Tool
- [ ] Add to `tools.py`:
  ```python
  def match_wards_tool(tpr_wards, shapefile_wards):
      """Returns matches with confidence scores"""
      matches = []
      for tpr_ward in tpr_wards:
          best_matches = fuzzy_match(tpr_ward, shapefile_wards)
          matches.append({
              'tpr_ward': tpr_ward,
              'suggestions': best_matches,
              'confidence': best_matches[0]['score'],
              'needs_confirmation': best_matches[0]['score'] < 85
          })
      return matches
  ```

#### 2.2 Add Confirmation Dialogue Flow
- [ ] In `llm_tpr_handler.py`:
  ```python
  def handle_ward_confirmation(self, user_response, pending_match):
      """Process user's ward matching decision"""
      if user_response == 'accept':
          self.state['confirmed_matches'][pending_match['tpr']] = pending_match['suggested']
      elif user_response == 'skip':
          self.state['skipped_wards'].append(pending_match['tpr'])
      elif user_response.startswith('manual:'):
          self.state['confirmed_matches'][pending_match['tpr']] = user_response[7:]
      
      # Continue with next ambiguous match
      return self.get_next_confirmation()
  ```

### Phase 3: TPR Map Integration ⏰ (1 hour)

#### 3.1 Add Map Generation Tool
- [ ] Add to `tools.py`:
  ```python
  {
      "name": "generate_tpr_map",
      "description": "Create choropleth map of TPR distribution",
      "executes_after": "calculate_tpr",
      "automatic": True  # Runs automatically after TPR calculation
  }
  ```

#### 3.2 Integrate with Visualization Service
- [ ] In `llm_tpr_handler.py`:
  ```python
  def generate_tpr_map(self):
      """Generate and display TPR distribution map"""
      from app.services.tpr_visualization_service import TPRVisualizationService
      
      viz_service = TPRVisualizationService(self.session_id)
      map_result = viz_service.create_tpr_map(
          self.state['tpr_results'],
          self.state['state_name']
      )
      
      return {
          'type': 'visualization',
          'map_url': map_result['map_path'],
          'summary': f"TPR distribution map for {self.state['state_name']}"
      }
  ```

### Phase 4: State Management & Progress ⏰ (1 hour)

#### 4.1 Implement Conversation State Machine
- [ ] Create `app/tpr_module/state_machine.py`:
  ```python
  class TPRStateMachine:
      STATES = {
          'initial': ['data_uploaded'],
          'data_uploaded': ['analyzing'],
          'analyzing': ['state_selection'],
          'state_selection': ['facility_selection'],
          'facility_selection': ['calculating'],
          'calculating': ['ward_matching'],
          'ward_matching': ['generating_map'],
          'generating_map': ['complete']
      }
      
      def transition(self, from_state, action):
          """Validate and perform state transition"""
          if action in self.STATES[from_state]:
              return action
          raise ValueError(f"Invalid transition: {from_state} -> {action}")
  ```

#### 4.2 Add Progress Tracking
- [ ] Enhance response with progress:
  ```python
  def process_with_progress(self, operation, total_items):
      """Stream progress updates"""
      for i, item in enumerate(operation):
          if i % 10 == 0:  # Update every 10 items
              yield {
                  'type': 'progress',
                  'current': i,
                  'total': total_items,
                  'message': f"Processing {i}/{total_items} wards..."
              }
      yield {'type': 'complete', 'result': result}
  ```

### Phase 5: Complete Flow Integration ⏰ (1.5 hours)

#### 5.1 Update Main TPR Routes
- [ ] Modify `app/web/routes/tpr_routes.py`:
  ```python
  @bp.route('/api/tpr/message', methods=['POST'])
  def process_tpr_message():
      handler = get_tpr_handler(session_id)
      response = handler.process_message(user_message)
      
      # Handle different response types
      if response['type'] == 'confirmation_needed':
          session['pending_confirmation'] = response['tool']
          return jsonify(response)
      elif response['type'] == 'visualization':
          return jsonify({
              'message': response['summary'],
              'visualization': response['map_url']
          })
      # ... handle other types
  ```

#### 5.2 Frontend Dialogue Handling
- [ ] Create frontend handler guide:
  ```javascript
  // In app/static/js/modules/chat/tpr-handler.js
  handleTPRResponse(response) {
      switch(response.type) {
          case 'confirmation_needed':
              this.showConfirmationDialog(response);
              break;
          case 'ward_matching':
              this.showWardMatchingUI(response);
              break;
          case 'visualization':
              this.displayMap(response.map_url);
              break;
          case 'progress':
              this.updateProgressBar(response);
              break;
      }
  }
  ```

### Phase 6: Testing & Refinement ⏰ (1 hour)

#### 6.1 Create Comprehensive Test
- [ ] Create `test_complete_tpr_flow.py`:
  - Upload → Analyze → Select State → Calculate TPR
  - Ward Matching with confirmations
  - Map generation
  - Transition to risk analysis

#### 6.2 Error Handling
- [ ] Add fallback mechanisms:
  - Timeout handling for LLM calls
  - Graceful degradation if map fails
  - Recovery from sandbox errors

---

## Success Criteria

### Must Have:
✅ Tool-calling pattern (LLM suggests, system executes)
✅ Ward matching with user confirmation
✅ TPR map generation and display
✅ State management throughout conversation
✅ Progress updates for long operations

### Nice to Have:
🎯 Batch ward confirmations
🎯 Undo/redo for user decisions
🎯 Export conversation history

---

## Timeline

**Day 1 (Today):**
- Morning: Phase 1 & 2 (Tool-calling pattern + Ward matching)
- Afternoon: Phase 3 & 4 (Map integration + State management)

**Day 2:**
- Morning: Phase 5 (Complete integration)
- Afternoon: Phase 6 (Testing & refinement)

**Day 3:**
- Deploy to staging
- User testing
- Bug fixes

---

## Key Differences from Pure LLM Approach

| Pure LLM (What we had) | Tool-Calling (What we're building) |
|------------------------|-------------------------------------|
| LLM executes directly | LLM suggests, system executes |
| No user confirmation | Confirmation at critical points |
| No state tracking | Explicit state machine |
| No progress updates | Real-time progress feedback |
| Maps not integrated | Automatic map generation |

---

## Files to Modify/Create

### New Files:
1. `app/tpr_module/tools.py` - Tool definitions
2. `app/tpr_module/state_machine.py` - State management
3. `app/static/js/modules/chat/tpr-handler.js` - Frontend handler

### Modified Files:
1. `app/tpr_module/conversation.py` - Add tool suggestion
2. `app/tpr_module/integration/llm_tpr_handler.py` - Tool execution control
3. `app/web/routes/tpr_routes.py` - Handle response types

---

## Review Section
[To be completed after implementation]