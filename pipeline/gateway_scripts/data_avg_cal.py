import glob
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timezone
from dotenv import load_dotenv
from pathlib import Path

retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET", "POST"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

load_dotenv("/home/ubuntu/tsx/sysdata/data.env")

LOCATION = Path(os.getenv("FILE"))
Web_file = Path(os.getenv("webfile"))
Last_data = Path(os.getenv("last_path"))
SERVER_INFO = Path(os.getenv("SERV_INFO"))
TOTAL_SERVER_COUNT = Path(os.getenv("SERV_CNT"))
URL = os.getenv("URL")
CLIENT_ID = os.getenv("CLIENT_ID")

def on_missing(node_id):
    print(f"[MISSING NODE DETECTED] {node_id}")


def read_expected_servers():
    if not SERVER_INFO.exists():
        return set()

    with open(SERVER_INFO) as f:
        return {line.strip() for line in f if line.strip()}

def read_current_servers():
    if not LOCATION.exists():
        return set()
    return {
        p.stem
        for p in LOCATION.iterdir()
        if p.is_file() and p.suffix == ".log"
    }

def detect_missing(expected, current):
    missing = expected - current
    for node in missing:
        on_missing(node)
    return missing

def sync_server_info():
    current_servers = read_current_servers()
    expected_servers = read_expected_servers()


    new_servers = current_servers - expected_servers

    if not new_servers:
        return

    SERVER_INFO.touch(exist_ok=True)
    with open(SERVER_INFO, "a") as f:
        for server in new_servers:
            f.write(server + "\n")

def for_backends():
    v = [0.0] * 8
    count = 0

    for file_path in glob.glob(f"{LOCATION}/*.log"):
        try:
            with open(file_path) as f:
                line = f.read().strip()

            parts = line.split(",")
            if len(parts) != 8:
                continue

            values = list(map(float, parts))

            for i in range(8):
                v[i] += values[i]

            count += 1

        except Exception:
            continue

    if count > 0:
        v = [x / count for x in v]

    return v,count

def load_last():

    try:

        with open(Last_data,"r") as f:
            line = f.read().strip()

            if not line:

                update_load(0,0)
                return 0.0, 0.0
        accepts, request = map(float, line.split())
        return  accepts, request
    except Exception as e:
        print("issue in load_last")

        return 0.0,0.0

def update_load(accepts,request):

    try:

        with open(Last_data,"w") as f:

            f.write(f"{int(accepts)} {int(request)}\n")



    except Exception as e:

        print(e)

def webser():

    w = [0.0] * 7
    count_w = 0

    for i in glob.glob(f"{Web_file}/*.log"):
        try:

            with open(i) as f:

                line = f.read().strip()

            parts = line.split(",")
            if len(parts) != 7:
                continue

            values = list(map(float, parts))

            for j in range(7):
                w[j] += values[j]

            count_w+=1

        except Exception as e:
            print(e)

    return w,count_w



current_servers = read_current_servers()
sync_server_info()
expected_servers = read_expected_servers()

missing_servers = detect_missing(expected_servers, current_servers)

server_expected = len(expected_servers)
server_responded = len(current_servers)

if TOTAL_SERVER_COUNT.exists():
    with open(TOTAL_SERVER_COUNT, "r+") as f:
        try:
            prev = int(f.read().strip())
        except:
            prev = 0

        if server_responded > prev:
            f.seek(0)
            f.truncate()
            f.write(str(server_responded))

now = datetime.now(timezone.utc)

v, backend_count = for_backends()

w, web_count= webser()

accepts = w[1]
request = w[3]

Time = 180

last_accepts , last_request = load_last()

rps = (request - last_request) / Time
conn_rate = (accepts - last_accepts) / Time
pressure = w[6] + w[4]
rps_per_node = rps / max(web_count, 1)


print(rps)
print(conn_rate)

update_load(accepts, request)


if not v:
    v = [0.0] * 8

payload = {
    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
    "freeze_window": int(now.timestamp()),
    "client_id": str(CLIENT_ID),

    "cpu_percantage": v[0],
    "cpu_idle_percent": v[1],
    "total_ram": v[2],
    "ram_used": v[3],
    "disk_usage_percent": v[4],
    "network_in": v[5],
    "network_out": v[6],
    "live_connections": int(v[7]),

    "rps": rps,
    "conn_rate": conn_rate,
    "queue_pressure": pressure,
    "rps_per_node": rps_per_node,

    "server_expected": server_expected,
    "server_responded": server_responded,
    "missing_server": list(missing_servers)
}

print(payload)

try:
    r = session.post(URL, json=payload, timeout=3)
    print(f"[SENT] status={r.status_code}")
except Exception as e:
    print(f"[ERROR] {e}")
