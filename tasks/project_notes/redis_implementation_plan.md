# Redis Implementation Plan for ChatMRPT
## Date: July 29, 2025

### Phase 1: Create Redis Session Configuration

1. **Create new config file** for Redis sessions
2. **Test Redis connection** from staging
3. **Create session serialization helpers** for DataFrames

### Phase 2: Modify Session Handling

1. **Update Flask app initialization** to use Redis
2. **Fix DataFrame serialization** (convert to JSON before storing)
3. **Update all session access patterns** to be Redis-compatible

### Phase 3: Testing Protocol

1. **Test with 1 worker first** to ensure Redis works
2. **Then test with 2 workers** to verify session sharing
3. **Full workflow test**: Upload → TPR → Risk Analysis
4. **Load test with 4 workers** if stable

### Critical Code Changes Needed

#### 1. Session Configuration
```python
# app/config/development.py
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url('redis://chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379/0')
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'chatmrpt:'
```

#### 2. DataFrame Handling
```python
# Before: session['data'] = df
# After: 
session['data'] = df.to_json(orient='split')
# And when reading:
df = pd.read_json(session['data'], orient='split')
```

#### 3. File Path Handling
```python
# Store only relative paths in session
# Full paths constructed at runtime
session['file_id'] = unique_id
# Not: session['file_path'] = '/full/path/to/file'
```

### Risks & Mitigation

1. **Risk**: Breaking existing sessions
   - **Mitigation**: Test on staging only

2. **Risk**: Performance impact
   - **Mitigation**: Redis is faster than file sessions

3. **Risk**: Data serialization errors
   - **Mitigation**: Comprehensive testing of all data types

### Success Criteria

- ✅ Sessions persist across workers
- ✅ No "session not found" errors
- ✅ TPR → Risk Analysis transition works
- ✅ 50 concurrent users supported
- ✅ No data loss or corruption