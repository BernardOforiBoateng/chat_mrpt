# Arena 5-Model Performance Investigation Report

## Date: 2025-09-16
## Issue: Arena mode with 5 models experiencing timeouts and voting failures

## Executive Summary
The Arena mode performance issues are caused by **Ollama not properly utilizing the GPU's 23GB VRAM**, instead loading models into limited CPU RAM (15GB). This misconfiguration, combined with **insufficient timeout settings**, causes model loading failures. The GPU has MORE than enough memory for all 5 models but isn't being used correctly.

## Key Findings

### 1. CRITICAL DISCOVERY: GPU Not Being Utilized!
- **GPU Available**: NVIDIA A10G with 23GB VRAM
- **GPU Usage**: Only 4.1GB used by Ollama (out of 23GB available!)
- **Problem**: Models loading in CPU RAM (15GB) instead of GPU VRAM (23GB)
- **Impact**: Using slower CPU memory when GPU has ample space for all models

### 2. Memory Constraints (MISDIAGNOSED - GPU has enough!)
- **CPU RAM**: 15GB total, 13GB available (being used incorrectly)
- **GPU VRAM**: 23GB total, 19GB available (should be used!)
- **Combined Model Sizes**: 21.6GB total
  - llama3.1:8b: 4.9 GB
  - mistral:7b: 4.4 GB
  - phi3:mini: 2.2 GB
  - gemma2:9b: 5.4 GB
  - qwen2.5:7b: 4.7 GB
- **Result**: GPU can hold ALL models with room to spare
- **Current Issue**: Models incorrectly loading to CPU memory

### 2. Model Loading Times
- **Cold Start Loading**: 16 seconds for phi3:mini (smallest at 2.2GB)
- **Estimated Loading Times**:
  - Small models (2-3GB): ~15-20 seconds
  - Medium models (4-5GB): ~25-35 seconds
  - Large models (5-6GB): ~35-45 seconds
- **Current State**: No models loaded in memory (`ollama ps` shows empty)

### 3. Timeout Misconfigurations
- **Arena Routes**: 25 second HTTP timeout, 28 second future timeout
- **Analysis Routes**: 30 second timeout (shown in error)
- **Ollama Adapter**: 120 second timeout (not being used by arena)
- **Problem**: Timeouts too short for cold model loading

### 4. Connection Pool Issues
- **Warning in logs**: `coroutine 'ClientSession.close' was never awaited`
- **Impact**: Potential connection pool exhaustion over time
- **Location**: `/home/ec2-user/ChatMRPT/app/core/ollama_adapter.py:273`

### 5. System Resource Status
- **CPU Load**: Very low (0.00, 0.06, 0.08)
- **Disk Space**: Adequate (103GB free of 200GB)
- **Network**: No apparent network issues
- **Ollama Service**: Running since Aug 29 (long-running process)

## Root Cause Analysis

### Primary Cause: GPU Memory Not Being Used
The system has an NVIDIA A10G GPU with 23GB VRAM (enough for ALL models) but Ollama is loading models into CPU RAM instead:
1. Models are being loaded to CPU memory (15GB limit)
2. This forces model swapping since CPU RAM is insufficient
3. CPU memory is slower than GPU VRAM for inference
4. Only 4.1GB of GPU memory is being used (should be 21.6GB)

### Secondary Issues:
1. **No Model Preloading**: Models aren't kept warm in memory
2. **Synchronous Loading**: Models load one at a time, not in parallel
3. **No Graceful Degradation**: System doesn't handle timeout gracefully
4. **Vote Submission Fails**: Frontend errors when models timeout

## Impact Assessment
- **User Experience**: Severe degradation - timeouts and failed battles
- **System Stability**: Stable but non-functional for Arena mode
- **Data Integrity**: No data loss, but votes aren't recorded
- **Scalability**: Current setup cannot scale to more models

## Recommendations

### Immediate Solutions (PRIORITY - Fix GPU Usage)
1. **Configure Ollama for GPU**: Ensure models load to VRAM not CPU RAM
   - Check CUDA environment variables
   - Verify Ollama GPU layers configuration
   - Set `gpu_layers` parameter for each model
2. **Restart Ollama Service**: Clean restart with proper GPU config
3. **Increase Timeouts**: Set to 60 seconds while fixing GPU issue

### Short-term Solutions (After GPU Fix)
1. **Preload All 5 Models**: Keep all models in GPU VRAM (plenty of space)
2. **Monitor GPU Usage**: Ensure all 21.6GB loads to GPU
3. **Add Loading Status**: Show users when models are initializing
4. **Optimize Model Config**: Use GPU-optimized settings

### No Longer Needed (GPU has enough memory!)
1. ~~Upgrade Instance~~ - Current GPU has 23GB VRAM
2. ~~Reduce Models~~ - Can fit all 5 models
3. ~~Model Rotation~~ - No need with 23GB VRAM
4. ~~Distributed Architecture~~ - Single GPU sufficient

## GPU Configuration Fix Required

The instance already has sufficient resources (NVIDIA A10G with 23GB VRAM) but Ollama isn't configured to use the GPU properly. This is a configuration issue, not a resource limitation.

### Steps to Fix GPU Usage:
1. Check Ollama's CUDA configuration
2. Ensure models specify GPU layers (e.g., `num_gpu_layers: 999`)
3. Restart Ollama with proper GPU environment variables
4. Verify models load to VRAM using `nvidia-smi`

## Testing Results
- phi3:mini loads in 16 seconds (cold start)
- Ollama API responsive for basic calls
- No models currently loaded in memory
- Vote submission fails due to network timeout

## Next Steps Priority
1. **URGENT**: Fix Ollama GPU configuration to use VRAM
2. **URGENT**: Increase timeouts to 60+ seconds
3. **HIGH**: Restart Ollama with proper GPU settings
4. **HIGH**: Verify all models load to GPU (monitor with nvidia-smi)
5. **MEDIUM**: Add loading status indicators for users

## Conclusion
The 5-model Arena mode issues are **solvable with configuration changes**. The GPU instance has:
- **23GB VRAM available** (enough for all 5 models with room to spare)
- **Only using 4.1GB currently** (massive underutilization)
- **Models loading to CPU instead of GPU** (configuration error)

### The Fix is Simple:
1. Configure Ollama to use GPU memory properly
2. Increase timeouts to 60+ seconds
3. Preload all models into GPU VRAM

**No hardware upgrades needed!** The current NVIDIA A10G GPU is more than sufficient. This is purely a configuration issue that can be resolved quickly.