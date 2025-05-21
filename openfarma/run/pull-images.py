import sys
import gspread, json
import pandas as pd
import streamlit as st
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from openfarma.src.params import *
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# Authenticate with service account
credentials = json.loads(st.secrets["credentials"]["json"])
with open(CREDENTIALS_PATH, "w") as json_file:
    json.dump(credentials, json_file, indent=4)
credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)

# Create gspread client with credentials
gc = gspread.authorize(credentials)

try:
    spreadsheet = gc.open_by_key(SPREADSHEET_ID_IMAGES)    # Open Google Spreadsheet using its ID
    worksheet = spreadsheet.sheet1                          # Or use .worksheet("Sheet name")
    data = worksheet.get_all_values()                       # Read current data
    if data:
        print(f"Data retrieved successfully. {len(data)-1} product's images.")
    else:
        print("No data found.")

except HttpError as error:
    print("An error occurred:", error)

# Convert data to pandas DataFrame
df = pd.DataFrame(data[1:], columns=data[0])

# Keep all values as strings, including empty cells
df = df.astype(str)

# Save the DataFrame to a CSV file
df.to_csv(IMAGES_PATH, index=False)
