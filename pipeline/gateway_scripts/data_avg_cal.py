import glob
import os
import requests
from datetime import datetime , timezone
from dotenv import load_dotenv
from pathlib import Path


load_dotenv(r"/home/ubuntu/tsx/sysdata/data.env")

missing_ids = set()
location =os.getenv("FILE")
url = os.getenv("URL")
server_info = os.getenv("SERV_INFO")
total_server_count = os.getenv("SERV_CNT")
path = Path(os.getenv("FILE"))

def on_missing(node_id):
    print(f"[MISSING NODE DETECTED] {node_id}")



def missingfile(location,server_info,on_missing):
    with open(server_info) as f:
        expected_ids = {line.strip() for line in f if line.strip()}
    current_ids = {
        p.stem for p in Path(location).iterdir()
        if p.is_file()
    }
    missing_ids = expected_ids - current_ids
    for node_id in missing_ids:
        on_missing(node_id)

    return missing_ids


v1 = v2 = v3 = v4 = v5 = v6 = v7 = v8 = 0
count = 0


with open(server_info, "w") as f:
    for i in glob.glob(f"{location}/*.log"):
        f.write(f"{Path(i).stem}\n")

file_count = sum(1 for p in path.iterdir() if p.is_file())

missing_id = None

with open(total_server_count,"r+") as f:

    number = int(f.read().strip())

    if(file_count>number):

        f.seek(0)
        f.truncate()
        f.write(str(file_count))

    if(file_count<number):
        missing_ids = missingfile(
            location=location,
            server_info=server_info,
            on_missing=on_missing
        )



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
with open(server_info) as f:
    server_expected = sum(1 for line in f if line.strip())

server_responded = file_count


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
    "client_id": os.getenv("CLIENT_ID"),
    "freeze_window": freez_window,
    "server_excepted": server_expected,
    "server_responded": server_responded,
    "missing_server": list(missing_ids)
}
try:
    r = requests.post(url, json=payload,timeout = 3)

    print(f"datasend and {r}")

except Exception as e:

    print(e)