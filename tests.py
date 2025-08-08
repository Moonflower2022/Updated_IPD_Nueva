import unittest
from ipd_local.simulation import get_scores, pack_functions, play_match, run_simulation
import marshal
from utils import suppress_output


def cheat(my_moves, other_moves, current_round):
    return True


def cooperate(my_moves, other_moves, current_round):
    return False


class TestSimulation(unittest.TestCase):
    def test_pack_functions(self):
        self.assertEqual(
            pack_functions((cheat, cooperate)),
            (
                (marshal.dumps(cheat.__code__), "cheat"),
                (marshal.dumps(cooperate.__code__), "cooperate"),
            ),
        )

    def test_get_scores(self):
        payoffs = [5, 0, 9, 1]
        self.assertEqual(
            get_scores([True, True, True], [False, False, False], *payoffs), (27.0, 0.0)
        )

    def test_play_match(self):
        self.assertEqual(
            play_match(
                pack_functions((cheat, cooperate)),
                noise=False,
                rounds=150,
                num_noise_games_to_avg=10,
            ),
            list(get_scores([True] * 150, [False] * 150)),
        )

    def test_run_simulation(self):
        with suppress_output():
            simulation_result = run_simulation(
                [cheat, cooperate],
                noise=False,
                rounds=10,
                num_noise_games_to_avg=50,
            )

        self.assertEqual(simulation_result["cheat"]["cooperate"], [90.0, 0.0])


if __name__ == "__main__":
    unittest.main()
