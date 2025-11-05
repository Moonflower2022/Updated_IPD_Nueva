"""Unit tests for the simulation module only"""

from ipd_local.simulation import get_scores, pack_functions, unpack_functions, play_match, run_simulation
from ipd_local.utils import suppress_output

import unittest
import marshal
import random

# ========== Test Strategy Functions ==========

def cheat(my_moves, other_moves, current_round):
    """Always defects"""
    return True


def cooperate(my_moves, other_moves, current_round):
    """Always cooperates"""
    return False


def tit_for_tat(my_moves, other_moves, current_round):
    """Cooperates first, then copies opponent's last move"""
    if current_round == 0:
        return False
    return other_moves[-1]


def alternating(my_moves, other_moves, current_round):
    """Alternates between cooperate and defect"""
    return current_round % 2 == 1


def random_strategy(my_moves, other_moves, current_round):
    """Random moves"""
    return random.random() > 0.5


def grudger(my_moves, other_moves, current_round):
    """Cooperates until opponent defects, then always defects"""
    if current_round == 0:
        return False
    if True in other_moves:
        return True
    return False


def return_list_strategy(my_moves, other_moves, current_round):
    """Returns a list of bools for testing multi-round planning"""
    if current_round == 0:
        return [False, False, True, True]
    return False


def broken_strategy(my_moves, other_moves, current_round):
    """Strategy that raises an exception"""
    raise ValueError("Intentional error for testing")


def invalid_return_strategy(my_moves, other_moves, current_round):
    """Strategy that returns invalid type"""
    return "not a boolean"


def modifying_strategy(my_moves, other_moves, current_round):
    """Strategy that tries to modify input lists (should still work due to copies)"""
    if len(other_moves) > 0:
        # This should not affect the actual game state
        other_moves.append(True)
    return False


class TestGetScores(unittest.TestCase):
    """Test the get_scores function for calculating points"""

    def test_both_cooperate_all_rounds(self):
        """Test when both players always cooperate"""
        moves1 = [False] * 10
        moves2 = [False] * 10
        self.assertEqual(get_scores(moves1, moves2), (50.0, 50.0))

    def test_both_defect_all_rounds(self):
        """Test when both players always defect"""
        moves1 = [True] * 10
        moves2 = [True] * 10
        self.assertEqual(get_scores(moves1, moves2), (10.0, 10.0))

    def test_one_exploits_other(self):
        """Test when player1 always defects and player2 always cooperates"""
        moves1 = [True] * 10
        moves2 = [False] * 10
        self.assertEqual(get_scores(moves1, moves2), (90.0, 0.0))

    def test_symmetric_exploitation(self):
        """Test when player2 always defects and player1 always cooperates"""
        moves1 = [False] * 10
        moves2 = [True] * 10
        self.assertEqual(get_scores(moves1, moves2), (0.0, 90.0))

    def test_alternating_moves(self):
        """Test with alternating cooperation and defection"""
        moves1 = [False, True, False, True]
        moves2 = [True, False, True, False]
        # Round 1: p1=F, p2=T -> p1 gets 0, p2 gets 9
        # Round 2: p1=T, p2=F -> p1 gets 9, p2 gets 0
        # Round 3: p1=F, p2=T -> p1 gets 0, p2 gets 9
        # Round 4: p1=T, p2=F -> p1 gets 9, p2 gets 0
        self.assertEqual(get_scores(moves1, moves2), (18.0, 18.0))

    def test_empty_moves(self):
        """Test with empty move lists"""
        self.assertEqual(get_scores([], []), (0.0, 0.0))

    def test_single_round(self):
        """Test with a single round"""
        self.assertEqual(get_scores([True], [True]), (1.0, 1.0))
        self.assertEqual(get_scores([False], [False]), (5.0, 5.0))

    def test_custom_payoffs(self):
        """Test with custom payoff values"""
        moves1 = [False, True]
        moves2 = [False, False]
        # Custom: both_coop=10, loser=2, winner=15, both_rat=3
        # Round 1: both cooperate -> (10, 10)
        # Round 2: p1 defects -> (15, 2)
        self.assertEqual(get_scores(moves1, moves2, 10, 2, 15, 3), (25.0, 12.0))

    def test_large_number_of_rounds(self):
        """Test with many rounds for performance"""
        moves1 = [False] * 1000
        moves2 = [False] * 1000
        self.assertEqual(get_scores(moves1, moves2), (5000.0, 5000.0))


class TestPackUnpackFunctions(unittest.TestCase):
    """Test function marshaling for multiprocessing"""

    def test_pack_functions_basic(self):
        """Test basic packing of two functions"""
        packed = pack_functions((cheat, cooperate))
        self.assertEqual(packed[0][0], marshal.dumps(cheat.__code__))
        self.assertEqual(packed[0][1], "cheat")
        self.assertEqual(packed[1][0], marshal.dumps(cooperate.__code__))
        self.assertEqual(packed[1][1], "cooperate")

    def test_unpack_functions_basic(self):
        """Test basic unpacking of two functions"""
        packed = pack_functions((cheat, cooperate))
        unpacked = unpack_functions(packed)
        self.assertEqual(unpacked[0].__name__, "cheat")
        self.assertEqual(unpacked[1].__name__, "cooperate")

    def test_round_trip_simple_strategies(self):
        """Test pack -> unpack -> execute for simple strategies"""
        packed = pack_functions((cheat, cooperate))
        unpacked = unpack_functions(packed)

        # Test that unpacked functions work correctly
        self.assertEqual(unpacked[0]([], [], 0), True)  # cheat always returns True
        self.assertEqual(unpacked[1]([], [], 0), False)  # cooperate always returns False

    def test_round_trip_complex_strategy(self):
        """Test pack -> unpack -> execute for tit-for-tat"""
        packed = pack_functions((tit_for_tat, cooperate))
        unpacked = unpack_functions(packed)

        # Test tit-for-tat logic
        self.assertEqual(unpacked[0]([], [], 0), False)  # First move: cooperate
        self.assertEqual(unpacked[0]([], [True], 1), True)  # Copy opponent's defect
        self.assertEqual(unpacked[0]([], [False], 1), False)  # Copy opponent's cooperate


class TestPlayMatch(unittest.TestCase):
    """Test the play_match function for individual matches"""

    def test_play_match_no_noise_deterministic(self):
        """Test play_match without noise is deterministic"""
        result = play_match(
            pack_functions((cheat, cooperate)),
            noise=False,
            rounds=150,
            random_seed=42,
        )
        self.assertEqual(result, get_scores([True] * 150, [False] * 150))

    def test_play_match_tit_for_tat_vs_cooperate(self):
        """Test tit-for-tat against always cooperate"""
        result = play_match(
            pack_functions((tit_for_tat, cooperate)),
            noise=False,
            rounds=10,
            random_seed=42,
        )
        # Both should cooperate all rounds
        expected = get_scores([False] * 10, [False] * 10)
        self.assertEqual(result, expected)

    def test_play_match_tit_for_tat_vs_cheat(self):
        """Test tit-for-tat against always defect"""
        result = play_match(
            pack_functions((tit_for_tat, cheat)),
            noise=False,
            rounds=10,
            random_seed=42,
        )
        # Round 0: tft cooperates, cheat defects -> tft: 0, cheat: 9
        # Rounds 1-9: both defect -> tft: 9, cheat: 9
        expected_tft = [False] + [True] * 9
        expected_cheat = [True] * 10
        expected = get_scores(expected_tft, expected_cheat)
        self.assertEqual(result, expected)

    def test_play_match_with_list_return(self):
        """Test strategy that returns list of bools"""
        result = play_match(
            pack_functions((return_list_strategy, cooperate)),
            noise=False,
            rounds=10,
            random_seed=42,
        )
        # return_list_strategy returns [False, False, True, True] on round 0
        # Then False for remaining rounds
        expected_moves = [False, False, True, True] + [False] * 6
        expected = get_scores(expected_moves, [False] * 10)
        self.assertEqual(result, expected)

    def test_play_match_broken_strategy_returns_none(self):
        """Test that broken strategies return None"""
        with suppress_output():
            result = play_match(
                pack_functions((broken_strategy, cooperate)),
                noise=False,
                rounds=10,
                random_seed=42,
            )
        self.assertIsNone(result)

    def test_play_match_invalid_return_type_returns_none(self):
        """Test that strategies with invalid return types return None"""
        with suppress_output():
            result = play_match(
                pack_functions((invalid_return_strategy, cooperate)),
                noise=False,
                rounds=10,
                random_seed=42,
            )
        self.assertIsNone(result)

    def test_play_match_with_noise_same_seed_deterministic(self):
        """Test that noise with same seed produces same results"""
        result1 = play_match(
            pack_functions((cheat, cooperate)),
            noise=True,
            noise_level=0.1,
            rounds=50,
            num_noise_games_to_avg=10,
            random_seed=42,
        )
        result2 = play_match(
            pack_functions((cheat, cooperate)),
            noise=True,
            noise_level=0.1,
            rounds=50,
            num_noise_games_to_avg=10,
            random_seed=42,
        )
        self.assertEqual(result1, result2)

    def test_play_match_with_noise_different_seed(self):
        """Test that noise with different seeds produces different results"""
        result1 = play_match(
            pack_functions((random_strategy, random_strategy)),
            noise=True,
            noise_level=0.1,
            rounds=50,
            num_noise_games_to_avg=10,
            random_seed=42,
        )
        result2 = play_match(
            pack_functions((random_strategy, random_strategy)),
            noise=True,
            noise_level=0.1,
            rounds=50,
            num_noise_games_to_avg=10,
            random_seed=99,
        )
        # Results should be different (very high probability)
        self.assertNotEqual(result1, result2)

    def test_play_match_zero_noise_level(self):
        """Test with noise enabled but noise_level=0"""
        result = play_match(
            pack_functions((cheat, cooperate)),
            noise=True,
            noise_level=0.0,
            rounds=50,
            num_noise_games_to_avg=5,
            random_seed=42,
        )
        expected = get_scores([True] * 50, [False] * 50)
        self.assertEqual(result, expected)

    def test_play_match_data_isolation(self):
        """Test that strategies receive copies and can't modify game state"""
        result = play_match(
            pack_functions((modifying_strategy, cooperate)),
            noise=False,
            rounds=10,
            random_seed=42,
        )
        # Should complete successfully despite modification attempts
        expected = get_scores([False] * 10, [False] * 10)
        self.assertEqual(result, expected)


class TestRunSimulation(unittest.TestCase):
    """Test the run_simulation function for full tournaments"""

    def test_run_simulation_two_strategies(self):
        """Test basic simulation with two strategies"""
        with suppress_output():
            result = run_simulation(
                [cheat, cooperate],
                noise=False,
                rounds=10,
                random_seed=42,
            )

        self.assertEqual(result["cheat"]["cooperate"], (90.0, 0.0))
        self.assertEqual(result["cooperate"]["cheat"], (0.0, 90.0))

    def test_run_simulation_symmetry(self):
        """Test that results are symmetric: A vs B = reversed(B vs A)"""
        with suppress_output():
            result = run_simulation(
                [cheat, cooperate, tit_for_tat],
                noise=False,
                rounds=10,
                random_seed=42,
            )

        # Check symmetry for all pairs
        self.assertEqual(
            result["cheat"]["cooperate"],
            tuple(reversed(result["cooperate"]["cheat"]))
        )
        self.assertEqual(
            result["cheat"]["tit_for_tat"],
            tuple(reversed(result["tit_for_tat"]["cheat"]))
        )
        self.assertEqual(
            result["cooperate"]["tit_for_tat"],
            tuple(reversed(result["tit_for_tat"]["cooperate"]))
        )

    def test_run_simulation_all_pairs_played(self):
        """Test that all strategy pairs play exactly once"""
        strategies = [cheat, cooperate, tit_for_tat, alternating]
        with suppress_output():
            result = run_simulation(
                strategies,
                noise=False,
                rounds=10,
                random_seed=42,
            )

        # Should have 4 strategies, each with 3 opponents (4 choose 2 = 6 matchups)
        strategy_names = [s.__name__ for s in strategies]

        # Check each strategy has results against all others
        for name in strategy_names:
            self.assertIn(name, result)
            self.assertEqual(len(result[name]), len(strategy_names) - 1)

            # Check it played against all others
            for other_name in strategy_names:
                if name != other_name:
                    self.assertIn(other_name, result[name])

    def test_run_simulation_with_failing_strategy(self):
        """Test that simulation continues even if one strategy fails"""
        with suppress_output():
            result = run_simulation(
                [cheat, cooperate, broken_strategy],
                noise=False,
                rounds=10,
                random_seed=42,
            )

        # cheat vs cooperate should still have results
        self.assertIn("cheat", result)
        self.assertIn("cooperate", result["cheat"])

        # broken_strategy should not have successful matches
        # (or if it does, they should be incomplete)
        if "broken_strategy" in result:
            # Check that it has fewer matches than expected
            self.assertLess(len(result["broken_strategy"]), 2)

    def test_run_simulation_deterministic_with_seed(self):
        """Test that same seed produces same results"""
        with suppress_output():
            result1 = run_simulation(
                [cheat, cooperate, tit_for_tat],
                noise=False,
                rounds=10,
                random_seed=42,
            )
            result2 = run_simulation(
                [cheat, cooperate, tit_for_tat],
                noise=False,
                rounds=10,
                random_seed=42,
            )

        self.assertEqual(result1, result2)

    def test_run_simulation_single_strategy(self):
        """Test simulation with only one strategy (edge case)"""
        with suppress_output():
            result = run_simulation(
                [cheat],
                noise=False,
                rounds=10,
                random_seed=42,
            )

        # Should have no matchups (can't play against itself in round-robin)
        self.assertEqual(len(result.get("cheat", {})), 0)

    def test_run_simulation_complex_strategies(self):
        """Integration test with multiple complex strategies"""
        with suppress_output():
            result = run_simulation(
                [cheat, cooperate, tit_for_tat, grudger, alternating],
                noise=False,
                rounds=20,
                random_seed=42,
            )

        # All strategies should have results
        for strat_name in ["cheat", "cooperate", "tit_for_tat", "grudger", "alternating"]:
            self.assertIn(strat_name, result)
            self.assertEqual(len(result[strat_name]), 4)  # Each plays 4 others

        # Test specific expected behaviors
        # tit_for_tat vs cooperate: both should cooperate all rounds
        tft_coop_score = result["tit_for_tat"]["cooperate"]
        expected = get_scores([False] * 20, [False] * 20)
        self.assertEqual(tft_coop_score, expected)

        # grudger vs cheat: grudger cooperates once, then always defects
        grudger_cheat = result["grudger"]["cheat"]
        grudger_moves = [False] + [True] * 19
        cheat_moves = [True] * 20
        expected = get_scores(grudger_moves, cheat_moves)
        self.assertEqual(grudger_cheat, expected)


if __name__ == "__main__":
    unittest.main()
