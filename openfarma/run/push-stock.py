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

# Define mappings
spreadsheet_by_store_id = {
    '10': SPREADSHEET_ID_BOT_10,
    '11': SPREADSHEET_ID_BOT_11,
    '12': SPREADSHEET_ID_BOT_12,
    '13': SPREADSHEET_ID_BOT_13,
    '14': SPREADSHEET_ID_BOT_14,
    '15': SPREADSHEET_ID_BOT_15,
    '16': SPREADSHEET_ID_BOT_16,
    '17': SPREADSHEET_ID_BOT_17,
    '18': SPREADSHEET_ID_BOT_18,
    '19': SPREADSHEET_ID_BOT_19,
    '20': SPREADSHEET_ID_BOT_20,
    '21': SPREADSHEET_ID_BOT_21,
    '22': SPREADSHEET_ID_BOT_22,
    '23': SPREADSHEET_ID_BOT_23,
    '24': SPREADSHEET_ID_BOT_24,
    '31': SPREADSHEET_ID_BOT_31,
    '65': SPREADSHEET_ID_BOT_65,
    '71': SPREADSHEET_ID_BOT_71,
}

stock_path_by_store_id = {
    '10': STOCK_BOT_10_PATH,
    '11': STOCK_BOT_11_PATH,
    '12': STOCK_BOT_12_PATH,
    '13': STOCK_BOT_13_PATH,
    '14': STOCK_BOT_14_PATH,
    '15': STOCK_BOT_15_PATH,
    '16': STOCK_BOT_16_PATH,
    '17': STOCK_BOT_17_PATH,
    '18': STOCK_BOT_18_PATH,
    '19': STOCK_BOT_19_PATH,
    '20': STOCK_BOT_20_PATH,
    '21': STOCK_BOT_21_PATH,
    '22': STOCK_BOT_22_PATH,
    '23': STOCK_BOT_23_PATH,
    '24': STOCK_BOT_24_PATH,
    '31': STOCK_BOT_31_PATH,
    '65': STOCK_BOT_65_PATH,
    '71': STOCK_BOT_71_PATH,
}

# Process each store
for store_id, csv_path in stock_path_by_store_id.items():
    try:
        # Read CSV file
        df = pd.read_csv(csv_path, encoding='latin1', on_bad_lines='skip')
        df = df.map(str)
        
        # Replace single quotes with double quotes for CSV handling
        # But preserve single quotes that are part of the text
        for col in df.columns:
            df[col] = df[col].str.replace(r'^\'|\'$', '"', regex=True)
            df[col] = df[col].str.replace(r'"', '', regex=True)
        
        # Prepare data for Google Sheets
        # Rename columns back to original names
        df.columns = ["codigo_fcia", "ean", "stock", "precio_vta", "promocion", "descrip"]
        
        # Convert DataFrame to list of lists (including headers)
        data = [df.columns.tolist()] + df.values.tolist()
        
        # Upload to Google Sheets
        spreadsheet_id = spreadsheet_by_store_id[store_id]
        spreadsheet = gc.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.sheet1
        
        # Clear existing content and update with new data
        worksheet.clear()
        worksheet.update(values=data, range_name='A1')
        
        print(f"Store {store_id}: Data uploaded successfully. {len(df)} products.")
        
    except Exception as error:
        print(f"Error processing store {store_id}:", error)