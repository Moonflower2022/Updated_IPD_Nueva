# all default functions of the simulation can be found here.
# presumably written by ian lum '22

import random
from .types import *


def rat(mymoves: List[bool], othermoves: List[bool], currentRound: int) -> bool:
    # Always Rats (returns True)
    return True


def silent(mymoves: List[bool], othermoves: List[bool], currentRound: int) -> bool:
    # Always stays silent (returns False)
    return False


def rand(mymoves: List[bool], othermoves: List[bool], currentRound: int) -> bool:
    return bool(random.getrandbits(1))


def kinda_random(
    mymoves: List[bool], othermoves: List[bool], currentRound: int
) -> bool:
    cheat_probability = 0.9
    return random.random() < cheat_probability


def tit_for_tat(mymoves: List[bool], othermoves: List[bool], currentRound: int) -> bool:
    if len(othermoves) == 0:
        return False
    return othermoves[-1]


def tit_for_two_tats(
    mymoves: List[bool], othermoves: List[bool], currentRound: int
) -> bool:
    if len(othermoves) < 2:
        return False
    return othermoves[-1] and othermoves[-2]


def nuke_for_tat(
    mymoves: List[bool], othermoves: List[bool], currentRound: int
) -> bool:
    if len(othermoves) == 0:
        return False
    return True in othermoves


def nuke_for_two_tats(
    mymoves: List[bool], othermoves: List[bool], currentRound: int
) -> bool:
    if len(othermoves) < 2:
        return False
    indices = [i for i, x in enumerate(othermoves) if x]
    for i in range(len(indices) - 1):
        if indices[i] == indices[i + 1] - 1:
            return True
    return False


def two_tits_for_tat(
    mymoves: List[bool], othermoves: List[bool], currentRound: int
) -> bool:
    if currentRound == 0:
        return False
    if (currentRound >= 1 and othermoves[-1]) or (currentRound >= 2 and othermoves[-2]):
        return True
    return False


def pavlov(mymoves: List[bool], othermoves: List[bool], currentRound: int) -> bool:
    if currentRound == 0:
        return False
    return not mymoves[-1] == othermoves[-1]


def suspicious_tit_for_tat(
    mymoves: List[bool], othermoves: List[bool], currentRound: int
) -> bool:
    if currentRound == 0:
        return True
    return othermoves[-1]


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
