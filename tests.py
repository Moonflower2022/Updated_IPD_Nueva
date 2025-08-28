from ipd_local.simulation import get_scores, pack_functions, play_match, run_simulation
from ipd_local.get_inputs import get_strategy_code_pairs
from ipd_local.descriptor import get_client, get_response, describe_strategy
from ipd_local.utils import suppress_output

import unittest
import marshal
import json

def cheat(my_moves, other_moves, current_round):
    return True


def cooperate(my_moves, other_moves, current_round):
    return False

test_code = """import random

def a(aoresnt):
    return 1

import math

def b(arosent, aoresnt, arstoenars: int) -> int:
    "aiernst"

def c():
    pass"""


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

    def test_play_match_no_noise(self):
        self.assertEqual(
            play_match(
                pack_functions((cheat, cooperate)),
                noise=False,
                rounds=150,
                num_noise_games_to_avg=10,
            ),
            get_scores([True] * 150, [False] * 150),
        )

    def test_play_match_noise(self):
        self.assertEqual(
            play_match(
                pack_functions((cheat, cooperate)),
                noise=True,
                noise_level=0.1,
                rounds=150,
                num_noise_games_to_avg=10,
            ),
            get_scores([True] * 150, [False] * 150),
        )

    def test_run_simulation(self):
        with suppress_output():
            simulation_result = run_simulation(
                [cheat, cooperate],
                noise=False,
                rounds=10,
                num_noise_games_to_avg=50,
            )

        self.assertEqual(simulation_result["cheat"]["cooperate"], (90.0, 0.0))


class TestGetStrategyCodePairs(unittest.TestCase):
    def test_get_strategy_code_pairs(self):
        self.assertEqual(
            get_strategy_code_pairs(test_code),
            {
                "a": "    return 1\n",
                "b": "    \"aiernst\"\n",
                "c": "    pass",
            },
        )

class TestDescriptor(unittest.TestCase):
    def test_create_completion_paris(self):
        client = get_client()
        response = get_response(client, [{"role": "user", "content": "what is the capital of france? answer in only one word. ex: 'what is the captial of china?' answer: 'beijing"}])
        self.assertIsNotNone(response)
        # Check for multiple variations of "Paris"
        response_content = response.strip()
        self.assertIn(response_content.lower(), ["paris", "paris.", "paris!"])

    def test_describe_strategy_is_json(self):
        response = describe_strategy(True, """def cheat():
            return True""")
        self.assertIsNotNone(response)
        self.assertIsInstance(json.loads(response), dict)

    def test_describe_strategy_is_json_10_times(self):
        for i in range(10):
            response = describe_strategy(True, f"""def cheat{i}():
                return True""")
            self.assertIsNotNone(response)
            self.assertIsInstance(json.loads(response), dict)



if __name__ == "__main__":
    unittest.main()
