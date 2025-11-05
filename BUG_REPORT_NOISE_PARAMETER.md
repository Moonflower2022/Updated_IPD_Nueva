# Critical Bug Report: Noise Parameter Ignored in Main Codebase

**Date:** 2025-11-05
**Severity:** HIGH
**Location:** `ipd_local/simulation.py` lines 181, 186

---

## Executive Summary

The main codebase has a **critical bug** where the `noise` parameter in `play_match()` is completely ignored. Instead, the function uses the global `NOISE` constant from `game_specs.py`, which is hardcoded to `True`.

This means:
- Passing `noise=False` has **no effect**
- All matches run with noise enabled, regardless of what the caller requests
- Tests that attempt to run without noise are actually running WITH noise
- The notebook implementation is **correct**, the main codebase is **wrong**

---

## Evidence

### Test Results

Running `tit_for_tat` vs `rat` with 100 rounds:

| Implementation | noise param | Expected Score | Actual Score | Status |
|----------------|-------------|----------------|--------------|---------|
| **Notebook** | `False` | `[99, 108]` | `[99, 108]` | ✅ CORRECT |
| **Main** | `False` | `[99, 108]` | `[87, 204]` | ❌ WRONG (applying noise!) |
| **Notebook** | `True (0.1)` | `[87, 204]` | `[87, 204]` | ✅ CORRECT |
| **Main** | `True (0.1)` | `[87, 204]` | `[87, 204]` | ✅ CORRECT |

**Key Finding:** Main codebase with `noise=False` produces the SAME results as `noise=True`, proving the parameter is ignored.

### The Bug

**File:** `ipd_local/simulation.py`

**Lines 179-188:**
```python
player1percieved.append(
    not player1move
    if NOISE and random.random() < noise_level  # ← BUG: using global NOISE
    else player1move
)
player2percieved.append(
    not player2move
    if NOISE and random.random() < noise_level  # ← BUG: using global NOISE
    else player2move
)
```

**Should be:**
```python
player1percieved.append(
    not player1move
    if noise and random.random() < noise_level  # ← FIX: use parameter
    else player1move
)
player2percieved.append(
    not player2move
    if noise and random.random() < noise_level  # ← FIX: use parameter
    else player2move
)
```

### Global Constant Value

**File:** `ipd_local/game_specs.py`

**Line 6:**
```python
NOISE = True  # whether or not this tournament has noise
```

This is used as the default value for the parameter, which is correct:
```python
def play_match(
    bytecode: Tuple[bytes, bytes],
    noise: bool = NOISE,  # ← Default is fine
    ...
)
```

But inside the function, it should use the **parameter** `noise`, not the **constant** `NOISE`.

---

## Impact Assessment

### High Impact Issues

1. **All tests are invalid**
   - Any test that tries to test without noise is actually testing WITH noise
   - `test_simulation.py` likely has false positives/negatives

2. **Reproducibility broken**
   - Cannot run deterministic matches
   - Even with seed, noise introduces randomness

3. **Performance impact**
   - When noise is off, matches should be faster and deterministic
   - Currently, noise is ALWAYS applied (10% of moves are flipped)

4. **API contract violated**
   - Function signature promises control over noise
   - Callers have no way to disable noise

### Components Affected

- ✅ **Notebook:** CORRECT - uses parameters properly
- ❌ **Main simulation:** WRONG - ignores `noise` parameter
- ❌ **Tests:** INVALID - thinks it's testing without noise
- ❌ **Benchmarks:** INACCURATE - all include noise overhead

---

## Reproduction Steps

1. Run the test:
   ```bash
   python test_detailed_comparison.py
   ```

2. Observe Test 3 results:
   ```
   TEST 3: History-Dependent Strategy (tit_for_tat vs rat)
   ======================================================================
   Notebook:  [99, 108]    # No noise (correct)
   Main:      (87.0, 204.0) # Has noise (incorrect!)
   ```

3. Notice that main's "no noise" matches notebook's "with noise":
   ```
   TEST 5: Noise Behavior
   ======================================================================
   Notebook WITH noise: [87, 204]
   Main WITH noise:     (87.0, 204.0)
   ```

---

## Additional Findings

### Random Strategy Behavior

For `rand` vs `silent` with seed=42:
- **Notebook (no noise):** `[700, 250]` ← Different from seed=999 result
- **Main (no noise):** `[688, 265]` ← Same as seed=999 result!

This proves the random seed is being used in the main codebase, but noise is ALSO being applied.

The 12-point difference suggests:
- Both use same random seed for strategy
- Main applies additional noise flips (10% of 100 rounds ≈ 10 moves)
- Those 10 flipped moves cause ~12-15 point swing

### Deterministic Strategies Work

`silent` vs `rat` produces correct results in both:
- **Expected:** `[0, 900]`
- **Notebook:** `[0, 900]` ✓
- **Main:** `[0, 900]` ✓

This makes sense because:
- `silent` always returns `False`
- `rat` always returns `True`
- Noise flips the *perceived* moves, but doesn't affect scoring
- Scoring uses *actual* moves, not perceived

So deterministic strategies are unaffected by the bug (lucky!), but any strategy that depends on opponent history IS affected.

---

## Recommended Fix

### Option 1: Fix the parameter usage (RECOMMENDED)

**Change lines 181 and 186 in `ipd_local/simulation.py`:**

```python
# Before:
if NOISE and random.random() < noise_level

# After:
if noise and random.random() < noise_level
```

This is a 2-character fix (`NOISE` → `noise`)

### Option 2: Remove the parameter

If the intention was for noise to always be controlled globally:
- Remove `noise` parameter from function signature
- Update all callers
- Document that noise is global-only

However, this seems incorrect given the function signature.

---

## Testing the Fix

After applying the fix, run:

```bash
python test_detailed_comparison.py
```

**Expected results:**
- Test 1 (deterministic): ✓ PASS (already passing)
- Test 2 (random): ✓ PASS (should now match)
- Test 3 (history): ✓ PASS (should now match)
- Test 4 (reproducibility): ✓ PASS (already passing)
- Test 5 (noise): ✓ PASS (already passing)

---

## Comparison: Notebook vs Main Codebase

| Feature | Notebook | Main Codebase | Status |
|---------|----------|---------------|---------|
| Respects `noise` parameter | ✅ Yes | ❌ No | Notebook correct |
| Uses `blindness` parameter | ✅ Yes | ➖ N/A | Different approach |
| Copies input lists | ✅ Yes (after fix) | ✅ Yes | Both correct |
| Multiprocessing | ❌ No | ✅ Yes | Feature difference |
| Asymmetric noise | ✅ Supported | ❌ Not supported | Feature difference |

---

## Verification Checklist

Before considering this bug fixed:

- [ ] Update `ipd_local/simulation.py` lines 181, 186
- [ ] Run `python test_detailed_comparison.py` - all tests pass
- [ ] Run `python test_simulation.py` - check for any failures
- [ ] Run `python main.py` with `NOISE = False` - verify deterministic
- [ ] Run `python main.py` with `NOISE = True` - verify noise works
- [ ] Check that existing results are still valid
- [ ] Document the fix in commit message
- [ ] Consider if this affects any published results

---

## Related Issues

This bug is **separate** from the notebook issues that were fixed earlier:
- ✅ **Notebook issue 1:** Missing `opposite_of_last` function - FIXED
- ✅ **Notebook issue 2:** Missing `.copy()` on lists - FIXED
- ❌ **Main codebase issue:** Ignoring `noise` parameter - NOT YET FIXED

---

## Questions for Review

1. **Was this intentional?**
   - Is there a reason noise should always be global?
   - The parameter suggests per-call control was intended

2. **Are published results affected?**
   - If all runs used `NOISE = True`, results are still valid
   - But they're not truly "no noise" results

3. **Should we support asymmetric noise?**
   - Notebook allows `[0.1, 0.2]` (different noise per player)
   - Main only has symmetric noise
   - This is a feature gap, not a bug

---

## Conclusion

The notebook implementation is **more correct** than the main codebase in this regard. The main codebase has a clear bug where a function parameter is defined but completely ignored in favor of a global constant.

**Severity: HIGH** - This affects correctness of all matches where noise should be disabled.

**Priority: HIGH** - Simple 2-character fix, but has wide impact.

**Status: NOT YET FIXED** - Awaiting approval to fix main codebase.
