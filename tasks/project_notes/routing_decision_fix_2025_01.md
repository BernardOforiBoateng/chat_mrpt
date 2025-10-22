# Routing Decision Fix - January 2025

## Problem Statement
After users complete TPR workflow and exit data analysis mode, tool requests were failing because request_interpreter was making its own data_loaded check and ignoring the routing decision from Mistral.

### Symptoms
- "Tell me about the variables in my data" → Arena mode (should use tools)
- "Run the risk analysis" → Arena mode (should use tools)
- "Plot me the map distribution for the evi variable" → Arena mode (should use tools)

## Root Cause Analysis

### Two-Layer Disconnect
1. **Mistral routing** (in analysis_routes.py) correctly decides: 'needs_tools' vs 'can_answer'
2. **Request interpreter** never receives the routing_decision and makes its OWN decision based solely on data_loaded flag
3. When data_loaded=False, request_interpreter returns early with "No data loaded" message

### Specific Code Issues

#### request_interpreter.py
- Line 145-146: Early return for non-streaming when no data_loaded
- Line 195-196: Early return for streaming when no data_loaded
- Multiple tool methods checking data independently

#### The Flow Problem
```
User Query → Mistral decides "needs_tools" →
Request Interpreter called →
Checks data_loaded=False →
Returns "No data loaded" →
Tools never executed!
```

## Solution Implemented

### Design Principle
- Routing decides, interpreter executes
- Single source of truth: routing_decision from Mistral
- No duplicate decision-making

### Code Changes

#### 1. request_interpreter.py - process_message
Added routing_decision parameter handling:
```python
# CRITICAL FIX: Respect routing decision from Mistral
routing_decision = kwargs.get('routing_decision', None)
logger.info(f"🎯 Routing decision passed: {routing_decision}")

# Only check data_loaded if routing hasn't already decided
if not session_context.get('data_loaded', False) and routing_decision != 'needs_tools':
    logger.info(f"❌ No data loaded and no routing override, using conversational response")
    return self._simple_conversational_response(user_message, session_context)
```

#### 2. request_interpreter.py - process_message_streaming
Similar fix for streaming endpoint:
```python
if routing_decision == 'needs_tools':
    logger.info(f"✅ Routing decision is 'needs_tools' - proceeding with tools regardless of data_loaded")
elif not session_context.get('data_loaded', False) and routing_decision != 'needs_tools':
    logger.info(f"❌ No data loaded and no routing override, using conversational streaming")
```

#### 3. analysis_routes.py
Pass routing_decision to interpreter:
```python
# Non-streaming
response = request_interpreter.process_message(
    user_message,
    session_id,
    is_data_analysis=is_data_analysis,
    tab_context=tab_context,
    routing_decision=routing_decision  # Pass routing decision to respect it
)

# Streaming
for chunk in request_interpreter.process_message_streaming(
    user_message,
    session_id,
    session_data,
    is_data_analysis=is_data_analysis,
    tab_context=tab_context,
    routing_decision=routing_decision  # Pass routing decision to respect it
):
```

## Testing Approach
- Created unit test (had Flask context issues)
- Deployed to AWS for real-world testing
- Both production instances updated

## Deployment
- Deployed to both production instances (3.21.167.170, 18.220.103.20)
- Services restarted successfully
- Ready for user testing

## Expected Behavior After Fix
1. User completes TPR workflow
2. User exits data analysis mode
3. User asks "Tell me about the variables in my data"
4. Mistral routes to 'needs_tools'
5. Request interpreter receives routing_decision='needs_tools'
6. Request interpreter skips data_loaded check
7. Tools execute successfully

## Monitoring
Check logs with:
```bash
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep -E "Routing decision|data_loaded"'
```

## Long-term Benefits
- Clean separation of concerns
- No duplicate routing logic
- Respects semantic routing decisions
- Works even when session flags are inconsistent