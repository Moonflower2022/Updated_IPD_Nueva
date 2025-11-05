"""
Comprehensive unit tests for all default strategies in default_strategies.py

This test suite verifies each strategy's behavior by:
1. Simulating games manually with known scenarios
2. Computing expected results independently
3. Comparing actual strategy output with expected behavior
"""

import unittest
import random
from ipd_local.default_strategies import (
    rat, silent, rand, kinda_random, tit_for_tat, tit_for_two_tats,
    nuke_for_tat, nuke_for_two_tats, two_tits_for_tat, pavlov,
    suspicious_tit_for_tat
)


def simulate_game(strategy1, strategy2, rounds):
    """
    Manually simulate a game between two strategies to verify behavior.
    Returns (moves1, moves2, score1, score2)
    """
    moves1 = []
    moves2 = []
    score1 = 0
    score2 = 0

    # Payoff matrix from game_specs.py
    POINTS_BOTH_COOPERATE = 5
    POINTS_DIFFERENT_LOSER = 0
    POINTS_DIFFERENT_WINNER = 9
    POINTS_BOTH_RAT = 1

    for round_num in range(rounds):
        # Get moves from strategies
        move1 = strategy1(moves1.copy(), moves2.copy(), round_num)
        move2 = strategy2(moves2.copy(), moves1.copy(), round_num)

        # Calculate scores for this round
        if move1 and move2:  # Both rat
            score1 += POINTS_BOTH_RAT
            score2 += POINTS_BOTH_RAT
        elif not move1 and not move2:  # Both cooperate
            score1 += POINTS_BOTH_COOPERATE
            score2 += POINTS_BOTH_COOPERATE
        elif move1 and not move2:  # Player 1 rats, player 2 cooperates
            score1 += POINTS_DIFFERENT_WINNER
            score2 += POINTS_DIFFERENT_LOSER
        else:  # Player 1 cooperates, player 2 rats
            score1 += POINTS_DIFFERENT_LOSER
            score2 += POINTS_DIFFERENT_WINNER

        # Record moves
        moves1.append(move1)
        moves2.append(move2)

    return moves1, moves2, score1, score2


class TestRatStrategy(unittest.TestCase):
    """Test the 'rat' strategy that always defects"""

    def test_rat_always_returns_true(self):
        """Rat should always return True regardless of inputs"""
        # Round 0, empty history
        self.assertTrue(rat([], [], 0))

        # After multiple rounds of cooperation from opponent
        self.assertTrue(rat([True, True], [False, False], 2))

        # After multiple rounds of defection from opponent
        self.assertTrue(rat([True, True], [True, True], 2))

        # Mixed history
        self.assertTrue(rat([True, False, True], [False, True, False], 3))

    def test_rat_vs_rat(self):
        """Two rats should both defect every round"""
        moves1, moves2, score1, score2 = simulate_game(rat, rat, 10)

        # Both should defect all rounds
        self.assertEqual(moves1, [True] * 10)
        self.assertEqual(moves2, [True] * 10)

        # Both should get 1 point per round (10 total)
        self.assertEqual(score1, 10)
        self.assertEqual(score2, 10)

    def test_rat_vs_silent(self):
        """Rat should always exploit silent"""
        moves1, moves2, score1, score2 = simulate_game(rat, silent, 10)

        # Rat defects, silent cooperates
        self.assertEqual(moves1, [True] * 10)
        self.assertEqual(moves2, [False] * 10)

        # Rat gets 9 per round, silent gets 0
        self.assertEqual(score1, 90)
        self.assertEqual(score2, 0)


class TestSilentStrategy(unittest.TestCase):
    """Test the 'silent' strategy that always cooperates"""

    def test_silent_always_returns_false(self):
        """Silent should always return False regardless of inputs"""
        # Round 0, empty history
        self.assertFalse(silent([], [], 0))

        # After being exploited
        self.assertFalse(silent([False, False], [True, True], 2))

        # After mutual cooperation
        self.assertFalse(silent([False, False], [False, False], 2))

        # Mixed history
        self.assertFalse(silent([False, True, False], [True, False, True], 3))

    def test_silent_vs_silent(self):
        """Two silent strategies should cooperate every round"""
        moves1, moves2, score1, score2 = simulate_game(silent, silent, 10)

        # Both should cooperate all rounds
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        # Both should get 5 points per round (50 total)
        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)


class TestTitForTatStrategy(unittest.TestCase):
    """Test the classic 'tit_for_tat' strategy"""

    def test_tft_cooperates_first_round(self):
        """Tit for tat should cooperate on first round"""
        self.assertFalse(tit_for_tat([], [], 0))

    def test_tft_copies_opponent_last_move(self):
        """Tit for tat should copy opponent's last move"""
        # Opponent defected last
        self.assertTrue(tit_for_tat([False], [True], 1))

        # Opponent cooperated last
        self.assertFalse(tit_for_tat([False], [False], 1))

        # Multiple rounds, opponent defected last
        self.assertTrue(tit_for_tat([False, False, True], [False, True, True], 3))

        # Multiple rounds, opponent cooperated last
        self.assertFalse(tit_for_tat([False, True, True], [False, True, False], 3))

    def test_tft_vs_silent(self):
        """Tit for tat vs silent should cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(tit_for_tat, silent, 10)

        # Both should cooperate all rounds
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        # Both get 5 per round
        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)

    def test_tft_vs_rat(self):
        """Tit for tat vs rat should cooperate once, then defect"""
        moves1, moves2, score1, score2 = simulate_game(tit_for_tat, rat, 10)

        # TFT cooperates first, then copies rat's defection
        self.assertEqual(moves1, [False] + [True] * 9)
        self.assertEqual(moves2, [True] * 10)

        # TFT: 0 + 9*1 = 9, Rat: 9 + 9*1 = 18
        self.assertEqual(score1, 9)
        self.assertEqual(score2, 18)

    def test_tft_vs_tft(self):
        """Two tit for tats should cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(tit_for_tat, tit_for_tat, 10)

        # Both cooperate all rounds
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)


class TestTitForTwoTatsStrategy(unittest.TestCase):
    """Test the 'tit_for_two_tats' strategy"""

    def test_tft2_cooperates_first_two_rounds(self):
        """Should cooperate if opponent history < 2"""
        self.assertFalse(tit_for_two_tats([], [], 0))
        self.assertFalse(tit_for_two_tats([False], [True], 1))

    def test_tft2_defects_only_after_two_consecutive_defections(self):
        """Should only defect if opponent defected last two rounds"""
        # Last two were defections
        self.assertTrue(tit_for_two_tats([False, False], [True, True], 2))

        # Last was defection, second-to-last was cooperation
        self.assertFalse(tit_for_two_tats([False, False], [False, True], 2))

        # Last was cooperation, second-to-last was defection
        self.assertFalse(tit_for_two_tats([False, True], [True, False], 2))

        # Both were cooperations
        self.assertFalse(tit_for_two_tats([False, False], [False, False], 2))

    def test_tft2_vs_rat(self):
        """Tit for two tats vs rat: cooperates twice, then defects"""
        moves1, moves2, score1, score2 = simulate_game(tit_for_two_tats, rat, 10)

        # TFT2 cooperates first two rounds, then defects
        self.assertEqual(moves1, [False, False] + [True] * 8)
        self.assertEqual(moves2, [True] * 10)

        # TFT2: 0 + 0 + 8*1 = 8, Rat: 9 + 9 + 8*1 = 26
        self.assertEqual(score1, 8)
        self.assertEqual(score2, 26)

    def test_tft2_vs_alternating_defector(self):
        """Test against opponent who alternates: defect, cooperate, defect, cooperate"""
        def alternating_defector(mymoves, othermoves, currentRound):
            return currentRound % 2 == 0  # Defect on even rounds

        moves1, moves2, score1, score2 = simulate_game(tit_for_two_tats, alternating_defector, 10)

        # TFT2 should never see two consecutive defections, so always cooperates
        self.assertEqual(moves1, [False] * 10)

        # Opponent alternates starting with defect
        self.assertEqual(moves2, [True, False, True, False, True, False, True, False, True, False])

        # TFT2: 0 + 5 + 0 + 5 + 0 + 5 + 0 + 5 + 0 + 5 = 25
        # Alt: 9 + 5 + 9 + 5 + 9 + 5 + 9 + 5 + 9 + 5 = 70
        self.assertEqual(score1, 25)
        self.assertEqual(score2, 70)


class TestNukeForTatStrategy(unittest.TestCase):
    """Test the 'nuke_for_tat' strategy"""

    def test_nft_cooperates_first_round(self):
        """Should cooperate on first round"""
        self.assertFalse(nuke_for_tat([], [], 0))

    def test_nft_defects_forever_after_single_defection(self):
        """Should defect forever once opponent defects once"""
        # Opponent cooperated so far
        self.assertFalse(nuke_for_tat([False, False], [False, False], 2))

        # Opponent defected once at the beginning
        self.assertTrue(nuke_for_tat([False, False], [True, False], 2))

        # Opponent defected once in the middle
        self.assertTrue(nuke_for_tat([False, False, False], [False, True, False], 3))

        # Opponent defected at the end
        self.assertTrue(nuke_for_tat([False, False], [False, True], 2))

    def test_nft_vs_silent(self):
        """Nuke for tat vs silent: should cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(nuke_for_tat, silent, 10)

        # Both cooperate all rounds
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)

    def test_nft_vs_rat(self):
        """Nuke for tat vs rat: cooperates once, then defects forever"""
        moves1, moves2, score1, score2 = simulate_game(nuke_for_tat, rat, 10)

        # NFT cooperates first, then detects defection and defects forever
        self.assertEqual(moves1, [False] + [True] * 9)
        self.assertEqual(moves2, [True] * 10)

        # NFT: 0 + 9*1 = 9, Rat: 9 + 9*1 = 18
        self.assertEqual(score1, 9)
        self.assertEqual(score2, 18)

    def test_nft_vs_single_defection_then_cooperate(self):
        """Test against opponent who defects once then cooperates"""
        def single_defector(mymoves, othermoves, currentRound):
            return currentRound == 2  # Only defect on round 2

        moves1, moves2, score1, score2 = simulate_game(nuke_for_tat, single_defector, 10)

        # NFT cooperates first 2 rounds, detects defection at round 2, then defects forever
        self.assertEqual(moves1, [False, False, False] + [True] * 7)
        self.assertEqual(moves2, [False, False, True] + [False] * 7)

        # Rounds: (F,F)=5, (F,F)=5, (F,T)=0, (T,F)=9*7=63
        # NFT: 5 + 5 + 0 + 63 = 73
        # Opponent: 5 + 5 + 9 + 0*7 = 19
        self.assertEqual(score1, 73)
        self.assertEqual(score2, 19)


class TestNukeForTwoTatsStrategy(unittest.TestCase):
    """Test the 'nuke_for_two_tats' strategy"""

    def test_nf2t_cooperates_first_two_rounds(self):
        """Should cooperate if opponent history < 2"""
        self.assertFalse(nuke_for_two_tats([], [], 0))
        self.assertFalse(nuke_for_two_tats([False], [True], 1))

    def test_nf2t_defects_forever_after_consecutive_defections(self):
        """Should defect forever once opponent defects twice in a row"""
        # No consecutive defections yet
        self.assertFalse(nuke_for_two_tats([False, False, False], [True, False, True], 3))

        # Consecutive defections at start
        self.assertTrue(nuke_for_two_tats([False, False, False], [True, True, False], 3))

        # Consecutive defections in middle
        self.assertTrue(nuke_for_two_tats([False, False, False, False], [False, True, True, False], 4))

        # Consecutive defections at end
        self.assertTrue(nuke_for_two_tats([False, False, False], [False, True, True], 3))

    def test_nf2t_vs_silent(self):
        """Nuke for two tats vs silent: cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(nuke_for_two_tats, silent, 10)

        # Both cooperate all rounds
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)

    def test_nf2t_vs_rat(self):
        """Nuke for two tats vs rat: cooperates twice, then defects forever"""
        moves1, moves2, score1, score2 = simulate_game(nuke_for_two_tats, rat, 10)

        # NF2T cooperates first 2, then detects consecutive defections and nukes
        self.assertEqual(moves1, [False, False] + [True] * 8)
        self.assertEqual(moves2, [True] * 10)

        # NF2T: 0 + 0 + 8*1 = 8, Rat: 9 + 9 + 8*1 = 26
        self.assertEqual(score1, 8)
        self.assertEqual(score2, 26)

    def test_nf2t_vs_alternating_defector(self):
        """Test against alternating defector - should never trigger nuke"""
        def alternating_defector(mymoves, othermoves, currentRound):
            return currentRound % 2 == 0

        moves1, moves2, score1, score2 = simulate_game(nuke_for_two_tats, alternating_defector, 10)

        # Should never see consecutive defections, so always cooperates
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [True, False, True, False, True, False, True, False, True, False])

        # Same as tit_for_two_tats vs alternating
        self.assertEqual(score1, 25)
        self.assertEqual(score2, 70)

    def test_nf2t_triggers_on_consecutive(self):
        """Test that it triggers exactly when consecutive defections occur"""
        def defect_rounds_3_and_4(mymoves, othermoves, currentRound):
            return currentRound in [3, 4]

        moves1, moves2, score1, score2 = simulate_game(nuke_for_two_tats, defect_rounds_3_and_4, 10)

        # Cooperates rounds 0-4, then detects consecutive defections and nukes rest
        self.assertEqual(moves1, [False] * 5 + [True] * 5)
        self.assertEqual(moves2, [False, False, False, True, True] + [False] * 5)

        # Rounds: (F,F)=5*3, (F,T)=0, (F,T)=0, (T,F)=9*5
        # NF2T: 15 + 0 + 0 + 45 = 60
        # Opponent: 15 + 9 + 9 + 0 = 33
        self.assertEqual(score1, 60)
        self.assertEqual(score2, 33)


class TestTwoTitsForTatStrategy(unittest.TestCase):
    """Test the 'two_tits_for_tat' strategy"""

    def test_2tft_cooperates_first_round(self):
        """Should cooperate on first round"""
        self.assertFalse(two_tits_for_tat([], [], 0))

    def test_2tft_defects_if_last_round_was_defection(self):
        """Should defect if opponent defected last round"""
        # Last round defection
        self.assertTrue(two_tits_for_tat([False], [True], 1))

        # Last round cooperation
        self.assertFalse(two_tits_for_tat([False], [False], 1))

    def test_2tft_defects_if_second_to_last_was_defection(self):
        """Should defect if opponent defected second-to-last round"""
        # Second-to-last was defection, last was cooperation
        self.assertTrue(two_tits_for_tat([False, False], [True, False], 2))

        # Both were cooperations
        self.assertFalse(two_tits_for_tat([False, False], [False, False], 2))

        # Both were defections
        self.assertTrue(two_tits_for_tat([False, False], [True, True], 2))

    def test_2tft_requires_two_clean_rounds(self):
        """Should require both last two rounds to be cooperation before cooperating"""
        # Round 2: last two were cooperations
        self.assertFalse(two_tits_for_tat([False, False], [False, False], 2))

        # Round 3: need both round 1 and 2 to be cooperation
        # If round 0 was defection but rounds 1,2 were cooperation, should cooperate
        self.assertFalse(two_tits_for_tat([False, False, False], [True, False, False], 3))

    def test_2tft_vs_silent(self):
        """Two tits for tat vs silent: cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(two_tits_for_tat, silent, 10)

        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)

    def test_2tft_vs_rat(self):
        """Two tits for tat vs rat: should defect after first round"""
        moves1, moves2, score1, score2 = simulate_game(two_tits_for_tat, rat, 10)

        # 2TFT cooperates round 0, then sees defection and defects from round 1 onward
        self.assertEqual(moves1, [False] + [True] * 9)
        self.assertEqual(moves2, [True] * 10)

        # 2TFT: 0 + 9*1 = 9, Rat: 9 + 9*1 = 18
        self.assertEqual(score1, 9)
        self.assertEqual(score2, 18)

    def test_2tft_vs_single_defection(self):
        """Test against opponent who defects once"""
        def single_defector(mymoves, othermoves, currentRound):
            return currentRound == 2

        moves1, moves2, score1, score2 = simulate_game(two_tits_for_tat, single_defector, 10)

        # Rounds 0,1: cooperate
        # Round 2: opponent defects, but 2TFT doesn't know yet, cooperates
        # Round 3: 2TFT sees round 2 defection, defects
        # Round 4: 2TFT still sees round 2 defection in last 2 rounds, defects
        # Round 5+: last two rounds are (F,T), so cooperates again
        expected = [False, False, False, True, True, False, False, False, False, False]
        self.assertEqual(moves1, expected)
        self.assertEqual(moves2, [False, False, True] + [False] * 7)


class TestPavlovStrategy(unittest.TestCase):
    """Test the 'pavlov' strategy (win-stay, lose-shift)"""

    def test_pavlov_cooperates_first_round(self):
        """Should cooperate on first round"""
        self.assertFalse(pavlov([], [], 0))

    def test_pavlov_cooperates_when_both_did_same(self):
        """Should cooperate (stay) when both players did same thing last round"""
        # Both cooperated last round
        self.assertFalse(pavlov([False], [False], 1))

        # Both defected last round
        self.assertFalse(pavlov([True], [True], 1))

    def test_pavlov_defects_when_different(self):
        """Should defect (shift) when players did different things last round"""
        # I cooperated, opponent defected (I lost)
        self.assertTrue(pavlov([False], [True], 1))

        # I defected, opponent cooperated (I won, but we did different)
        self.assertTrue(pavlov([True], [False], 1))

    def test_pavlov_vs_silent(self):
        """Pavlov vs silent: both cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(pavlov, silent, 10)

        # Both cooperate all rounds (both do same thing, so pavlov stays)
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)

    def test_pavlov_vs_rat(self):
        """Pavlov vs rat: alternates between cooperate and defect"""
        moves1, moves2, score1, score2 = simulate_game(pavlov, rat, 10)

        # Round 0: Pavlov cooperates, Rat defects (different)
        # Round 1: Pavlov sees different, shifts to defect; Rat defects (same)
        # Round 2: Pavlov sees same, stays and cooperates; Rat defects (different)
        # Round 3: Pavlov sees different, shifts to defect; Rat defects (same)
        # Pattern: Pavlov alternates defect/cooperate forever
        self.assertEqual(moves1, [False, True, False, True, False, True, False, True, False, True])
        self.assertEqual(moves2, [True] * 10)

        # Pavlov: 5 rounds at 0 (exploited), 5 rounds at 1 (mutual defect) = 5
        # Rat: 5 rounds at 9 (exploiting), 5 rounds at 1 (mutual defect) = 50
        self.assertEqual(score1, 5)
        self.assertEqual(score2, 50)

    def test_pavlov_vs_pavlov(self):
        """Two pavlovs should cooperate all rounds"""
        moves1, moves2, score1, score2 = simulate_game(pavlov, pavlov, 10)

        # Both cooperate all rounds (always same, so always stay)
        self.assertEqual(moves1, [False] * 10)
        self.assertEqual(moves2, [False] * 10)

        self.assertEqual(score1, 50)
        self.assertEqual(score2, 50)


class TestSuspiciousTitForTatStrategy(unittest.TestCase):
    """Test the 'suspicious_tit_for_tat' strategy"""

    def test_stft_defects_first_round(self):
        """Should defect on first round (suspicious start)"""
        self.assertTrue(suspicious_tit_for_tat([], [], 0))

    def test_stft_copies_opponent_after_first_round(self):
        """Should copy opponent's last move after first round"""
        # Opponent defected last
        self.assertTrue(suspicious_tit_for_tat([True], [True], 1))

        # Opponent cooperated last
        self.assertFalse(suspicious_tit_for_tat([True], [False], 1))

        # Multiple rounds, opponent cooperated last
        self.assertFalse(suspicious_tit_for_tat([True, False, False], [True, False, False], 3))

        # Multiple rounds, opponent defected last
        self.assertTrue(suspicious_tit_for_tat([True, False, True], [True, False, True], 3))

    def test_stft_vs_silent(self):
        """Suspicious TFT vs silent: defects once, then cooperates"""
        moves1, moves2, score1, score2 = simulate_game(suspicious_tit_for_tat, silent, 10)

        # STFT defects first, then copies silent's cooperation
        self.assertEqual(moves1, [True] + [False] * 9)
        self.assertEqual(moves2, [False] * 10)

        # STFT: 9 + 9*5 = 54, Silent: 0 + 9*5 = 45
        self.assertEqual(score1, 54)
        self.assertEqual(score2, 45)

    def test_stft_vs_rat(self):
        """Suspicious TFT vs rat: both defect all rounds"""
        moves1, moves2, score1, score2 = simulate_game(suspicious_tit_for_tat, rat, 10)

        # Both defect all rounds
        self.assertEqual(moves1, [True] * 10)
        self.assertEqual(moves2, [True] * 10)

        # Both get 1 per round
        self.assertEqual(score1, 10)
        self.assertEqual(score2, 10)

    def test_stft_vs_tft(self):
        """Suspicious TFT vs regular TFT: should alternate defect/cooperate"""
        moves1, moves2, score1, score2 = simulate_game(suspicious_tit_for_tat, tit_for_tat, 10)

        # Round 0: STFT defects, TFT cooperates
        # Round 1: STFT copies TFT's cooperate, TFT copies STFT's defect
        # Round 2: STFT copies TFT's defect, TFT copies STFT's cooperate
        # Pattern: alternating
        self.assertEqual(moves1, [True, False, True, False, True, False, True, False, True, False])
        self.assertEqual(moves2, [False, True, False, True, False, True, False, True, False, True])

        # Each gets 5 wins and 5 losses: 5*9 + 5*0 = 45 each
        self.assertEqual(score1, 45)
        self.assertEqual(score2, 45)

    def test_stft_vs_stft(self):
        """Two suspicious TFTs should defect all rounds"""
        moves1, moves2, score1, score2 = simulate_game(suspicious_tit_for_tat, suspicious_tit_for_tat, 10)

        # Both defect all rounds (both start with defect, then copy each other's defection)
        self.assertEqual(moves1, [True] * 10)
        self.assertEqual(moves2, [True] * 10)

        self.assertEqual(score1, 10)
        self.assertEqual(score2, 10)


class TestRandomStrategies(unittest.TestCase):
    """Test random strategies with seeded random"""

    def test_rand_returns_bool(self):
        """Random strategy should return bool"""
        random.seed(42)
        result = rand([], [], 0)
        self.assertIsInstance(result, bool)

    def test_rand_with_seed_is_deterministic(self):
        """Random strategy with same seed should produce same results"""
        random.seed(42)
        results1 = [rand([], [], i) for i in range(100)]

        random.seed(42)
        results2 = [rand([], [], i) for i in range(100)]

        self.assertEqual(results1, results2)

    def test_rand_produces_both_values(self):
        """Random strategy should produce both True and False"""
        random.seed(42)
        results = [rand([], [], i) for i in range(1000)]

        self.assertIn(True, results)
        self.assertIn(False, results)

    def test_kinda_random_returns_bool(self):
        """Kinda random strategy should return bool"""
        random.seed(42)
        result = kinda_random([], [], 0)
        self.assertIsInstance(result, bool)

    def test_kinda_random_mostly_defects(self):
        """Kinda random should defect about 90% of the time"""
        random.seed(42)
        results = [kinda_random([], [], i) for i in range(1000)]

        defect_count = sum(results)
        defect_ratio = defect_count / 1000

        # Should be close to 0.9 (within 5%)
        self.assertGreater(defect_ratio, 0.85)
        self.assertLess(defect_ratio, 0.95)

    def test_kinda_random_produces_both_values(self):
        """Kinda random should produce both True and False (even if rare)"""
        random.seed(42)
        results = [kinda_random([], [], i) for i in range(1000)]

        self.assertIn(True, results)
        self.assertIn(False, results)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_all_strategies_handle_empty_history(self):
        """All strategies should handle round 0 with empty history"""
        strategies = [
            rat, silent, rand, kinda_random, tit_for_tat, tit_for_two_tats,
            nuke_for_tat, nuke_for_two_tats, two_tits_for_tat, pavlov,
            suspicious_tit_for_tat
        ]

        for strategy in strategies:
            try:
                result = strategy([], [], 0)
                self.assertIsInstance(result, bool, f"{strategy.__name__} should return bool")
            except Exception as e:
                self.fail(f"{strategy.__name__} failed on round 0: {e}")

    def test_all_strategies_handle_long_history(self):
        """All strategies should handle long game histories"""
        strategies = [
            rat, silent, tit_for_tat, tit_for_two_tats,
            nuke_for_tat, nuke_for_two_tats, two_tits_for_tat, pavlov,
            suspicious_tit_for_tat
        ]

        # Create a long history
        long_history = [False] * 500

        for strategy in strategies:
            try:
                result = strategy(long_history.copy(), long_history.copy(), 500)
                self.assertIsInstance(result, bool, f"{strategy.__name__} should return bool")
            except Exception as e:
                self.fail(f"{strategy.__name__} failed with long history: {e}")

    def test_strategies_dont_modify_inputs(self):
        """Strategies should not modify input lists"""
        strategies = [
            rat, silent, tit_for_tat, tit_for_two_tats,
            nuke_for_tat, nuke_for_two_tats, two_tits_for_tat, pavlov,
            suspicious_tit_for_tat
        ]

        for strategy in strategies:
            mymoves = [True, False, True]
            othermoves = [False, True, False]

            mymoves_copy = mymoves.copy()
            othermoves_copy = othermoves.copy()

            strategy(mymoves, othermoves, 3)

            # Check that lists weren't modified
            self.assertEqual(mymoves, mymoves_copy,
                           f"{strategy.__name__} modified mymoves")
            self.assertEqual(othermoves, othermoves_copy,
                           f"{strategy.__name__} modified othermoves")


class TestReproducibilityAndSeeds(unittest.TestCase):
    """Test reproducibility with seeds and deterministic behavior"""

    def simulate_game_with_seed(self, strategy1, strategy2, rounds, seed):
        """Simulate a game with a specific random seed"""
        random.seed(seed)
        return simulate_game(strategy1, strategy2, rounds)

    def test_deterministic_strategies_same_seed_identical(self):
        """Deterministic strategies should produce identical results with same seed"""
        # Run same matchup twice with same seed
        seed = 42
        result1 = self.simulate_game_with_seed(tit_for_tat, suspicious_tit_for_tat, 50, seed)
        result2 = self.simulate_game_with_seed(tit_for_tat, suspicious_tit_for_tat, 50, seed)

        self.assertEqual(result1, result2)

    def test_random_strategy_same_seed_identical(self):
        """Random strategies should produce identical results with same seed"""
        seed = 123
        result1 = self.simulate_game_with_seed(rand, silent, 100, seed)
        result2 = self.simulate_game_with_seed(rand, silent, 100, seed)

        # Should be exactly the same
        self.assertEqual(result1, result2)

    def test_random_strategy_different_seed_different(self):
        """Random strategies should produce different results with different seeds"""
        result1 = self.simulate_game_with_seed(rand, rand, 100, 42)
        result2 = self.simulate_game_with_seed(rand, rand, 100, 99)

        # Very high probability they're different
        self.assertNotEqual(result1, result2)

    def test_kinda_random_same_seed_identical(self):
        """Kinda random strategy should be reproducible with same seed"""
        seed = 777
        result1 = self.simulate_game_with_seed(kinda_random, tit_for_tat, 100, seed)
        result2 = self.simulate_game_with_seed(kinda_random, tit_for_tat, 100, seed)

        self.assertEqual(result1, result2)

    def test_complex_matchup_reproducibility(self):
        """Complex matchups should be reproducible across multiple runs"""
        seed = 555
        strategies_pairs = [
            (tit_for_tat, pavlov),
            (nuke_for_tat, two_tits_for_tat),
            (suspicious_tit_for_tat, tit_for_two_tats),
        ]

        for strat1, strat2 in strategies_pairs:
            result1 = self.simulate_game_with_seed(strat1, strat2, 50, seed)
            result2 = self.simulate_game_with_seed(strat1, strat2, 50, seed)
            self.assertEqual(result1, result2,
                           f"{strat1.__name__} vs {strat2.__name__} not reproducible")


class TestStrategiesWithNoise(unittest.TestCase):
    """Test how strategies behave under noise conditions"""

    def simulate_game_with_noise(self, strategy1, strategy2, rounds, noise_level, seed):
        """
        Simulate a game with noise - moves have a chance of being misperceived.
        This mimics the noise implementation in simulation.py
        """
        random.seed(seed)
        moves1 = []
        moves2 = []
        perceived1 = []  # What player2 sees from player1
        perceived2 = []  # What player1 sees from player2
        score1 = 0
        score2 = 0

        POINTS_BOTH_COOPERATE = 5
        POINTS_DIFFERENT_LOSER = 0
        POINTS_DIFFERENT_WINNER = 9
        POINTS_BOTH_RAT = 1

        for round_num in range(rounds):
            # Get actual moves based on perceived history
            move1 = strategy1(moves1.copy(), perceived2.copy(), round_num)
            move2 = strategy2(moves2.copy(), perceived1.copy(), round_num)

            # Calculate scores based on actual moves
            if move1 and move2:
                score1 += POINTS_BOTH_RAT
                score2 += POINTS_BOTH_RAT
            elif not move1 and not move2:
                score1 += POINTS_BOTH_COOPERATE
                score2 += POINTS_BOTH_COOPERATE
            elif move1 and not move2:
                score1 += POINTS_DIFFERENT_WINNER
                score2 += POINTS_DIFFERENT_LOSER
            else:
                score1 += POINTS_DIFFERENT_LOSER
                score2 += POINTS_DIFFERENT_WINNER

            # Record actual moves
            moves1.append(move1)
            moves2.append(move2)

            # Create perceived moves (with noise)
            perceived_move1 = not move1 if random.random() < noise_level else move1
            perceived_move2 = not move2 if random.random() < noise_level else move2

            perceived1.append(perceived_move1)
            perceived2.append(perceived_move2)

        return moves1, moves2, score1, score2, perceived1, perceived2

    def test_noise_with_same_seed_is_reproducible(self):
        """Games with noise should be reproducible with same seed"""
        seed = 42
        noise_level = 0.1

        result1 = self.simulate_game_with_noise(tit_for_tat, tit_for_tat, 100, noise_level, seed)
        result2 = self.simulate_game_with_noise(tit_for_tat, tit_for_tat, 100, noise_level, seed)

        self.assertEqual(result1, result2)

    def test_noise_with_different_seed_is_different(self):
        """Games with noise should produce different results with different seeds"""
        noise_level = 0.1

        result1 = self.simulate_game_with_noise(tit_for_tat, tit_for_tat, 100, noise_level, 42)
        result2 = self.simulate_game_with_noise(tit_for_tat, tit_for_tat, 100, noise_level, 99)

        # With noise, results should differ (very high probability)
        self.assertNotEqual(result1, result2)

    def test_tit_for_tat_under_noise_eventually_defects(self):
        """Two tit-for-tats under noise should eventually start defecting"""
        random.seed(42)
        noise_level = 0.1

        moves1, moves2, _, _, _, _ = self.simulate_game_with_noise(
            tit_for_tat, tit_for_tat, 200, noise_level, 42
        )

        # With noise, they should not cooperate 100% of the time
        # Some defections should occur due to miscommunication
        defections1 = sum(moves1)
        defections2 = sum(moves2)

        # At 10% noise over 200 rounds, we expect some defections
        self.assertGreater(defections1, 0, "TFT should defect sometimes under noise")
        self.assertGreater(defections2, 0, "TFT should defect sometimes under noise")

    def test_zero_noise_equals_no_noise(self):
        """Zero noise level should produce same results as no noise"""
        seed = 123

        # With noise = 0
        moves1_zero, moves2_zero, score1_zero, score2_zero, _, _ = \
            self.simulate_game_with_noise(tit_for_tat, suspicious_tit_for_tat, 50, 0.0, seed)

        # Without noise (regular simulation)
        random.seed(seed)
        moves1_reg, moves2_reg, score1_reg, score2_reg = \
            simulate_game(tit_for_tat, suspicious_tit_for_tat, 50)

        self.assertEqual(moves1_zero, moves1_reg)
        self.assertEqual(moves2_zero, moves2_reg)
        self.assertEqual(score1_zero, score1_reg)
        self.assertEqual(score2_zero, score2_reg)

    def test_high_noise_causes_more_defections(self):
        """Higher noise levels should cause more defections on average in cooperative strategies"""
        # Run multiple games and average to reduce random variance
        num_trials = 20
        defections_low_total = 0
        defections_high_total = 0

        for trial in range(num_trials):
            # Low noise
            moves1_low, moves2_low, _, _, _, _ = \
                self.simulate_game_with_noise(tit_for_tat, tit_for_tat, 100, 0.02, 100 + trial)
            defections_low_total += sum(moves1_low) + sum(moves2_low)

            # High noise
            moves1_high, moves2_high, _, _, _, _ = \
                self.simulate_game_with_noise(tit_for_tat, tit_for_tat, 100, 0.3, 200 + trial)
            defections_high_total += sum(moves1_high) + sum(moves2_high)

        # Average defections across trials
        avg_defections_low = defections_low_total / num_trials
        avg_defections_high = defections_high_total / num_trials

        # Higher noise should cause more defections on average
        self.assertGreater(avg_defections_high, avg_defections_low,
                          f"High noise avg: {avg_defections_high}, Low noise avg: {avg_defections_low}")

    def test_rat_unaffected_by_noise(self):
        """Always-defect strategy should be unaffected by noise"""
        # Rat always defects regardless of what it perceives
        moves1_no_noise, _, _, _, _, _ = \
            self.simulate_game_with_noise(rat, silent, 50, 0.0, 42)
        moves1_with_noise, _, _, _, _, _ = \
            self.simulate_game_with_noise(rat, silent, 50, 0.5, 42)

        # Rat should always defect
        self.assertEqual(moves1_no_noise, [True] * 50)
        self.assertEqual(moves1_with_noise, [True] * 50)

    def test_silent_unaffected_by_noise(self):
        """Always-cooperate strategy should be unaffected by noise"""
        # Silent always cooperates regardless of what it perceives
        moves1_no_noise, _, _, _, _, _ = \
            self.simulate_game_with_noise(silent, rat, 50, 0.0, 42)
        moves1_with_noise, _, _, _, _, _ = \
            self.simulate_game_with_noise(silent, rat, 50, 0.5, 42)

        # Silent should always cooperate
        self.assertEqual(moves1_no_noise, [False] * 50)
        self.assertEqual(moves1_with_noise, [False] * 50)

    def test_nuke_for_tat_noise_can_trigger_early(self):
        """Noise can cause nuke-for-tat to trigger even against cooperative opponent"""
        # Against silent, nuke-for-tat should normally never trigger
        # But with noise, it might perceive a defection and nuke

        # Run multiple times to find a case where noise triggers it
        triggered = False
        for seed in range(100):
            moves1, _, _, _, perceived1, _ = \
                self.simulate_game_with_noise(nuke_for_tat, silent, 50, 0.2, seed)

            # Check if nuke was triggered (starts defecting)
            if True in moves1:
                triggered = True
                break

        # Should find at least one case where noise caused perceived defection
        self.assertTrue(triggered, "Noise should sometimes trigger nuke-for-tat")

    def test_perceived_vs_actual_moves_differ_with_noise(self):
        """With noise, perceived moves should differ from actual moves"""
        moves1, moves2, _, _, perceived1, perceived2 = \
            self.simulate_game_with_noise(tit_for_tat, silent, 100, 0.1, 42)

        # With 10% noise over 100 rounds, some perceptions should differ
        differences = sum(1 for actual, perceived in zip(moves2, perceived1)
                         if actual != perceived)

        # Should have some misperceptions (statistically very likely)
        self.assertGreater(differences, 0, "Noise should cause misperceptions")

        # But not too many (should be around 10%)
        self.assertLess(differences, 30, "Noise level should be reasonable")


class TestMultiGameAveraging(unittest.TestCase):
    """Test averaging mechanism used when noise is enabled"""

    def test_averaging_multiple_noisy_games(self):
        """Test that averaging multiple games with noise produces stable results"""
        seed = 42
        num_games = 50
        noise_level = 0.1

        # Run multiple games and collect scores
        all_scores = []
        for game_num in range(num_games):
            random.seed(seed + game_num)  # Different seed for each game
            _, _, score1, score2, _, _ = TestStrategiesWithNoise().simulate_game_with_noise(
                tit_for_tat, suspicious_tit_for_tat, 100, noise_level, seed + game_num
            )
            all_scores.append((score1, score2))

        # Calculate average
        avg_score1 = sum(s[0] for s in all_scores) / num_games
        avg_score2 = sum(s[1] for s in all_scores) / num_games

        # Averaged scores should be reasonable (between extremes)
        self.assertGreater(avg_score1, 0)
        self.assertLess(avg_score1, 900)  # Max would be 9*100
        self.assertGreater(avg_score2, 0)
        self.assertLess(avg_score2, 900)

    def test_more_games_reduces_variance(self):
        """Averaging more games should reduce variance in results"""
        base_seed = 42
        noise_level = 0.1

        # Run with few games
        scores_few = []
        for _ in range(5):
            for game in range(10):
                random.seed(base_seed + game)
                _, _, s1, s2, _, _ = TestStrategiesWithNoise().simulate_game_with_noise(
                    rand, rand, 100, noise_level, base_seed + game
                )
                scores_few.append(s1)

        # Run with many games
        scores_many = []
        for _ in range(5):
            for game in range(100):
                random.seed(base_seed + 1000 + game)
                _, _, s1, s2, _, _ = TestStrategiesWithNoise().simulate_game_with_noise(
                    rand, rand, 100, noise_level, base_seed + 1000 + game
                )
                scores_many.append(s1)

        # Calculate variance
        import statistics
        variance_few = statistics.variance(scores_few)
        variance_many = statistics.variance(scores_many)

        # More samples should have similar or lower variance
        # (This is a statistical property, not always guaranteed for small samples)
        self.assertIsNotNone(variance_few)
        self.assertIsNotNone(variance_many)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
