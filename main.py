# main!!
# run this file to run the actual simulation

from ipd_local.game_specs import *
from ipd_local.simulation import run_simulation
from ipd_local.get_inputs import get_spreadsheet_data, get_and_load_functions
from ipd_local.output_locations import *
from ipd_local.output import *
from ipd_local.default_strategies import all_default_functions
from ipd_local.descriptor import describe_strategy
from ipd_local.utils import clean_json_like, recover_summary_fields

from tqdm import tqdm
import json
from loguru import logger
import sys
import time
import random
import numpy as np

if RANDOM_SEED:
    print(f"setting random seed to {RANDOM_SEED}")
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

if __name__ == "__main__":
    logger.remove()
    logger.add(PROBLEMS_LOG_LOCATION)
    logger.info("Starting!")

    data = get_spreadsheet_data(INPUT_SHEET_NAME, TAB_NAME)
    imported_strategies, strategy_code_pairs = get_and_load_functions(data, cache=False)

    if INCLUDE_DEFAULTS:
        print(f"Added {len(all_default_functions)} default strategies.")
        all_strategies = imported_strategies + all_default_functions
    else:
        all_strategies = imported_strategies

    raw_data = run_simulation(
        all_strategies,
        noise=NOISE,
        noise_level=NOISE_LEVEL,
        rounds=ROUNDS,
        num_noise_games_to_avg=NUM_NOISE_GAMES_TO_AVG,
    )

    with open(RAW_OUT_LOCATION, "w") as output_file:
        output_file.write(json.dumps(raw_data))

    specs = {
        "Noise": NOISE,
        "Noise Level (if applicable)": NOISE_LEVEL,
        "Noise Games Played Before Averaging (if applicable)": NUM_NOISE_GAMES_TO_AVG,
        "Number of Rounds": ROUNDS,
        "Points when both rat": POINTS_BOTH_RAT,
        "Points for winner when different": POINTS_DIFFERENT_WINNER,
        "Points for loser when different": POINTS_DIFFERENT_LOSER,
        "Points when both cooperate": POINTS_BOTH_COOPERATE,
        "Random Seed": RANDOM_SEED,
    }
    with open("./latest_specs.json", "w") as output_file:
        output_file.write(json.dumps(specs))

    print(f"describing {len(all_strategies)} strategies...")

    if DESCRIBE_STRATEGIES:
        strategy_to_description = {}
        for strategy in tqdm(imported_strategies):
            name = strategy.__name__
            raw = describe_strategy(NOISE, strategy_code_pairs[name])
            try:
                strategy_to_description[name] = json.loads(raw)
            except json.JSONDecodeError:
                cleaned = clean_json_like(raw)
                try:
                    strategy_to_description[name] = json.loads(cleaned)
                except Exception as e:
                    rec = recover_summary_fields(raw)
                    if rec:
                        strategy_to_description[name] = rec
                    else:
                        logger.error(f"Failed to parse description for {name}: {e}; raw: {raw!r}")
                        continue

            with open(STRATEGY_DESCRIPTIONS_LOCATION, "w") as output_file:
                output_file.write(json.dumps(strategy_to_description))

    update_sheet()
