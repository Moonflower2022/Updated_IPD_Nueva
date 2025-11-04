# CLAUDE.md - AI Assistant Guide for IPD Simulation Codebase

## Project Overview

This is an **Iterated Prisoner's Dilemma (IPD) Tournament Simulation** designed for MicroEconomics education. The system allows students to submit their own strategies via Google Forms/Pastebin, which are then automatically fetched, validated, and run in a round-robin tournament against each other and default strategies.

**Key Features:**
- Automated strategy collection from Google Sheets + Pastebin
- Multiprocessing-based simulation engine for performance
- Optional noise simulation (miscommunication between players)
- Strategy validation and blacklisting
- AI-powered strategy descriptions using LLM
- Automated results publishing to Google Sheets

## Architecture

### High-Level Flow

```
Google Sheets (Submissions)
    ↓
get_inputs.py (Fetch & Validate)
    ↓
simulation.py (Run Tournament)
    ↓
descriptor.py (AI Descriptions)
    ↓
output.py (Export Results)
    ↓
Google Sheets (Results)
```

### Core Components

1. **Input Layer** (`get_inputs.py`)
   - Fetches student submissions from Google Sheets
   - Downloads Python code from Pastebin links
   - Validates and loads strategy functions
   - Enforces character/function limits
   - Applies blocklists

2. **Simulation Engine** (`simulation.py`)
   - Runs matches between strategy pairs
   - Handles noise/miscommunication
   - Uses multiprocessing for parallel execution
   - Marshals functions for safe IPC
   - Tracks and logs errors

3. **Strategy Description** (`descriptor.py`)
   - Uses LLM (Llama 3.1 70B via NVIDIA API) to describe strategies
   - Generates 5-word and 40-word summaries
   - Uses structured JSON output via Pydantic

4. **Output Layer** (`output.py`)
   - Calculates rankings and pairwise scores
   - Generates pandas DataFrames
   - Publishes results to Google Sheets

## File Structure

```
Updated_IPD_Nueva/
├── main.py                          # Entry point - orchestrates entire flow
├── tests.py                         # Unit tests for core functionality
├── requirements.txt                 # Python dependencies
├── blocked_functions.txt            # Blocklist for individual functions
├── blocked_submissions.txt          # Blocklist for entire submissions
├── service_account.json            # Google Sheets API credentials (not in repo)
└── ipd_local/                      # Main package
    ├── __init__.py
    ├── types.py                    # Type definitions (Strategy alias)
    ├── game_specs.py               # Configuration constants
    ├── get_inputs.py               # Input fetching and validation
    ├── simulation.py               # Core game simulation logic
    ├── default_strategies.py       # Built-in strategies (tit-for-tat, etc.)
    ├── descriptor.py               # LLM-based strategy descriptions
    ├── output.py                   # Results processing and export
    ├── output_locations.py         # File path constants
    ├── prompts.py                  # LLM prompts for descriptions
    └── utils.py                    # Helper functions
```

## Configuration (`game_specs.py`)

**Critical Constants:**

```python
NOISE = True                        # Enable noise/miscommunication
NOISE_LEVEL = 0.1                   # 10% chance of move being misread
NUM_NOISE_GAMES_TO_AVG = 50        # Games to average when noise is on
ROUNDS = randint(100, 200)         # Random rounds per match
MAXIMUM_NUM_FUNCTIONS = 10         # Max functions per submission
MAXIMUM_CHAR_COUNT = 5000          # Max characters per submission
INCLUDE_DEFAULTS = True            # Include default strategies

# Payoff matrix (classic prisoner's dilemma)
POINTS_BOTH_COOPERATE = 5          # Mutual cooperation
POINTS_DIFFERENT_WINNER = 9        # Successful defection
POINTS_DIFFERENT_LOSER = 0         # Failed cooperation
POINTS_BOTH_RAT = 1                # Mutual defection
```

## Strategy Function Contract

All strategies must follow this signature:

```python
def strategy_name(
    mymoves: List[bool],      # My previous moves (True = rat/defect)
    othermoves: List[bool],   # Opponent's previous moves
    currentRound: int         # Current round number (0-indexed)
) -> bool | List[bool]:       # Return bool or list of bools
    """
    True = Rat/Defect
    False = Silent/Cooperate

    Can return a single bool or a list of bools for multi-round planning.
    """
    pass
```

**Important Notes:**
- Strategies must NOT modify input lists
- Strategies must import their own dependencies (except random, math, numpy)
- Strategies run in sandboxed environment with suppressed stdout
- Invalid strategies are caught during validation and logged

## Working with This Codebase

### Common Tasks

#### 1. Modifying Game Parameters
Edit `ipd_local/game_specs.py`:
```python
ROUNDS = 150              # Fixed rounds instead of random
NOISE = False             # Disable noise
POINTS_BOTH_COOPERATE = 3 # Change payoff matrix
```

#### 2. Adding New Default Strategies
Add to `ipd_local/default_strategies.py`:
```python
def my_strategy(mymoves, othermoves, currentRound):
    # Implementation
    return False

# Add to the list at bottom
all_default_functions.append(my_strategy)
```

#### 3. Running the Simulation
```bash
python main.py
# or
python3 main.py
```

#### 4. Running Tests
```bash
python tests.py
# or
python3 tests.py
```

### Important Implementation Details

#### Multiprocessing and Function Marshaling

The simulation uses `marshal` to serialize functions for multiprocessing:

```python
# From simulation.py
def pack_functions(functions):
    return (
        (marshal.dumps(functions[0].__code__), functions[0].__name__),
        (marshal.dumps(functions[1].__code__), functions[1].__name__),
    )
```

**Why?** Multiprocessing requires pickling, but many user-defined functions can't be pickled. Marshaling bytecode works around this, but means functions cannot reference external globals.

**Important:** This is why `random`, `math`, and `numpy` are imported in both `get_inputs.py` and `simulation.py` - to provide them as globals for unmarshaled functions.

#### Noise Simulation

When `NOISE = True`:
- Each move has `NOISE_LEVEL` chance of being misread by opponent
- Multiple games are played and averaged (`NUM_NOISE_GAMES_TO_AVG`)
- Implementation in `simulation.py:179-188`:

```python
player1percieved.append(
    not player1move if NOISE and random.random() < noise_level
    else player1move
)
```

#### Output Suppression

Student code might contain print statements. These are suppressed using:
```python
with suppress_output():
    # Run student code
```

This redirects stdout/stderr to prevent console spam.

#### Boolean List Returns

Strategies can return `List[bool]` for multi-round planning:
```python
# From simulation.py:142-144
if check_type(player1move, list[bool]):
    player1currentreturnedmoves = player1move.copy()
    player1move = player1currentreturnedmoves.pop(0)
```

The system will pop moves from the list in subsequent rounds until empty.

### Performance Optimizations

1. **Multiprocessing**: All matches run in parallel across CPU cores
   ```python
   with mp.Pool(mp.cpu_count()) as pool:
       result = list(tqdm(pool.imap(...)))
   ```

2. **Output Suppression Moved Outward**: Major speedup (~10x) by moving `suppress_output()` to outer layer instead of per-move

3. **Round-Robin Only Upper Triangle**: Only plays each matchup once (not both orders)
   ```python
   for i, p1 in enumerate(strats):
       for j, p2 in enumerate(strats):
           if j <= i:
               continue  # Skip already-played matchups
   ```

4. **Pastebin Caching**: Optional caching of downloaded code
   ```python
   get_pastebin(link, cache=True)
   ```

### Testing

The `tests.py` file includes:
- **Simulation tests**: `get_scores`, `pack_functions`, `play_match`, `run_simulation`
- **Input tests**: `get_strategy_code_pairs`
- **Descriptor tests**: LLM API integration tests

Run with:
```bash
python tests.py
```

Note: Descriptor tests require valid NVIDIA API key.

### Error Handling and Logging

- **Logger**: Uses `loguru` for structured logging
- **Log Location**: Defined in `output_locations.py` as `PROBLEMS_LOG_LOCATION`
- **Error Tracking**:
  - Erroneous pastebins (syntax errors, import errors)
  - Function-overloaded pastebins (too many functions)
  - Character-overloaded pastebins (too long)
  - Bad I/O functions (wrong signature, modifies inputs)
  - Runtime errors during matches

All errors are logged with context (student name, function name, round number, opponent).

### Google Sheets Integration

Requires `service_account.json` with credentials:

```python
# From get_inputs.py
service_account = gspread.service_account(filename="service_account.json")
spreadsheet = service_account.open(INPUT_SHEET_NAME)
```

**Input Sheet Columns:**
- Column 1: Student Name
- Column 2: Regular Strategy Pastebin Link
- Column 3: Noise Strategy Pastebin Link

**Output Sheets:**
- Summary Statistics
- Ranking (sorted by total points)
- Pairwise Scores (matrix of all matchups)

## Common Issues and Solutions

### Issue: Functions failing validation
**Solution**: Check that functions:
- Don't modify input lists
- Return bool or List[bool]
- Don't rely on external globals
- Import their own dependencies

### Issue: Multiprocessing errors
**Solution**: Ensure functions don't reference globals. If needed, add imports to `simulation.py` and `get_inputs.py`.

### Issue: Slow simulation
**Solution**:
- Reduce `NUM_NOISE_GAMES_TO_AVG`
- Reduce `ROUNDS`
- Disable `DESCRIBE_STRATEGIES`
- Set `INCLUDE_DEFAULTS = False` if not needed

### Issue: LLM descriptions failing
**Solution**: Check NVIDIA API key in `descriptor.py`. This is hardcoded and should be moved to environment variable.

## Security Considerations

⚠️ **This code executes arbitrary Python from Pastebin submissions!**

- Uses `exec()` to load student code
- Suppresses output but doesn't sandbox execution
- Functions run in multiprocessing workers (some isolation)
- Blocklists provide basic protection

**Recommended for trusted educational environments only.**

## Code Quality Notes

Recent improvements (see README.md):
- ✅ Fixed typing issues
- ✅ Removed `import *` statements (mostly)
- ✅ Added comprehensive tests
- ✅ Used Black formatter
- ✅ Snake_case for consistency

Remaining TODOs:
- Remove remaining `import *` usage
- Put control settings in a class
- Add support for single-threaded function execution
- Redo command line parsing
- Export pairwise scores as CSV
- Parse strategies individually to handle partial errors

## Development Workflow

1. **Making Changes**:
   ```bash
   # Edit files
   # Run tests
   python tests.py

   # Test full simulation with small dataset
   # (modify game_specs.py to reduce rounds/noise games)
   python main.py
   ```

2. **Adding Features**:
   - Add implementation
   - Add tests to `tests.py`
   - Update this documentation
   - Test with real data

3. **Debugging**:
   - Check `ipd.log` for errors (via `loguru`)
   - Check `blacklist.txt` for failed functions
   - Check `successful_blocks.txt` for blocked items
   - Use `python -m pdb main.py` for step debugging

## LLM Integration (Descriptor Module)

The system uses **Llama 3.1 70B Instruct** via NVIDIA API for strategy descriptions:

```python
# From descriptor.py
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="nvapi-..." # ⚠️ Hardcoded - should use env var
)
```

**Response Format** (Pydantic model):
```python
class SummaryResponse(BaseModel):
    summary5: str    # 5-word summary
    summary40: str   # 40-word summary
```

The prompt asks the LLM to explain the strategy's behavior in plain English.

## Git History Notes

This repository was forked from:
- Original: `github.com/annliz/IPD`
- Intermediate: `github.com/AleTuch17/Updated_IPD_Nueva`

Major changes in this fork include performance optimizations, type safety, and enhanced testing.

---

## Quick Reference

**Run simulation**: `python main.py`
**Run tests**: `python tests.py`
**Configure**: Edit `ipd_local/game_specs.py`
**Block strategies**: Add to `blocked_functions.txt` or `blocked_submissions.txt`
**View logs**: Check `ipd.log` (location in `output_locations.py`)
**Output**: Raw JSON in locations defined by `output_locations.py`

**Strategy Return Values**:
- `True` = Rat/Defect
- `False` = Silent/Cooperate

**Payoff Matrix** (default):
```
                Silent    Rat
Silent          (5,5)     (0,9)
Rat             (9,0)     (1,1)
```
