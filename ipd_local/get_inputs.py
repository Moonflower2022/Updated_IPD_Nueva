"""Submodule for handling inputs. Responsible for spreadsheet fetching, pastebin downloads, function verification/loading."""

import gspread
import requests
from tqdm import tqdm

from typing import Optional, List, Callable, NewType, Tuple
import parse

from loguru import logger

from .game_specs import *
from .default_functions import *
from .simulation import *
from .output_locations import *
import os
import urllib

Strategy = NewType("Strategy", Callable[[List[bool], List[bool], int], bool])


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

    ident = parse.parse("/raw/{}", url.path)
    if ident == None:
        ident = parse.parse("/{}", url.path)
        if ident == None:
            return None

    ident = ident[0]
    if (
        len(ident) != 8 or not ident.isalnum()
    ):  # pastebin IDs are always 8 alphanumeric chars
        return None

    if not os.path.exists("./cache"):
        os.mkdir("./cache")
    if cache:
        if os.path.exists(f"./cache/{ident}"):
            return open(f"./cache/{ident}", "r").read()

    raw_link = f"https://pastebin.com/raw/{ident}"
    code = requests.get(raw_link).text
    if not cache:  # no need to re-write cache's contents to itself
        open(f"./cache/{ident}", "w").write(code)
    return code


def get_and_load_functions(
    data: List[List[str]],
    name_col: int = STUDENT_NAME_COL,
    regular_col: int = REGULAR_STRAT_COL,
    noise_col: int = NOISE_STRAT_COL,
    noise: bool = NOISE,
) -> List[Strategy]:
    """
    Downloads, loads, and filters all of the python code in the provided pastebin links.
    Filtering of functions is done via `check_functions_io`

    Arguments:
    - `data`: the column-row list of lists representing the spreadsheet contents. See `get_spreadsheet_data()`
    - `name_col`: the column that the student names are located in. One-indexed! Defaults to specified value in `game_specs.py`
    - `regular_col`: the column that the regular strategies are located in. One-indexed! Defaults to specified value in `game_specs.py`
    - `noise_col`: the column that the noise strategies are located in. One-indexed! Defaults to specified value in `game_specs.py`
    - `noise`: whether or not the current game is being run with noise. Defaults to specified value in `game_specs.py`
    """
    print("Retrieving student code...")

    block = open("blocked.txt", "r").read()

    # iterate through all submissions (every student)
    for i in tqdm(range(1, len(data))):
        if data[i][name_col] in block:
            with open("successful_block.txt", "w") as f:
                f.write("Successfully blocked " + str(data[i][name_col]))
            continue
        link = data[i][noise_col if noise else regular_col]

        # HACK reports a false error if the pastebin is empty
        # because empty strings are falsy
        if not (code := get_pastebin(link)):
            logger.error(f"Could not parse pastebin link for {data[i][name_col]}!")
            continue

        try:
            exec(code)
        except Exception as e:
            logger.error(f"Failed to execute code: {str(e)}")

    # get all the functions that have been loaded without issue
    loaded_functions = [f for f in locals().values() if callable(f)]

    # filter for functions that pass basic input/output check
    good, bad = check_functions_io(loaded_functions)
    loaded_functions = good

    with open(
        BLACKLIST, "w"
    ) as f:  # DON'T KNOW IF THIS WILL WORK, but should check somehow
        for error in bad:
            function, e = error
            f.write("From " + function.__name__ + ", error: " + str(e) + "\n")

    print("Removed", len(bad), "functions for bad IO.")
    print("Loaded", len(loaded_functions), " good functions.")
    return loaded_functions


def check_functions_io(
    functions: List[Strategy],
) -> Tuple[List[Strategy], List[Strategy]]:
    """
    Tests a list of functions on sample inputs and outputs to see if they work.
    Functions must take three arguments (their moves, opponent's moves, round number) and return a boolean.

    Returns tuple of the good and bad functions (in that order).
    """
    good_functions = []
    bad_functions = []

    test_cases = [[[True] * i, [False] * i, i] for i in range(0, ROUNDS)]

    for function in functions:
        try:
            with suppress_stdout():  # ignore all printed statements from these functions
                is_bad = False
                for test_case in test_cases:
                    output = function(*test_case)  # run the function
                    if not isinstance(output, bool):
                        logger.error(
                            f"Testing I/O of {function.__name__} failed: output was not bool"
                        )
                        bad_functions.append((function, "output was not bool"))
                        is_bad = True
                        break

                if not is_bad:
                    good_functions.append(function)
        except Exception as e:
            logger.error(f"Testing I/O of {function.__name__} failed: {str(e)}")
            bad_functions.append((function, e))

    return good_functions, bad_functions
