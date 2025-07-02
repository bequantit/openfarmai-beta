import sys
import gspread, json
import pandas as pd
import streamlit as st
from pathlib import Path
import argparse

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from openfarma.src.params import *
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# Parse command line arguments
parser = argparse.ArgumentParser(description="Pull stock data for a specific store")
parser.add_argument("store_id", help="Store ID to process")
args = parser.parse_args()

store_id = args.store_id

# Authenticate with service account
# credentials = json.loads(st.secrets["credentials"]["json"])
# with open(CREDENTIALS_PATH, "w") as json_file:
#     json.dump(credentials, json_file, indent=4)
credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)

# Create gspread client with credentials
gc = gspread.authorize(credentials)

# Access the Google Sheets API and retrieve data
spreadsheet_by_store_id = {
    "10": SPREADSHEET_ID_BOT_10,
    "11": SPREADSHEET_ID_BOT_11,
    "12": SPREADSHEET_ID_BOT_12,
    "13": SPREADSHEET_ID_BOT_13,
    "14": SPREADSHEET_ID_BOT_14,
    "15": SPREADSHEET_ID_BOT_15,
    "16": SPREADSHEET_ID_BOT_16,
    "17": SPREADSHEET_ID_BOT_17,
    "18": SPREADSHEET_ID_BOT_18,
    "19": SPREADSHEET_ID_BOT_19,
    "20": SPREADSHEET_ID_BOT_20,
    "21": SPREADSHEET_ID_BOT_21,
    "22": SPREADSHEET_ID_BOT_22,
    "23": SPREADSHEET_ID_BOT_23,
    "24": SPREADSHEET_ID_BOT_24,
    "31": SPREADSHEET_ID_BOT_31,
    "65": SPREADSHEET_ID_BOT_65,
    "71": SPREADSHEET_ID_BOT_71,
}

try:
    spreadsheet_id = spreadsheet_by_store_id[store_id]
    spreadsheet = gc.open_by_key(spreadsheet_id)  # Open Google Spreadsheet using its ID
    worksheet = spreadsheet.sheet1  # Or use .worksheet("Sheet name")
    data = worksheet.get_all_values()  # Read current data
    if data:
        print(f"Store ID: {store_id}")
        print(f"Spreadsheet ID: {spreadsheet_id}")
        print(f"Data retrieved successfully. {len(data) - 1} products.")
    else:
        print("No data found.")

except HttpError as error:
    print("An error occurred:", error)

# Convert data to pandas DataFrame
df = pd.DataFrame(data[1:], columns=data[0])
df = df[df.notna().all(axis=1)]  # remove empty rows
# Columns:
# "codigo_fcia" | pharmacy code (store id)
# "ean"         | product identifier
# "stock"       | quantity of units in stock
# "precio_vta"  | sale price
# "promocion"   | promotion of the product
# "descrip"     | product description

# Turns Ids to string
df.iloc[:, 1] = df.iloc[:, 1].astype(str)
# Adjust stock value
df.iloc[:, 2] = df.iloc[:, 2].astype(float).astype(int)
# Adjust price format
df.iloc[:, 3] = df.iloc[:, 3].astype("float")

# Remove rows with 'stock' column equal to 0
df = df[df.iloc[:, 2] > 0]
df.reset_index(drop=True, inplace=True)

# Rename columns
df.columns = ["codigo", "ean", "stock", "precio", "promo", "descripcion"]

# Save the DataFrame to a CSV file
df.to_csv(STOCK_PATH, index=False)
