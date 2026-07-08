# upload.py
# https://gist.github.com/nahidsaikat/61ecfe9e333bd55fec287e1e04dfbafd#file-csv_to_google_sheet-py

import csv
import gspread

client = gspread.service_account(filename="client_secret.json")
spreadsheet = client.open("[autosync] Rundle Jamf Report")

def upload_csv_to_sheet(filepath, tab_name):
  with open(filepath, "r") as f:
    data = list(csv.reader(f))

  # overwrite in place instead of clear()-then-update(): if the update fails,
  # the tab keeps yesterday's data rather than being left empty
  worksheet = spreadsheet.worksheet(tab_name)
  worksheet.update(data)

  # trim leftover rows/cols from a larger previous upload
  rows = len(data)
  cols = max((len(r) for r in data), default=0)
  if worksheet.row_count > rows or worksheet.col_count > cols:
    worksheet.resize(rows=max(rows, 1), cols=max(cols, 1))

def main():
  upload_csv_to_sheet("data/computers.csv", "Computer Report")
  upload_csv_to_sheet("data/devices.csv", "Device Report")
  print("Done upload.py")

if __name__ == "__main__":
  main()
