"""Submodule for handling inputs. Responsible for spreadsheet fetching, pastebin downloads, function verification/loading."""

from .types import *
from .game_specs import *
from .output_locations import BLACKLIST_LOCATION
from utils import suppress_output, get_length_no_whitespace_no_comments

import gspread
import requests
from tqdm import tqdm
import parse
from loguru import logger
import os
import urllib
import statistics

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

    with suppress_output():
        for function in functions:
            globals()[function.__name__] = function
            try:
                for test_case in test_cases:
                    my_moves = test_case[0]
                    my_moves_copy = my_moves.copy()
                    other_moves = test_case[1]
                    other_moves_copy = other_moves.copy()
                    output = function(my_moves, other_moves, test_case[2])
                    if my_moves_copy != my_moves:
                        raise Exception("my_moves was modified")
                    if other_moves_copy != other_moves:
                        raise Exception("other_moves was modified")
                    if not isinstance(output, bool):
                        raise Exception("function output was not bool")

                good_functions.append(function)
            except Exception as e:
                logger.error(f"Testing of {function.__name__} failed: {str(e)}")
                bad_function_results.append((function, e))
            finally:
                if function.__name__ in globals():
                    del globals()[function.__name__]

    return good_functions, bad_function_results

def get_and_load_functions(
    data: List[List[str]],
    name_col: int = STUDENT_NAME_COL,
    regular_col: int = REGULAR_STRAT_COL,
    noise_col: int = NOISE_STRAT_COL,
    noise: bool = NOISE,
    maximum_num_functions: int = MAXIMUM_NUM_FUNCTIONS,
    maximum_char_count: int = MAXIMUM_CHAR_COUNT,
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
    num_function_overloaded_pastebins = 0
    num_character_overloaded_pastebins = 0
    num_blocked_pastebins = 0

    strategies_namespace = {}

    char_counts = []

    # iterate through all submissions (every student)
    for i in tqdm(range(1, len(data))):
        if data[i][name_col] in blocked_submissions:
            sucessfully_blocked_items.append(str(data[i][name_col]))
            num_blocked_pastebins += 1
            continue
        link = data[i][noise_col if noise else regular_col]

        # HACK reports a false error if the pastebin is empty
        # because empty strings are 
        
        if not (code := get_pastebin(link, cache=cache)):
            logger.error(f"Could not parse pastebin link for {data[i][name_col]}!")
            num_erroneous_pastebins += 1
            continue
        
        num_functions = get_num_functions(code)
        if num_functions > maximum_num_functions:
            num_function_overloaded_pastebins += 1
            logger.error(
                f"Pastebin link {link} has too many functions: (actual: {num_functions}, maximum: {maximum_num_functions})"
            )
            continue

        char_count = get_length_no_whitespace_no_comments(code)
        char_counts.append(char_count)

        if char_count > maximum_char_count:
            num_character_overloaded_pastebins += 1
            logger.error(
                f"Pastebin link {link} has too many characters: (actual: {char_count}, maximum: {maximum_char_count})"
            )
            continue


        # oh boy here we go
        try:
            
            exec(code, strategies_namespace)
        except Exception as error:
            num_erroneous_pastebins += 1
            logger.error(f"Failed to execute code for student {data[i][name_col]}: {str(error)}")

    # get all the functions that have been loaded without issue
    loaded_functions = []

    for element in strategies_namespace.values():
        if callable(element):
            if not element.__name__ in blocked_functions:
                loaded_functions.append(element)
            elif element.__name__ in blocked_functions:
                sucessfully_blocked_items.append(element.__name__)            

    # filter for functions that pass basic input/output check
    good_functions, bad_function_pairs = check_functions(loaded_functions)

    with open(BLACKLIST_LOCATION, "w") as blacklist_file:
        for function, error in bad_function_pairs:
            blacklist_file.write(f"From {function.__name__} error: {error}\n")

    with open("successful_blocks.txt", "w") as blocks_file:
        for successfully_blocked_item in sucessfully_blocked_items:
            blocks_file.write(f"Successfully blocked {successfully_blocked_item}\n")

    if num_erroneous_pastebins > 0:
        print(f"Could not load code from {num_erroneous_pastebins} pastebins (you can see which ones by looking at 'ipd.log').")
    if num_function_overloaded_pastebins > 0:
        print(
            f"Removed {num_function_overloaded_pastebins} pastebins for having more than {maximum_num_functions} functions."
        )
    if num_character_overloaded_pastebins > 0:
        print(
            f"Removed {num_character_overloaded_pastebins} pastebins for having more than {maximum_char_count} characters."
        )
    if num_blocked_pastebins > 0:
        print(f"Blocked {num_blocked_pastebins} pastebins.")
    if len(sucessfully_blocked_items) - num_blocked_pastebins > 0:
        print(
            f"Blocked {len(sucessfully_blocked_items) - num_blocked_pastebins} individual functions."
        )
    if len(bad_function_pairs) > 0:
        print(f"Removed {len(bad_function_pairs)} functions for bad IO.")

    print(f"Loaded {len(good_functions)} good functions.")

    print("Number of characters (no whitespace or comments)")
    print("std dev:", statistics.stdev(char_counts))
    print("mean:", statistics.mean(char_counts))
    print("q1, q2, q3:", statistics.quantiles(char_counts))
    print("min:", min(char_counts))
    print("max:", max(char_counts))

    return good_functions