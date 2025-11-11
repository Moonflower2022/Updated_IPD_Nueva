"""
Test script to verify that individual matchup results are consistent
between the notebook implementation and the main codebase.

Tests:
1. Reproducibility (same seed -> same results)
2. Result format consistency
3. Noise behavior consistency
"""

import sys
import importlib.util
import random
import numpy as np

def load_python_file_as_module(filepath, module_name):
    """Load a Python file as a module."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def test_reproducibility():
    """Test that running with same seed produces same results."""
    print("=" * 60)
    print("TEST 1: Reproducibility (same seed -> same results)")
    print("=" * 60)

    issues = []

    try:
        # Load notebook module
        notebook = load_python_file_as_module(
            '/Users/hq/github_projects/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_repro'
        )

        # Test strategies
        strategies = [notebook.tit_for_tat, notebook.silent, notebook.rat]

        # Test 1: No noise reproducibility
        print("\n--- Testing NO NOISE reproducibility ---")
        notebook.rounds = 100

        run1 = notebook.run_no_noise_tournament(strategies, 100, [5, 9, 0, 1], seed=42)
        run2 = notebook.run_no_noise_tournament(strategies, 100, [5, 9, 0, 1], seed=42)

        # Compare all scores
        for strat1 in strategies:
            for strat2 in strategies:
                score1 = run1[strat1.__name__][strat2.__name__]['score']
                score2 = run2[strat1.__name__][strat2.__name__]['score']

                if score1 != score2:
                    issue = f"✗ ISSUE: Results differ for {strat1.__name__} vs {strat2.__name__}"
                    print(issue)
                    print(f"  Run 1: {score1}")
                    print(f"  Run 2: {score2}")
                    issues.append(issue)

        if not any("Results differ" in i for i in issues):
            print("✓ No noise: Results are reproducible")

        # Test 2: With noise reproducibility
        print("\n--- Testing WITH NOISE reproducibility ---")

        run1 = notebook.run_noise_tournament(
            strategies, 100, [0.1, 0.1], 5, [5, 9, 0, 1],
            seeds=[42, 43, 44, 45, 46]
        )
        run2 = notebook.run_noise_tournament(
            strategies, 100, [0.1, 0.1], 5, [5, 9, 0, 1],
            seeds=[42, 43, 44, 45, 46]
        )

        # Compare all scores
        noise_consistent = True
        for strat1 in strategies:
            for strat2 in strategies:
                score1 = run1[strat1.__name__][strat2.__name__]['score']
                score2 = run2[strat1.__name__][strat2.__name__]['score']

                if score1 != score2:
                    issue = f"✗ ISSUE: Noise results differ for {strat1.__name__} vs {strat2.__name__}"
                    print(issue)
                    print(f"  Run 1: {score1}")
                    print(f"  Run 2: {score2}")
                    issues.append(issue)
                    noise_consistent = False

        if noise_consistent:
            print("✓ With noise: Results are reproducible")

    except Exception as e:
        issue = f"✗ ISSUE: Reproducibility test failed: {e}"
        print(issue)
        issues.append(issue)
        import traceback
        traceback.print_exc()

    return issues

def test_notebook_vs_codebase():
    """Test that notebook and main codebase produce similar results."""
    print("\n" + "=" * 60)
    print("TEST 2: Notebook vs Main Codebase Consistency")
    print("=" * 60)

    issues = []

    try:
        # Load notebook module
        notebook = load_python_file_as_module(
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_vs_main'
        )

        # Import main codebase
        from ipd_local.simulation import play_match, pack_functions
        from ipd_local.default_strategies import tit_for_tat, silent, rat
        from ipd_local.game_specs import (
            POINTS_BOTH_COOPERATE, POINTS_DIFFERENT_WINNER,
            POINTS_DIFFERENT_LOSER, POINTS_BOTH_RAT
        )

        print("\n--- Comparing single matchup: tit_for_tat vs rat ---")

        # Set up notebook match
        notebook.rounds = 100
        payoff_dict_nb = {
            (False, False): 5,
            (True, False): 9,
            (False, True): 0,
            (True, True): 1
        }

        # Run notebook version (no noise)
        random.seed(42)
        np.random.seed(42)
        nb_total, nb_results = notebook.play_match(
            notebook.tit_for_tat, notebook.rat, [0, 0], payoff_dict_nb
        )

        print(f"Notebook result: {nb_results['score']}")
        print(f"  - Total for player 2: {nb_total}")
        print(f"  - tit_for_tat moves (first 10): {nb_results['details'][0][:10]}")
        print(f"  - rat moves (first 10): {nb_results['details'][1][:10]}")

        # Run main codebase version (no noise)
        main_result = play_match(
            pack_functions((tit_for_tat, rat)),
            noise=False,
            rounds=100,
            random_seed=42
        )

        print(f"Main codebase result: {main_result}")

        # Calculate percentage difference
        if main_result:
            diff_p1 = abs(nb_results['score'][0] - main_result[0])
            diff_p2 = abs(nb_results['score'][1] - main_result[1])
            print(f"  - Difference: Player1={diff_p1}, Player2={diff_p2}")

        # Compare scores
        if nb_results['score'][0] == main_result[0] and nb_results['score'][1] == main_result[1]:
            print("✓ Scores match exactly!")
        else:
            issue = f"✗ ISSUE: Scores differ between notebook and main codebase"
            print(issue)
            print(f"  Notebook: {nb_results['score']}")
            print(f"  Main:     {main_result}")
            issues.append(issue)

        # Test with another pair
        print("\n--- Comparing: silent vs tit_for_tat ---")

        random.seed(42)
        np.random.seed(42)
        nb_total2, nb_results2 = notebook.play_match(
            notebook.silent, notebook.tit_for_tat, [0, 0], payoff_dict_nb
        )

        main_result2 = play_match(
            pack_functions((silent, tit_for_tat)),
            noise=False,
            rounds=100,
            random_seed=42
        )

        print(f"Notebook: {nb_results2['score']}")
        print(f"Main:     {main_result2}")

        if nb_results2['score'][0] == main_result2[0] and nb_results2['score'][1] == main_result2[1]:
            print("✓ Scores match!")
        else:
            issue = f"✗ ISSUE: Scores differ for silent vs tit_for_tat"
            print(issue)
            issues.append(issue)

    except Exception as e:
        issue = f"✗ ISSUE: Comparison test failed: {e}"
        print(issue)
        issues.append(issue)
        import traceback
        traceback.print_exc()

    return issues

def test_noise_behavior():
    """Test that noise behaves consistently."""
    print("\n" + "=" * 60)
    print("TEST 3: Noise Behavior")
    print("=" * 60)

    issues = []

    try:
        notebook = load_python_file_as_module(
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_noise'
        )

        notebook.rounds = 100
        payoff_dict = {
            (False, False): 5,
            (True, False): 9,
            (False, True): 0,
            (True, True): 1
        }

        print("\n--- Testing symmetric noise [0.1, 0.1] ---")

        # Run multiple times with noise
        scores = []
        for i in range(5):
            random.seed(42 + i)
            np.random.seed(42 + i)
            total, results = notebook.play_match(
                notebook.tit_for_tat, notebook.rat, [0.1, 0.1], payoff_dict
            )
            scores.append(results['score'])
            print(f"  Run {i+1}: {results['score']}")

        # With noise, scores should vary (but not by too much)
        score_variation = len(set([tuple(s) for s in scores]))
        if score_variation > 1:
            print(f"✓ Noise produces variation ({score_variation} different outcomes)")
        else:
            issue = "⚠ WARNING: All noise runs produced identical results"
            print(issue)
            issues.append(issue)

        print("\n--- Testing asymmetric noise [0.2, 0.0] ---")

        # Player 1 has 20% noise, Player 2 has 0% noise
        random.seed(42)
        np.random.seed(42)
        total1, results1 = notebook.play_match(
            notebook.tit_for_tat, notebook.rat, [0.2, 0.0], payoff_dict
        )

        # Swap: Player 1 has 0% noise, Player 2 has 20% noise
        random.seed(42)
        np.random.seed(42)
        total2, results2 = notebook.play_match(
            notebook.tit_for_tat, notebook.rat, [0.0, 0.2], payoff_dict
        )

        print(f"  [0.2, 0.0]: {results1['score']}")
        print(f"  [0.0, 0.2]: {results2['score']}")

        if results1['score'] != results2['score']:
            print("✓ Asymmetric noise produces different results (as expected)")
        else:
            issue = "⚠ WARNING: Asymmetric noise produced same results"
            print(issue)
            issues.append(issue)

        print("\n--- Testing noise averaging ---")

        # Run tournament with noise averaging
        strategies = [notebook.tit_for_tat, notebook.rat]
        data = notebook.run_noise_tournament(
            strategies, 100, [0.1, 0.1], 10, [5, 9, 0, 1],
            seeds=list(range(42, 52))
        )

        avg_score = data['tit_for_tat']['rat']['score']
        print(f"  Average score over 10 games: {avg_score}")

        # Check that we have multiple game details
        if len(data['tit_for_tat']['rat']['details']) == 10:
            print("✓ Noise averaging stores all game details")
        else:
            issue = f"✗ ISSUE: Expected 10 game details, got {len(data['tit_for_tat']['rat']['details'])}"
            print(issue)
            issues.append(issue)

    except Exception as e:
        issue = f"✗ ISSUE: Noise behavior test failed: {e}"
        print(issue)
        issues.append(issue)
        import traceback
        traceback.print_exc()

    return issues

def test_return_value_formats():
    """Test that return values have correct format."""
    print("\n" + "=" * 60)
    print("TEST 4: Return Value Formats")
    print("=" * 60)

    issues = []

    try:
        notebook = load_python_file_as_module(
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_format'
        )

        notebook.rounds = 50
        payoff_dict = {
            (False, False): 5,
            (True, False): 9,
            (False, True): 0,
            (True, True): 1
        }

        print("\n--- Checking play_match return format ---")

        random.seed(42)
        np.random.seed(42)
        total, results = notebook.play_match(
            notebook.tit_for_tat, notebook.rat, [0, 0], payoff_dict
        )

        # Check structure
        checks = [
            ('total is number', isinstance(total, (int, float))),
            ('results is dict', isinstance(results, dict)),
            ('results has "score"', 'score' in results),
            ('results has "details"', 'details' in results),
            ('score is list of 2', isinstance(results['score'], list) and len(results['score']) == 2),
            ('details is list of 2', isinstance(results['details'], list) and len(results['details']) == 2),
            ('details[0] is list', isinstance(results['details'][0], list)),
            ('details[0] length == rounds', len(results['details'][0]) == 50),
            ('moves are bools', all(isinstance(m, bool) for m in results['details'][0])),
        ]

        for check_name, passed in checks:
            if passed:
                print(f"  ✓ {check_name}")
            else:
                issue = f"✗ ISSUE: {check_name} - FAILED"
                print(f"  {issue}")
                issues.append(issue)

        print("\n--- Checking tournament return format ---")

        strategies = [notebook.tit_for_tat, notebook.silent]
        data = notebook.run_no_noise_tournament(strategies, 50, [5, 9, 0, 1], seed=42)

        checks2 = [
            ('data is dict', isinstance(data, dict)),
            ('has strategy keys', 'tit_for_tat' in data and 'silent' in data),
            ('has Average', 'Average' in data['tit_for_tat']),
            ('has Total', 'Total' in data['tit_for_tat']),
            ('has matchup data', 'silent' in data['tit_for_tat']),
            ('matchup has score', 'score' in data['tit_for_tat']['silent']),
            ('matchup has details', 'details' in data['tit_for_tat']['silent']),
        ]

        for check_name, passed in checks2:
            if passed:
                print(f"  ✓ {check_name}")
            else:
                issue = f"✗ ISSUE: {check_name} - FAILED"
                print(f"  {issue}")
                issues.append(issue)

    except Exception as e:
        issue = f"✗ ISSUE: Format test failed: {e}"
        print(issue)
        issues.append(issue)
        import traceback
        traceback.print_exc()

    return issues

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MATCHUP CONSISTENCY & REPRODUCIBILITY TEST SUITE")
    print("=" * 60)

    all_issues = []

    # Run all tests
    all_issues.extend(test_reproducibility())
    all_issues.extend(test_notebook_vs_codebase())
    all_issues.extend(test_noise_behavior())
    all_issues.extend(test_return_value_formats())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all_issues:
        print(f"\n⚠ Found {len(all_issues)} issue(s):\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
        return 1
    else:
        print("\n✓ All tests passed! Matchup results are consistent and reproducible.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
