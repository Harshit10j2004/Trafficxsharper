import glob
import os

import requests
from datetime import datetime , timezone
from dotenv import load_dotenv

load_dotenv(r"")


location =os.getenv("FILE")
v1 = v2 = v3 = v4 = v5 = v6 = v7 = v8 = 0
count = 0
url = os.getenv("URL")

now = datetime.now(timezone.utc)
timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
freez_window = int((now.timestamp() * 1000)//300)

for file_path in glob.glob(f"{location}/*.log"):
    print(file_path)
    with open(file_path) as f:
        line = f.read().strip()
        parts = line.split(",")


        values = parts

        x1, x2, x3, x4, x5, x6, x7,x8 = map(float, values)

        v1 += x1
        v2 += x2
        v3 += x3
        v4 += x4
        v5 += x5
        v6 += x6
        v7 += x7
        v8 += x8

    count += 1

if count > 0:
    v1 /= count
    v2 /= count
    v3 /= count
    v4 /= count
    v5 /= count
    v6 /= count
    v7 /= count
    v8 /= count

print("Averages:")
print(v1, v2, v3, v4, v5, v6, v7,v8)

payload = {
    "timestamp": timestamp,
    "cpu_percantage": v1,
    "cpu_idle_percent": v2,
    "total_ram": v3,
    "ram_used": v4,
    "disk_usage_percent": v5,
    "network_in": v6,
    "network_out": v7,
    "live_connections": v8,
    "client_id": 3828,
    "freeze_id": freez_window
}
try:
    r = requests.post(url, json=payload,timeout = 3)

    print(f"datasend and {r}")

except Exception as e:

    print(e)