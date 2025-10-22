# LM Arena Style Implementation for ChatMRPT

## Overview
Implement a side-by-side blind comparison interface similar to LM Arena/Chatbot Arena for local models.

## UI Design (Based on Screenshot)

### Layout
```
┌─────────────────────────────────────────────────────────┐
│                    ⚔️ Battle Mode                        │
├──────────────────────┬──────────────────────────────────┤
│   Assistant A        │   Assistant B                    │
│   (Model Hidden)      │   (Model Hidden)                 │
├──────────────────────┼──────────────────────────────────┤
│                      │                                  │
│  [Response Area]     │  [Response Area]                 │
│                      │                                  │
│  [📋][👍][🔄]        │  [📋][👎][🔄]                   │
├──────────────────────┴──────────────────────────────────┤
│  [⬅️ Left is Better] [It's a tie 🤝] [Right is Better ➡️] │
├──────────────────────────────────────────────────────────┤
│              [Ask followup question...]                  │
└─────────────────────────────────────────────────────────┘
```

## Technical Architecture

### 1. Local Model Setup with vLLM

```python
# model_server.py
import os
from vllm import LLM, SamplingParams

class LocalModelServer:
    def __init__(self):
        # Download models once and store locally
        self.models = {
            'llama3.1-8b': LLM(
                model="meta-llama/Llama-3.1-8B-Instruct",
                tensor_parallel_size=1,
                gpu_memory_utilization=0.9
            ),
            'mistral-7b': LLM(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                tensor_parallel_size=1,
                gpu_memory_utilization=0.9
            ),
            'qwen2.5-7b': LLM(
                model="Qwen/Qwen2.5-7B-Instruct",
                tensor_parallel_size=1,
                gpu_memory_utilization=0.9
            ),
            'phi3-mini': LLM(
                model="microsoft/Phi-3-mini-4k-instruct",
                tensor_parallel_size=1,
                gpu_memory_utilization=0.5  # Smaller model
            )
        }
        
    def get_random_pair(self):
        """Select 2 random models for battle"""
        import random
        models = list(self.models.keys())
        return random.sample(models, 2)
```

### 2. Model Download & Storage

```bash
# download_models.sh
#!/bin/bash

# Create model directory
mkdir -p /opt/models

# Download models using huggingface-cli
pip install huggingface-hub

# Download each model (7-15GB each)
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct \
    --local-dir /opt/models/llama3.1-8b

huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3 \
    --local-dir /opt/models/mistral-7b

huggingface-cli download Qwen/Qwen2.5-7B-Instruct \
    --local-dir /opt/models/qwen2.5-7b

# Total disk space needed: ~40-50GB for 4 models
```

### 3. AWS EC2 Instance Requirements

```yaml
# For running 2 models simultaneously
Instance Type: g5.2xlarge (recommended)
  - 1 NVIDIA A10G GPU (24GB VRAM)
  - 8 vCPUs
  - 32 GB RAM
  - Cost: ~$1.20/hour

Alternative: g4dn.2xlarge (budget option)
  - 1 NVIDIA T4 GPU (16GB VRAM)
  - 8 vCPUs  
  - 32 GB RAM
  - Cost: ~$0.75/hour

Storage: 100GB EBS volume for models
```

### 4. Backend Implementation

```python
# app/core/arena_manager.py
class ArenaManager:
    def __init__(self):
        self.battles = {}  # Track ongoing battles
        self.results = []  # Store comparison results
        
    async def start_battle(self, session_id: str, message: str):
        """Initialize a new battle"""
        # Select random models
        model_a, model_b = self.get_random_pair()
        
        # Store battle info (hidden from user)
        self.battles[session_id] = {
            'model_a': model_a,
            'model_b': model_b,
            'messages': []
        }
        
        # Get responses in parallel
        response_a = await self.get_response(model_a, message)
        response_b = await self.get_response(model_b, message)
        
        return {
            'response_a': response_a,
            'response_b': response_b,
            'battle_id': session_id
        }
    
    def record_preference(self, session_id: str, preference: str):
        """Record user's preference"""
        battle = self.battles.get(session_id)
        if battle:
            self.results.append({
                'model_a': battle['model_a'],
                'model_b': battle['model_b'],
                'winner': preference,  # 'left', 'right', or 'tie'
                'timestamp': datetime.now()
            })
            
            # Calculate ELO ratings (optional)
            self.update_elo_ratings(battle, preference)
```

### 5. Frontend Implementation

```javascript
// arena-interface.js
class ArenaInterface {
    constructor() {
        this.currentBattle = null;
        this.initUI();
    }
    
    initUI() {
        // Create split view
        this.container = document.getElementById('arena-container');
        this.container.innerHTML = `
            <div class="arena-split-view">
                <div class="model-panel left-panel">
                    <h3>Assistant A</h3>
                    <div class="response-area" id="response-a"></div>
                    <div class="actions">
                        <button onclick="copyResponse('a')">📋</button>
                        <button onclick="regenerate('a')">🔄</button>
                    </div>
                </div>
                <div class="model-panel right-panel">
                    <h3>Assistant B</h3>
                    <div class="response-area" id="response-b"></div>
                    <div class="actions">
                        <button onclick="copyResponse('b')">📋</button>
                        <button onclick="regenerate('b')">🔄</button>
                    </div>
                </div>
            </div>
            <div class="voting-area">
                <button onclick="vote('left')" class="vote-btn">
                    ⬅️ Left is Better
                </button>
                <button onclick="vote('tie')" class="vote-btn">
                    🤝 It's a tie
                </button>
                <button onclick="vote('right')" class="vote-btn">
                    Right is Better ➡️
                </button>
            </div>
        `;
    }
    
    async startBattle(message) {
        // Show loading
        this.showLoading();
        
        // Get responses from backend
        const response = await fetch('/api/arena/battle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message})
        });
        
        const data = await response.json();
        this.currentBattle = data.battle_id;
        
        // Display responses simultaneously
        this.displayResponse('a', data.response_a);
        this.displayResponse('b', data.response_b);
    }
    
    async vote(preference) {
        // Send vote to backend
        await fetch('/api/arena/vote', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                battle_id: this.currentBattle,
                preference: preference
            })
        });
        
        // Reveal models after voting
        this.revealModels();
    }
}
```

### 6. Alternative: Toggle View (Your Suggestion)

```javascript
// Simple toggle approach - one response at a time
class ToggleModelView {
    constructor() {
        this.models = ['llama3.1', 'mistral', 'qwen'];
        this.currentModel = 0;
        this.responses = {};
    }
    
    async getAllResponses(message) {
        // Get all responses in background
        for (let model of this.models) {
            this.responses[model] = await this.getResponse(model, message);
        }
    }
    
    showResponse(modelIndex) {
        const model = this.models[modelIndex];
        document.getElementById('response-area').innerHTML = this.responses[model];
        document.getElementById('model-indicator').textContent = `Model ${modelIndex + 1} of ${this.models.length}`;
    }
    
    nextModel() {
        this.currentModel = (this.currentModel + 1) % this.models.length;
        this.showResponse(this.currentModel);
    }
}
```

## Implementation Timeline

### Week 1: Infrastructure Setup
- [ ] Provision GPU instance on AWS
- [ ] Install vLLM and dependencies
- [ ] Download and test models locally
- [ ] Set up model serving endpoints

### Week 2: Backend Development
- [ ] Create ArenaManager class
- [ ] Implement parallel inference
- [ ] Add session management
- [ ] Build voting/preference API

### Week 3: Frontend Development
- [ ] Build split-screen interface
- [ ] Add voting buttons
- [ ] Implement model reveal feature
- [ ] Create mobile-responsive design

### Week 4: Testing & Analytics
- [ ] Load testing with multiple models
- [ ] Build analytics dashboard
- [ ] ELO rating calculation (optional)
- [ ] Deploy to production

## Cost Analysis

### One-Time Costs
- Model downloads: Free (from HuggingFace)
- Development time: 3-4 weeks

### Ongoing Costs (AWS)
- GPU instance (g5.2xlarge): ~$870/month if running 24/7
- Or use spot instances: ~$350/month
- Storage (100GB): ~$10/month
- **Total: $360-880/month**

### Compared to API Costs
- OpenAI GPT-4: $30-60 per million tokens
- Mistral API: $2-8 per million tokens
- **Break-even: ~20-30 million tokens/month**

## Advantages of Local Deployment

1. **No API costs** after initial setup
2. **Complete privacy** - data never leaves your servers
3. **No rate limits** - process as many requests as GPU allows
4. **Consistent latency** - no API variability
5. **Model control** - choose exact versions, fine-tune if needed

## Challenges & Solutions

### Challenge: GPU Memory for Multiple Models
**Solution**: Use model quantization (4-bit) to fit more models:
```python
# Load models in 4-bit to save memory
model = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",
    quantization="awq",  # 4-bit quantization
    gpu_memory_utilization=0.4  # Use only 40% per model
)
```

### Challenge: Response Time
**Solution**: 
- Pre-load all models at startup
- Use batch inference when possible
- Implement response caching

### Challenge: Model Quality vs Size
**Solution**: Mix of model sizes:
- 1 large model (13B) for quality
- 2-3 smaller models (7B) for variety
- 1 tiny model (3B) for speed baseline

## Recommendation

**Go with the Arena-style interface!** It's proven to work well (LMSYS has run millions of comparisons this way). 

**Start with:**
1. 3 models: Llama 3.1, Mistral 7B, Qwen 2.5
2. Simple split-screen view (like LM Arena)
3. Blind testing (hide model names)
4. Basic voting buttons

**AWS Setup:**
- Use g5.xlarge for testing ($0.50/hour)
- Scale to g5.2xlarge for production
- Consider spot instances to save 70% on costs

This gives you complete control, no API costs, and valuable comparison data for your thesis!