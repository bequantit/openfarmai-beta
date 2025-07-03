import os
import re
from dotenv import load_dotenv

load_dotenv()

# root path
ROOT = os.getcwd()

# paths
## csv
LOGIN_PATH = os.path.join(ROOT, "openfarma/database/login.csv")  # login database path
IMAGES_PATH = os.path.join(
    ROOT, "openfarma/database/imagenes.csv"
)  # images database path
ABM_PATH = os.path.join(ROOT, "openfarma/database/abm.csv")  # abm database path
STORES_PATH = os.path.join(
    ROOT, "openfarma/database/sucursales.csv"
)  # stores database path
STOCK_PATH = os.path.join(ROOT, "openfarma/database/stock.csv")  # stock database path

STOCK_BOT_10_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_10.csv"
)  # stock from id=10 store
STOCK_BOT_11_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_11.csv"
)  # stock from id=11 store
STOCK_BOT_12_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_12.csv"
)  # stock from id=12 store
STOCK_BOT_13_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_13.csv"
)  # stock from id=13 store
STOCK_BOT_14_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_14.csv"
)  # stock from id=14 store
STOCK_BOT_15_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_15.csv"
)  # stock from id=15 store
STOCK_BOT_16_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_16.csv"
)  # stock from id=16 store
STOCK_BOT_17_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_17.csv"
)  # stock from id=17 store
STOCK_BOT_18_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_18.csv"
)  # stock from id=18 store
STOCK_BOT_19_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_19.csv"
)  # stock from id=19 store
STOCK_BOT_20_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_20.csv"
)  # stock from id=20 store
STOCK_BOT_21_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_21.csv"
)  # stock from id=21 store
STOCK_BOT_22_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_22.csv"
)  # stock from id=22 store
STOCK_BOT_23_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_23.csv"
)  # stock from id=23 store
STOCK_BOT_24_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_24.csv"
)  # stock from id=24 store
STOCK_BOT_31_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_31.csv"
)  # stock from id=31 store
STOCK_BOT_65_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_65.csv"
)  # stock from id=65 store
STOCK_BOT_71_PATH = os.path.join(
    ROOT, "openfarma/database/stock/bot_71.csv"
)  # stock from id=71 store

## folders
CHROMA_DB_PATH = os.path.join(ROOT, "openfarma/database/chroma")  # Chroma database path
HISTORY_PATH = os.path.join(ROOT, "openfarma/history")  # History folder path

## json
ASSISTANT_CONFIG_PATH = os.path.join(ROOT, "openfarma/config/assistant.json")
FC_CONFIG_PATH = os.path.join(ROOT, "openfarma/config/fc.json")
CREDENTIALS_PATH = os.path.join(ROOT, "openfarma/config/credentials.json")

## images
AVATAR_USER_PATH = os.path.join(ROOT, "openfarma/images/avatar_user.png")
AVATAR_BOT_PATH = os.path.join(ROOT, "openfarma/images/avatar_bot.png")
HEADER_LOGO_PATH = os.path.join(ROOT, "openfarma/images/header_logo.png")

## run
PULL_STOCK_PATH = os.path.join(ROOT, "openfarma/run/pull-stock.py")
PULL_IMAGES_PATH = os.path.join(ROOT, "openfarma/run/pull-images.py")
PULL_ABM_PATH = os.path.join(ROOT, "openfarma/run/pull-abm.py")
PUSH_ABM_PATH = os.path.join(ROOT, "openfarma/run/push-abm.py")
PUSH_IMAGES_PATH = os.path.join(ROOT, "openfarma/run/push-images.py")
PUSH_STOCK_PATH = os.path.join(ROOT, "openfarma/run/push-stock.py")
BUILD_ABM_DB_PATH = os.path.join(ROOT, "openfarma/run/build-abm-db.py")

# constants
K_VALUE_SEARCH = 30  # K value for the search
K_VALUE_THOLD = 5  # K value for the threshold
STOCK_UPDATE_INTERVAL = 3600  # 1 hour
USER_CHAT_COLUMNS = [0.5, 0.5]  # percentage of the column for the user chat
BOT_CHAT_COLUMNS = [0.8, 0.2]  # percentage of the column for the bot chat

# google sheets
SPREADSHEET_ID_IMAGES = "19CfuLw6dui_-pIUyq3g7_tNAUvRk7kbCjQ76jINPR0k"
SPREADSHEET_ID_ABM = "1DwQq2jyXkdEWOt76lLKb4LMdIiGX1RYoyhWE1gGPVOc"

SPREADSHEET_ID_BOT_10 = "1XNYgjTiVW85A_pFFMMFtC8fkNlzO44C8_0bMBxgv-g0"
SPREADSHEET_ID_BOT_11 = "1r8ah5Fb4m_ca_FzynF9x86oOstZa2GNd6MwA87rffn4"
SPREADSHEET_ID_BOT_12 = "1Kq2r77h1GI-E6wPTwxWGhzewxdY9aE3Xdil6-Q2lSIg"
SPREADSHEET_ID_BOT_13 = "1vZnb2emqNBCT3kBoE-TldtDexmTmMG3AKkedAQQ6Fsg"
SPREADSHEET_ID_BOT_14 = "1VPRx1wsQFjIXLUvRPAL08z0uWCVvNGK8JyLYuaiie4o"
SPREADSHEET_ID_BOT_15 = "1WWyA_YLZPf2AMlTsONrbR326mqgm7v2eCJxSTTzuE8M"
SPREADSHEET_ID_BOT_16 = "1Pe_mHYsD1tsRznc6rNjVffKwRCz0Cbfgr_XZepPqGB8"
SPREADSHEET_ID_BOT_17 = "1oL0dYjlFyoj-GSGAS_--se3AzspW6qJ8-6DHctw6W1E"
SPREADSHEET_ID_BOT_18 = "1X-jgDPdofub-bLksZKBLiJ2YgjupDDS4-XDY5pH7mok"
SPREADSHEET_ID_BOT_19 = "1ax3CraCVlIDXfDAHkd80VdrGjwzEyqycrsQj53yX3fA"
SPREADSHEET_ID_BOT_20 = "1ulAoStGq7pI5pTSA1H1WKVGcf5vjVhf_CUPsJHBKuNM"
SPREADSHEET_ID_BOT_21 = "1OOHOGgI0U9dlLdA3tpYCedhVAnKuJzBoKgUj3dq9DiE"
SPREADSHEET_ID_BOT_22 = "1rL6XvMEm875vkyOnR0QpSa4Te2loo29jNkB0x5kTIoI"
SPREADSHEET_ID_BOT_23 = "13Iac_0vwQ0EVJ7IlAyrh-D-JAR9y2w2kOkQ10RixWPE"
SPREADSHEET_ID_BOT_24 = "1hmpkQcf6J-GXlh7tCBr23lR4o7bfRz-g_CuPkxRbHBw"
SPREADSHEET_ID_BOT_31 = "1mrVZyjHwQqEnQ9oVwrNNoWsG--xBilAiFaCOEbEoi90"
SPREADSHEET_ID_BOT_65 = "1VMn7GNdV8S04BXE6gJB09UDsEM_EPL9rvp5GkYbkdnA"
SPREADSHEET_ID_BOT_71 = "1gEQZMs5XKOnUMLyZybZvg9vA18maj3DHorSqEWbOV6I"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

HEADER_CAPTION = re.sub(
    pattern=" +",
    repl=" ",
    string="""Soy un asistente virtual especializado en dermocosmética. \
                                  Podré brindarte información sobre productos, modo de uso, sus beneficios \
                                  e ingredientes.""",
)

# email
EMAIL_FROM = os.getenv("EMAIL_FROM")  # email sender
EMAIL_TO = os.getenv("EMAIL_TO")  # email receiver
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # email password

# Prompt tracking settings
PROMPT_TRACKING_INTERVAL_MINUTES = 60  # Report time in minutes
PROMPT_TRACKING_INTERVAL_HOURS = 1  # Report time in hours
PROMPT_TRACKING_SHEET_ID = "1LJcJvdsy0zOIjzloYXcQHKb5n6EBv_4mWl8lB0iowp4"
