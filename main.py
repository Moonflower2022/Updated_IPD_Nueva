# main!!
# run this file to run the actual simulation

from ipd_local.game_specs import *
from ipd_local.simulation import run_simulation
from ipd_local.get_inputs import get_spreadsheet_data, get_and_load_functions
from ipd_local.output_locations import *
from ipd_local.output import *
from ipd_local.default_strategies import all_default_functions

import json
from loguru import logger
import sys
import time
import random

if DEBUG_MODE == True:
    random.seed(0)

if __name__ == "__main__":
    logger.remove()
    logger.add(PROBLEMS_LOG_LOCATION)
    logger.info("Starting!")

    data = get_spreadsheet_data(INPUT_SHEET_NAME, TAB_NAME)
    imported_strategies = get_and_load_functions(data, cache=False)

    all_strategies = (
        all_default_functions + imported_strategies
        if INCLUDE_DEFAULTS
        else imported_strategies
    )

    if INCLUDE_DEFAULTS:
        print(f"Added {len(all_default_functions)} default strategies.")

    raw_data = run_simulation(all_strategies, noise=NOISE, noise_level=NOISE_LEVEL, rounds=ROUNDS, num_noise_games_to_avg=NUM_NOISE_GAMES_TO_AVG)

    with open(RAW_OUT_LOCATION, "w") as fp:
        fp.write(json.dumps(raw_data))

    specs = {
        "Noise": NOISE,
        "Noise Level (if applicable)": NOISE_LEVEL,
        "Noise Games Played Before Averaging (if applicable)": NUM_NOISE_GAMES_TO_AVG,
        "Number of Rounds": ROUNDS,
        "Points when both rat": POINTS_BOTH_RAT,
        "Points for winner when different": POINTS_DIFFERENT_WINNER,
        "Points for loser when different": POINTS_DIFFERENT_LOSER,
        "Points when both cooperate": POINTS_BOTH_COOPERATE,
        "Debug mode (fixed random seed - should be off)": DEBUG_MODE,
    }
    with open("./latest_specs.json", "w") as fp:
        fp.write(json.dumps(specs))

    update_sheet()
