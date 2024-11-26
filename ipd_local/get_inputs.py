"""Submodule for handling inputs. Responsible for spreadsheet fetching, pastebin downloads, function verification/loading."""

from .types import *
from .game_specs import *
from .output_locations import BLACKLIST_LOCATION
from utils import suppress_output

import gspread
import requests
from tqdm import tqdm
import parse
from loguru import logger
import os
import urllib

import random
import math

# ↑ this seciton of imports is pretty important, a lot 
# of functions use these modules without importing it 
# in their own code; without the imports, they will not 
# run


def get_spreadsheet_data(sheet: str, tab: str) -> List[List[str]]:
    """
    Retrieve latest list of submissions from Google Sheet.
    Link: https://docs.google.com/spreadsheets/d/1YZZQFShRcYO4p3pCqBY5LPZf4pO9zfmt6b6BNItVb3g/edit?usp=sharing

    Arguments:
    - `sheet`: the name of the spreadsheet to query.
    - `tab`: the tab of the spreadsheet the data is in.

    Returns: list of lists containing spreadsheet data in column-row format.
    """
    print("Retrieving spreadsheet data...")
    service_account = gspread.service_account(filename="service_account.json")
    spreadsheet = service_account.open(sheet)
    worksheet = spreadsheet.worksheet(tab)
    print("Retrieved spreadsheet data.")
    return worksheet.get_all_values()


def get_pastebin(link: str, cache: bool = False) -> Optional[str]:
    """
    Downloads content of pastebin link and returns it.
    Caches content for optional faster future lookups (assuming code has not changed).

    Arguments:
    - `link`: the pastebin link to query
    - `cache`: whether or not to pull from a cached copy (if applicable).

    Returns: the contents of the pastebin as a string.
    """
    url = urllib.parse.urlparse(link)
    if url.netloc != "pastebin.com":
        return None

    id = parse.parse("/raw/{}", url.path)
    if id == None:
        id = parse.parse("/{}", url.path)
        if id == None:
            return None

    id = id[0]
    if len(id) != 8 or not id.isalnum():  # pastebin IDs are always 8 alphanumeric chars
        return None

    if not os.path.exists("./cache"):
        os.mkdir("./cache")
    if cache:
        if os.path.exists(f"./cache/{id}"):
            return open(f"./cache/{id}", "r").read()

    raw_link = f"https://pastebin.com/raw/{id}"
    code = requests.get(raw_link).text
    if not cache:  # no need to re-write cache's contents to itself
        open(f"./cache/{id}", "w").write(code)
    return code


def get_and_load_functions(
    data: List[List[str]],
    name_col: int = STUDENT_NAME_COL,
    regular_col: int = REGULAR_STRAT_COL,
    noise_col: int = NOISE_STRAT_COL,
    noise: bool = NOISE,
    maximum_num_functions: int = MAXIMUM_NUM_FUNCTIONS,
    cache: bool = False,
) -> List[Strategy]:
    """
    Downloads, loads, and filters all of the python code in the provided pastebin links.
    Filtering of functions is done via `check_functions_io`

    Arguments:
    - `data`: the column-row list of lists representing the spreadsheet contents. See `get_spreadsheet_data()`
    - `name_col`: the column that the student names are located in. One-indexed!
    - `regular_col`: the column that the regular strategies are located in. One-indexed!
    - `noise_col`: the column that the noise strategies are located in. One-indexed!
    - `noise`: whether or not the current game is being run with noise.

    All arguments except for `data` defaults to specified value in `game_specs.py`.
    """
    print("Retrieving student code...")

    with open("blocked_functions.txt", "r") as blocked_functions_file:
        blocked_functions = blocked_functions_file.read().split("\n")

    with open("blocked_submissions.txt", "r") as blocked_submissions_file:
        blocked_submissions = blocked_submissions_file.read().split("\n")

    sucessfully_blocked_items = []

    num_erroneous_pastebins = 0
    num_overloaded_pastebins = 0
    num_blocked_pastebins = 0

    # iterate through all submissions (every student)
    for i in tqdm(range(1, len(data))):
        if data[i][name_col] == blocked_submissions:
            sucessfully_blocked_items.append(str(data[i][name_col]))
            num_blocked_pastebins += 1
            continue
        link = data[i][noise_col if noise else regular_col]

        # HACK reports a false error if the pastebin is empty
        # because empty strings are falsy
        if not (code := get_pastebin(link, cache=cache)):
            logger.error(f"Could not parse pastebin link for {data[i][name_col]}!")
            num_erroneous_pastebins += 1
            continue

        try:
            num_functions = get_num_functions(code)
            if num_functions > maximum_num_functions:
                num_overloaded_pastebins += 1
                raise Exception(
                    f"Pastebin link {link} has too many functions: "
                    f"(actual: {num_functions}, maximum: {maximum_num_functions})"
                )
            exec(code)
        except Exception as error:
            logger.error(f"Failed to execute code: {str(error)}")

    # get all the functions that have been loaded without issue
    loaded_functions = [
        func
        for func in locals().values()
        if callable(func) and not func.__name__ in blocked_functions
    ]

    sucessfully_blocked_items += [
        func.__name__
        for func in locals().values()
        if callable(func) and func.__name__ in blocked_functions
    ]

    # filter for functions that pass basic input/output check
    good_functions, bad_function_pairs = check_functions(loaded_functions)

    with open(BLACKLIST_LOCATION, "w") as blacklist_file:
        for function, error in bad_function_pairs:
            blacklist_file.write(f"From {function.__name__} error: {error}\n")

    with open("successful_blocks.txt", "w") as blocks_file:
        for successfully_blocked_item in sucessfully_blocked_items:
            blocks_file.write(f"Successfully blocked {successfully_blocked_item}\n")

    print(f"Could not load code from {num_erroneous_pastebins} pastebins.")
    print(
        f"Removed {num_overloaded_pastebins} pastebins for having more than {maximum_num_functions} functions."
    )
    print(f"Blocked {num_blocked_pastebins} pastebins.")
    print(
        f"Blocked {len(sucessfully_blocked_items) - num_blocked_pastebins} individual functions."
    )
    print(f"Removed {len(bad_function_pairs)} functions for bad IO.")
    print(f"Loaded {len(good_functions)} good functions.")
    return good_functions


def get_num_functions(code: str):
    lines = code.split("\n")

    num_functions = 0
    for line in lines:
        if line.startswith("def "):
            num_functions += 1

    return num_functions


def check_functions(
    functions: List[Strategy],
) -> Tuple[List[Strategy], List[Strategy]]:
    """
    Tests a list of functions on sample inputs and outputs to see if they work.
    Functions must take three arguments (their moves, opponent's moves, round number) and return a boolean.

    Returns tuple of the good and bad functions (in that order).
    """

    good_functions = []
    bad_function_results = []

    test_cases = [[[True] * i, [False] * i, i] for i in range(0, ROUNDS)]

    for function in functions:
        try:
            is_bad = False
            for test_case in test_cases:
                with suppress_output():
                    output = function(*test_case)
                if not isinstance(output, bool):
                    logger.error(
                        f"Testing of {function.__name__} failed: output was not bool"
                    )
                    bad_function_results.append((function, "output was not bool"))
                    is_bad = True
                    break

            if not is_bad:
                good_functions.append(function)
        except Exception as e:
            logger.error(f"Testing of {function.__name__} failed: {str(e)}")
            bad_function_results.append((function, e))

    return good_functions, bad_function_results
