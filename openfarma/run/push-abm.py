import sys
import gspread, json
import pandas as pd
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from openfarma.src.params import *
from google.oauth2.service_account import Credentials

# Authenticate with service account
credentials = json.loads(st.secrets["credentials"]["json"])
with open(CREDENTIALS_PATH, "w") as json_file:
    json.dump(credentials, json_file, indent=4)
credentials = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)

# Create gspread client with credentials
gc = gspread.authorize(credentials)

try:
    # Read CSV file with UTF-8 encoding
    df = pd.read_csv(ABM_PATH, encoding='utf-8', on_bad_lines='skip', sep=',')
    
    # Convert all values to strings and handle NaN values
    df = df.fillna('')  # Replace NaN with empty string
    df = df.astype(str)
    
    # Replace single quotes with double quotes for CSV handling
    # But preserve single quotes that are part of the text
    for col in df.columns:
        df[col] = df[col].str.replace(r'^\'|\'$', '"', regex=True)
        df[col] = df[col].str.replace(r'"', '', regex=True)
    
    # Convert DataFrame to list of lists (including headers)
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Upload to Google Sheets
    spreadsheet = gc.open_by_key(SPREADSHEET_ID_ABM)
    worksheet = spreadsheet.sheet1
    
    # Clear existing content and update with new data
    worksheet.clear()
    worksheet.update(values=data, range_name='A1')
    
    print(f"ABM data uploaded successfully. {len(df)} records.")
    
except Exception as error:
    print("Error processing ABM data:", error)
