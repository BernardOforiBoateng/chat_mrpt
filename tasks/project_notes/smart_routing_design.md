# Smart Routing System Design for ChatMRPT

## Design Philosophy
Instead of hardcoding patterns, we create an intelligent routing system that understands:
1. **User Intent** - What does the user actually want?
2. **Tool Capabilities** - What can each tool do?
3. **Data Context** - What data is available?
4. **Conversation Context** - What have we been discussing?

## Architecture Overview

```
User Message
    ↓
[Intent Classifier]
    ↓
[Context Analyzer]
    ↓
[Capability Matcher]
    ↓
[Route Decision]
    ↓
Arena Mode / Tools / Clarification
```

## Detailed Implementation Design

### 1. Intent Classification System

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class BroadIntent(Enum):
    """High-level user intent categories"""
    GREETING = "greeting"                    # Hi, hello, thanks
    IDENTITY = "identity"                    # Who are you, what are you
    KNOWLEDGE_QUERY = "knowledge_query"      # What is X, explain Y
    DATA_OPERATION = "data_operation"        # Analyze, plot, visualize
    STATUS_CHECK = "status_check"            # What data do I have
    HELP_REQUEST = "help_request"            # How do I use this
    AMBIGUOUS = "ambiguous"                  # Needs clarification

class SpecificIntent(Enum):
    """Detailed intent for data operations"""
    ANALYZE_UPLOADED_DATA = "analyze_uploaded_data"
    VISUALIZE_DATA = "visualize_data"
    EXPLAIN_METHODOLOGY = "explain_methodology"
    EXPLAIN_CONCEPT = "explain_concept"
    CHECK_DATA_STATUS = "check_data_status"
    EXPORT_RESULTS = "export_results"
    GENERAL_CONVERSATION = "general_conversation"

@dataclass
class IntentClassification:
    broad_intent: BroadIntent
    specific_intent: Optional[SpecificIntent]
    confidence: float
    requires_data: bool
    suggested_tools: List[str]
```

### 2. Context-Aware Intent Classifier

```python
class SmartIntentClassifier:
    """
    Multi-stage intent classifier that considers context
    """
    
    def __init__(self):
        # Define intent patterns with semantic understanding
        self.intent_patterns = {
            BroadIntent.GREETING: {
                'patterns': ['hello', 'hi', 'hey', 'good morning', 'thanks'],
                'requires_context': False
            },
            BroadIntent.IDENTITY: {
                'patterns': ['who are you', 'what are you', 'your purpose'],
                'requires_context': False
            },
            BroadIntent.KNOWLEDGE_QUERY: {
                'patterns': ['what is', 'explain', 'how does', 'tell me about'],
                'requires_context': True  # Need to check if about data or concepts
            },
            BroadIntent.DATA_OPERATION: {
                'patterns': ['analyze', 'plot', 'visualize', 'summarize', 'calculate'],
                'requires_context': True  # Need to check if data exists
            }
        }
    
    def classify(self, message: str, context: dict) -> IntentClassification:
        """
        Classify user intent considering context
        """
        message_lower = message.lower().strip()
        
        # Stage 1: Quick classification for obvious cases
        if self._is_greeting(message_lower):
            return IntentClassification(
                broad_intent=BroadIntent.GREETING,
                specific_intent=SpecificIntent.GENERAL_CONVERSATION,
                confidence=1.0,
                requires_data=False,
                suggested_tools=[]
            )
        
        if self._is_identity_question(message_lower):
            return IntentClassification(
                broad_intent=BroadIntent.IDENTITY,
                specific_intent=SpecificIntent.GENERAL_CONVERSATION,
                confidence=1.0,
                requires_data=False,
                suggested_tools=[]
            )
        
        # Stage 2: Context-aware classification
        has_data = context.get('has_uploaded_files', False)
        
        # Check if message references data explicitly
        data_references = self._check_data_references(message_lower)
        
        # Stage 3: Semantic analysis for ambiguous cases
        if self._contains_operation_verb(message_lower):
            if data_references or (has_data and not self._is_asking_about_concept(message_lower)):
                return IntentClassification(
                    broad_intent=BroadIntent.DATA_OPERATION,
                    specific_intent=self._get_specific_operation(message_lower),
                    confidence=0.8,
                    requires_data=True,
                    suggested_tools=self._suggest_tools(message_lower)
                )
            else:
                # Asking about the concept, not performing operation
                return IntentClassification(
                    broad_intent=BroadIntent.KNOWLEDGE_QUERY,
                    specific_intent=SpecificIntent.EXPLAIN_METHODOLOGY,
                    confidence=0.7,
                    requires_data=False,
                    suggested_tools=[]
                )
        
        # Default to knowledge query for questions
        if self._is_question(message_lower):
            return IntentClassification(
                broad_intent=BroadIntent.KNOWLEDGE_QUERY,
                specific_intent=SpecificIntent.EXPLAIN_CONCEPT,
                confidence=0.6,
                requires_data=False,
                suggested_tools=[]
            )
        
        # Ambiguous - need clarification
        return IntentClassification(
            broad_intent=BroadIntent.AMBIGUOUS,
            specific_intent=None,
            confidence=0.3,
            requires_data=False,
            suggested_tools=[]
        )
    
    def _check_data_references(self, message: str) -> bool:
        """Check if message explicitly references uploaded data"""
        data_refs = [
            'my data', 'the data', 'my file', 'the file',
            'uploaded', 'my csv', 'the csv', 'my shapefile',
            'this data', 'these values', 'the dataset'
        ]
        return any(ref in message for ref in data_refs)
    
    def _is_asking_about_concept(self, message: str) -> bool:
        """Check if user is asking about a concept rather than performing action"""
        concept_indicators = [
            'what is', 'what does', 'how does', 'explain',
            'tell me about', 'describe', 'mean', 'definition'
        ]
        return any(indicator in message for indicator in concept_indicators)
    
    def _contains_operation_verb(self, message: str) -> bool:
        """Check if message contains action verbs"""
        operations = [
            'analyze', 'analyse', 'plot', 'visualize', 'visualise',
            'calculate', 'compute', 'generate', 'create', 'run',
            'perform', 'execute', 'summarize', 'summarise'
        ]
        return any(op in message for op in operations)
```

### 3. Smart Router Implementation

```python
class SmartRouter:
    """
    Intelligent routing system that combines intent classification
    with tool capabilities and context awareness
    """
    
    def __init__(self):
        self.intent_classifier = SmartIntentClassifier()
        self.tool_registry = self._load_tool_registry()
        
    def route(self, message: str, session_context: dict) -> str:
        """
        Smart routing based on intent, context, and capabilities
        
        Returns: 'can_answer' | 'needs_tools' | 'needs_clarification'
        """
        
        # Step 1: Classify intent
        intent = self.intent_classifier.classify(message, session_context)
        
        # Step 2: Quick routing for high-confidence cases
        if intent.confidence > 0.9:
            if intent.requires_data and not session_context.get('has_uploaded_files'):
                # Need data but don't have it
                return 'needs_clarification'
            
            if intent.broad_intent in [BroadIntent.GREETING, BroadIntent.IDENTITY]:
                return 'can_answer'
            
            if intent.broad_intent == BroadIntent.DATA_OPERATION:
                return 'needs_tools'
        
        # Step 3: Handle knowledge queries
        if intent.broad_intent == BroadIntent.KNOWLEDGE_QUERY:
            # Check if it's about uploaded data or general concept
            if self._is_data_specific_query(message, session_context):
                return 'needs_tools'
            else:
                return 'can_answer'
        
        # Step 4: Handle ambiguous cases
        if intent.confidence < 0.5:
            # Use semantic similarity as fallback
            return self._semantic_routing_fallback(message, session_context)
        
        # Step 5: Default routing based on data availability
        if session_context.get('has_uploaded_files'):
            # When data exists and intent unclear, check if tools can help
            if self._can_tools_help(message, intent.suggested_tools):
                return 'needs_tools'
        
        # Default to conversational
        return 'can_answer'
    
    def _is_data_specific_query(self, message: str, context: dict) -> bool:
        """
        Determine if a knowledge query is about uploaded data
        """
        if not context.get('has_uploaded_files'):
            return False
        
        # Check for data-specific questions
        data_queries = [
            'what is in', 'what variables', 'what columns',
            'describe the data', 'data quality', 'missing values',
            'statistics', 'summary of the data'
        ]
        
        message_lower = message.lower()
        return any(query in message_lower for query in data_queries)
    
    def _can_tools_help(self, message: str, suggested_tools: List[str]) -> bool:
        """
        Check if available tools can meaningfully help with the request
        """
        if not suggested_tools:
            return False
        
        # Check if suggested tools are available and appropriate
        for tool in suggested_tools:
            if tool in self.tool_registry:
                tool_info = self.tool_registry[tool]
                if not tool_info.get('requires_data', True):
                    return True  # Tool doesn't need data
                # Tool needs data, which we have
                return True
        
        return False
    
    def _semantic_routing_fallback(self, message: str, context: dict) -> str:
        """
        Use semantic similarity when pattern matching fails
        """
        # This would use embeddings in production
        # For now, conservative fallback
        
        # If message is very short, likely conversational
        if len(message.split()) <= 3:
            return 'can_answer'
        
        # If data exists and message has action words, likely tools
        if context.get('has_uploaded_files'):
            action_words = ['make', 'create', 'generate', 'show', 'display']
            if any(word in message.lower() for word in action_words):
                return 'needs_tools'
        
        # Conservative default
        return 'can_answer'
```

### 4. Integration with Existing System

```python
# In analysis_routes.py, replace route_with_mistral with:

async def smart_route(message: str, session_context: dict) -> str:
    """
    Smart routing using intent classification and context awareness
    """
    router = SmartRouter()
    
    # Add conversation history to context if available
    if 'conversation_history' in session:
        session_context['conversation_history'] = session['conversation_history']
    
    # Get routing decision
    decision = router.route(message, session_context)
    
    # Log routing decision for learning
    logger.info(f"Smart routing: '{message[:50]}...' -> {decision}")
    
    return decision
```

## Key Advantages

### 1. Context Awareness
- Understands when "analyze" means concept vs. data operation
- Considers conversation history
- Knows what data is available

### 2. Intent-Based
- Focuses on what user wants to achieve
- Not fooled by keyword presence
- Handles paraphrasing naturally

### 3. Graceful Degradation
- Multiple fallback strategies
- Semantic similarity when patterns fail
- Conservative defaults to avoid errors

### 4. Extensible
- Easy to add new intents
- Can learn from user corrections
- Tool registry can be updated dynamically

### 5. Maintainable
- No hardcoded keyword lists
- Clear separation of concerns
- Testable components

## Migration Strategy

### Phase 1: Parallel Testing
- Run both old and new routing
- Log differences for analysis
- Measure accuracy improvement

### Phase 2: Gradual Rollout
- Use new routing for high-confidence cases
- Fall back to old routing when uncertain
- Gather user feedback

### Phase 3: Full Replacement
- Replace old routing completely
- Remove hardcoded patterns
- Continuous improvement through logging

## Success Metrics

1. **Routing Accuracy**: Target 95%+ correct routing
2. **Clarification Rate**: < 5% of messages need clarification
3. **User Satisfaction**: Reduced complaints about wrong routing
4. **Response Time**: < 100ms routing decision
5. **Edge Case Handling**: 90%+ success on ambiguous queries

## Conclusion

This smart routing system solves the fundamental problems:
- **No more hardcoding** - Intent-based, not keyword-based
- **Context aware** - Understands data availability and conversation
- **Tool aware** - Knows what tools can actually do
- **Graceful handling** - Multiple fallback strategies
- **Maintainable** - Clean architecture, easy to extend

The system can be implemented incrementally and will significantly improve the user experience by correctly routing messages based on actual intent rather than brittle pattern matching.