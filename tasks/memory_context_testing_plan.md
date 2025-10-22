# Memory Context Feature - Testing & Deployment Plan

**Date**: October 13, 2025
**Feature**: Enhanced conversation memory with LLM-generated summaries
**Status**: Ready for testing

---

## Overview

The memory context enhancement adds conversation continuity across ChatMRPT by:
1. **Storing conversation history** per session in `instance/memory/<session_id>.json`
2. **Generating LLM summaries** of key facts, data selections, results, and user goals (max 5 bullets, ~120 words)
3. **Injecting memory into prompts** for both main chat flow and Data Analysis V3 agent
4. **Providing context recall** so users can ask follow-up questions using pronouns ("it", "that", "those")

---

## Implementation Details

### Modified Files
1. **`app/core/request_interpreter.py`**
   - Added `_store_conversation()` - persists user/assistant messages
   - Added `_ensure_memory_summary()` - generates LLM summaries every 2+ messages or 60s
   - Added `_enrich_session_context_with_memory()` - injects memory into session context

2. **`app/services/memory_service.py`**
   - Core memory service with file-based storage (Redis-ready)
   - `append_message()` - stores conversation turns (max 100 messages)
   - `set_fact()`/`get_fact()` - stores/retrieves named facts (e.g., conversation_summary)
   - `get_messages()` - retrieves message history
   - `get_summary()` - creates compact summary for classifiers

3. **`app/core/prompt_builder.py`**
   - Updated to weave memory summaries into system prompts
   - Lines 125-129: Adds "## Conversation Memory" and "## Recent Turns" sections

4. **`app/data_analysis_v3/core/agent.py`**
   - Lines 720-740: Injects memory into LangGraph agent messages
   - Provides conversation continuity during TPR workflow

---

## Testing Plan

### Phase 1: Local Development Testing (Manual)

#### Test 1: Memory File Creation
**Objective**: Verify memory files are created and populated

**Steps**:
1. Start local dev server: `python run.py`
2. Open browser to http://127.0.0.1:5000
3. Log in and start a new session
4. Upload a CSV file in Standard Upload tab
5. Ask: "What's the average malaria prevalence?"
6. Check if memory file exists: `ls -la instance/memory/`
7. Read memory file: `cat instance/memory/<session_id>.json`

**Expected Result**:
- Memory file created with structure:
  ```json
  {
    "messages": [
      {"t": "2025-10-13T10:00:00Z", "role": "user", "content": "What's..."}
    ],
    "facts": {}
  }
  ```

---

#### Test 2: Memory Summary Generation
**Objective**: Verify LLM generates conversation summaries

**Steps**:
1. Continue from Test 1
2. Ask: "Run risk analysis"
3. Wait for analysis to complete
4. Ask: "Show me the top 5 high-risk wards"
5. Ask: "What interventions do you recommend?"
6. Check memory file: `cat instance/memory/<session_id>.json | jq '.facts'`

**Expected Result**:
- Memory file contains `conversation_summary` fact:
  ```json
  {
    "facts": {
      "conversation_summary": "- User uploaded malaria data\n- Ran risk analysis\n- Requesting high-risk ward rankings\n- Interested in intervention recommendations"
    }
  }
  ```
- Summary is concise (5 bullets, ~120 words)

---

#### Test 3: Context Recall - Pronoun-Based Questions
**Objective**: Verify agent understands context from previous turns

**Steps**:
1. Continue from Test 2
2. Ask: "What factors contributed to **that**?" (referring to high-risk wards)
3. Ask: "Can you explain **it** in simpler terms?" (referring to previous answer)
4. Ask: "Show me **those** on a map" (referring to high-risk wards)

**Expected Result**:
- Agent correctly interprets "that", "it", "those" based on conversation history
- Responses reference previous context without requiring user to repeat details

---

#### Test 4: Data Analysis V3 Workflow Memory
**Objective**: Verify memory works in TPR workflow

**Steps**:
1. Start new session, switch to **Data Analysis** tab
2. Upload facility-level malaria testing data CSV
3. Type: "tpr"
4. Complete TPR workflow: select state → facility level → age group
5. After TPR map appears, ask: "What was the average TPR?"
6. Ask: "Can you compare **that** to the national average?" (pronoun reference)
7. Check memory file: `cat instance/memory/<session_id>.json`

**Expected Result**:
- Memory captures TPR workflow selections (state, facility, age group)
- Agent recalls TPR value when asked with pronoun
- Conversation summary includes TPR-specific facts

---

#### Test 5: Memory Persistence Across Requests
**Objective**: Verify memory persists across multiple page interactions

**Steps**:
1. Continue from any previous test
2. Refresh the browser page (F5)
3. Ask a follow-up question referencing earlier conversation
4. Example: "What was the state I selected earlier?"

**Expected Result**:
- Memory is loaded from file after page refresh
- Agent recalls previous context correctly

---

### Phase 2: Production Testing (Staging Environment)

#### Test 6: Multi-User Isolation
**Objective**: Verify memory is isolated per session (no data bleed)

**Steps**:
1. Open ChatMRPT in 2 different browsers (Chrome + Firefox)
2. Log in with 2 different accounts (or use incognito mode)
3. Upload different datasets in each session
4. Have conversations about different topics
5. Check memory files: `ls instance/memory/`
6. Verify session IDs are different
7. Ask context-dependent questions in each session

**Expected Result**:
- Each session has unique memory file
- No cross-contamination between sessions
- Each agent only recalls its own session's context

---

#### Test 7: Memory Summary Limit Enforcement
**Objective**: Verify summaries don't grow unbounded

**Steps**:
1. Have a long conversation (20+ turns)
2. Upload data, run analysis, ask many follow-up questions
3. Check memory file size: `du -h instance/memory/<session_id>.json`
4. Check summary length: `cat instance/memory/<session_id>.json | jq '.facts.conversation_summary' | wc -w`

**Expected Result**:
- Summary stays under 120 words (5 bullets)
- Message history capped at 100 messages (configurable via `CHATMRPT_MEMORY_MAX_MESSAGES`)
- Memory file stays small (< 50KB)

---

#### Test 8: Redis Backing (Optional)
**Objective**: Verify Redis-backed memory works (if enabled)

**Steps**:
1. Set environment variable: `export CHATMRPT_USE_REDIS_MEMORY=1`
2. Restart application
3. Run Test 1-3 again
4. Check Redis keys: `redis-cli KEYS "chatmrpt:*"`

**Expected Result**:
- Memory stored in Redis instead of files
- Faster cross-worker access in multi-instance setup

---

### Phase 3: Automated Testing

#### Test 9: Unit Tests for Memory Service
**Create**: `tests/test_memory_service.py`

```python
import pytest
import os
import json
from app.services.memory_service import MemoryService

def test_memory_service_append_message():
    service = MemoryService(base_dir="instance/test_memory")
    session_id = "test_session_001"

    # Append messages
    service.append_message(session_id, "user", "What is malaria?")
    service.append_message(session_id, "assistant", "Malaria is a disease...")

    # Retrieve messages
    messages = service.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0]['role'] == 'user'
    assert messages[1]['role'] == 'assistant'

    # Cleanup
    service.clear_session(session_id)
    os.rmdir("instance/test_memory")

def test_memory_service_facts():
    service = MemoryService(base_dir="instance/test_memory")
    session_id = "test_session_002"

    # Set facts
    service.set_fact(session_id, "state_selected", "Kano")
    service.set_fact(session_id, "facility_level", "primary")

    # Get facts
    assert service.get_fact(session_id, "state_selected") == "Kano"
    assert service.get_fact(session_id, "facility_level") == "primary"

    # Get all facts
    all_facts = service.get_all_facts(session_id)
    assert "state_selected" in all_facts

    # Cleanup
    service.clear_session(session_id)
    os.rmdir("instance/test_memory")

def test_memory_service_message_limit():
    service = MemoryService(base_dir="instance/test_memory", max_messages=5)
    session_id = "test_session_003"

    # Append 10 messages
    for i in range(10):
        service.append_message(session_id, "user", f"Message {i}")

    # Should only keep last 5
    messages = service.get_messages(session_id)
    assert len(messages) == 5
    assert messages[-1]['content'] == "Message 9"

    # Cleanup
    service.clear_session(session_id)
    os.rmdir("instance/test_memory")
```

**Run**: `pytest tests/test_memory_service.py -v`

---

#### Test 10: Integration Test for Context Recall
**Create**: `tests/test_context_recall.py`

```python
import pytest
from app.core.request_interpreter import RequestInterpreter
from app.services.memory_service import MemoryService

@pytest.fixture
def request_interpreter():
    # Initialize with test dependencies
    from app.core.llm_manager import get_llm_manager
    from app.services.data_service import DataService

    llm_manager = get_llm_manager()
    data_service = DataService()

    return RequestInterpreter(
        llm_manager=llm_manager,
        data_service=data_service,
        analysis_service=None,
        visualization_service=None
    )

def test_context_recall_with_pronouns(request_interpreter):
    session_id = "test_context_001"

    # Simulate conversation
    response1 = request_interpreter.interpret_request(
        "What are the top 3 high-risk wards?",
        session_id=session_id,
        session_data={"data_loaded": True}
    )

    # Follow-up with pronoun
    response2 = request_interpreter.interpret_request(
        "What factors make those wards high-risk?",
        session_id=session_id,
        session_data={"data_loaded": True}
    )

    # Verify memory was used
    memory = MemoryService()
    messages = memory.get_messages(session_id)
    assert len(messages) >= 2

    # Cleanup
    memory.clear_session(session_id)
```

**Run**: `pytest tests/test_context_recall.py -v`

---

## Deployment Plan

### Pre-Deployment Checklist

- [ ] All manual tests (Test 1-5) passed locally
- [ ] Memory files created in `instance/memory/`
- [ ] Conversation summaries generated correctly
- [ ] Context recall works with pronouns
- [ ] Unit tests created and passing
- [ ] Integration tests passing
- [ ] No regressions in existing functionality

---

### Deployment Steps

#### Step 1: Deploy to Production Instances

```bash
# Deploy to both production instances
for ip in 3.21.167.170 18.220.103.20; do
    echo "=== Deploying to $ip ==="

    # Copy modified files
    scp -i /tmp/chatmrpt-key2.pem app/services/memory_service.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/services/
    scp -i /tmp/chatmrpt-key2.pem app/core/request_interpreter.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    scp -i /tmp/chatmrpt-key2.pem app/core/prompt_builder.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/core/
    scp -i /tmp/chatmrpt-key2.pem app/data_analysis_v3/core/agent.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

    # Create memory directory
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "
        mkdir -p /home/ec2-user/ChatMRPT/instance/memory
        chmod 755 /home/ec2-user/ChatMRPT/instance/memory

        # Clear Python cache
        cd /home/ec2-user/ChatMRPT
        find app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
        find app -name '*.pyc' -delete 2>/dev/null || true

        # Restart service
        sudo systemctl restart chatmrpt
        sleep 3
        sudo systemctl status chatmrpt --no-pager | head -15
    "

    echo ""
done
```

---

#### Step 2: Verify Deployment

```bash
# Check service status
for ip in 3.21.167.170 18.220.103.20; do
    echo "=== Checking $ip ==="
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "
        # Check if memory service file exists
        ls -la /home/ec2-user/ChatMRPT/app/services/memory_service.py

        # Check if memory directory exists
        ls -ld /home/ec2-user/ChatMRPT/instance/memory

        # Check service status
        sudo systemctl status chatmrpt --no-pager | grep -E '(Active|Main PID)'
    "
    echo ""
done
```

---

#### Step 3: Monitor Production Logs

```bash
# Watch logs for memory service activity
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170
sudo journalctl -u chatmrpt -f | grep -E '(memory|Memory|summary|Summary)'
```

**Look for log lines like**:
- `Memory service initialized`
- `Memory summary generated for session <session_id>`
- `Conversation history stored for session <session_id>`

---

#### Step 4: Production Smoke Test

1. **Access production**: https://d225ar6c86586s.cloudfront.net
2. **Test basic flow**:
   - Upload data
   - Ask: "What's the average TPR?"
   - Ask: "Can you explain that?"
   - Verify agent recalls context
3. **Check memory files**:
   ```bash
   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170
   ls -la /home/ec2-user/ChatMRPT/instance/memory/
   ```

---

### Post-Deployment Monitoring

#### Metrics to Monitor

1. **Memory file growth**:
   ```bash
   watch -n 60 'du -sh /home/ec2-user/ChatMRPT/instance/memory/'
   ```

2. **Memory file count**:
   ```bash
   watch -n 60 'ls /home/ec2-user/ChatMRPT/instance/memory/ | wc -l'
   ```

3. **Average memory file size**:
   ```bash
   ls -l /home/ec2-user/ChatMRPT/instance/memory/*.json | awk '{sum+=$5; count++} END {print sum/count " bytes avg"}'
   ```

4. **LLM API calls** (for summary generation):
   - Check OpenAI usage dashboard for increased API calls
   - Should be ~1 extra call per 2 messages

---

### Rollback Plan

If issues occur in production:

```bash
# Restore from backup
for ip in 3.21.167.170 18.220.103.20; do
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "
        cd /home/ec2-user
        sudo systemctl stop chatmrpt
        rm -rf ChatMRPT.broken
        mv ChatMRPT ChatMRPT.broken
        tar -xzf ChatMRPT_WITH_TPR_TRIGGER_FIX_20251013.tar.gz
        sudo systemctl start chatmrpt
    "
done
```

---

## Known Limitations

1. **Memory cleanup**: No automatic cleanup of old session memory files (implement later with cron job)
2. **Redis optional**: File-based storage by default, Redis backing requires explicit env var
3. **Summary quality**: Depends on LLM quality (using gpt-4o, so should be good)
4. **Latency**: Additional ~200ms for LLM summary generation every 2+ messages

---

## Success Criteria

✅ **Feature is successful if**:
- Memory files created and populated correctly
- Conversation summaries generated and stored
- Context recall works with pronoun-based questions
- No data bleed between sessions
- No performance degradation
- No increase in error rates

---

## Next Steps After Deployment

1. **Monitor for 24 hours** - watch logs, check memory files
2. **Gather user feedback** - ask users if context recall improved
3. **Optimize if needed**:
   - Adjust summary frequency (currently 2 messages or 60s)
   - Tune summary length (currently 5 bullets, 120 words)
   - Enable Redis backing for better multi-instance performance
4. **Add memory cleanup cron job**:
   ```bash
   # Delete memory files older than 7 days
   find /home/ec2-user/ChatMRPT/instance/memory/ -name "*.json" -mtime +7 -delete
   ```

---

## Documentation Updates

After successful deployment, update:
- [ ] `CLAUDE.md` - Add memory context feature documentation
- [ ] User guide - Explain improved context awareness
- [ ] API documentation - Document memory service methods

---

## Questions & Answers

**Q: Will this affect performance?**
A: Minimal impact. Summary generation adds ~200ms every 2+ messages, but runs async.

**Q: What if memory files grow too large?**
A: Message history capped at 100 messages, summaries limited to 120 words. Max file size ~50KB per session.

**Q: Can users access their memory files?**
A: No, memory files are internal. Users don't see them directly.

**Q: What about GDPR/data privacy?**
A: Memory files stored on server like other session data. Should be included in data retention policies.

---

**End of Testing & Deployment Plan**
