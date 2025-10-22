# Streaming Endpoint Interception Analysis

## All Interception Points Preventing Mistral Routing

### `/send_message_streaming` Flow Analysis (Lines 1414-2068)

#### ❌ INTERCEPTION POINT 1: Empty Message Check (Lines 1429-1445)
```python
if not user_message:
    # Returns early with error message
    return response  # BLOCKS MISTRAL
```
**Impact**: Empty messages never reach Mistral
**Fix**: Keep this - it's reasonable

---

#### ❌ INTERCEPTION POINT 2: Old Data Analysis Flag (Lines 1463-1470)
```python
if session.get('data_analysis_active', False):
    # OLD DATA ANALYSIS - DEPRECATED
    session.pop('data_analysis_active', None)
    # Falls through now, but could block
```
**Impact**: Currently clears and continues, but could intercept
**Fix**: Remove this entire block

---

#### ❌ INTERCEPTION POINT 3: TPR Workflow Active (Lines 1473-1567)
```python
elif session.get('tpr_workflow_active', False):
    # 94 lines of TPR handling
    # Multiple paths that can return:

    # Line 1490: If result is '__DATA_UPLOADED__' → falls through
    # Line 1517: If status is 'tpr_to_main_transition' → falls through
    # Line 1544-1567: Otherwise → RETURNS TPR response
    return response  # BLOCKS MISTRAL for active TPR
```
**Impact**: When TPR workflow is active, returns without reaching Mistral
**Fix**: This might be intentional for TPR flow, but after TPR exit should NOT trigger

---

#### ❌ INTERCEPTION POINT 4: Clarification Prompt Response (Lines 1649-1753)
```python
if session.get('pending_clarification'):
    # Handles clarification responses
    # Lines 1710-1753: Can return clarification prompt
    if routing_decision == 'needs_clarification':
        if len(user_message.strip().split()) <= 3:
            routing_decision = 'can_answer'  # Forces Arena
        else:
            return response  # BLOCKS with clarification
```
**Impact**: Clarification prompts can block Mistral
**Fix**: Might be needed, but the override to 'can_answer' is problematic

---

#### ❌ INTERCEPTION POINT 5: Arena Mode Decision (Lines 1762-1927)
```python
if use_arena:
    # 165 lines of Arena code
    # Line 1927: return response  # BLOCKS tools path
```
**Impact**: When routing_decision == 'can_answer', returns Arena response
**Problem**: NO ELSE BLOCK for tools! Falls through to request_interpreter

---

#### ⚠️ HIDDEN ISSUE: No Early Tool Path
After Mistral routing (line 1695), the code structure is:
```python
use_arena = (routing_decision == 'can_answer')
use_tools = (routing_decision == 'needs_tools')

if use_arena:
    # Arena handling...
    return response

# NO ELSE for use_tools!
# Just falls through to request_interpreter at line 1936
```
**Impact**: Tools path has no dedicated handler before falling through

---

### Key Problems Identified:

1. **TPR Workflow Flag Persistence**:
   - `tpr_workflow_active` might still be True after exit
   - This would catch ALL messages at line 1473

2. **No Dedicated Tools Path**:
   - After Mistral decides 'needs_tools', there's no explicit handler
   - Code falls through to request_interpreter (lines 1936+)

3. **Arena Bias**:
   - Arena gets a full implementation (lines 1762-1927)
   - Tools have no equivalent block

4. **Session Flag Confusion**:
   - Multiple flags: `tpr_workflow_active`, `data_analysis_active`, `pending_clarification`
   - These can intercept BEFORE Mistral routing

---

## Evidence from Browser Console:

Looking at contxt.md:
- Line 212: `exit_data_analysis_mode: true`
- Line 237: `Data Analysis Mode: false`
- Line 245: **IMMEDIATE** Arena battle starts

This suggests the interception happens at:
1. TPR workflow check (if flag not cleared)
2. OR something else we haven't found yet

---

## Recommendations:

### Must Fix:
1. **Remove/disable TPR workflow check** after TPR exits
2. **Add explicit tools handling** after Mistral routing
3. **Ensure session flags are cleared** after workflow transitions

### Should Fix:
4. Remove old `data_analysis_active` check completely
5. Fix the "no else for tools" problem
6. Remove automatic 'can_answer' override for short messages

### Investigation Needed:
- Why does browser show Arena immediately?
- Is `tpr_workflow_active` still True after exit?
- What's the actual routing_decision for "Plot me the evi variable"?