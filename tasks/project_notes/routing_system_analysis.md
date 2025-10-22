# ChatMRPT Routing System Analysis

## Current Routing Architecture Flaws

### 1. Hardcoded Pattern Matching
```python
# Current approach - brittle and context-unaware
data_operation_verbs = ['summarize', 'analyze', 'plot', ...]
if any(verb in message for verb in data_operation_verbs):
    route_to_tools()
```

**Problems:**
- "Analyze the concept of malaria" → Wrong: Routes to tools
- "Tell me about analysis methods" → Wrong: Routes to tools
- "What does analyze mean?" → Wrong: Routes to tools

### 2. Binary Decision Making
Current system only has two destinations:
- Arena mode (local Ollama models)
- OpenAI with tools

**Problems:**
- No middle ground for questions that need knowledge but not full tools
- Can't handle mixed requests (part general, part specific)
- No way to use specific tools without full OpenAI

### 3. Context Blindness
The routing doesn't consider:
- What tools are actually available
- Whether required data exists for specific tools
- Conversation history
- User's actual intent

### 4. Mistral Routing Issues
Using Mistral:7b for routing has problems:
- Prompt engineering dependent
- Can be biased by how context is presented
- No understanding of actual tool capabilities
- Makes decisions without knowing what tools can do

## Root Cause Analysis

### The Fundamental Problem
**We're routing based on WORDS not INTENT**

Examples:
- "summarize" → Always tools (but what if "summarize the concept of PCA"?)
- "plot" → Always tools (but what if "explain what a plot is"?)
- "analyze" → Always tools (but what if "how do you analyze data"?)

### Why This Happened
1. **Incremental fixes** - Each edge case got a new hardcoded rule
2. **No tool metadata** - Router doesn't know what tools can actually do
3. **Missing abstraction** - No intermediate layer between user message and execution
4. **Over-simplification** - Trying to solve complex intent with simple patterns

## Proposed Solution: Intent-Based Routing

### Core Principles

#### 1. Tool Capability Awareness
```python
class ToolCapability:
    name: str
    requires_data: bool
    can_handle_general: bool
    keywords: List[str]  # Semantic keywords, not literal
    intents: List[str]   # What intents this tool serves
```

#### 2. Multi-Stage Intent Classification
```
Stage 1: Broad Intent
├── INFORMATION_SEEKING (wants to know something)
├── ACTION_REQUESTING (wants to do something)
├── CONVERSATIONAL (greeting, thanks, etc.)
└── CLARIFICATION_NEEDED (ambiguous)

Stage 2: Specific Intent (if ACTION_REQUESTING)
├── ANALYZE_DATA (work with uploaded data)
├── VISUALIZE_DATA (create charts/maps)
├── EXPLAIN_CONCEPT (methodology, concepts)
├── SYSTEM_QUERY (check status, available data)
└── EXPORT_RESULTS (download, save)

Stage 3: Tool Selection
Based on specific intent + available data + tool capabilities
```

#### 3. Context-Aware Routing
```python
class RoutingContext:
    message: str
    has_data: bool
    data_type: str  # csv, shapefile, both
    conversation_history: List[str]
    previous_intent: str
    available_tools: List[ToolCapability]
```

### Improved Routing Logic

```python
def route_message(context: RoutingContext):
    # Step 1: Classify broad intent
    broad_intent = classify_broad_intent(context.message)
    
    # Step 2: Quick returns for clear cases
    if broad_intent == CONVERSATIONAL:
        return route_to_arena()  # Greetings, thanks, etc.
    
    if broad_intent == INFORMATION_SEEKING:
        # Check if it's about data or concepts
        if is_asking_about_uploaded_data(context):
            return route_to_tools()  # "What's in my file?"
        else:
            return route_to_arena()  # "What is malaria?"
    
    # Step 3: For actions, determine specific intent
    if broad_intent == ACTION_REQUESTING:
        specific_intent = classify_specific_intent(context)
        
        # Step 4: Check if we can fulfill the intent
        if specific_intent == ANALYZE_DATA:
            if not context.has_data:
                return clarify("Please upload data first")
            return route_to_tools()
        
        if specific_intent == EXPLAIN_CONCEPT:
            return route_to_arena()  # Knowledge questions
        
        # ... handle other intents
    
    # Step 5: When unclear, use semantic similarity
    if broad_intent == CLARIFICATION_NEEDED:
        return use_semantic_routing(context)
```

### Semantic Routing Fallback

When patterns fail, use embeddings:
1. Embed the user message
2. Compare with embeddings of:
   - Tool descriptions
   - Example queries for each route
   - Previous successful routings
3. Route to most similar

### Key Improvements

1. **Intent-First**: Focus on what user wants, not keywords
2. **Multi-Stage**: Progressive refinement of intent
3. **Context-Aware**: Consider data availability and history
4. **Tool-Aware**: Know what each tool can actually do
5. **Graceful Degradation**: Multiple fallback strategies

## Implementation Strategy

### Phase 1: Document Tool Capabilities
- Create metadata for each tool
- Define what intents each tool serves
- Mark data requirements clearly

### Phase 2: Build Intent Classifier
- Use LLM for initial classification
- Build training data from successful interactions
- Consider fine-tuning small model for speed

### Phase 3: Implement Semantic Fallback
- Use sentence transformers for embeddings
- Build corpus of example queries
- Cache successful routings for learning

### Phase 4: Add Context Management
- Track conversation history
- Maintain intent context across messages
- Learn from user corrections

## Success Metrics

1. **Routing Accuracy**: % of messages routed correctly
2. **User Corrections**: How often users have to clarify
3. **Response Relevance**: Are responses addressing the intent?
4. **Latency**: Time to make routing decision
5. **Edge Case Handling**: Performance on ambiguous queries

## Examples of Improved Routing

| User Message | Current (Wrong) | Proposed (Correct) |
|--------------|-----------------|-------------------|
| "analyze" | Tools (always) | Check context: concept or data? |
| "summarize the theory" | Tools | Arena (concept explanation) |
| "what's the analysis?" | Arena | Check: asking about results or concept? |
| "plot explanation" | Tools | Arena (explaining what plots are) |
| "run analysis on my data" | Correct | Tools (explicit data operation) |

## Conclusion

The current routing system fails because it:
1. Uses brittle keyword matching
2. Ignores user intent
3. Lacks awareness of tool capabilities
4. Has no semantic understanding

The proposed solution:
1. Classifies intent progressively
2. Considers context and capabilities
3. Uses semantic similarity as fallback
4. Learns from interactions

This will create a robust, maintainable routing system that handles edge cases gracefully.