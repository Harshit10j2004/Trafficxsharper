from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import joblib
import requests
import os
import logging

load_dotenv(r"/home/ubuntu/tsx/data/data.env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - req_id=%(req_id)s client_id=%(client_id)s - %(message)s',
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
    client_id: str
    missing_server_count: int
    req_id: str
    conn_rate: float
    queue_pressure: float
    rps: float


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
    client_id: str
    missing_server_count: int
    req_id: str
    conn_rate: float
    queue_pressure: float
    rps: float


mlapi = FastAPI()


@mlapi.post("/clean")
async def mlfunc(metrics: CleanMetrics):
    cpu = metrics.cpu
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = metrics.req_id
    queue_pressure = metrics.queue_pressure
    rps = metrics.rps

    logging.info(
        "ml_api_pred request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    print(f"REQUEST ARRIVED {client_id} and generated requested id is {req_id}")

    try:

        base_file = os.getenv("FILE")

        client_file = Path(f"{base_file}/{client_id}/file.csv")

        df = pd.read_csv(client_file)

        ml = Path(f"{base_file}/{client_id}/model.pkl")
        model = joblib.load(ml)

    except Exception:

        logging.exception("Error caused during loading the model/files",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise HTTPException(
            status_code=500,
            detail="ml_data_load_failed"
        )

    try:

        latest = {}

        latest["cpu_percentage"] = cpu
        latest["rps"] = rps
        latest["live_connections"] = live_connections
        latest["queue_pressure"] = queue_pressure
        if len(df) < 5:
            raise ValueError("Need at least 5 historical windows for lag features")

        for lag in [1, 2, 3, 4, 5]:
            latest[f"cpu_lag{lag}"] = df.iloc[-lag]["cpu_percentage"]
            latest[f"rps_lag{lag}"] = df.iloc[-lag]["rps"]
            latest[f"live_connection_lag{lag}"] = df.iloc[-lag]["live_connections"]

        window_df = df.tail(5)

        latest["cpu_roll_mean"] = window_df["cpu_percentage"].mean()
        latest["cpu_roll_std"] = window_df["cpu_percentage"].std()
        latest["rps_roll_mean"] = window_df["rps"].mean()

        X_now = pd.DataFrame([latest])

    except Exception:

        logging.exception("Error caused during setting up the data for prediction",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise HTTPException(
            status_code=500,
            detail="ml_dataset_load_failed"
        )

    try:

        prediction = model.predict(X_now)[0]

    except Exception:

        logging.exception("Error caused during prediction",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise HTTPException(
            status_code=500,
            detail="prediction failed"
        )

    try:

        rows = [cpu, rps, queue_pressure, live_connections]

        with open(client_file, "a") as f:
            f.write(",".join(map(str, rows)) + "\n")

    except Exception:

        logging.exception("Error caused during data writing",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

    return prediction


@mlapi.post("/insert")
async def inserting(metrics: InsertMetrics):
    cpu = metrics.cpu
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = metrics.req_id
    queue_pressure = metrics.queue_pressure
    rps = metrics.rps

    logging.info(
        "ml_api_insert request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    print(f"REQUEST ARRIVED {client_id} and generated requested id is {req_id}")

    rows = [cpu, rps, queue_pressure, live_connections]

    base_file = os.getenv("FILE")

    client_file = Path(f"{base_file}/{client_id}/file.csv")

    try:

        rows = [cpu, rps, queue_pressure, live_connections]

        with open(client_file, "a") as f:
            f.write(",".join(map(str, rows)) + "\n")

    except Exception:

        logging.exception("Error caused during data writing",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise

