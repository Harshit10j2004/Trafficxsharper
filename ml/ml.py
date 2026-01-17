from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from pathlib import Path
from sklearn.linear_model import LinearRegression
import numpy as np
import requests
import os
import logging

load_dotenv(r"/home/ubuntu/tsx/data/data.env")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE"),
    filemode='a'
)

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



class InsertMetrics(BaseModel):
    timestamp: str
    cpu: float
    cpu_idle: float
    total_ram: float
    ram_used: float
    disk_usage: float
    network_in: float
    network_out: float
    live_connections: int
    window_id: int
    client_id: int
    missing_server_count: int
    req_id: str


class CleanMetrics(BaseModel):
    timestamp: str
    cpu: float
    cpu_idle: float
    total_ram: float
    ram_used: float
    disk_usage: float
    network_in: float
    network_out: float
    live_connections: int
    window_id: int
    client_id: int
    missing_server_count: int
    req_id: str


def count_rows(file_path,client_id,req_id):
    if not file_path.exists():
        return 0

    try:

        with open(file_path, "r") as f:
            return sum(1 for line in f if line.strip())

    except Exception:

        logging.exception("counting rows caused issue",
                          extra={"client_id":client_id, "req_id": req_id}
                          )


def appendin(new_row,FILE_PATH,client_id,req_id):


    rows = []
    MAX_ROWS = 10

    try:


        if FILE_PATH.exists():
            with open(FILE_PATH, "r") as f:
                rows = [line.strip() for line in f if line.strip()]

        rows.append(",".join(map(str, new_row)))


        rows = rows[-MAX_ROWS:]


        with open(FILE_PATH, "w") as f:
            f.write("\n".join(rows) + "\n")

    except Exception:

        logging.exception("Error caused during reading and writing the file at dataset",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

def load_metrics_by_column(FILE_PATH,EXPECTED_COLS,client_id,req_id):
    if not FILE_PATH.exists():
        raise FileNotFoundError("metrics file not found")

    try:

        columns = [[] for _ in range(EXPECTED_COLS)]

        with open(FILE_PATH, "r") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                parts = line.split(",")

                if len(parts) != EXPECTED_COLS:
                    raise ValueError(
                        f"Line {line_no}: expected {EXPECTED_COLS} columns, got {len(parts)}"
                    )

                for i, value in enumerate(parts):
                    columns[i].append(float(value))
    except Exception:

        logging.exception("Error caused during loading the metrics into the columns",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

    return columns


mlapi = FastAPI()

@mlapi.post("/clean")
async def mlfunc(metrics: CleanMetrics):

    cpu = metrics.cpu
    cpu_idle = metrics.cpu_idle
    totalram = metrics.total_ram
    ramused = metrics.ram_used
    diskusage = metrics.disk_usage
    networkin = metrics.network_in
    networkout = metrics.network_out
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = metrics.req_id

    logging.info(
        "ml_api_pred request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    base_file = os.getenv("FILE")

    client_file = Path(f"{base_file}/{client_id}/file.csv")

    row = [cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout, live_connections]

    try:

        columns = load_metrics_by_column(client_file,client_id,req_id, EXPECTED_COLS=8)


        cpu_l = np.array(columns[0])
        cpu_idle_l = np.array(columns[1])
        totalram_l = np.array(columns[2])
        ramused_l = np.array(columns[3])
        diskusage_l = np.array(columns[4])
        networkin_l = np.array(columns[5])
        networkout_l = np.array(columns[6])
        live_connections_l = np.array(columns[7])

        X = np.column_stack((cpu_idle_l,totalram_l,ramused_l,diskusage_l,networkin_l,networkout_l,live_connections_l))

        y = cpu_l

        model = LinearRegression()
        model.fit(X, y)

        n_row = [cpu_idle, totalram, ramused, diskusage, networkin, networkout, live_connections]

        next_window = np.array([n_row])
        next_cpu = model.predict(next_window)[0]

        ret_value = next_cpu



    except Exception:

        ret_value = window_id

        logging.exception("Error caused during data prediction",
                          extra={"client_id": client_id,"req_id": req_id}
                          )

    MAX_ROWS = 10

    try:
        row_count = count_rows(client_file,client_id,req_id)

        if row_count >= MAX_ROWS:

            write_file = appendin(row, client_file,client_id, req_id)

        else:

            with open(client_file, "a") as f:
                f.write(",".join(map(str, row)) + "\n")

    except Exception:

        logging.exception("Error caused during counting rows",
                          extra={"client_id": client_id, "req_id": req_id}

                          )

    return ret_value


@mlapi.post("/insert")
async def inserting(metrics: InsertMetrics):

    cpu = metrics.cpu
    cpu_idle = metrics.cpu_idle
    totalram = metrics.total_ram
    ramused = metrics.ram_used
    diskusage = metrics.disk_usage
    networkin = metrics.network_in
    networkout = metrics.network_out
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = metrics.req_id

    logging.info(
        "ml_api_pred request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    MAX_ROWS = 10

    row = [cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,live_connections]

    base_file = os.getenv("FILE")

    client_file = Path(f"{base_file}/{client_id}/file.csv")

    row_count = count_rows(client_file,client_id,req_id)

    if row_count >= MAX_ROWS:

        write_file = appendin(row,client_file)

    else:

        with open(client_file,"a") as f:
            f.write(",".join(map(str, row)) + "\n")
