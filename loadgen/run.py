import os
import time
import requests

TARGET_URL = os.getenv("TARGET_URL", "http://demo-app.default.svc.cluster.local")
REQUEST_INTERVAL = float(os.getenv("REQUEST_INTERVAL", "0.2"))

def generate_load():
    print(f"Starting load generation against {TARGET_URL}...")
    while True:
        try:
            response = requests.get(TARGET_URL, timeout=5)
            print(f"Request sent. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        time.sleep(REQUEST_INTERVAL)

if __name__ == "__main__":
    generate_load()
