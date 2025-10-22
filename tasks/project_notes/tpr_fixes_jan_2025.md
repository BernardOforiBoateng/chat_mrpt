# TPR Workflow Fixes - January 2025

## The Two Critical Issues

### Issue 1: Missing "Over 5 Years" Age Group
**Problem**: Only 2 age groups appeared (Under 5 and Pregnant Women), missing Over 5 Years
**Root Cause**: The `ftfy` library was NOT installed on staging servers

The "≥" symbol in column names was corrupted to "â‰¥" (mojibake - UTF-8 interpreted as Windows-1252). Without `ftfy` to fix this encoding issue, the pattern matching for "≥5yrs" columns failed completely.

**Solution**:
```bash
# Install ftfy on both staging instances
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 "/home/ec2-user/chatmrpt_env/bin/pip install ftfy"
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 "/home/ec2-user/chatmrpt_env/bin/pip install ftfy"

# Restart services
sudo systemctl restart chatmrpt
```

### Issue 2: Bullet Points on Single Lines
**Problem**: All bullet points appeared crunched together on one line instead of separate lines
**Root Cause**: JavaScript regex not matching indented bullets

The regex `/^[•\-] (.+)$/gm` only matched bullets at the start of lines, but the actual data had indented bullets like `   • RDT: 1,504,993 tests`

**Solution**: Updated message-handler.js
```javascript
// OLD - didn't match indented bullets
text = text.replace(/^[•\-] (.+)$/gm, '<li>$1</li>');

// NEW - matches bullets with any leading whitespace
text = text.replace(/^\s*[•\-] (.+)$/gm, '<li>$1</li>');
```

## Technical Details

### Encoding Fix Verification
```python
# Before ftfy installation
'Persons presenting with fever & tested by RDT  â‰¥5yrs (excl PW)'

# After ftfy installation
'Persons presenting with fever & tested by RDT  ≥5yrs (excl PW)'
```

### JavaScript Improvements
1. **Indented bullet detection**: Added `\s*` to match any leading whitespace
2. **Better line break handling**: Separate patterns for indented vs non-indented bullets
3. **Preserved list formatting**: Changed from `paragraph.replace(/\n/g, ' ')` to just `return paragraph`

## Files Modified

### Python Files
- **No changes needed** - The encoding handler was already correct, just missing the `ftfy` dependency

### JavaScript Files
- `app/static/js/modules/chat/core/message-handler.js`:
  - Line 336: Updated bullet regex to match indented bullets
  - Line 343-344: Improved line break insertion before bullets
  - Line 352: Preserved newlines in lists instead of removing them

## Deployment Commands
```bash
# Deploy JavaScript to both staging instances
scp -i /tmp/chatmrpt-key2.pem app/static/js/modules/chat/core/message-handler.js \
    ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js

scp -i /tmp/chatmrpt-key2.pem app/static/js/modules/chat/core/message-handler.js \
    ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/message-handler.js
```

## Testing Results

### Before Fix
- Only 2 age groups detected
- Bullets all on one line
- Console showed: `'Persons presenting with fever & tested by RDT  â‰¥5yrs'`

### After Fix
- All 3 age groups detected (Under 5, Over 5, Pregnant Women)
- Bullets properly formatted on separate lines
- Console shows: `'Persons presenting with fever & tested by RDT  ≥5yrs'`

## Key Lessons

1. **Missing Dependencies**: Always verify that ALL required libraries are installed on production/staging
2. **Regex Patterns**: Consider all variations (indented, non-indented) when matching text patterns
3. **Encoding Issues**: Mojibake is often the culprit when special characters appear corrupted
4. **Testing**: What works locally may fail in production due to missing dependencies

## Prevention for Future

Add to requirements.txt:
```
ftfy>=6.0.0
chardet>=4.0.0
```

This ensures these critical encoding libraries are always installed during deployment.