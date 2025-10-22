# Arena Network Configuration Fix

## Date: 2025-09-16
## Issue: Connection Refused (Errno 111) to GPU Instance

## Root Cause
Ollama was configured to listen only on `127.0.0.1:11434` (localhost), preventing connections from other servers in the VPC.

## Discovery
```bash
# Problem found with netstat:
tcp  0  0  127.0.0.1:11434  0.0.0.0:*  LISTEN
# Should be:
tcp6 0  0  :::11434         :::*       LISTEN
```

## Solution Applied
Added `OLLAMA_HOST=0.0.0.0:11434` environment variable to Ollama service configuration.

## Steps Taken
1. Identified Ollama was running but only on localhost
2. Modified `/etc/systemd/system/ollama.service`
3. Added: `Environment="OLLAMA_HOST=0.0.0.0:11434"`
4. Reloaded systemd daemon
5. Restarted Ollama service
6. Verified now listening on all interfaces

## Configuration Change
```ini
[Service]
# ... existing config ...
Environment="OLLAMA_HOST=0.0.0.0:11434"  # Added this line
```

## Verification
- Ollama now listening on `:::11434` (all IPv6/IPv4 interfaces)
- Production servers can connect: `curl http://172.31.45.157:11434/api/version` ✅
- API calls successful with 200 status
- Arena mode should now function correctly

## Impact
- All production instances can now reach the GPU instance
- Arena battles will work with all 5 models
- No more "Connection refused" errors

## Testing Completed
- ✅ Direct API test from production: Success
- ✅ Model response test: phi3:mini responded correctly
- ✅ Network connectivity verified between all instances

## Important Notes
- This was a critical misconfiguration that prevented Arena mode from working
- The GPU and models were fine; it was purely a network binding issue
- Future Ollama installations should always include `OLLAMA_HOST=0.0.0.0:11434`