"""Submodule that actually simulates the IPD game."""

from .types import *
from .game_specs import *
from .output_locations import *
from utils import suppress_output

from tqdm import tqdm
from functools import partial
from loguru import logger
import multiprocessing as mp
import marshal
from collections import defaultdict

import random
import math

# ↑ this seciton of imports is pretty important, a lot 
# of functions use these modules without importing it 
# in their own code; without the imports, they will not 
# run

def pack_functions(
    functions: Tuple[Callable[..., Any], Callable[..., Any]]
) -> Tuple[Tuple[bytes, str], Tuple[bytes, str]]:
    """Packs a tuple of two functions into a tuples of with their bytecode and name.
    Note:
    - If the function references globals, it will not work!
    """
    return (
        (marshal.dumps(functions[0].__code__), functions[0].__name__),
        (marshal.dumps(functions[1].__code__), functions[1].__name__),
    )


def unpack_functions(
    bytecodes: Tuple[Tuple[bytes, str], Tuple[bytes, str]]
) -> Tuple[Callable[..., Any], Callable[..., Any]]:
    """Unpacks a tuple of two tuples of bytecode sequences and names into a tuple of functions.
    Default function names are "p1" and "p2".
    """
    return (
        FunctionType(
            marshal.loads(bytecodes[0][0]), globals(), bytecodes[0][1] or "p1"
        ),
        FunctionType(
            marshal.loads(bytecodes[1][0]), globals(), bytecodes[1][1] or "p2"
        ),
    )


def get_scores(
    player1_moves: List[bool],
    player2_moves: List[bool],
    both_coop: int = POINTS_BOTH_COOPERATE,
    loser: int = POINTS_DIFFERENT_LOSER,
    winner: int = POINTS_DIFFERENT_WINNER,
    both_rat: int = POINTS_BOTH_RAT,
) -> List[float]:
    """
    Calculates the points each player has given their set of moves.

    Note: `player1_moves` and `player2_moves` are assumed to be equal length!

    Arguments:
    - `player1_moves`: the list of moves player 1 made
    - `player2_moves`: the list of moves player 2 made
    - `both_rat`: the points received if both players rat.
    - `both_coop`: the points received if both players cooperate.
    - `loser`: the points received by the cooperating player if the other one rats
    - `winner`: the points received by the rat player if the other one cooperates

    `both_rat`, `both_coop`, `loser`, and `winner` all default to the values set in `game_specs.py`

    Returns: a 2-element list of the points of player 1 and player 2.
    """

    # both coop, get exploited, exploit other, both cheat
    payoffs = [both_coop, loser, winner, both_rat]

    player1_score, player2_score = 0.0, 0.0

    for player1_move, player2_move in zip(player1_moves, player2_moves):
        player1_score += payoffs[2 * player1_move + player2_move]
        player2_score += payoffs[2 * player2_move + player1_move]

    return (player1_score, player2_score)


def play_match(
    bytecode: Tuple[bytes, bytes],
    noise: bool = NOISE,
    noise_level: float = NOISE_LEVEL,
    rounds: int = ROUNDS,
    num_noise_games_to_avg: int = NUM_NOISE_GAMES_TO_AVG,
) -> Optional[List[float]]:
    """
    Plays a match of Iterated Prisoner's Dilemma between two players.

    Arguments:
    - `bytecode`: a tuple of the bytecode representations of the two players.
    - `noise`: whether or not noise is enabled.
    - `noise_level`: chance of miscommunicating (only takes affect if noise is on)
    - `rounds`: the number of rounds for the game.
    - `noise_games_to_average`: the number of games to play before averaging results if noise is on.

    `noise`, `noise_level`, `rounds`, and `num_games` all default to the values specified in `game_specs.py`

    Returns: a 2-element list of their scores.
    """
    player1, player2 = unpack_functions(bytecode)
    globals()[player1.__name__] = player1
    globals()[player2.__name__] = player2

    games = []
    with suppress_output():
        for _ in range(num_noise_games_to_avg if noise else 1):
            player1moves = []
            player2moves = []
            player1percieved = []
            player2percieved = []

            for i in range(rounds):
                try:
                    player1move = player1(
                        player1moves,
                        player2percieved,
                        i,
                    )

                    if not isinstance(player1move, bool):
                        raise Exception("Strategy returned invalid response!")
                except Exception as e:
                    logger.error(
                        f"An error occurred for function {player1.__name__}: {e}"
                    )
                    return None

                try:
                    player2move = player2(
                        player2moves,
                        player1percieved,
                        i,
                    )

                    if not isinstance(player2move, bool):
                        raise Exception("Strategy returned invalid response!")
                except Exception as e:
                    logger.error(
                        f"An error occurred for function {player2.__name__}: {e}"
                    )
                    return None

                player1moves.append(player1move)
                player2moves.append(player2move)
                player1percieved.append(
                    not player1move
                    if NOISE and random.random() < noise_level
                    else player1move
                )
                player2percieved.append(
                    not player2move
                    if NOISE and random.random() < noise_level
                    else player2move
                )

            if len(player1moves) != rounds or len(player2moves) != rounds:
                return None

            games.append(get_scores(player1moves, player2moves))
    if player1.__name__ in globals():
        del globals()[player1.__name__]
    if player2.__name__ in globals():
        del globals()[player2.__name__]

    return [
        sum([game[0] for game in games]) / (num_noise_games_to_avg if noise else 1),
        sum([game[1] for game in games]) / (num_noise_games_to_avg if noise else 1),
    ]


def run_simulation(
    strats: List[Strategy],
    noise: bool = NOISE,
    noise_level: float = NOISE_LEVEL,
    rounds: int = ROUNDS,
    num_noise_games_to_avg: int = NUM_NOISE_GAMES_TO_AVG,
) -> Dict[str, Dict[str, List[int]]]:
    """
    Runs the full IPD simulation.

    Arguments:
    - `strats`: a list of strategies to run in the tournament.
    - `noise`: whether or not noise is enabled.
    - `noise_level`: chance of miscommunicating (only takes affect if noise is on)
    - `rounds`: the number of rounds for the game.
    - `noise_games_to_average`: the number of games to play before averaging results if noise is on.

    `noise`, `noise_level`, `rounds`, and `num_games` all default to the values specified in `game_specs.py`

    Returns a nested dictionary that maps matchups to results.
    Example:
    ```
    out = run_simulation([SteveFunc, QuackaryFunc, JackaryFunc])
    print(out["SteveFunc"]["QuackaryFunc"]) # gives results of Steve vs. Quackary
    ```
    """
    matchups = []
    print(len(strats))
    for i, p1 in enumerate(strats):
        for j, p2 in enumerate(strats):
            if j <= i:
                continue
            matchups.append((p1, p2))
    with mp.Pool(mp.cpu_count()) as pool:
        specified_play_match = partial(
            play_match,
            noise=noise,
            noise_level=noise_level,
            rounds=rounds,
            num_noise_games_to_avg=num_noise_games_to_avg,
        )

        result = list(
            tqdm(
                pool.imap(  # NOTE imap() may be the source of the slowness...?
                    specified_play_match,
                    [pack_functions(x) for x in matchups],
                ),
                total=len(matchups),
            )
        )
    output = defaultdict(dict)
    for i, matchup in enumerate(matchups):
        match_result = result[i]
        if match_result == None:
            continue
        output[matchup[0].__name__][matchup[1].__name__] = match_result
        output[matchup[1].__name__][matchup[0].__name__] = list(reversed(match_result))
    return output
