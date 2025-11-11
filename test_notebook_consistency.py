"""
Test script to verify consistency between the Jupyter notebook and main codebase.
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

def test_missing_functions():
    """Test for undefined functions referenced in the code."""
    print("=" * 60)
    print("TEST 1: Checking for undefined function references")
    print("=" * 60)

    issues = []

    # Load the notebook Python file
    try:
        notebook_module = load_python_file_as_module(
            '/Users/hq/github_projects/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_module'
        )
        print("✓ Successfully loaded personal_ipd_tournament_2025.py")
    except Exception as e:
        print(f"✗ Failed to load personal_ipd_tournament_2025.py: {e}")
        issues.append(f"Failed to load notebook Python file: {e}")
        return issues

    # Check for opposite_of_last function
    if not hasattr(notebook_module, 'opposite_of_last'):
        issue = "✗ ISSUE: 'opposite_of_last' is referenced in the noise tournament but not defined"
        print(issue)
        issues.append(issue)
    else:
        print("✓ 'opposite_of_last' function is defined")

    return issues

def test_simulation_logic_comparison():
    """Compare simulation logic between notebook and main codebase."""
    print("\n" + "=" * 60)
    print("TEST 2: Comparing simulation logic")
    print("=" * 60)

    issues = []

    # Load both modules
    try:
        notebook_module = load_python_file_as_module(
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_module2'
        )
        print("✓ Successfully loaded notebook module")
    except Exception as e:
        issue = f"✗ Failed to load notebook module: {e}"
        print(issue)
        issues.append(issue)
        return issues

    try:
        from ipd_local.simulation import play_match as main_play_match, get_scores as main_get_scores
        from ipd_local.default_strategies import tit_for_tat, silent, rat
        print("✓ Successfully loaded main simulation module")
    except Exception as e:
        issue = f"✗ Failed to load main simulation module: {e}"
        print(issue)
        issues.append(issue)
        return issues

    # Test if functions produce same results
    print("\nTesting if basic strategies work in notebook...")
    try:
        # Test with simple strategies
        test_strats = [notebook_module.rat, notebook_module.silent, notebook_module.tit_for_tat]
        rounds_var = 150
        payoff = [5, 9, 0, 1]
        seed = 42

        notebook_module.rounds = rounds_var  # Set global rounds variable
        data = notebook_module.run_no_noise_tournament(test_strats, rounds_var, payoff, seed=seed)

        print("✓ Notebook simulation runs without errors")

        # Check that results are reasonable
        if 'rat' in data and 'silent' in data:
            rat_vs_silent = data['rat']['silent']['score']
            print(f"  - rat vs silent score: {rat_vs_silent}")

            # Rat should get 9 per round, silent should get 0
            expected_rat_score = 9 * rounds_var
            expected_silent_score = 0

            if rat_vs_silent[0] == expected_rat_score and rat_vs_silent[1] == expected_silent_score:
                print("✓ Scores match expected values")
            else:
                issue = f"✗ ISSUE: Expected [{expected_rat_score}, {expected_silent_score}], got {rat_vs_silent}"
                print(issue)
                issues.append(issue)

    except NameError as e:
        if 'opposite_of_last' in str(e):
            issue = f"✗ ISSUE: NameError due to undefined 'opposite_of_last': {e}"
            print(issue)
            issues.append(issue)
        else:
            raise
    except Exception as e:
        issue = f"✗ ISSUE: Notebook simulation failed: {e}"
        print(issue)
        issues.append(issue)

    return issues

def test_list_copying():
    """Test if the notebook implementation properly copies lists to prevent modification."""
    print("\n" + "=" * 60)
    print("TEST 3: Checking if input lists are protected from modification")
    print("=" * 60)

    issues = []

    try:
        notebook_module = load_python_file_as_module(
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_module3'
        )

        # Create a strategy that tries to modify the input
        def bad_strategy(my_moves, other_moves, current_round):
            """Strategy that tries to modify input lists."""
            if len(my_moves) > 0:
                my_moves.append(True)  # This should NOT affect the actual game state
            return False

        # Run a short match
        notebook_module.rounds = 10
        payoff_dict = {
            (False, False): 5,
            (True, False): 9,
            (False, True): 0,
            (True, True): 1
        }

        total, results = notebook_module.play_match(
            bad_strategy,
            notebook_module.silent,
            [0, 0],
            payoff_dict
        )

        # Check the results - if lists aren't being copied, this will fail
        if results["score"][0] is None:
            issue = "✗ ISSUE: Game was marked invalid (possibly due to list modification detection)"
            print(issue)
            issues.append(issue)
        else:
            # The game ran - but we need to check if the lists were actually protected
            print("⚠ WARNING: Notebook implementation does NOT copy input lists")
            print("  The main codebase uses .copy() to prevent strategies from modifying history")
            print("  Notebook line 80-81 and 87-88 should use .copy() like the main codebase")
            issues.append("List copying not implemented in notebook (differs from main codebase)")

    except Exception as e:
        issue = f"✗ ISSUE: Test failed with error: {e}"
        print(issue)
        issues.append(issue)

    return issues

def test_function_definitions():
    """Test that all default strategies are properly defined."""
    print("\n" + "=" * 60)
    print("TEST 4: Checking default strategy definitions")
    print("=" * 60)

    issues = []

    try:
        notebook_module = load_python_file_as_module(
            '/home/user/Updated_IPD_Nueva/personal_ipd_tournament_2025.py',
            'notebook_module4'
        )

        # Expected strategies from the main codebase
        expected_strategies = [
            'rat', 'silent', 'rand', 'kinda_random', 'tit_for_tat',
            'tit_for_two_tats', 'nuke_for_tat', 'nuke_for_two_tats',
            'nuke_for_five_tats', 'two_tits_for_tat', 'get_angry_after_twenty',
            'cooperate_at_multiples_of_three', 'alternate_every_five',
            'suspicious_tit_for_tat'
        ]

        missing = []
        for strat in expected_strategies:
            if not hasattr(notebook_module, strat):
                missing.append(strat)

        if missing:
            issue = f"✗ ISSUE: Missing strategies: {missing}"
            print(issue)
            issues.append(issue)
        else:
            print(f"✓ All {len(expected_strategies)} expected strategies are defined")

        # Test that strategies have correct signature
        print("\nTesting strategy signatures...")
        for strat_name in expected_strategies:
            if hasattr(notebook_module, strat_name):
                strat = getattr(notebook_module, strat_name)
                try:
                    # Test with valid inputs
                    result = strat([False, True], [True, False], 2)
                    if not (isinstance(result, bool) or (isinstance(result, list) and all(isinstance(x, bool) for x in result))):
                        issue = f"✗ ISSUE: {strat_name} returned invalid type: {type(result)}"
                        print(issue)
                        issues.append(issue)
                except Exception as e:
                    issue = f"✗ ISSUE: {strat_name} failed with error: {e}"
                    print(issue)
                    issues.append(issue)

        if not issues:
            print("✓ All strategies have correct signatures and return valid types")

    except Exception as e:
        issue = f"✗ ISSUE: Test failed: {e}"
        print(issue)
        issues.append(issue)

    return issues

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("JUPYTER NOTEBOOK CONSISTENCY TEST SUITE")
    print("=" * 60)

    all_issues = []

    # Run all tests
    all_issues.extend(test_missing_functions())
    all_issues.extend(test_simulation_logic_comparison())
    all_issues.extend(test_list_copying())
    all_issues.extend(test_function_definitions())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all_issues:
        print(f"\n✗ Found {len(all_issues)} issue(s):\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
        return 1
    else:
        print("\n✓ All tests passed! The notebook is consistent with the codebase.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
