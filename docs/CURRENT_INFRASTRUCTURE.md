# Current AWS Infrastructure Analysis

## Production Instances (ACTIVE)

### Instance 1: 3.21.167.170
- **Type**: CPU-only instance (likely t3.xlarge or m5.xlarge)
- **CPU**: 4 vCPUs - Intel Xeon Platinum 8259CL @ 2.50GHz  
- **RAM**: 16 GB
- **Storage**: 100 GB (80% used)
- **GPU**: ❌ **NONE**
- **Purpose**: Main ChatMRPT application server

### Instance 2: 18.220.103.20  
- **Type**: CPU-only instance (likely t3.medium)
- **CPU**: 2 vCPUs - Intel Xeon Platinum 8259CL @ 2.50GHz
- **RAM**: 4 GB
- **Storage**: 40 GB (77% used)
- **GPU**: ❌ **NONE**
- **Purpose**: Secondary application server

## GPU Instance Status

### Configured GPU IP: 172.31.45.157
- **Status**: ❌ **NOT RUNNING/NOT ACCESSIBLE**
- **Type**: Was planned as g5.2xlarge (if it existed)
- **Expected**: 1x NVIDIA A10G (24GB VRAM)
- **Current State**: Either never launched or terminated

## Key Findings

### ⚠️ NO GPU INSTANCES CURRENTLY RUNNING
- Both production instances are **CPU-only**
- Cannot run vLLM or local models on current instances
- The IP `172.31.45.157` in `.env` points to a non-existent GPU instance

### Why This Matters for Arena Mode
Arena mode requires GPU for running 5 local models:
1. Llama 3.1 8B - Needs ~4-5GB VRAM
2. Mistral 7B - Needs ~4GB VRAM  
3. Qwen 3 8B - Needs ~5GB VRAM
4. BioMistral 7B - Needs ~4GB VRAM
5. Gemma 2 9B - Needs ~6GB VRAM

**Total VRAM needed**: ~23-24GB (perfect for g5.2xlarge)

## Current Options

### Option 1: Launch New GPU Instance (RECOMMENDED)
- **Instance Type**: g5.2xlarge or g5.4xlarge
- **Cost**: ~$1.21-$1.61/hour
- **Setup Time**: 30-60 minutes with model downloads

### Option 2: Use Cloud LLM APIs (Alternative)
- Keep using OpenAI for all queries
- Higher per-request cost
- No local model control

### Option 3: CPU-based Inference (NOT Recommended)
- Extremely slow (10-100x slower than GPU)
- Would max out CPU on production servers
- Poor user experience

## Next Steps

To enable Arena mode with 5 local models, you MUST:
1. **Launch a GPU instance** (g5.2xlarge minimum)
2. **Download all 5 models** (~75GB total)
3. **Run vLLM server** on the GPU instance
4. **Update .env** with new GPU instance IP

## Cost Comparison

### Current (CPU only + OpenAI API):
- 2 CPU instances: ~$100-150/month
- OpenAI API: Variable ($200-1000+/month based on usage)

### With GPU Instance:
- 2 CPU instances: ~$100-150/month
- 1 GPU instance: ~$875/month (g5.2xlarge)
- OpenAI API: Reduced (only for tool-using queries)

**Potential savings**: If API usage > $875/month, GPU becomes cost-effective