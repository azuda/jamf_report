# https://developer.jamf.com/jamf-pro/docs/client-credentials
# https://developer.jamf.com/jamf-pro/reference/findcomputersbasic

from dotenv import load_dotenv
import os
import requests
import time

# source .env
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
JAMF_URL = os.getenv("JAMF_URL")

_missing = [name for name, val in [("CLIENT_ID", CLIENT_ID), ("CLIENT_SECRET", CLIENT_SECRET), ("JAMF_URL", JAMF_URL)] if not val]
if _missing:
  raise SystemExit(f"jamf_credential.py: missing required .env values: {', '.join(_missing)}")

def get_token():
  url = f"{JAMF_URL}/api/oauth/token"
  data = {
    "client_id": CLIENT_ID,
    "grant_type": "client_credentials",
    "client_secret": CLIENT_SECRET
  }
  headers = {"Content-Type": "application/x-www-form-urlencoded"}
  response = requests.post(url, data=data, headers=headers, timeout=30)
  response.raise_for_status()
  return response.json()["access_token"], response.json()["expires_in"]

def invalidate_token(token):
  url = f"{JAMF_URL}/api/v1/auth/invalidate-token"
  headers = {"Authorization": f"Bearer {token}"}
  response = requests.post(url, headers=headers, timeout=30)
  if response.status_code == 204:
    print("Token successfully invalidated")
  elif response.status_code == 401:
    print("Token already invalid")
  else:
    print(f"Unexpected status invalidating token: {response.status_code} {response.text[:200]}")

# auto renew token if it expires in < 15 secs
def check_token_expiration(access_token, token_expiration_epoch):
  current_epoch = int(time.time())
  if current_epoch > token_expiration_epoch - 15:
    access_token, expires_in = get_token()
    token_expiration_epoch = current_epoch + expires_in
    print(f"Token valid for {expires_in} seconds")
  return access_token, token_expiration_epoch
