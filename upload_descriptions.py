#!/usr/bin/env python3
"""Upload strategy descriptions to Google Sheets."""

import json
import gspread
import pandas as pd
import gspread_dataframe

SHEET_NAME = "IPD 2025 Strategy Descriptions"

# Load the JSON file
with open("latest_strategy_descriptions.json", "r") as f:
    descriptions = json.load(f)

# Convert to DataFrame with capitalized headers
data = []
for strategy_name, description in descriptions.items():
    data.append({"Strategy": strategy_name, "Description": description})

df = pd.DataFrame(data)

# Connect to Google Sheets
service_account = gspread.service_account(filename="service_account.json")

# Try to open existing sheet or create new one
try:
    spreadsheet = service_account.open(SHEET_NAME)
    print(f"Found existing spreadsheet: {SHEET_NAME}")
except gspread.SpreadsheetNotFound:
    spreadsheet = service_account.create(SHEET_NAME)
    print(f"Created new spreadsheet: {SHEET_NAME}")

# Get or create the first worksheet
try:
    worksheet = spreadsheet.sheet1
except:
    worksheet = spreadsheet.add_worksheet("Sheet1", rows=100, cols=20)

# Clear existing data
worksheet.clear()

# Upload the data
gspread_dataframe.set_with_dataframe(
    worksheet=worksheet,
    dataframe=df,
    include_index=False,
    include_column_header=True,
    resize=True,
)

print(f"Successfully uploaded {len(data)} strategies to {SHEET_NAME}")
print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
