# Data Analysis V3 Implementation Plan
*Based on AgenticDataAnalysis architecture with ChatMRPT adaptations*

## Executive Summary
Implement a clean, LangGraph-based data analysis system that provides intelligent, conversational data analysis while hiding technical complexity from non-technical users. This replaces the failed V2 implementation with a simpler, more effective approach inspired by AgenticDataAnalysis.

## Core Architecture (from AgenticDataAnalysis)

### 1. Simplified Two-Node LangGraph Workflow
```
User Query → [Agent Node] ←→ [Tools Node] → Response
                ↑                    ↓
                └────── State ───────┘
```

### 2. State Management Structure
```python
class DataAnalysisState(TypedDict):
    messages: List[BaseMessage]  # Conversation history
    input_data: dict             # Loaded datasets
    current_variables: dict      # Active Python variables
    intermediate_outputs: list   # Analysis steps (hidden from user)
    visualizations: list         # Generated charts/maps
    insights: list              # User-friendly explanations
```

## Implementation Phases

### Phase 1: Foundation (Day 1)
**Goal**: Set up core infrastructure based on AgenticDataAnalysis

1. **Create Directory Structure**
   ```
   app/data_analysis_v3/
   ├── __init__.py
   ├── core/
   │   ├── state.py         # State management
   │   ├── agent.py         # LangGraph workflow
   │   └── executor.py      # Code execution engine
   ├── tools/
   │   ├── python_tool.py   # Main analysis tool
   │   └── validators.py    # Input validation
   ├── prompts/
   │   ├── system.py        # System prompts
   │   └── templates.py     # Response templates
   └── interface/
       └── chat_handler.py   # Integration with existing chat
   ```

2. **Core Components**
   - Port AgenticDataAnalysis state management
   - Implement simplified LangGraph workflow
   - Create secure code execution environment
   - Set up variable persistence mechanism

### Phase 2: Execution Environment (Day 1-2)
**Goal**: Build secure, user-friendly code execution

1. **Sandbox Implementation**
   ```python
   class SecureExecutor:
       allowed_modules = ['pandas', 'numpy', 'sklearn', 'plotly']
       max_execution_time = 30  # seconds
       memory_limit = 512  # MB
   ```

2. **Key Features from AgenticDataAnalysis**
   - Auto-load uploaded CSV/Excel files as DataFrames
   - Persist variables between executions
   - Capture and format outputs appropriately
   - Handle plotly visualizations automatically

3. **Security Enhancements**
   - RestrictedPython for code validation
   - Resource usage monitoring
   - Input sanitization
   - No file system access beyond data directory

### Phase 3: User Experience (Day 2)
**Goal**: Hide complexity, show insights

1. **Natural Language Processing**
   - Convert code outputs to user-friendly explanations
   - Generate business-context insights
   - Create narrative flow for analysis steps

2. **Response Formatting**
   ```python
   # Instead of showing:
   "df.groupby('State').mean()['Value']"
   
   # Show:
   "I've calculated the average values for each state. 
    Here are the key findings..."
   ```

3. **Visualization Integration**
   - Seamless plotly chart rendering
   - Interactive visualizations in chat
   - Export capabilities for reports

### Phase 4: Integration (Day 2-3)
**Goal**: Connect with existing ChatMRPT systems

1. **Data Pipeline Integration**
   - Connect to existing upload system
   - Access unified dataset builder
   - Leverage existing data validation

2. **Chat Interface Integration**
   - Use existing message handler
   - Maintain current UI/UX
   - No new gray boxes or separate panels

3. **Session Management**
   - Per-session data isolation
   - Cross-worker compatibility
   - Redis state storage for scaling

## Key Differences from AgenticDataAnalysis

### What We Keep:
✅ LangGraph two-node architecture
✅ State-based workflow management
✅ Persistent variable system
✅ Plotly visualization pipeline
✅ Iterative analysis capability
✅ Clean code execution sandbox

### What We Change:
❌ Remove Streamlit UI → Use existing chat interface
❌ Hide code/debug tabs → Show only insights
❌ Remove technical errors → User-friendly messages
❌ No code display → Natural language explanations
❌ Single page app → Integrated into main ChatMRPT

### What We Add:
➕ Qwen3 vLLM integration (172.31.45.157:8000)
➕ Malaria domain knowledge
➕ Integration with existing analysis tools
➕ Multi-worker session support
➕ AWS deployment compatibility

## Technical Implementation Details

### 1. Agent Configuration
```python
class DataAnalysisAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="qwen3-8b",
            base_url="http://172.31.45.157:8000/v1",
            temperature=0.7
        )
        self.graph = self._build_graph()
    
    def _build_graph(self):
        workflow = StateGraph(DataAnalysisState)
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", self.tool_node)
        # Simplified routing logic
        return workflow.compile()
```

### 2. Tool Definition
```python
@tool
def analyze_data(
    thought: str,  # Agent's reasoning (hidden from user)
    code: str      # Python code to execute
) -> dict:
    """Execute data analysis code and return results."""
    # Execute in sandbox
    # Format results for user
    # Return insights, not code
```

### 3. Prompt Engineering
```python
SYSTEM_PROMPT = """
You are a data analysis expert helping non-technical users understand their data.

IMPORTANT RULES:
1. Never show Python code to the user
2. Explain findings in simple, business terms
3. Focus on insights and recommendations
4. Use visualizations to support explanations
5. Ask clarifying questions when needed

Available data: {available_datasets}
Current analysis context: {context}
"""
```

## File Structure to Create

```
app/data_analysis_v3/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── state.py           # State definitions
│   ├── agent.py           # Main agent logic
│   ├── executor.py        # Code execution
│   └── router.py          # Request routing
├── tools/
│   ├── __init__.py
│   ├── python_tool.py     # Analysis tool
│   ├── validators.py      # Input validation
│   └── formatters.py      # Output formatting
├── prompts/
│   ├── __init__.py
│   ├── system.py          # System prompts
│   ├── templates.py       # Response templates
│   └── explanations.py    # Code-to-text conversion
├── interface/
│   ├── __init__.py
│   └── chat_handler.py    # Chat integration
└── utils/
    ├── __init__.py
    ├── security.py        # Security utilities
    └── visualization.py   # Chart handling
```

## Integration Points

### 1. Entry Point (app/web/routes/analysis_routes.py)
```python
# Add routing for data analysis queries
if is_data_analysis_query(message):
    from app.data_analysis_v3 import DataAnalysisAgent
    agent = DataAnalysisAgent(session_id)
    response = await agent.analyze(message)
    return format_analysis_response(response)
```

### 2. Frontend Integration
- No new JavaScript files needed
- Use existing chat interface
- Intercept data analysis queries in message handler
- Display visualizations inline

### 3. Data Access
```python
# Leverage existing data loading
from app.data.unified_dataset_builder import UnifiedDatasetBuilder
datasets = builder.get_session_datasets(session_id)
```

## Success Criteria

1. **Performance**: Responses within 5 seconds for simple queries
2. **Accuracy**: Correct analysis results matching pandas operations
3. **User Experience**: No code visible, clear explanations
4. **Reliability**: Graceful error handling, no crashes
5. **Integration**: Seamless with existing ChatMRPT workflows

## Testing Strategy

1. **Unit Tests**: Each component tested independently
2. **Integration Tests**: End-to-end workflow validation
3. **User Acceptance**: Non-technical user feedback
4. **Performance Tests**: Load testing with multiple sessions
5. **Security Tests**: Malicious code injection attempts

## Deployment Plan

1. **Local Development**: Test on development server
2. **Staging Deployment**: Deploy to both staging instances
3. **User Testing**: Gather feedback from test users
4. **Production Rollout**: Deploy to all production instances
5. **Monitoring**: Track usage and performance metrics

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Code execution security | RestrictedPython + sandboxing |
| Performance issues | Timeout limits + caching |
| User confusion | Clear explanations + examples |
| Integration conflicts | Isolated module design |
| Scaling concerns | Redis state + worker pooling |

## Timeline

- **Day 1**: Core architecture + execution environment
- **Day 2**: User experience + integration
- **Day 3**: Testing + deployment preparation
- **Day 4**: Staging deployment + user testing
- **Day 5**: Production deployment + monitoring

## Next Steps

1. Create directory structure
2. Implement core state management
3. Build LangGraph workflow
4. Create secure executor
5. Integrate with chat interface
6. Test with sample queries
7. Deploy to staging
8. Gather feedback and iterate

This plan combines the simplicity and effectiveness of AgenticDataAnalysis with ChatMRPT's specific requirements for user-friendliness and integration.