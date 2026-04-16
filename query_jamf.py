# query_jamf.py

from jamf_credential import JAMF_URL, get_token, invalidate_token, check_token_expiration
import json
import os
import requests
import time
import urllib3

"""
- gets basic info about all computers + mobile devices in jamf
- writes results to `data/response_computers.json` and `data/response_devices.json`
"""

# ==================================================================================

def get_computers_basic(access_token, token_expiration_epoch):
  access_token, token_expiration_epoch = check_token_expiration(access_token, token_expiration_epoch)

  # GET basic info all computers
  url = f"{JAMF_URL}/JSSResource/computers/subset/basic"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers, verify=False)
  return response, access_token, token_expiration_epoch

def get_computers_userandlocation(access_token, token_expiration_epoch):
  access_token, token_expiration_epoch = check_token_expiration(access_token, token_expiration_epoch)

  # GET userAndLocation all computers
  url = f"{JAMF_URL}/api/v2/computers-inventory?section=USER_AND_LOCATION&page=0&page-size=2000&sort=id%3Aasc"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers, verify=False)

  return response, access_token, token_expiration_epoch

def combine_computers(computers_response, computers_userandlocation_response):
  computers_json = {}
  computers_json["computers"] = computers_response.json().get("computers", [])
  computers_users_json = computers_userandlocation_response.json().get("results", [])
  total = 0
  for c in computers_json["computers"]:
    total += 1
    c["realname"], c["email"], c["position"] = None, None, None
    for cu in computers_users_json:
      if c["id"] == int(cu["id"]):
        cu_data = cu["userAndLocation"]
        c["realname"] = cu_data["realname"]
        c["email"] = cu_data["email"]
        c["position"] = cu_data["position"]
        break

  computers_json["total"] = total
  computers_json["max_id"] = max([c["id"] for c in computers_json.get("computers", [])]) if total > 0 else 0
  return computers_json

def get_devices(access_token, token_expiration_epoch):
  access_token, token_expiration_epoch = check_token_expiration(access_token, token_expiration_epoch)

  # GET all mobile devices
  url = f"{JAMF_URL}/JSSResource/mobiledevices"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers, verify=False)
  return response, access_token, token_expiration_epoch

def get_devices_userandlocation(access_token, token_expiration_epoch):
  access_token, token_expiration_epoch = check_token_expiration(access_token, token_expiration_epoch)

  # GET userAndLocation all computers
  url = f"{JAMF_URL}/api/v2/mobile-devices/detail?section=USER_AND_LOCATION&page=0&page-size=2000&sort=deviceId%3Aasc"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers, verify=False)

  return response, access_token, token_expiration_epoch

def combine_devices(devices_response, devices_userandlocation_response):
  devices_json = {}
  devices_json["devices"] = devices_response.json().get("mobile_devices", [])
  devices_users_json = devices_userandlocation_response.json().get("results", [])
  total = 0
  for d in devices_json["devices"]:
    total += 1
    d["realname"], d["email"], d["position"] = None, None, None
    for du in devices_users_json:
      if d["id"] == int(du["mobileDeviceId"]):
        du_data = du["userAndLocation"]
        d["realname"] = du_data["realName"]
        d["email"] = du_data["emailAddress"]
        d["position"] = du_data["position"]
        break

  devices_json["total"] = total
  devices_json["max_id"] = max([d["id"] for d in devices_json.get("devices", [])]) if total > 0 else 0
  return devices_json

# ==================================================================================

def main():
  # create access token
  access_token, expires_in = get_token()
  token_expiration_epoch = int(time.time()) + expires_in
  print(f"Token valid for {expires_in} seconds")

  # print jamf pro version
  version_url = f"{JAMF_URL}/api/v1/jamf-pro-version"
  headers = {"Authorization": f"Bearer {access_token}"}
  version = requests.get(version_url, headers=headers, verify=False)
  print("Jamf Pro version:", version.json()["version"])

  # # get basic info for all computers
  # computers_url = f"{JAMF_URL}/JSSResource/computers/subset/basic"
  # headers = {
  #   "accept": "application/json",
  #   "authorization": f"Bearer {access_token}"
  # }
  # response = requests.get(computers_url, headers=headers, verify=False)
  # response_json = response.json()
  # total = 0
  # for computer in response_json.get("computers", []):
  #   total += 1
  # response_json["total"] = total
  # response_json["max_id"] = max([c["id"] for c in response_json.get("computers", [])]) if total > 0 else 0

  # get info for all computers
  computers, access_token, token_expiration_epoch  = get_computers_basic(access_token, token_expiration_epoch)
  computers_users, access_token, token_expiration_epoch  = get_computers_userandlocation(access_token, token_expiration_epoch)
  computers_json = combine_computers(computers, computers_users)

  # get info for all mobile devices
  devices, access_token, token_expiration_epoch = get_devices(access_token, token_expiration_epoch)
  devices_users, access_token, token_expiration_epoch = get_devices_userandlocation(access_token, token_expiration_epoch)
  devices_json = combine_devices(devices, devices_users)

  # write to file
  if not os.path.exists("data"):
    os.makedirs("data")

  with open("data/response_computers.json", "w") as f:
    f.write(json.dumps(computers_json, indent=2))
  print("--- Jamf computers saved to ./data/response_computers.json ---")

  with open("data/response_devices.json", "w") as f:
    f.write(json.dumps(devices_json, indent=2))
  print("--- Jamf devices saved to ./data/response_devices.json ---")

  # kill access token
  invalidate_token(access_token)
  print("Done query_jamf.py\n")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
