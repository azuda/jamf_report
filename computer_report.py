# computer_report.py

import csv
from dateutil import parser
from dateutil.tz import tzoffset
import json
import re
import urllib3

"""
- parses response_computers.json
- convert report string to json
- cleanup columns for report
- write results to data/computers.csv
"""

# define ambiguous timezones thx claude
TZ_INFO = {
  "CDT": tzoffset("CDT", -5 * 3600),  # UTC-5
  "CST": tzoffset("CST", -6 * 3600),  # UTC-6
  "EDT": tzoffset("EDT", -4 * 3600),  # UTC-4
  "EST": tzoffset("EST", -5 * 3600),  # UTC-5
  "MDT": tzoffset("MDT", -6 * 3600),  # UTC-6
  "MST": tzoffset("MST", -7 * 3600),  # UTC-7
  "PDT": tzoffset("PDT", -7 * 3600),  # UTC-7
  "PST": tzoffset("PST", -8 * 3600),  # UTC-8
}

with open("data/response_computers.json") as f:
  DATA = json.load(f)

# ==================================================================================

def convert_report(report_str):
  report_dict = {}
  lines = report_str.split("\n\n")
  for line in lines:
    kvp = line.split("\n")
    report_dict[kvp[0]] = kvp[1] if len(kvp) > 1 else None
  return report_dict

def convert_time(timestamp):
  dt = parser.parse(timestamp, tzinfos=TZ_INFO)
  return dt.strftime("%Y-%m-%d %H:%M:%S")

def normalize_uptime(uptime_str: str) -> int:
  # uptime str format: `Time since boot: x day(s), y hour(s), z minute(s)`
  uptime_int = 0
  # extract days
  match_days = re.search(r'(\d+)\s+day', uptime_str)
  if match_days:
    uptime_int += int(match_days.group(1)) * 24
  # extract hours
  match_hours = re.search(r'(\d+)\s+hour', uptime_str)
  if match_hours:
    uptime_int += int(match_hours.group(1))
  # extract hours if format matches when uptime < 24 hours
  match_less = re.search(r'\d+:\d+', uptime_str)
  if match_less:
    uptime_int += int(match_less.group(0).split(":")[0])
  return uptime_int

def clean_outputs(computer):
  report = computer.get("report_dict")

  # uptime
  try:
    hours = normalize_uptime(report["UPTIME"])
    report["UPTIME"] = hours
  except:
    pass

  # filevault
  try:
    report["FILEVAULT"] = report["FILEVAULT"].split("token is")[-1].strip()
  except:
    pass

  computer["report_dict"] = report
  return

# ==================================================================================

def _get_date(computer):
  report = computer.get("report_dict")
  # print(f"converting date for computer {computer.get("name")}")
  if report and report.get("DATE"):
    try:
      return convert_time(report["DATE"])
    except:
      return report.get("DATE")
  # fallback to last checkin date
  try:
    return convert_time(computer["report_date_utc"])
  except:
    try:
      return computer["report_date_utc"].split(".")[0]
    except:
      return None

def _get_name(computer):
  return computer.get("name")

def _get_sn(computer):
  return computer.get("serial_number")

def _get_os(computer):
  report = computer.get("report_dict")
  return report.get("OS") if report else None

def _get_logged_in_user(computer):
  return computer.get("username")

def _get_department(computer):
  full = computer.get("department")
  if re.search(r'(?i)\bStudent\b', full):
    return "Student"
  elif re.search(r'(?i)\b(?:Staff|Teacher|Admin|Childcare)\b', full):
    return "Staff"
  else:
    return full

def _get_position(computer):
  full = computer.get("position") if computer else None
  if not full:
    return None
  m = re.search(r'(EGY)(\d{4})', full, re.IGNORECASE)
  if m:
    return int(m.group(2))
  return full

def _get_uptime(computer):
  report = computer.get("report_dict") if computer else None
  # assume parsed uptime is normalized (int hours) if present
  if report and report.get("UPTIME") is not None:
    return report.get("UPTIME")
  return None

def _get_filevault(computer):
  report = computer.get("report_dict")
  return report.get("FILEVAULT") if report else None

def _get_jamf_manage(computer):
  report = computer.get("report_dict")
  return report.get("JAMF_MANAGE") if report else None

def _get_cloudflare_status(computer):
  report = computer.get("report_dict")
  return report.get("CLOUDFLARE_STATUS") if report else None

def _get_cloudflare_org(computer):
  report = computer.get("report_dict")
  return report.get("CLOUDFLARE_ORG") if report else None

# add or modify columns here to be included in the final report
COLUMNS = [
  {"header": "DATE", "func": _get_date},
  {"header": "NAME", "func": _get_name},
  {"header": "SN", "func": _get_sn},
  {"header": "OS", "func": _get_os},
  {"header": "LOGGED_IN_USER", "func": _get_logged_in_user},
  {"header": "DEPT", "func": _get_department},
  {"header": "EGY", "func": _get_position},
  {"header": "UPTIME", "func": _get_uptime},
  {"header": "FILEVAULT", "func": _get_filevault},
  {"header": "JAMF_MANAGE", "func": _get_jamf_manage},
  {"header": "CLOUDFLARE_STATUS", "func": _get_cloudflare_status},
  {"header": "CLOUDFLARE_ORG", "func": _get_cloudflare_org},
]

# ==================================================================================

def main():
  computers = DATA["computers"]

  # convert report string to dict and add to all computers
  for computer in computers:
    report_str = computer.get("report")
    if report_str:
      computer["report_dict"] = convert_report(report_str)
    else:
      computer["report_dict"] = None
    clean_outputs(computer)

  # # write to debug file
  # with open("debug/c_final.json", "w") as f:
  #   json.dump(computers, f, indent=2)

  # write entries to csv
  with open("data/computers.csv", "w", newline='') as f:
    writer = csv.writer(f)
    headers = [col["header"] for col in COLUMNS]
    writer.writerow(headers)
    for computer in computers:
      row = []
      for col in COLUMNS:
        try:
          val = col["func"](computer)
        except Exception:
          val = None
        # normalize None -> empty cell, keep numeric and string values as-is
        row.append("" if val is None else val)
      writer.writerow(row)

  print("Done computer_report.py")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
