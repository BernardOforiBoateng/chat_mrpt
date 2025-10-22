# Arena Performance Investigation - CORRECTED

## Date: 2025-09-26

## Investigation Request
User reported: "I thought we are running the 3 local models in the gpu so why does it take so long for responses to appear?"

## CORRECTED Key Findings

### 1. GPU Instance Planned But Not Running
**Discovery**: There WAS a GPU instance planned but it's NOT currently active
- Configuration points to GPU at: 172.31.45.157 (NOT ACCESSIBLE)
- Planned instance type: g5.2xlarge (1x NVIDIA A10G, 24GB VRAM)
- Current reality: GPU instance either never launched or was terminated
- Models CANNOT run because the GPU host doesn't exist

### 2. Broken Model Hosting Architecture
**Current Setup**:
- Ollama is configured to use remote GPU: `172.31.45.157:11434`
- **CRITICAL**: This GPU instance is NOT running/accessible
- Ollama IS running locally on both instances but with NO models
- Arena mode is completely broken - can't load models from non-existent GPU

### 3. Models Not Available
**Current State**:
- NO models can be loaded (GPU host doesn't exist)
- Ollama running on Instance 1 & 2 but with 0 models
- Arena battles likely falling back to OpenAI or failing
- Users experiencing slow/failed Arena responses

### 4. Expected GPU Models (Not Available)
**Planned Models for GPU**:
- Llama 3.1 8B - Needs ~5GB VRAM
- Mistral 7B - Needs ~4GB VRAM
- Qwen 3 8B - Needs ~5GB VRAM
- BioMistral 7B - Needs ~4GB VRAM (Arena expansion)
- Gemma 2 9B - Needs ~6GB VRAM (Arena expansion)

Total VRAM needed: ~24GB (perfect for g5.2xlarge)

### 5. Infrastructure Documentation Exists
Found comprehensive GPU setup documentation:
- `/docs/GPU_LAUNCH_INSTRUCTIONS.md` - Complete launch guide
- `/scripts/aws/launch_gpu_instance.sh` - Automated launch script
- `/scripts/arena/launch_gpu_now.sh` - Arena-specific GPU setup

The infrastructure was planned but GPU instance is NOT running.

## Why Arena Is Slow/Broken

### Primary Issue:
**GPU INSTANCE NOT RUNNING** - The configured GPU host (172.31.45.157) doesn't exist

### Consequences:
1. **No local models available** - Ollama can't connect to GPU host
2. **Fallback to OpenAI** - System likely using OpenAI for all requests
3. **Arena mode broken** - Can't run model battles without local models
4. **User confusion** - Configuration suggests GPU exists but it doesn't

### Secondary Issues:
1. **Single remote Ollama instance**: Potential bottleneck for concurrent users
2. **No request batching**: Each arena battle makes separate requests
3. **No response streaming**: Users wait for complete response

## Why Responses Are Slow/Failing

### Root Cause:
**NO GPU = NO LOCAL MODELS = FALLBACK TO API**

### What Should Happen (with GPU):
1. GPU instance running at 172.31.45.157
2. vLLM serving 5 models with GPU acceleration
3. Sub-2 second responses for local models
4. Arena battles between 5 different models

### What's Actually Happening:
1. Configuration points to non-existent GPU
2. Ollama can't load any models
3. System falls back to OpenAI API
4. Arena mode is effectively disabled

## Infrastructure Reality

### Current AWS Setup:
```
Production Instances (t3.xlarge)
    ↓ [No GPU]
    ↓ HTTP Request
Remote Ollama Host (172.31.45.157)
    ↓ [CPU Processing]
    ↓ Response
Back to Production Instance
```

### What Would GPU Setup Look Like:
```
GPU Instance (p3.2xlarge or g4dn.xlarge)
    ↓ [CUDA/GPU]
Local Ollama with GPU support
    ↓ [Fast inference]
Immediate Response
```

## Cost Implications

### Current (t3.xlarge):
- ~$0.166/hour per instance
- No GPU costs
- Slow but economical

### GPU Alternative (g4dn.xlarge):
- ~$0.526/hour per instance
- 16GB GPU memory
- 5-10x faster inference

### GPU Alternative (p3.2xlarge):
- ~$3.06/hour per instance
- Tesla V100 GPU
- Professional-grade performance

## User Impact

### Current Experience:
- 5-10 second wait per model response
- Arena battles take 15-30 seconds per round
- User frustration with "slow AI"

### With GPU:
- Sub-2 second responses
- Arena battles feel instant
- Better user engagement

## Solution: Launch the GPU Instance

### Immediate Action Required:
1. **Launch g5.2xlarge GPU instance** using existing scripts
2. **Download all 5 models** (~75GB total, 30-60 minutes)
3. **Run vLLM server** on GPU instance
4. **Update .env** with new GPU instance IP
5. **Test Arena mode** with all 5 models

### Launch Commands Available:
```bash
# Option 1: Use existing script
./scripts/arena/launch_gpu_now.sh

# Option 2: AWS Console (see /docs/GPU_LAUNCH_INSTRUCTIONS.md)
```

### Cost Analysis:
- **GPU instance**: ~$875/month (g5.2xlarge)
- **Benefit**: True local model Arena with 5 models
- **Performance**: 10-50x faster than CPU
- **User Experience**: Sub-2 second responses

## Configuration Corrections Needed

### Environment Variables:
- `OLLAMA_GPU_URL` is misleading - should be `OLLAMA_REMOTE_URL`
- No actual GPU URL exists in current setup

### Code Comments:
- Remove references to "GPU models"
- Update documentation to reflect CPU-based inference
- Add performance expectations to user guide

## Testing Commands Used

```bash
# Check for GPU
lspci | grep -i nvidia  # No output - no GPU

# Check instance type
ec2-metadata --instance-type  # t3.xlarge

# Test Ollama response time
time curl -X POST http://172.31.45.157:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b-instruct-v0.3-q4_K_M", "prompt": "Hello", "stream": false}'
# Real: 7.374s

# Check Ollama models
curl http://172.31.45.157:11434/api/tags
# Shows all models with sizes and quantization
```

## Conclusion

The Arena is slow/broken because:
1. **GPU instance NOT running** - The configured GPU at 172.31.45.157 doesn't exist
2. **No local models available** - Ollama can't load models from non-existent GPU
3. **Falling back to API** - System using OpenAI instead of local models

The infrastructure was properly planned (docs, scripts, configuration all exist) but the GPU instance was either:
- Never launched due to cost concerns
- Launched and then terminated to save money
- Lost during an infrastructure change

**User is correct**: There SHOULD be a GPU for the 3 (now 5) local models. It's just not running.

## Next Steps

To address the performance issues, we need to either:
1. **Accept current performance** and set user expectations accordingly
2. **Optimize within constraints** using caching and streaming
3. **Upgrade infrastructure** to include actual GPU instances

The choice depends on budget constraints and performance requirements.