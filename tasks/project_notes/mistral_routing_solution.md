# Mistral Routing Solution - No New Files Needed!

## The Real Problem
We're not trusting Mistral! We keep adding pre-routing checks that bypass Mistral's intelligence.

## Current Issues

### 1. Excessive Pre-routing (Lines 40-99)
- 60+ lines of hardcoded checks BEFORE Mistral
- Mistral only sees what gets through these filters
- We're essentially doing the routing ourselves, defeating the purpose

### 2. Poor Mistral Context
The prompt doesn't tell Mistral:
- What tools are available
- What each tool does
- Which tools need data
- When to use tools vs general response

### 3. Biased Prompt
Current prompt has bias:
- "Session has data: True" → Makes Mistral think everything is about data
- No examples of when NOT to use tools even with data

## The Fix: Trust Mistral!

### Step 1: Minimize Pre-routing
Only pre-route the MOST obvious cases:
```python
# Only pre-route greetings and thanks - that's it!
if message_lower in ['hi', 'hello', 'hey', 'thanks', 'bye']:
    return "can_answer"

# Everything else goes to Mistral
```

### Step 2: Give Mistral Tool Information
```python
prompt = f"""You are a routing assistant for ChatMRPT.

AVAILABLE TOOLS (require uploaded data):
- Analysis tools: RunCompleteAnalysis, RunPCAAnalysis, RunCompositeAnalysis
- Visualization tools: CreateVulnerabilityMap, CreateBoxPlot, CreateHistogram, etc.
- Export tools: ExportResults, GenerateReport

KNOWLEDGE CAPABILITIES (no data needed):
- Explain malaria concepts
- Describe methodologies (PCA, composite scoring)
- General epidemiology knowledge
- ChatMRPT help and guidance

Context:
- User has uploaded data: {session_context.get('has_uploaded_files', False)}
- Message: "{message}"

ROUTING RULES:
1. If user wants to USE their uploaded data → NEEDS_TOOLS
   Examples: "analyze my data", "plot the distribution", "run analysis"
   
2. If user wants INFORMATION or CONCEPTS → CAN_ANSWER
   Examples: "what is malaria", "explain PCA", "how does analysis work"
   
3. If user is asking ABOUT their data conceptually → CAN_ANSWER
   Examples: "what kind of analysis can you do", "explain the methodology"

4. If user wants to OPERATE on their data → NEEDS_TOOLS
   Examples: "summarize", "visualize", "calculate" (when data exists)

CRITICAL: Just because data exists doesn't mean every question needs tools!
- "what is analysis" → CAN_ANSWER (concept question)
- "analyze my data" → NEEDS_TOOLS (data operation)

Reply ONLY: NEEDS_TOOLS or CAN_ANSWER
"""
```

### Step 3: Remove Fallback Biases
Current fallback:
```python
# BAD - assumes data means tools
if session_context.get('has_uploaded_files'):
    return "needs_tools"
```

Better fallback:
```python
# Let Mistral's decision stand
# If Mistral is unsure, ask for clarification
return "needs_clarification"
```

## Why This Works

### 1. Mistral is Smart
- It's a 7B parameter model
- It understands context and nuance
- It can distinguish "analyze the concept" from "analyze my data"

### 2. Better Information
- Telling Mistral about tools helps it make informed decisions
- Clear examples guide its reasoning
- Context about data availability is useful

### 3. Less Complexity
- No more maintaining 100+ lines of pre-routing
- No more edge cases from hardcoded patterns
- Single source of truth for routing logic

## Implementation Steps

### 1. Strip Down Pre-routing
Remove lines 52-95, keep only:
- Greetings (hi, hello, hey)
- Thanks/bye
- Everything else → Mistral

### 2. Enhance Mistral Prompt
- List available tools and their purposes
- Provide clear routing rules with examples
- Emphasize that data existence ≠ always use tools

### 3. Trust Mistral's Decision
- Remove biased fallbacks
- Log decisions for monitoring
- Use clarification when confidence is low

## Benefits

1. **Simpler Code**: 100+ lines → ~20 lines
2. **Better Accuracy**: Mistral understands context
3. **Maintainable**: Update prompt, not code
4. **Scalable**: Add new tools to prompt, not patterns
5. **Intelligent**: Handles nuance and ambiguity

## No New Files Needed!

We don't need:
- New intent classifier (Mistral IS the classifier)
- New routing system (just improve what we have)
- Complex architectures (simpler is better)

Just:
1. Trust Mistral more
2. Give it better information
3. Remove the hardcoded mess