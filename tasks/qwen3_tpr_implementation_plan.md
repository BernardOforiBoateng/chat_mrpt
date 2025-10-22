# Qwen3 Local LLM Implementation for TPR Analysis
## Staging Server Deployment Plan

---

## 🎯 Goal
Enable fully private, exploratory TPR data analysis using Qwen3 on staging server where the model has FULL access to the uploaded TPR data and can answer ANY question about it.

---

## 📋 Implementation Steps

### Phase 1: Infrastructure Setup (Day 1)

#### Step 1: Check Current Staging Specs
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.117.115.217
free -h
df -h
lscpu
```

#### Step 2: Upgrade Staging Instance (if needed)
- Current: t3.medium (2 vCPU, 4GB RAM)
- Target: t3.xlarge (4 vCPU, 16GB RAM) or t3.2xlarge (8 vCPU, 32GB RAM)
- For Qwen3-30B: Need at least 32GB RAM

```bash
# Stop instance, change type in AWS Console, restart
```

#### Step 3: Install Ollama
```bash
# SSH to staging
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.117.115.217

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Verify installation
ollama --version
curl http://localhost:11434/api/tags
```

#### Step 4: Download Qwen3 Model
```bash
# Start with smaller model for testing
ollama pull qwen3:8b

# Once validated, pull larger model
ollama pull qwen3:30b-a3b  # MoE model, good balance

# Test model
ollama run qwen3:8b "What is test positivity rate?"
```

---

### Phase 2: Code Integration (Day 1-2)

#### Step 5: Create OllamaManager Class
Create `app/core/ollama_manager.py`:

```python
import json
import requests
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class OllamaManager:
    """Local LLM manager using Ollama for TPR analysis."""
    
    def __init__(self, model: str = "qwen3:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
    def generate_response(self, prompt: str, context: Optional[Any] = None, 
                         system_message: Optional[str] = None, **kwargs) -> str:
        """Generate response with full data context."""
        
        # Build the full prompt with context
        full_prompt = ""
        if system_message:
            full_prompt += f"System: {system_message}\n\n"
        
        if context and isinstance(context, dict) and 'tpr_data' in context:
            # Include full TPR data in prompt
            full_prompt += "TPR Data Available:\n"
            full_prompt += json.dumps(context['tpr_data'], indent=2)[:10000]  # Limit for testing
            full_prompt += "\n\nUser Query: " + prompt
        else:
            full_prompt = prompt
            
        # Call Ollama API
        response = requests.post(
            f"{self.api_url}/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "format": "json" if kwargs.get('json_mode') else None
            }
        )
        
        if response.status_code == 200:
            return response.json()['response']
        else:
            return f"Error: {response.status_code}"
    
    def analyze_tpr_data(self, tpr_df, query: str) -> Dict[str, Any]:
        """Analyze TPR data with structured output."""
        
        # Convert dataframe to dict for model
        data_summary = {
            "shape": tpr_df.shape,
            "columns": list(tpr_df.columns),
            "sample_data": tpr_df.head(10).to_dict('records'),
            "statistics": tpr_df.describe().to_dict()
        }
        
        prompt = f"""
        You have access to TPR (Test Positivity Rate) data with the following structure:
        {json.dumps(data_summary, indent=2)}
        
        User Query: {query}
        
        Respond with a JSON object containing:
        - answer: Direct answer to the query
        - analysis: Detailed analysis
        - recommendations: Any recommendations based on the data
        - data_points: Specific data points referenced
        """
        
        response = self.generate_response(
            prompt=prompt,
            json_mode=True
        )
        
        try:
            return json.loads(response)
        except:
            return {"answer": response, "analysis": "", "recommendations": []}
```

#### Step 6: Update Service Container
Modify `app/services/container.py`:

```python
def _create_llm_manager(self, container: 'ServiceContainer'):
    """Create LLM manager based on configuration."""
    
    # Check if we should use local LLM for TPR
    use_local_for_tpr = self._app.config.get('USE_LOCAL_LLM_TPR', False)
    
    # Check if current request is TPR-related (you'll need to implement this check)
    is_tpr_request = container.get('is_tpr_request', False)
    
    if use_local_for_tpr and is_tpr_request:
        # Use Ollama for TPR analysis
        from ..core.ollama_manager import OllamaManager
        logger.info("Using Ollama/Qwen3 for TPR analysis")
        return OllamaManager(
            model=self._app.config.get('OLLAMA_MODEL', 'qwen3:8b'),
            base_url=self._app.config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        )
    else:
        # Use OpenAI for general queries
        from ..core.llm_manager import LLMManager
        return LLMManager(
            api_key=self._app.config.get('OPENAI_API_KEY'),
            model=self._app.config.get('OPENAI_MODEL_NAME', 'gpt-4o'),
            interaction_logger=interaction_logger
        )
```

#### Step 7: Create TPR Context Feeder
Create `app/services/tpr_ollama_service.py`:

```python
import pandas as pd
from typing import Dict, Any
import os

class TPROllamaService:
    """Service to feed full TPR data to Ollama."""
    
    def __init__(self, ollama_manager):
        self.llm = ollama_manager
        
    def load_and_analyze_tpr(self, session_id: str, file_path: str, query: str) -> Dict[str, Any]:
        """Load TPR file and provide full context to Ollama."""
        
        # Load the TPR data
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        # Prepare full context
        context = {
            "file_name": os.path.basename(file_path),
            "total_rows": len(df),
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict(),
            "full_data": df.to_dict('records')  # FULL DATA ACCESS!
        }
        
        # Create comprehensive prompt
        prompt = f"""
        You have COMPLETE access to TPR (Test Positivity Rate) data.
        
        Data Overview:
        - File: {context['file_name']}
        - Rows: {context['total_rows']}
        - Columns: {', '.join(context['columns'])}
        
        FULL DATA:
        {df.to_string()}
        
        User Query: {query}
        
        Analyze this data and provide insights. You can:
        - Calculate any statistics
        - Identify trends and patterns
        - Compare across locations/time
        - Find anomalies
        - Make recommendations
        """
        
        # Get response from Ollama with full data context
        response = self.llm.analyze_tpr_data(df, query)
        
        return {
            "success": True,
            "response": response,
            "data_shape": df.shape,
            "model_used": "qwen3_local"
        }
```

---

### Phase 3: Testing & Validation (Day 2)

#### Step 8: Test Script
Create `test_ollama_tpr.py`:

```python
#!/usr/bin/env python3
import sys
import pandas as pd
from app.core.ollama_manager import OllamaManager

# Test queries
test_queries = [
    "Which ward has the highest test positivity rate?",
    "What is the trend over the last 3 months?",
    "Find anomalies in the data",
    "Which facilities need immediate intervention?",
    "Compare urban vs rural positivity rates"
]

# Load sample TPR data
df = pd.read_excel('sample_tpr_data.xlsx')

# Initialize Ollama
ollama = OllamaManager(model="qwen3:8b")

print("Testing Ollama/Qwen3 with TPR data...")
print(f"Data shape: {df.shape}")
print("-" * 50)

for query in test_queries:
    print(f"\nQuery: {query}")
    result = ollama.analyze_tpr_data(df, query)
    print(f"Response: {result.get('answer', 'No answer')}")
    print("-" * 50)
```

#### Step 9: Privacy Validation
```bash
# Monitor network traffic while running queries
sudo tcpdump -i any -w ollama_test.pcap &

# Run test queries
python test_ollama_tpr.py

# Stop capture and analyze
sudo pkill tcpdump
tcpdump -r ollama_test.pcap | grep -E "openai|api\."
# Should show NO external API calls
```

---

### Phase 4: Deployment (Day 2-3)

#### Step 10: Environment Configuration
Add to `.env` on staging:
```bash
# Local LLM Configuration
USE_LOCAL_LLM_TPR=true
OLLAMA_MODEL=qwen3:8b
OLLAMA_BASE_URL=http://localhost:11434

# Keep OpenAI for non-TPR queries
OPENAI_API_KEY=your_key_here
```

#### Step 11: Update TPR Upload Route
Modify `app/web/routes/upload_routes.py` to use Ollama for TPR:

```python
@upload_bp.route('/process_tpr', methods=['POST'])
def process_tpr():
    # Existing upload logic...
    
    # Mark this as TPR request for service container
    current_app.services.set('is_tpr_request', True)
    
    # Use Ollama-powered service for analysis
    if current_app.config.get('USE_LOCAL_LLM_TPR'):
        from app.services.tpr_ollama_service import TPROllamaService
        tpr_service = TPROllamaService(current_app.services.llm_manager)
        result = tpr_service.load_and_analyze_tpr(
            session_id=session_id,
            file_path=file_path,
            query=request.json.get('query', 'Analyze this TPR data')
        )
    else:
        # Existing OpenAI logic
        pass
```

#### Step 12: Deploy to Staging
```bash
# Copy files to staging
scp -i aws_files/chatmrpt-key.pem \
    app/core/ollama_manager.py \
    app/services/tpr_ollama_service.py \
    ec2-user@18.117.115.217:~/ChatMRPT/app/

# Restart service
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.117.115.217
sudo systemctl restart chatmrpt

# Monitor logs
sudo journalctl -u chatmrpt -f
```

---

## 🧪 Testing Checklist

- [ ] Ollama installed and running on staging
- [ ] Qwen3 model downloaded and responsive
- [ ] OllamaManager class integrates with existing code
- [ ] TPR file upload triggers Ollama (not OpenAI)
- [ ] Model can answer exploratory questions about TPR data
- [ ] JSON structured outputs working
- [ ] No external API calls detected (privacy validated)
- [ ] Response time acceptable (<5 seconds)
- [ ] Can handle full TPR dataset (10,000+ rows)
- [ ] Memory usage stable

---

## 📊 Success Metrics

1. **Privacy**: Zero external API calls for TPR data
2. **Functionality**: Can answer 90% of exploratory TPR queries
3. **Performance**: <5 second response time
4. **Accuracy**: Correct calculations and insights
5. **Stability**: No crashes with large datasets

---

## 🎉 Expected Outcomes

After implementation, users can ask questions like:
- "Which facilities have increasing positivity rates?"
- "What's the correlation between rainfall and malaria cases?"
- "Find all wards where positivity > 30% last month"
- "Compare this month's data with last year"
- "Which LGAs need urgent intervention?"

And Qwen3 will analyze the FULL dataset locally and provide answers without any data leaving the server!

---

## 🚀 Next Steps After Success

1. Expand to other data types (not just TPR)
2. Fine-tune Qwen3 on malaria-specific terminology
3. Add visualization generation capabilities
4. Implement conversation memory for follow-up questions
5. Deploy to production after validation