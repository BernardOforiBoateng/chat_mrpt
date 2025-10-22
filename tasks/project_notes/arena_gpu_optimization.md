# Arena GPU Optimization - Fixing 1+ Minute Response Times

## Date: 2025-09-26

## Problem
Users reporting Arena responses take over 1 minute, despite having a GPU instance.

## Investigation Findings

### GPU Instance Status
- **Instance**: g5.xlarge with NVIDIA A10G (24GB VRAM)
- **Status**: ✅ Running and accessible at 172.31.45.157
- **Ollama**: ✅ Running with 3 models available
- **Cost**: $725/month

### Root Cause: Model Swapping Overhead

#### The Problem
When testing individual model response times:
- **First model** (already loaded): 0.1-0.4 seconds ✅
- **Second model** (needs swap): 7-10 seconds ⚠️
- **Third model** (needs swap): 30-40 seconds ❌

**Why?** Ollama was unloading models from GPU memory after ~5 minutes of inactivity.

#### GPU Memory Analysis
- **Total VRAM**: 23GB
- **Model sizes when loaded in GPU**:
  - llama3.1:8b: 6.1GB
  - mistral:7b: 5.8GB
  - qwen3:8b: 6.5GB
  - **Total**: 18.4GB (fits easily in 23GB!)

### The "Underutilization" Issue

Initially showed only 3MB/23GB used because:
1. Models were loaded in system RAM, not GPU VRAM
2. Ollama was swapping models in/out on each request
3. Default timeout was unloading models after 5 minutes

After optimization: 16.5GB/23GB used (all 3 models in GPU)

## Solution Implemented

### 1. Extended Keep-Alive Time
```bash
# Set models to stay loaded for 72 hours
echo "OLLAMA_KEEP_ALIVE=72h" | sudo tee -a /etc/environment
sudo systemctl restart ollama
```

### 2. Preloaded All Models
```bash
# Load all models with extended keep-alive
for model in llama3.1:8b mistral:7b qwen3:8b; do
    curl -X POST http://localhost:11434/api/generate \
        -d "{\"model\": \"$model\", \"prompt\": \"test\", \"keep_alive\": \"72h\"}"
done
```

### 3. Created Model Warmer Script
Deployed `/scripts/arena/keep_models_warm.sh` that:
- Pings each model every 5 minutes
- Keeps them loaded in GPU memory
- Prevents timeout unloading
- Running in screen session on GPU instance

## Results After Optimization

### Before (with model swapping):
- First request: 2-5 seconds
- Model switch: 7-40 seconds
- User experience: 1+ minute for some responses

### After (all models in GPU):
- **llama3.1:8b**: 0.4 seconds
- **mistral:7b**: 0.25 seconds
- **qwen3:8b**: 0.36 seconds
- Consistent sub-second responses!

## GPU Memory Usage
```
Before: 3MB / 23GB (0.01% - models not in GPU)
After: 16.5GB / 23GB (71% - all models in GPU)
```

## Monitoring Commands

Check model status:
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.118.171.148 'ollama ps'
```

Check GPU memory:
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.118.171.148 'nvidia-smi'
```

View warmer logs:
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@18.118.171.148 'screen -r model_warmer'
```

## Cost-Benefit Analysis

### Current Setup
- **GPU cost**: $725/month
- **Performance**: Sub-second responses when optimized
- **Capacity**: Can handle 3 models simultaneously
- **Remaining capacity**: ~5GB VRAM for 2 more small models

### Recommendations
1. ✅ Keep current g5.xlarge instance
2. ✅ Run model warmer continuously
3. Consider adding 2 more small models (still have 5GB VRAM free)
4. Monitor usage patterns - if models are used frequently, the warmer may not be needed

## User Impact
- **Before**: 1+ minute waits, user frustration
- **After**: Sub-second responses, smooth experience
- **Fix is live**: Models now stay loaded for 72 hours

## Next Steps
1. Monitor model warmer logs for stability
2. Consider systemd service for automatic restart
3. Add remaining 2 models (BioMistral, Gemma) if needed
4. Set up alerts if models get unloaded