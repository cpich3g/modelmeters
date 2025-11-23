import requests
import json

url = "https://apim-yiaefkyinmgwy.azure-api.net/msdocs"

payload = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 2
}

try:
    print(f"Sending to {url}...")
    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(e)
