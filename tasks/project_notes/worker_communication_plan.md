# Worker Communication Plan - Careful Approach

## Date: July 29, 2025

### Your Concern is Valid!
With multiple workers, these issues can occur:
1. **Session data not shared** between workers
2. **File uploads** going to different workers
3. **Long-running processes** interrupted
4. **State inconsistency** between requests

### Our Safe Testing Approach

#### Phase 1: Start with 2 Workers (Minimal Risk)
```python
# gunicorn_config_test.py
workers = 2  # Start small
worker_class = "sync"  # Synchronous workers
preload_app = True  # Load app before forking
```

#### Phase 2: Fix Critical Issues

1. **Session Storage Fix**
   - Move from filesystem sessions to Redis
   - Ensure all workers see same session data
   
2. **File Upload Handling**
   ```python
   # Store upload reference in session, not file data
   session['upload_id'] = unique_id
   # Save file to shared location all workers can access
   filepath = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/{unique_id}"
   ```

3. **DataFrame Serialization**
   ```python
   # Instead of: session['nmep_data'] = df
   # Use: 
   df_json = df.to_json(orient='split')
   session['nmep_data'] = df_json
   ```

#### Phase 3: Test Workflow Paths

Critical workflows to test:
1. **File Upload → Processing → Results**
   - Ensure same worker doesn't need to handle all steps
   
2. **Multi-step Analysis**
   - TPR calculation spans multiple requests
   - Each request might hit different worker

3. **Map Generation**
   - Long-running process
   - Progress tracking across workers

### Testing Protocol

1. **Start with 2 workers on port 8081**
2. **Test each workflow 10 times**
3. **Monitor for errors**
4. **Only increase workers if stable**

### Rollback Triggers
If ANY of these occur:
- Session data lost between requests
- File upload errors
- "Object not found" errors
- Workflow interruption

Then immediately:
- Stop test application
- Revert to 1 worker
- Analyze logs

### Worker Configuration Timeline
- **Today**: Test with 2 workers
- **If stable for 2 hours**: Try 3 workers
- **If stable for 4 hours**: Try 4 workers
- **Production**: Only after 24 hours stable testing