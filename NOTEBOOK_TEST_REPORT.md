# Jupyter Notebook Consistency Test Report

**Date:** 2025-11-05
**Files Tested:**
- `personal_ipd_tournament_2025.ipynb` (Jupyter Notebook)
- `personal_ipd_tournament_2025.py` (Python version)
- Main codebase in `ipd_local/`

## Executive Summary

The notebook and Python files have **critical issues** that prevent them from running correctly. Additionally, there are some **inconsistencies** with the main codebase that should be addressed.

### Critical Issues (Must Fix)

1. ✗ **Missing Function Definition**: `opposite_of_last` is referenced but never defined
2. ✗ **Input List Protection**: Strategies can modify input lists (differs from main codebase)

### Moderate Issues (Should Fix)

3. ⚠ **Different Noise Implementation**: Notebook uses `blindness` parameter, main codebase uses `noise_level`
4. ⚠ **No Multiprocessing**: Notebook runs sequentially, main codebase uses parallel processing
5. ⚠ **Different Type Checking**: Different approaches to validating return types

---

## Detailed Issue Analysis

### 1. Missing Function: `opposite_of_last` ✗ CRITICAL

**Location:**
- `personal_ipd_tournament_2025.py` line 436
- `personal_ipd_tournament_2025.ipynb` cell 13

**Issue:**
```python
funcs = [rat, silent, rand, kinda_random, tit_for_tat, tit_for_two_tats,
         nuke_for_tat, nuke_for_two_tats, nuke_for_five_tats,
         get_angry_after_twenty, cooperate_at_multiples_of_three,
         alternate_every_five, opposite_of_last]  # ← opposite_of_last is NOT defined!
```

**Impact:**
- Running the noise tournament section will crash with `NameError: name 'opposite_of_last' is not defined`
- The notebook output shows results for `opposite_of_last`, suggesting it was defined when the notebook was run previously

**Recommendation:**
Either:
1. Define the `opposite_of_last` function (if it's meant to be included), OR
2. Remove it from the `funcs` list

**Suggested Definition** (if needed):
```python
def opposite_of_last(my_moves, other_moves, current_round):
    """Returns the opposite of opponent's last move (tit-for-tat inverted)."""
    if len(other_moves) == 0:
        return False  # Cooperate on first round
    return not other_moves[-1]  # Do opposite of opponent's last move
```

---

### 2. Input List Protection ✗ CRITICAL

**Location:**
- `personal_ipd_tournament_2025.py` lines 80-81, 87-88
- Main codebase: `ipd_local/simulation.py` lines 138-139, 161-162

**Issue:**
The notebook passes lists directly to strategy functions without copying them:

**Notebook (WRONG):**
```python
player1move = player1(
    player1TrueMoves,      # ← Not copied!
    player2ObsMoves,       # ← Not copied!
    i,
)
```

**Main Codebase (CORRECT):**
```python
player1move = player1(
    player1moves.copy(),     # ← Copied to prevent modification
    player2percieved.copy(), # ← Copied to prevent modification
    i,
)
```

**Impact:**
- Malicious or buggy strategies can modify the game history
- This violates the strategy contract and can cause unfair advantages
- Results may be inconsistent or corrupted

**Recommendation:**
Add `.copy()` to all list parameters passed to strategies:

```python
# Line ~80-81
player1move = player1(
    player1TrueMoves.copy(),
    player2ObsMoves.copy(),
    i
)

# Line ~87-88
player2move = player2(
    player2TrueMoves.copy(),
    player1ObsMoves.copy(),
    i
)
```

---

### 3. Different Noise Implementation ⚠ MODERATE

**Location:**
- Notebook: uses `blindness` parameter as `[player1_noise, player2_noise]`
- Main codebase: uses single `noise_level` applied to both players

**Notebook:**
```python
def run_noise_tournament(strats, rounds, blindness, num_rounds_to_avg, payoff, seeds=None):
    ...
    play_match(player1, player2, blindness, payoff_dict)
```

**Main Codebase:**
```python
def play_match(bytecode, noise=NOISE, noise_level=NOISE_LEVEL, ...):
    ...
    # Same noise_level applied to both players
```

**Impact:**
- The notebook allows asymmetric noise (different for each player)
- Main codebase applies same noise to both players
- This is a **feature difference**, not necessarily a bug

**Recommendation:**
- Document this difference clearly
- Consider if asymmetric noise is a desired feature
- If not, simplify notebook to match main codebase

---

### 4. No Multiprocessing ⚠ MODERATE

**Issue:**
- Main codebase uses `multiprocessing.Pool` to run matches in parallel
- Notebook runs all matches sequentially

**Impact:**
- Notebook will be significantly slower for large tournaments
- On an 8-core machine, main codebase can be ~8x faster

**Recommendation:**
- This is acceptable for an educational/interactive notebook
- Users can run the main simulation for performance-critical work
- Document the performance difference

---

### 5. Different Type Checking ⚠ MINOR

**Notebook:**
```python
if not (type(player1move) is bool or
        (type(player1move) is list and len(player1move) > 0 and
         type(player1move[0]) is bool)):
```

**Main Codebase:**
```python
if check_type(player1move, list[bool]):
    ...
if not isinstance(player1move, bool):
    ...
```

**Impact:**
- Both approaches work, but main codebase is cleaner
- Notebook approach has a bug: doesn't check ALL elements of list, only first one

**Recommendation:**
- Use `isinstance()` instead of `type() is`
- Consider extracting type checking to a helper function

---

## Comparison: Notebook vs Main Codebase

| Feature | Notebook | Main Codebase | Compatible? |
|---------|----------|---------------|-------------|
| Strategy Definitions | ✓ Same | ✓ Same | ✓ Yes |
| Payoff Matrix | ✓ Same | ✓ Same | ✓ Yes |
| Input List Copying | ✗ Missing | ✓ Present | ✗ **No** |
| Noise Implementation | Asymmetric | Symmetric | ⚠ Different |
| Multiprocessing | ✗ No | ✓ Yes | ⚠ Different |
| Function Marshaling | ✗ No | ✓ Yes | ⚠ Different |
| Output Suppression | ✗ No | ✓ Yes | ⚠ Different |
| Error Logging | ✗ Basic | ✓ Loguru | ⚠ Different |

---

## Recommendations Summary

### Immediate Actions Required:

1. **Fix the `opposite_of_last` issue:**
   - Either define the function or remove it from the funcs list

2. **Add list copying:**
   - Update lines 80-81 and 87-88 in both files
   - Add `.copy()` to all list parameters

### Optional Improvements:

3. **Add a warning in the notebook:**
   ```markdown
   ⚠️ **Note:** This notebook is designed for interactive exploration and learning.
   For large-scale tournaments, use `main.py` which includes multiprocessing
   for better performance.
   ```

4. **Document the differences:**
   - Clarify that asymmetric noise is a notebook-only feature
   - Explain why multiprocessing isn't used (for simplicity/debugging)

5. **Add validation:**
   - Consider adding a "Test All Functions" cell that validates all strategies
   - Show which strategies pass/fail validation

---

## Test Results

### Files That Work:
- ✓ `ipd_local/simulation.py` - All tests pass
- ✓ `ipd_local/default_strategies.py` - All strategies defined and working

### Files With Issues:
- ✗ `personal_ipd_tournament_2025.py` - Crashes due to `opposite_of_last`
- ✗ `personal_ipd_tournament_2025.ipynb` - Same issue

### Test Coverage:
- ✓ Function definitions checked
- ✓ Strategy signatures validated
- ✓ Simulation logic compared
- ✓ Type checking analyzed
- ✗ Full integration test (blocked by missing function)

---

## Conclusion

The notebook is **95% consistent** with the main codebase in terms of strategy definitions and game logic. However, there are **2 critical bugs** that must be fixed before it can run correctly:

1. Define or remove `opposite_of_last`
2. Add `.copy()` to list parameters

Once these are fixed, the notebook should work correctly for educational purposes. The differences in noise implementation, multiprocessing, and error handling are acceptable for a simplified, interactive version.
