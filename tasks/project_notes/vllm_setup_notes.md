# vLLM Setup Notes for Arena Mode

## Date: January 2025

## Overview
Created comprehensive vLLM infrastructure setup for running multiple LLMs simultaneously in Arena mode. The setup uses AWS GPU instances (g4dn.xlarge) with efficient model management and dynamic loading.

## Setup Scripts Created

### 1. setup_vllm_multi_model.sh (Main Script)
- **Purpose**: Complete setup for multi-model vLLM server
- **Features**:
  - Checks for existing GPU instances
  - Launches new g4dn.xlarge if needed
  - Installs vLLM with CUDA support
  - Downloads 3 models (Llama 3.1, Mistral, Qwen)
  - Creates dynamic model manager
  - Sets up nginx reverse proxy
  - Includes health checks and testing

### 2. vllm_model_manager.py (Embedded in Setup)
- **Purpose**: FastAPI server managing multiple models
- **Key Features**:
  - Dynamic model loading/unloading
  - Memory management (max 2 models in GPU)
  - OpenAI-compatible API
  - Streaming support
  - Automatic GPU memory optimization

### 3. Existing launch_gpu_instance.sh
- **Purpose**: Launch base GPU instance
- **Instance Type**: g4dn.xlarge (NVIDIA T4, 16GB VRAM)
- **AMI**: Deep Learning Base with CUDA pre-installed
- **Ports**: 22 (SSH), 5000 (Flask), 8000 (vLLM)

## Technical Architecture

### GPU Resource Management
```python
MODEL_CONFIGS = {
    "llama-3.1-8b": {
        "gpu_memory_utilization": 0.3  # 30% of 16GB = ~5GB
    },
    "mistral-7b": {
        "gpu_memory_utilization": 0.3
    },
    "qwen-2.5-7b": {
        "gpu_memory_utilization": 0.3
    }
}
```

### Model Loading Strategy
1. **On-Demand Loading**: Models loaded when first requested
2. **LRU Eviction**: Oldest model unloaded when at capacity
3. **Max Capacity**: 2 models simultaneously in GPU memory
4. **Fallback**: Can run single model with higher memory allocation

## Infrastructure Details

### AWS Resources
- **Instance Type**: g4dn.xlarge
  - vCPUs: 4
  - Memory: 16 GB
  - GPU: NVIDIA T4 (16GB VRAM)
  - Network: Up to 25 Gbps
  - Storage: 100GB gp3 EBS

### Cost Analysis
- **g4dn.xlarge**: ~$0.526/hour
- **Monthly (24/7)**: ~$380
- **Monthly (12 hours/day)**: ~$190
- **Storage**: ~$8/month (100GB)

### Performance Expectations
- **Token Generation**: 20-50 tokens/sec per model
- **Concurrent Models**: 2 with 0.3 GPU utilization
- **Model Switch Time**: 10-15 seconds
- **First Token Latency**: 200-500ms

## Deployment Process

### Step 1: Launch GPU Instance
```bash
# Check existing or launch new
./setup_vllm_multi_model.sh
```

### Step 2: Wait for Setup
- Model downloads: 10-15 minutes
- Service startup: 2-3 minutes
- Total time: ~20 minutes

### Step 3: Verify Setup
```bash
# SSH to instance
ssh -i aws_files/chatmrpt-key.pem ubuntu@<PUBLIC_IP>

# Check service
sudo systemctl status vllm-arena

# Test endpoints
curl http://<PUBLIC_IP>:8000/health
curl http://<PUBLIC_IP>:8000/v1/models
```

### Step 4: Update Application Config
```bash
# Add to .env
VLLM_BASE_URL=http://<PUBLIC_IP>:8000
USE_VLLM=true
ARENA_MODE_ENABLED=true
```

## API Endpoints

### Health Check
```bash
GET /health
Response: {
  "status": "healthy",
  "loaded_models": ["llama-3.1-8b"],
  "available_models": ["llama-3.1-8b", "mistral-7b", "qwen-2.5-7b"]
}
```

### List Models
```bash
GET /v1/models
Response: {
  "data": [
    {"id": "llama-3.1-8b", "object": "model"},
    {"id": "mistral-7b", "object": "model"},
    {"id": "qwen-2.5-7b", "object": "model"}
  ]
}
```

### Chat Completion
```bash
POST /v1/chat/completions
{
  "model": "llama-3.1-8b",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.7,
  "stream": true
}
```

## Integration with Arena Mode

### LLM Adapter Configuration
```python
# app/core/llm_adapter.py
vllm_config = {
    'base_url': os.getenv('VLLM_BASE_URL'),
    'models': ['llama-3.1-8b', 'mistral-7b', 'qwen-2.5-7b'],
    'timeout': 30,
    'streaming': True
}
```

### Arena Manager Usage
```python
# Arena selects 2 random models
models = random.sample(['llama-3.1-8b', 'mistral-7b', 'qwen-2.5-7b'], 2)

# Parallel queries to vLLM
responses = await asyncio.gather(
    query_vllm(models[0], prompt),
    query_vllm(models[1], prompt)
)
```

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce gpu_memory_utilization to 0.25
   - Run only 1 model at a time
   - Use smaller models (7B instead of 8B)

2. **Slow Model Loading**
   - Pre-download models during setup
   - Keep frequently used models in cache
   - Consider using model sharding

3. **Connection Timeouts**
   - Increase nginx proxy timeouts
   - Check security group rules
   - Verify instance is running

### Monitoring Commands
```bash
# GPU usage
nvidia-smi

# Service logs
sudo journalctl -u vllm-arena -f

# Memory usage
free -h

# Model cache
ls -la /opt/models/

# Test specific model
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-8b", "messages": [{"role": "user", "content": "test"}]}'
```

## Future Optimizations

### Short Term
1. **Model Quantization**: Use 4-bit quantization to fit more models
2. **Batch Processing**: Group requests for better throughput
3. **Response Caching**: Cache common queries
4. **Health Monitoring**: Add Prometheus metrics

### Long Term
1. **Multi-GPU Support**: Use g4dn.2xlarge for 2x T4 GPUs
2. **Model Fine-Tuning**: Custom models for malaria domain
3. **Edge Deployment**: Run smaller models on CPU instances
4. **Kubernetes**: Container orchestration for scaling

## Security Considerations

1. **Network Security**:
   - vLLM only accessible from VPC
   - Use ALB for public access
   - Enable SSL/TLS termination

2. **Model Security**:
   - Validate all inputs
   - Rate limiting per IP
   - Authentication for model access

3. **Data Privacy**:
   - No logging of user queries
   - Encrypted storage for models
   - Regular security updates

## Decision Log

### Why g4dn.xlarge?
- **Pros**: Lowest cost GPU instance, sufficient for 7B models
- **Cons**: Limited to 2 models simultaneously
- **Alternative**: g5.xlarge has A10G (24GB) but costs 40% more

### Why vLLM over Ollama?
- **Performance**: 10x faster token generation
- **Features**: Better batching, streaming, OpenAI compatibility
- **Production Ready**: Battle-tested at scale

### Why Dynamic Loading?
- **Memory Efficiency**: Fit more models in limited VRAM
- **Flexibility**: Easy to add/remove models
- **Cost Optimization**: Don't need larger instance

## Conclusion

The vLLM setup successfully enables multi-model Arena mode with:
- ✅ 3 models available for comparison
- ✅ Dynamic loading for memory efficiency
- ✅ OpenAI-compatible API
- ✅ Production-ready performance
- ✅ Cost-effective GPU utilization

Total setup time: ~20 minutes
Total lines of code: ~400 (setup script + model manager)
Monthly cost: ~$200 (12 hours/day operation)