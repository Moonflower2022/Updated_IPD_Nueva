import numpy as np
import pandas as pd
import json
import copy
import gspread
import gspread_dataframe

from .output_locations import *
from .game_specs import *


# returns pairwise scores for all functions as a pandas dataframe.
# column is first function, row is second function.
def get_pairwise():
    with open(RAW_OUT_LOCATION, "r") as fp:
        clean_data = json.loads(fp.read())
    pairwise = pd.DataFrame.from_dict(clean_data)
    return pairwise


# returns functions ranked by total score as pandas dataframe
# also lists each function's average score and average margin (how much higher do they score compared to opponent)
def get_ranking():
    with open(RAW_OUT_LOCATION, "r") as fp:
        clean_data = json.loads(fp.read())
    all_stats = []

    # calculates statistics for each function
    for strategy in clean_data.keys():
        strategy_stats = {}
        strategy_stats["Strategy"] = strategy

        # retrive scores
        scores = []
        opponent_scores = []
        for strat2 in clean_data[strategy].keys():
            scores.append(clean_data[strategy][strat2][1])
            opponent_scores.append(clean_data[strategy][strat2][0])

        # calculate each metric
        total_points = np.sum(scores)
        average_points = total_points / len(scores)
        # average_margin = np.sum(np.asarray(scores)-np.asarray(opponent_scores))/len(scores)

        strategy_stats["Total Points"] = total_points
        strategy_stats["Average Points"] = average_points
        # strategy_stats["Average Margin"] = average_margin

        all_stats.append(strategy_stats)

    ranked = sorted(
        all_stats, key=lambda d: d["Total Points"], reverse=True
    )  # sorts functions by total score
    ranking = pd.DataFrame.from_dict(ranked)
    return ranking


# returns summary of game as pandas dataframe
# summary items include noise (true/false), noise level, number of rounds, and score matrix
def get_summary():
    specs = {}
    with open(SPECS_JSON_LOCATION, "r") as fp:
        specs = json.loads(fp.read())
    summary = pd.DataFrame.from_dict(specs, orient="index")
    return summary


# retrieves all statistics (pairwise, ranking, and summary) and updates them on google spreadsheet.
# this spreadsheet can be found here: https://docs.google.com/spreadsheets/d/138rZ0hdy4MfFmvb1wZqgmeckGUpNl0N0T4wpAPXWeZE/edit?usp=sharing
def update_sheet(spreadsheet_name: str = OUTPUT_SHEET_NAME) -> None:

    print("Updating results spreadsheet...")

    # accesses correct google spreadsheet for results
    service_account = gspread.service_account(filename="service_account.json")
    try:
        spreadsheet = service_account.open(spreadsheet_name)
    except gspread.SpreadsheetNotFound:
        spreadsheet = service_account.create(spreadsheet_name)

    # updates summary
    try:
        summary_sheet = spreadsheet.worksheet("Summary Statistics")
    except gspread.WorksheetNotFound:
        summary_sheet = spreadsheet.add_worksheet(
            "Summary Statistics", rows="100", cols="20"
        )
    summary_sheet.clear()
    gspread_dataframe.set_with_dataframe(
        worksheet=summary_sheet,
        dataframe=get_summary(),
        include_index=True,
        include_column_header=False,
        resize=True,
    )

    # updates ranking
    try:
        ranking_sheet = spreadsheet.worksheet("Ranking")
    except gspread.WorksheetNotFound:
        ranking_sheet = spreadsheet.add_worksheet("Ranking", rows="100", cols="20")

    ranking_sheet.clear()
    gspread_dataframe.set_with_dataframe(
        worksheet=ranking_sheet,
        dataframe=get_ranking(),
        include_index=False,
        include_column_header=True,
        resize=True,
    )

    # updates pairwise scores
    try:
        pairwise_sheet = spreadsheet.worksheet("Pairwise Scores")
    except gspread.WorksheetNotFound:
        pairwise_sheet = spreadsheet.add_worksheet(
            "Pairwise Scores", rows="100", cols="20"
        )

    pairwise_sheet.clear()
    # reverse order of score reporting
    clean_data = get_pairwise()
    gspread_dataframe.set_with_dataframe(
        worksheet=pairwise_sheet,
        dataframe=clean_data,
        include_index=True,
        include_column_header=True,
        resize=True,
    )

    print("Updated results spreadsheet.")
