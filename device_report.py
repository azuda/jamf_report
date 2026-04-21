# device_report.py

"""
- parses `response_devices.json`
- cleanup columns for report
- write results to `data/devices.csv`
"""

import csv
import json
import urllib3

from util import convert_datetime
from util import _get_name, _get_sn, _get_model, _get_user, _get_department, _get_position, _get_purchase_price, _get_purchase_date

with open("data/response_devices.json") as f:
  DATA = json.load(f)

# ==================================================================================

def _get_date(device):
  try:
    return convert_datetime(device["date"])
  except:
    try:
      return device["date"].split(".")[0]
    except:
      return None

def _get_os(device):
  return device.get("os")

# add or modify columns here to be included in the final report
COLUMNS = [
  {"header": "DATE", "func": _get_date},
  {"header": "NAME", "func": _get_name},
  {"header": "SN", "func": _get_sn},
  {"header": "OS", "func": _get_os},
  {"header": "MODEL", "func": _get_model},
  {"header": "USER", "func": _get_user},
  {"header": "DEPT", "func": _get_department},
  {"header": "EGY", "func": _get_position},
  {"header": "PURCHASE_PRICE", "func": _get_purchase_price},
  {"header": "PURCHASE_DATE", "func": _get_purchase_date},
]

# ==================================================================================

def main():
  devices = DATA["devices"]

  # write entries to csv
  with open("data/devices.csv", "w", newline='') as f:
    writer = csv.writer(f)
    headers = [col["header"] for col in COLUMNS]
    writer.writerow(headers)
    for d in devices:
      row = []
      for col in COLUMNS:
        try:
          val = col["func"](d)
        except Exception:
          val = None
        # normalize None -> empty cell, keep numeric and string values as-is
        row.append("" if val is None else val)
      writer.writerow(row)

  print("Done device_report.py")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
