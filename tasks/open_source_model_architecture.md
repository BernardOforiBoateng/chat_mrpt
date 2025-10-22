# Open Source Model Architecture Plan

## Current State
The codebase is tightly coupled to OpenAI's API:
- `llm_manager.py` expects OpenAI client format
- `request_interpreter.py` relies on `tool_calls` structure
- Streaming assumes OpenAI's chunk format
- Function calling is core to tool execution

## Required Components for Open Source Models

### 1. Model Abstraction Layer
```python
class ModelAdapter(ABC):
    @abstractmethod
    def format_prompt(self, messages, system_prompt, tools=None):
        """Format prompt for specific model"""
        pass
    
    @abstractmethod
    def parse_response(self, response):
        """Parse model output to standard format"""
        pass
    
    @abstractmethod
    def extract_tool_calls(self, text):
        """Extract tool intentions from text"""
        pass
```

### 2. Tool Call Parser
Since open source models output text, not structured calls:

```python
class ToolCallParser:
    def parse_llama_output(self, text):
        # Look for patterns like:
        # "I'll use the run_analysis tool with variables=['var1', 'var2']"
        # Convert to: {"name": "run_analysis", "args": {"variables": ["var1", "var2"]}}
        pass
    
    def parse_mistral_output(self, text):
        # Different parsing logic for Mistral's output style
        pass
```

### 3. Model Registry
```python
MODELS = {
    'llama-3.1-8b': {
        'adapter': LlamaAdapter,
        'supports_tools': False,  # Needs text parsing
        'context_length': 8192,
        'prompt_template': "[INST] {system} [/INST] {user}",
    },
    'mistral-7b': {
        'adapter': MistralAdapter,
        'supports_tools': False,
        'context_length': 32768,
        'prompt_template': "<s>[INST] {prompt} [/INST]",
    },
    'qwen-2.5-coder': {
        'adapter': QwenAdapter,
        'supports_tools': True,  # Has some function calling support
        'context_length': 32768,
    }
}
```

### 4. Prompt Engineering for Tool Use
Train models to output parseable format:

```python
TOOL_USE_PROMPT = """
When you need to use a tool, output in this exact format:
<tool_use>
tool_name: {name}
arguments: {json_args}
</tool_use>

Available tools:
{tool_descriptions}

Example:
User: "Check the data quality"
Assistant: I'll check the data quality for you.
<tool_use>
tool_name: run_data_quality_check
arguments: {"session_id": "abc123"}
</tool_use>
"""
```

### 5. Response Streaming Adapter
```python
class StreamingAdapter:
    def stream_openai(self, response):
        # Current implementation
        pass
    
    def stream_ollama(self, response):
        # Convert Ollama's format to expected format
        for chunk in response:
            yield {
                'content': chunk.get('response', ''),
                'done': chunk.get('done', False)
            }
    
    def stream_vllm(self, response):
        # Convert vLLM's format
        pass
```

## Implementation Steps

1. **Phase 1: Abstraction Layer**
   - Create `ModelAdapter` base class
   - Implement adapters for 2-3 models (Llama, Mistral, Qwen)
   - Add model selection UI

2. **Phase 2: Tool Calling Translation**
   - Build robust text-to-tool parser
   - Add validation and error handling
   - Create test suite for different model outputs

3. **Phase 3: Model Management**
   - Local model storage system
   - Model downloading/updating
   - Resource management (GPU/CPU allocation)

4. **Phase 4: UI Integration**
   - Model selector dropdown
   - Model capabilities indicator
   - Performance metrics display

## Challenges to Address

1. **Reliability**: Open source models may hallucinate tool names or arguments
2. **Performance**: Local models are slower than OpenAI
3. **Context Length**: Some models have smaller context windows
4. **Consistency**: Different models produce varying output quality
5. **Resource Requirements**: Need significant GPU/RAM for local models

## Recommended Models for Testing

1. **Llama 3.1 8B**: Good general performance, moderate resources
2. **Mistral 7B**: Strong reasoning, good context length
3. **Qwen 2.5 Coder**: Better at understanding code/tools
4. **Phi-3**: Smaller model, faster inference
5. **DeepSeek Coder**: Specialized for technical tasks

## Fallback Strategy

Always keep OpenAI as fallback when:
- Local models fail to parse correctly
- Complex tool orchestration needed
- User explicitly requests higher accuracy