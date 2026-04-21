# upload.py
# https://gist.github.com/nahidsaikat/61ecfe9e333bd55fec287e1e04dfbafd#file-csv_to_google_sheet-py

import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("client_secret.json", scope)
client = gspread.authorize(credentials)

spreadsheet = client.open("[csv2sheet] Rundle Jamf Report")

def upload_csv_to_sheet(filepath, tab_name):
  worksheet = spreadsheet.worksheet(tab_name)
  worksheet.clear()
  with open(filepath, "r") as f:
    data = list(csv.reader(f))
  worksheet.update(data)

upload_csv_to_sheet("data/computers.csv", "Computer Report")
upload_csv_to_sheet("data/devices.csv", "Device Report")

print("Done upload.py")

# with open("data/computers.csv", "r") as f:
#   content = f.read()
#   client.import_csv(spreadsheet.id, data=content)
