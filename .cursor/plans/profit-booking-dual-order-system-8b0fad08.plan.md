<!-- 8b0fad08-f252-4a22-8aab-57960aecf982 aba1940e-3b52-4312-91bb-dffd876b3d31 -->
# Restore Original TF Field Behavior Plan

## Goal

Restore original bot behavior where `tf` field is **REQUIRED** (not optional) for all signals. This ensures all 3 logics (LOGIC1, LOGIC2, LOGIC3) work correctly.

## Problem Identified

Current code makes `tf` field optional with default "5m", which causes:

- Entry signals without `tf` → default "5m" → always uses LOGIC1
- 15m entry signals without `tf` → wrong LOGIC1 used
- 1h entry signals without `tf` → wrong LOGIC1 used
- All 3 logics don't work correctly

## Solution

Restore original behavior:

- `tf` field REQUIRED for all signals (entry, bias, trend, reversal, exit)
- No default `tf` value
- If `tf` missing → ValidationError → Signal REJECTED
- All 3 logics work correctly (LOGIC1, LOGIC2, LOGIC3)

## Files to Fix

### 1. models.py

**Current Code (Line 10):**

```python
tf: Optional[str] = "5m"  # "1h", "15m", "5m", "1d" - default "5m" for backward compatibility
```

**Change To (Original):**

```python
tf: str  # "1h", "15m", "5m", "1d" - REQUIRED FIELD (no default)
```

**Changes:**

- Remove `Optional[str]`
- Remove default value `= "5m"`
- Make `tf` field required (no default)

### 2. alert_processor.py

**Current Code (Lines 21-31):**

```python
# Add default tf if not present (backward compatibility)
if 'tf' not in alert_data or not alert_data.get('tf'):
    # Default tf based on signal type
    if alert_data.get('type') == 'entry':
        alert_data['tf'] = '5m'  # Default for entry signals
    elif alert_data.get('type') in ['bias', 'trend']:
        alert_data['tf'] = '15m'  # Default for bias/trend
    elif alert_data.get('type') in ['reversal', 'exit']:
        alert_data['tf'] = '15m'  # Default for reversal/exit
    else:
        alert_data['tf'] = '5m'  # Fallback default
```

**Change To (Original - Remove Entire Block):**

```python
# NO DEFAULT TF FIELD LOGIC - tf field is REQUIRED
# If tf missing, Alert() will raise ValidationError
```

**Changes:**

- Remove entire default `tf` field logic block (lines 21-31)
- Keep original behavior where `tf` is required
- If `tf` missing → `Alert(**alert_data)` will raise ValidationError

## Implementation Steps

1. Fix `models.py`:

   - Change `tf: Optional[str] = "5m"` to `tf: str`
   - Remove Optional import if not used elsewhere
   - Verify `tf` field is required

2. Fix `alert_processor.py`:

   - Remove default `tf` field logic block (lines 21-31)
   - Keep original validation logic
   - Verify if `tf` missing → ValidationError raised

3. Test Original Behavior:

   - Test entry signal with `tf: "5m"` → LOGIC1
   - Test entry signal with `tf: "15m"` → LOGIC2
   - Test entry signal with `tf: "1h"` → LOGIC3
   - Test entry signal without `tf` → ValidationError → REJECTED
   - Test bias/trend signal without `tf` → ValidationError → REJECTED

4. Verify All Logics Work:

   - LOGIC1 (5m entry) → Works correctly
   - LOGIC2 (15m entry) → Works correctly
   - LOGIC3 (1h entry) → Works correctly

## Expected Results

### After Fix:

- ✅ `tf` field REQUIRED for all signals
- ✅ No default `tf` value
- ✅ If `tf` missing → ValidationError → Signal REJECTED
- ✅ Entry signal with `tf: "5m"` → LOGIC1
- ✅ Entry signal with `tf: "15m"` → LOGIC2
- ✅ Entry signal with `tf: "1h"` → LOGIC3
- ✅ All 3 logics work correctly
- ✅ Original behavior restored

## Testing Checklist

1. ✅ Entry signal with `tf: "5m"` → LOGIC1 used
2. ✅ Entry signal with `tf: "15m"` → LOGIC2 used
3. ✅ Entry signal with `tf: "1h"` → LOGIC3 used
4. ✅ Entry signal without `tf` → ValidationError → REJECTED
5. ✅ Bias signal without `tf` → ValidationError → REJECTED
6. ✅ Trend signal without `tf` → ValidationError → REJECTED
7. ✅ All 3 logics work correctly
8. ✅ Original behavior restored

### To-dos

- [x] Fix Unicode characters in alert_processor.py (lines 15, 29, 34, 39, 45, 49, 53, 57, 63, 67, 135)