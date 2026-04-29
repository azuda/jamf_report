# util.py

"""
- helper functions for report generation
"""

from datetime import date
from dateutil import parser
from dateutil.tz import tzoffset
import re

# ==================================================================================

# datetime handling

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

def convert_datetime(timestamp):
  dt = parser.parse(timestamp, tzinfos=TZ_INFO)
  return dt.strftime("%Y-%m-%d %H:%M:%S")

def convert_date_simple(timestamp):
  dt = parser.parse(timestamp)
  return dt.strftime("%Y-%m-%d")

# ==================================================================================

# column data extraction functions

def _get_name(e):
  return e.get("name")

def _get_sn(e):
  return e.get("serial_number")

def _get_model(e):
  return e.get("model")

def _get_user(e):
  return e.get("username")

def _get_building(e):
  raw = e.get("building")
  parts = [b for b in raw.split() if not re.search(r"^Rundle$", b, re.IGNORECASE)]
  return " ".join(parts) or None

def _get_department(e):
  full = e.get("department")
  if re.search(r'(?i)\bStudent\b', full):
    return "Student"
  elif re.search(r'(?i)\b(?:Staff|Teacher|Admin|Childcare)\b', full):
    return "Staff"
  elif re.search(r'(?i)\bLoaner\b', full):
    return "Loaner"
  else:
    return full

def _get_position(e):
  raw = e.get("position") if e else None
  if not raw:
    return None
  pos = re.search(r'(EGY)(\d{4})', raw, re.IGNORECASE)
  if pos:
    egy = int(pos.group(2))
    today = date.today()
    current_grad_year = today.year if today.month < 9 else today.year + 1
    grade = 12 - (egy - current_grad_year)
    if grade == 0:
      return "K"
    if 1 <= grade <= 12:
      return f"Grade {grade}"
  return raw

def _get_purchase_price(e):
  price = e.get("purchase_price")
  return price if price else None

def _get_purchase_date(e):
  date = e.get("purchase_date")
  # return convert_date_simple(date) if date else "1970-01-01"
  return convert_date_simple(date) if date else None
