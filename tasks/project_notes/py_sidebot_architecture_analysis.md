# Py-Sidebot Architecture Analysis: How They Handle Multiple Models

## Date: 2025-01-18

### Key Discovery: They Use `chatlas` Library

Py-sidebot achieves multi-model support through the **`chatlas`** library, which is a high-level abstraction layer developed by Posit (makers of RStudio). This is fundamentally different from ChatMRPT's direct OpenAI client approach.

## Their Architecture

### 1. **Model Selection (Simple but Manual)**
```python
# In app.py - They manually comment/uncomment to switch models
Chat = ChatAnthropic
chat_model = "claude-3-7-sonnet-latest"
# Chat = ChatOpenAI
# chat_model = "o1"
```

**Key Point**: They don't have dynamic model switching in the UI - it's hardcoded at startup!

### 2. **Tool Registration Pattern**
```python
# Tools are registered to the chat session
chat_session = Chat(system_prompt=query.system_prompt(tips, "tips"), model=chat_model)
chat_session.register_tool(update_dashboard)
chat_session.register_tool(query_db)
```

### 3. **SQL-Based Tool Approach**
Instead of executing Python functions directly, py-sidebot uses a **clever workaround**:
- All "tools" generate SQL queries
- The LLM outputs SQL as text
- The app executes the SQL and updates the dashboard
- **This avoids the function calling problem entirely!**

## How They Avoid Function Calling Issues

### The Genius Trick: Everything is SQL

Looking at their `prompt.md`:
```markdown
Your job is to write the appropriate SQL query for this database. 
Then, call the tool `update_dashboard`, passing in the SQL query...
```

**They don't need complex function calling** because:
1. The LLM generates SQL text (all models can do this)
2. They have only 2 simple tools: `update_dashboard` and `query_db`
3. Both tools just take SQL strings as input
4. The actual work happens in SQL execution, not in tool calling

### Example Flow:
1. User: "Show only rows where value > average"
2. LLM: Generates SQL and calls `update_dashboard(query="SELECT * FROM...")`
3. App: Executes SQL, updates dashboard
4. **Key**: The tool call is simple - just passing a string!

## What `chatlas` Provides

### 1. **Unified Interface**
```python
# Same interface for different providers
ChatOpenAI(model="gpt-4o")
ChatAnthropic(model="claude-3-sonnet")
ChatOllama(model="llama3")  # If supported
```

### 2. **Provider Abstraction**
- Handles different API formats internally
- Normalizes responses
- Manages streaming across providers

### 3. **Tool Registration Abstraction**
```python
# Register once, works with all providers
chat.register_tool(my_function)
```

## Critical Difference from ChatMRPT

### ChatMRPT's Problem:
- **30+ complex tools** that do actual Python work
- Tools need structured arguments (lists, dicts, complex types)
- Tools execute analysis, create visualizations, run algorithms
- Deep dependency on OpenAI's function calling format

### Py-sidebot's Solution:
- **2 simple tools** that only take SQL strings
- Real work happens in SQL/DuckDB (not in Python tools)
- LLM just generates text (SQL), which all models can do
- Avoids function calling complexity entirely

## Why This Won't Work for ChatMRPT

### 1. **Tool Complexity**
ChatMRPT tools like:
```python
run_complete_analysis(session_id, variables=['var1', 'var2', 'var3'])
create_vulnerability_map(method='pca', threshold=0.8)
```
Can't be reduced to SQL strings!

### 2. **Execution Model**
- Py-sidebot: SQL → Database → Results
- ChatMRPT: Python functions → Complex algorithms → Files/Visualizations

### 3. **State Management**
- Py-sidebot: Stateless SQL queries
- ChatMRPT: Stateful analysis pipelines with file I/O

## Lessons for ChatMRPT

### What We Can Learn:
1. **Use an abstraction library** like `chatlas` or `langchain`
2. **Simplify tool interfaces** where possible
3. **Consider SQL/query-based operations** for data exploration

### What Won't Transfer:
1. **SQL-only approach** - Too limiting for complex analysis
2. **Manual model switching** - Users need dynamic selection
3. **Simple tool pattern** - We need complex tool orchestration

## Recommended Approach for ChatMRPT

### 1. **Adopt LangChain or Similar**
```python
from langchain.chat_models import ChatOpenAI, ChatAnthropic, ChatOllama
from langchain.agents import initialize_agent

# Unified interface across models
llm = ChatOllama(model="llama3")  # or ChatOpenAI, etc.
agent = initialize_agent(tools, llm, agent_type="zero-shot")
```

### 2. **Build Tool Translation Layer**
For models without function calling:
```python
class ToolIntentionParser:
    def parse(self, text):
        # Use regex/NLP to extract tool intentions
        # "I'll analyze data with run_analysis using variables x,y,z"
        # → {"tool": "run_analysis", "args": {"variables": ["x", "y", "z"]}}
```

### 3. **Implement Fallback Strategy**
```python
try:
    # Try native function calling
    response = llm.invoke_with_tools(prompt, tools)
except NotSupportedError:
    # Fall back to text parsing
    text_response = llm.invoke(prompt_with_tool_descriptions)
    tool_calls = parse_tool_intentions(text_response)
```

### 4. **Create Model Capability Matrix**
```python
MODEL_CAPABILITIES = {
    'gpt-4o': {'function_calling': True, 'streaming': True},
    'claude-3': {'function_calling': True, 'streaming': True},
    'llama-3': {'function_calling': False, 'streaming': True},
    'mistral': {'function_calling': False, 'streaming': True}
}
```

## Conclusion

Py-sidebot's "multi-model support" is simpler than it appears:
1. They use `chatlas` for provider abstraction
2. They avoid function calling complexity by using SQL
3. They don't have dynamic model switching in the UI
4. Their approach works because their tools are simple

For ChatMRPT to support multiple models, we need:
1. A proper abstraction layer (LangChain or custom)
2. Tool intention parsing for non-function-calling models
3. Model capability detection and routing
4. Significant architectural changes to support different model formats

The key insight: **Py-sidebot sidesteps the problem, while ChatMRPT must solve it head-on.**