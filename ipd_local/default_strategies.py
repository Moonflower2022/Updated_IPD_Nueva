# all default functions of the simulation can be found here.
# presumably written by ian lum '22

import random
from .types import *


def rat(my_moves: List[bool], other_moves: List[bool], current_round: int) -> bool:
    # Always Rats (returns True)
    return True


def silent(my_moves: List[bool], other_moves: List[bool], current_round: int) -> bool:
    # Always stays silent (returns False)
    return False


def rand(my_moves: List[bool], other_moves: List[bool], current_round: int) -> bool:
    return bool(random.getrandbits(1))


def kinda_random(
    my_moves: List[bool], other_moves: List[bool], current_round: int
) -> bool:
    cheat_probability = 0.9
    return random.random() < cheat_probability


def tit_for_tat(my_moves: List[bool], other_moves: List[bool], current_round: int) -> bool:
    if len(other_moves) == 0:
        return False
    return other_moves[-1]


def tit_for_two_tats(
    my_moves: List[bool], other_moves: List[bool], current_round: int
) -> bool:
    if len(other_moves) < 2:
        return False
    return other_moves[-1] and other_moves[-2]


def nuke_for_tat(
    my_moves: List[bool], other_moves: List[bool], current_round: int
) -> bool:
    if len(other_moves) == 0:
        return False
    return True in other_moves


def nuke_for_two_tats(
    my_moves: List[bool], other_moves: List[bool], current_round: int
) -> bool:
    if len(other_moves) < 2:
        return False
    indices = [i for i, x in enumerate(other_moves) if x]
    for i in range(len(indices) - 1):
        if indices[i] == indices[i + 1] - 1:
            return True
    return False


def two_tits_for_tat(
    my_moves: List[bool], other_moves: List[bool], current_round: int
) -> bool:
    if current_round == 0:
        return False
    if (current_round >= 1 and other_moves[-1]) or (current_round >= 2 and other_moves[-2]):
        return True
    return False


def pavlov(my_moves: List[bool], other_moves: List[bool], current_round: int) -> bool:
    if current_round == 0:
        return False
    return not my_moves[-1] == other_moves[-1]


def suspicious_tit_for_tat(
    my_moves: List[bool], other_moves: List[bool], current_round: int
) -> bool:
    if current_round == 0:
        return True
    return other_moves[-1]


all_default_functions = [
    rat,
    silent,
    rand,
    kinda_random,
    tit_for_tat,
    tit_for_two_tats,
    nuke_for_tat,
    nuke_for_two_tats,
    two_tits_for_tat,
    pavlov,
    suspicious_tit_for_tat,
]
