# ChatMRPT Investigation Findings
## Initial User Experience & TPR Workflow Rigidity

**Date**: 2025-09-27
**Investigator**: Claude
**Scope**: Initial user experience problems and TPR workflow rigidity

---

## 1. INITIAL USER EXPERIENCE PROBLEMS

### 1.1 No Welcome Message or Initial Greeting
**Finding**: When users first enter ChatMRPT, they receive NO welcome message or introduction.

**Evidence**:
- `app/core/request_interpreter.py` line 1318: `_simple_conversational_response` passes user messages directly to LLM without any system prompt
- No "welcome", "greeting", or "hello" strings found in core modules
- React app (`app/static/react/index.html`) loads with just title "ChatMRPT - Malaria Risk Analysis"

**Impact**:
- Users don't know what ChatMRPT is or what it can do
- No guidance on available features (upload, TPR analysis, risk analysis)
- Meeting transcript confirms: "Platform doesn't clearly explain what ChatMRPT is when users first arrive"

### 1.2 LLM Not Context-Aware of UI Elements
**Finding**: The LLM doesn't know about available UI elements like upload buttons.

**Evidence**:
- Meeting transcript line 106-115: User asks about uploading, LLM says "typically it is a platform that supports file upload" instead of "Click the upload button on your left"
- System prompt in `app/core/prompt_builder.py` doesn't mention UI elements
- No references to "upload button", "data analysis tab", or other UI components

**Impact**:
- Users get generic responses instead of specific guidance
- LLM can't direct users to actual features
- Creates disconnect between chat interface and UI

### 1.3 No Friendly Assistant Personality
**Finding**: ChatMRPT lacks a conversational, assistant-like personality.

**Evidence**:
- Fallback prompt (line 1627): "You are ChatMRPT, an AI assistant for malaria risk analysis. Be accurate, concise, and action-oriented."
- No personalization or friendly greeting patterns
- Meeting request: Should say "How can I help you today?" like banking assistants

**Impact**:
- Tool feels impersonal and technical
- Not suitable for target users (state malaria officers)
- Lacks engagement and approachability

### 1.4 Poor Guidance for New Users
**Finding**: No clear onboarding flow or feature introduction.

**Evidence**:
- System prompt starts with technical details (line 20 in prompt_builder.py)
- No progressive disclosure of features
- Meeting feedback: "bombarding them with a lot of information"

**Recommendations**:
```python
# Example welcome message
"Hello! I'm ChatMRPT, your AI assistant for malaria risk analysis and intervention planning.

I can help you with:
• 📊 Analyzing malaria risk data for your state
• 🗺️ Creating vulnerability maps for targeted interventions
• 🔬 Calculating Test Positivity Rates (TPR)
• 🛏️ Planning ITN (bed net) distribution

To get started, you can:
1. Upload your data (CSV + shapefile) using the button on your left
2. Ask me questions about malaria epidemiology
3. Start a TPR analysis workflow

How can I help you today?"
```

---

## 2. TPR WORKFLOW RIGIDITY PROBLEMS

### 2.1 Workflow Locks User Into Rigid Pipeline
**Finding**: Once TPR workflow starts, users cannot ask questions or deviate.

**Evidence**:
- `app/data_analysis_v3/core/agent.py` line 502: Checks `is_tpr_workflow_active()` and routes ALL messages to TPR handler
- No escape mechanism or pause functionality
- Meeting transcript: "Once in TPR workflow, users can't ask questions or get clarifications"

**Impact**:
- Users feel trapped in the pipeline
- Cannot clarify terminology or get help
- Frustrating user experience

### 2.2 No Acknowledgment of User Input
**Finding**: TPR workflow doesn't acknowledge user choices before proceeding.

**Evidence**:
- `tpr_workflow_handler.py` line 455-492: `handle_state_selection` immediately moves to next stage without confirmation
- No "Great choice!" or "You selected X, now let's..." messages
- Meeting feedback: "it follows the workflow but does not allow me to interact"

**Example of Current Flow**:
```
User: "Kano"
System: [Immediately shows facility selection without acknowledging Kano was selected]
```

**Should Be**:
```
User: "Kano"
System: "Great! You've selected Kano State. Now let's look at the facility levels available..."
```

### 2.3 Workflow Stages Are Sequential and Inflexible
**Finding**: TPR workflow enforces strict stage progression with no ability to go back or skip.

**Evidence**:
- Stages enforced: STATE → FACILITY → AGE → CALCULATION → COMPLETE
- `ConversationStage` enum enforces linear progression
- No "back" or "change selection" options

**Impact**:
- Users cannot correct mistakes
- Cannot explore different options
- Feels like a rigid form instead of conversation

### 2.4 No Conversational Elements
**Finding**: TPR workflow responses are purely informational, not conversational.

**Evidence**:
- Formatter messages focus on data presentation
- No contextual help or explanations
- Meeting: "Too rigid... need flexibility or acknowledgment"

### 2.5 Error Handling Creates Loops
**Finding**: Invalid inputs during TPR create confusing re-prompts.

**Evidence**:
- Line 551-585 in `handle_age_group_selection`: Detects wrong input and re-prompts with warning
- Users may get stuck in loops if they don't understand what's expected

---

## 3. KEY ARCHITECTURAL ISSUES

### 3.1 Session Management
- TPR workflow state stored in `tpr_workflow_active` flag
- Once active, ALL messages routed to TPR handler
- No middleware for intercepting help requests

### 3.2 Missing Features
- No context-aware help system
- No workflow pause/resume
- No inline explanations
- No "exit workflow" command

### 3.3 UI/Backend Disconnect
- LLM doesn't know about UI elements
- System prompts don't reference interface components
- No dynamic prompt updates based on UI state

---

## 4. PRIORITIZED RECOMMENDATIONS

### HIGH PRIORITY
1. **Add Welcome Message System**
   - Implement initial greeting when session starts
   - List available features clearly
   - Guide users to first action

2. **Make LLM Context-Aware**
   - Update system prompts with UI element descriptions
   - Add dynamic context about current page/tab
   - Enable directing users to specific buttons/features

3. **Add TPR Workflow Flexibility**
   - Allow questions during workflow
   - Add confirmation messages for selections
   - Implement "pause" and "help" commands
   - Add ability to go back one step

### MEDIUM PRIORITY
4. **Improve Response Formatting**
   - Add proper spacing and structure
   - Use markdown for emphasis
   - Break up text walls

5. **Add Conversational Elements**
   - Acknowledge user inputs
   - Provide encouraging feedback
   - Explain next steps clearly

### LOW PRIORITY
6. **Enhanced Error Handling**
   - Clearer error messages
   - Suggestions for correction
   - Prevent infinite loops

---

## 5. AFFECTED FILES

### Initial User Experience
- `/app/core/request_interpreter.py` - Add welcome logic
- `/app/core/prompt_builder.py` - Update system prompts
- `/app/web/routes/core_routes.py` - Initialize with greeting
- `/app/static/react/` - Frontend welcome component

### TPR Workflow
- `/app/data_analysis_v3/core/tpr_workflow_handler.py` - Add flexibility
- `/app/data_analysis_v3/core/agent.py` - Allow interruptions
- `/app/data_analysis_v3/core/formatters.py` - Conversational messages
- `/app/data_analysis_v3/core/state_manager.py` - Workflow state handling

---

## 6. MEETING TRANSCRIPT REFERENCES

Key quotes confirming issues:
- Line 114: "Platform not context aware"
- Line 524: "Can't ask questions once in TPR workflow"
- Line 543: "How can I help you today? That is what I want this to be"
- Line 1586: "Workflow too rigid, user input ignored"
- Line 1690: "Tool not interactive, follows workflow but doesn't respond to user"

---

## END OF INVESTIGATION REPORT