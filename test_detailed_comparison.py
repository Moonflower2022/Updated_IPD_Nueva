"""
Detailed comparison test - suppresses output from notebook imports
"""

import sys
import os
import importlib.util
import random
import numpy as np
from io import StringIO

# Suppress stdout during imports
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

def load_notebook_quietly():
    """Load notebook module while suppressing its output."""
    with SuppressOutput():
        spec = importlib.util.spec_from_file_location(
            'notebook_quiet',
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py'
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules['notebook_quiet'] = module
        spec.loader.exec_module(module)
    return module

print("=" * 70)
print("DETAILED COMPARISON: Notebook vs Main Codebase")
print("=" * 70)

# Load notebook module
print("\nLoading notebook module...")
notebook = load_notebook_quietly()
print("✓ Loaded")

# Import main codebase
print("Loading main codebase...")
from ipd_local.simulation import play_match, pack_functions
from ipd_local.default_strategies import tit_for_tat, silent, rat, rand
print("✓ Loaded")

print("\n" + "=" * 70)
print("TEST 1: Deterministic Strategies (silent vs rat)")
print("=" * 70)

notebook.rounds = 100
payoff_dict = {
    (False, False): 5,
    (True, False): 9,
    (False, True): 0,
    (True, True): 1
}

# Notebook version
with SuppressOutput():
    nb_total, nb_results = notebook.play_match(
        notebook.silent, notebook.rat, [0, 0], payoff_dict
    )

# Main codebase version
main_result = play_match(
    pack_functions((silent, rat)),
    noise=False,
    rounds=100,
    random_seed=42
)

print(f"Notebook:  {nb_results['score']}")
print(f"Main:      {main_result}")
print(f"Expected:  [0, 900] (silent always cooperates, rat always defects)")

if nb_results['score'] == [0, 900] and list(main_result) == [0, 900]:
    print("✓ PASS: Both implementations match expected outcome")
else:
    print("✗ FAIL: Results don't match expected outcome")

print("\n" + "=" * 70)
print("TEST 2: Random Strategy (rand vs silent)")
print("=" * 70)

# Test with random strategy
print("\nWith seed=42:")

# Notebook version
with SuppressOutput():
    random.seed(42)
    np.random.seed(42)
    nb_total1, nb_results1 = notebook.play_match(
        notebook.rand, notebook.silent, [0, 0], payoff_dict
    )

# Main codebase version
main_result1 = play_match(
    pack_functions((rand, silent)),
    noise=False,
    rounds=100,
    random_seed=42
)

print(f"Notebook:  {nb_results1['score']}")
print(f"Main:      {main_result1}")

if list(nb_results1['score']) == list(main_result1):
    print("✓ PASS: Random strategies produce same results with same seed")
else:
    diff = [abs(a - b) for a, b in zip(nb_results1['score'], main_result1)]
    print(f"✗ FAIL: Difference = {diff}")

print("\nWith seed=999:")

# Notebook version
with SuppressOutput():
    random.seed(999)
    np.random.seed(999)
    nb_total2, nb_results2 = notebook.play_match(
        notebook.rand, notebook.silent, [0, 0], payoff_dict
    )

# Main codebase version
main_result2 = play_match(
    pack_functions((rand, silent)),
    noise=False,
    rounds=100,
    random_seed=999
)

print(f"Notebook:  {nb_results2['score']}")
print(f"Main:      {main_result2}")

if list(nb_results2['score']) == list(main_result2):
    print("✓ PASS: Different seed produces same results in both")
else:
    diff = [abs(a - b) for a, b in zip(nb_results2['score'], main_result2)]
    print(f"✗ FAIL: Difference = {diff}")

# Check that different seeds produce different results
if nb_results1['score'] != nb_results2['score']:
    print("✓ PASS: Different seeds produce different results (as expected)")
else:
    print("⚠ WARNING: Different seeds produced identical results")

print("\n" + "=" * 70)
print("TEST 3: History-Dependent Strategy (tit_for_tat vs rat)")
print("=" * 70)

# Notebook version
with SuppressOutput():
    random.seed(42)
    np.random.seed(42)
    nb_total3, nb_results3 = notebook.play_match(
        notebook.tit_for_tat, notebook.rat, [0, 0], payoff_dict
    )

# Main codebase version
main_result3 = play_match(
    pack_functions((tit_for_tat, rat)),
    noise=False,
    rounds=100,
    random_seed=42
)

print(f"Notebook:  {nb_results3['score']}")
print(f"Main:      {main_result3}")

# Analyze the moves
tft_moves = nb_results3['details'][0]
rat_moves = nb_results3['details'][1]

print(f"\nMove analysis:")
print(f"  tit_for_tat first 5 moves: {tft_moves[:5]}")
print(f"  rat first 5 moves:         {rat_moves[:5]}")
print(f"  Expected: tit_for_tat=[False, True, True, ...], rat=[True, True, ...]")

# tit_for_tat should cooperate first, then defect forever
expected_tft = [False] + [True] * 99
if tft_moves == expected_tft and all(rat_moves):
    print("✓ PASS: Move history is correct")
else:
    print("✗ FAIL: Move history doesn't match expected pattern")

if list(nb_results3['score']) == list(main_result3):
    print("✓ PASS: Scores match between notebook and main")
else:
    diff = [abs(a - b) for a, b in zip(nb_results3['score'], main_result3)]
    print(f"✗ FAIL: Score difference = {diff}")

print("\n" + "=" * 70)
print("TEST 4: Reproducibility Check")
print("=" * 70)

# Run same matchup multiple times with same seed
print("\nRunning tit_for_tat vs rat 3 times with seed=42...")

results = []
for i in range(3):
    with SuppressOutput():
        random.seed(42)
        np.random.seed(42)
        _, result = notebook.play_match(
            notebook.tit_for_tat, notebook.rat, [0, 0], payoff_dict
        )
    results.append(result['score'])
    print(f"  Run {i+1}: {result['score']}")

if results[0] == results[1] == results[2]:
    print("✓ PASS: Perfectly reproducible with same seed")
else:
    print("✗ FAIL: Results vary despite same seed")

print("\n" + "=" * 70)
print("TEST 5: Noise Behavior")
print("=" * 70)

print("\nWith noise [0.1, 0.1], seed=42:")

# Notebook with noise
with SuppressOutput():
    random.seed(42)
    np.random.seed(42)
    _, nb_noise = notebook.play_match(
        notebook.tit_for_tat, notebook.rat, [0.1, 0.1], payoff_dict
    )

# Main with noise
main_noise = play_match(
    pack_functions((tit_for_tat, rat)),
    noise=True,
    noise_level=0.1,
    rounds=100,
    num_noise_games_to_avg=1,
    random_seed=42
)

print(f"Notebook:  {nb_noise['score']}")
print(f"Main:      {main_noise}")

if list(nb_noise['score']) == list(main_noise):
    print("✓ PASS: Noise produces matching results")
else:
    diff = [abs(a - b) for a, b in zip(nb_noise['score'], main_noise)]
    print(f"✗ FAIL: Difference = {diff}")
    print("  Note: Noise may cause small variations")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print("\nKey findings:")
print("1. Deterministic strategies should always match")
print("2. Random strategies should match with same seed")
print("3. Move histories should be identical")
print("4. Noise behavior may differ slightly")
