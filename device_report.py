# device_report.py

import copy
import csv
from dateutil import parser
import json
import re
import time
import urllib3

"""
- parses response_devices.json
- cleanup columns for report
- write results to data/devices.csv
"""

with open("data/response_devices.json") as f:
  DATA = json.load(f)

# ==================================================================================

def convert_time(timestamp):
  dt = parser.parse(timestamp)
  return dt.strftime("%Y-%m-%d %H:%M:%S")

# ==================================================================================

def _get_date(device):
  try:
    return convert_time(device["date"])
  except:
    try:
      return device["date"].split(".")[0]
    except:
      return None

def _get_name(device):
  return device.get("name")

def _get_sn(device):
  return device.get("serial_number")

def _get_os(device):
  return device.get("os")

def _get_model(device):
  return device.get("model_display")

def _get_assigned_user(device):
  return device.get("username")

def _get_department(device):
  full = device.get("department")
  if re.search(r'(?i)\bStudent\b', full):
    return "Student"
  elif re.search(r'(?i)\b(?:Staff|Teacher|Admin|Childcare)\b', full):
    return "Staff"
  else:
    return full

def _get_position(device):
  full = device.get("position")
  if not full:
    return None
  m = re.search(r'(EGY)(\d{4})', full, re.IGNORECASE)
  if m:
    return int(m.group(2))
  return full

# add or modify columns here to be included in the final report
COLUMNS = [
  {"header": "DATE", "func": _get_date},
  {"header": "NAME", "func": _get_name},
  {"header": "SN", "func": _get_sn},
  {"header": "OS", "func": _get_os},
  {"header": "MODEL", "func": _get_model},
  {"header": "ASSIGNED_USER", "func": _get_assigned_user},
  {"header": "DEPT", "func": _get_department},
  {"header": "EGY", "func": _get_position},
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

  print("Done")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
