# query_jamf.py

from jamf_credential import JAMF_URL, get_token, invalidate_token, check_token_expiration
import json
import os
import requests
import time
import urllib3

"""
- get info on all computers + mobile devices via jamf api
- sort + combine relevant info into dicts
- write result dicts to `data/response_computers.json` and `data/response_devices.json`
"""

# ==================================================================================

def get(endpoint, access_token, token_expiration_epoch):
  access_token, token_expiration_epoch = check_token_expiration(access_token, token_expiration_epoch)

  url = f"{JAMF_URL}{endpoint}"
  headers = {
    "accept": "application/json",
    "authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers, verify=False)
  return response, access_token, token_expiration_epoch

def combine_computers(computers_response, computers_userandlocation_response, computers_purchasing_response, computers_extension_attributes_response):
  computers_json = {}
  computers_json["computers"] = computers_response.json().get("computers", [])
  computers_users_json = computers_userandlocation_response.json().get("results", [])
  computers_purchasing_json = computers_purchasing_response.json().get("results", [])
  computers_extension_attributes_json = computers_extension_attributes_response.json().get("results", [])
  total = 0

  for c in computers_json["computers"]:
    total += 1
    c["realname"], c["email"], c["position"], c["purchase_price"], c["purchase_date"], c["report"] = None, None, None, None, None, None
    for cu in computers_users_json:
      if c["id"] == int(cu["id"]):
        cu_data = cu["userAndLocation"]
        c["realname"] = cu_data["realname"]
        c["email"] = cu_data["email"]
        c["position"] = cu_data["position"]
        break
    for cp in computers_purchasing_json:
      if c["id"] == int(cp["id"]):
        cp_data = cp["purchasing"]
        c["purchase_price"] = cp_data["purchasePrice"]
        c["purchase_date"] = cp_data["poDate"]
        break
    for cea in computers_extension_attributes_json:
      if c["id"] == int(cea["id"]):
        cea_data = cea["extensionAttributes"]
        report = [c for c in cea_data if c["name"] == "Rundle Device Report"][0]["values"] if any(c["name"] == "Rundle Device Report" for c in cea_data) else None
        c["report"] = report[0] if report and len(report) > 0 else None
        break

  computers_json["total"] = total
  computers_json["max_id"] = max([c["id"] for c in computers_json.get("computers", [])]) if total > 0 else 0
  return computers_json

def combine_devices(devices_response, devices_userandlocation_response, devices_general_response, devices_purchasing_response):
  devices_json = {}
  devices_json["devices"] = devices_response.json().get("mobile_devices", [])
  devices_users_json = devices_userandlocation_response.json().get("results", [])
  devices_general_json = devices_general_response.json().get("results", [])
  devices_purchasing_json = devices_purchasing_response.json().get("results", [])

  total = 0
  for d in devices_json["devices"]:
    total += 1
    d["date"], d["os"], d["realname"], d["email"], d["position"], d["department"], d["purchase_price"], d["purchase_date"] = None, None, None, None, None, None, None, None
    for dg in devices_general_json:
      if d["id"] == int(dg["mobileDeviceId"]):
        dg_data = dg["general"]
        d["date"] = dg_data["lastInventoryUpdateDate"]
        d["os"] = dg_data["osVersion"]
        break
    for du in devices_users_json:
      if d["id"] == int(du["mobileDeviceId"]):
        du_data = du["userAndLocation"]
        d["realname"] = du_data["realName"]
        d["email"] = du_data["emailAddress"]
        d["position"] = du_data["position"]
        d["department"] = du_data["department"]
        break
    for dp in devices_purchasing_json:
      if d["id"] == int(dp["mobileDeviceId"]):
        dp_data = dp["purchasing"]
        d["purchase_price"] = dp_data["purchasePrice"]
        d["purchase_date"] = dp_data["poDate"]
        break

  devices_json["total"] = total
  devices_json["max_id"] = max([d["id"] for d in devices_json.get("devices", [])]) if total > 0 else 0
  return devices_json

# ==================================================================================

def main():
  # create jamf access token
  access_token, expires_in = get_token()
  token_expiration_epoch = int(time.time()) + expires_in
  print(f"Token valid for {expires_in} seconds")

  # print jamf pro version
  version_url = f"{JAMF_URL}/api/v1/jamf-pro-version"
  headers = {"Authorization": f"Bearer {access_token}"}
  version = requests.get(version_url, headers=headers, verify=False)
  print("Jamf Pro version:", version.json()["version"])

  # get info for all computers
  computers, access_token, token_expiration_epoch  = get("/JSSResource/computers/subset/basic", access_token, token_expiration_epoch)
  computers_users, access_token, token_expiration_epoch  = get("/api/v2/computers-inventory?section=USER_AND_LOCATION&page=0&page-size=2000&sort=id%3Aasc", access_token, token_expiration_epoch)
  computers_purchasing, access_token, token_expiration_epoch = get("/api/v2/computers-inventory?section=PURCHASING&page=0&page-size=2000&sort=id%3Aasc", access_token, token_expiration_epoch)
  computers_extension_attributes, access_token, token_expiration_epoch = get("/api/v2/computers-inventory?section=EXTENSION_ATTRIBUTES&page=0&page-size=2000&sort=id%3Aasc", access_token, token_expiration_epoch)
  computers_json = combine_computers(computers, computers_users, computers_purchasing, computers_extension_attributes)

  # get info for all mobile devices
  devices, access_token, token_expiration_epoch = get("/JSSResource/mobiledevices", access_token, token_expiration_epoch)
  devices_users, access_token, token_expiration_epoch = get("/api/v2/mobile-devices/detail?section=USER_AND_LOCATION&page=0&page-size=2000&sort=deviceId%3Aasc", access_token, token_expiration_epoch)
  devices_general, access_token, token_expiration_epoch = get("/api/v2/mobile-devices/detail?section=GENERAL&page=0&page-size=2000&sort=deviceId%3Aasc", access_token, token_expiration_epoch)
  devices_purchasing, access_token, token_expiration_epoch = get("/api/v2/mobile-devices/detail?section=PURCHASING&page=0&page-size=2000&sort=deviceId%3Aasc", access_token, token_expiration_epoch)
  devices_json = combine_devices(devices, devices_users, devices_general, devices_purchasing)

  # kill jamf access token
  invalidate_token(access_token)

  # raw api responses for debug
  if not os.path.exists("debug"):
    os.makedirs("debug")
  with open("debug/c.json", "w") as f:
    f.write(json.dumps(computers.json(), indent=2))
  with open("debug/cu.json", "w") as f:
    f.write(json.dumps(computers_users.json(), indent=2))
  with open("debug/cp.json", "w") as f:
    f.write(json.dumps(computers_purchasing.json(), indent=2))
  with open("debug/cea.json", "w") as f:
    f.write(json.dumps(computers_extension_attributes.json(), indent=2))
  with open("debug/d.json", "w") as f:
    f.write(json.dumps(devices.json(), indent=2))
  with open("debug/du.json", "w") as f:
    f.write(json.dumps(devices_users.json(), indent=2))
  with open("debug/dg.json", "w") as f:
    f.write(json.dumps(devices_general.json(), indent=2))
  with open("debug/dp.json", "w") as f:
    f.write(json.dumps(devices_purchasing.json(), indent=2))

  # write to file
  if not os.path.exists("data"):
    os.makedirs("data")
  with open("data/response_computers.json", "w") as f:
    f.write(json.dumps(computers_json, indent=2))
  print("--- Jamf computers saved to ./data/response_computers.json ---")
  with open("data/response_devices.json", "w") as f:
    f.write(json.dumps(devices_json, indent=2))
  print("--- Jamf devices saved to ./data/response_devices.json ---")

  print("\nDone query_jamf.py")

# ==================================================================================

if __name__ == "__main__":
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
