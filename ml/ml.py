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
    live_connections: int
    window_id: int
    client_id: str
    req_id: str


class CleanMetrics(BaseModel):
    timestamp: str
    cpu: float
    cpu_idle: float
    live_connections: int
    window_id: int
    client_id: str
    req_id: str


mlapi = FastAPI()


@mlapi.post("/clean")
async def mlfunc(metrics: CleanMetrics):
    cpu = metrics.cpu
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = metrics.req_id
    cpu_idle = metrics.cpu_idle

    logging.info(
        "ml_api_pred request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    FEATURE_ORDER = [
        'cpu_percentage',
        'cpu_idle_percent',
        'live_connections',
        'cpu_lag1', 'cpu_lag2', 'cpu_lag3', 'cpu_lag4', 'cpu_lag5',
        'live_connection_lag1', 'live_connection_lag2',
        'live_connection_lag3', 'live_connection_lag4',
        'live_connection_lag5',
        'cpu_roll_mean', 'cpu_roll_std',
        'cpu_delta_1', 'live_connection_delta_1'
    ]

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

        if len(df) < 6:
            raise ValueError("Need at least 6 historical windows for lag features")


        latest["cpu_percentage"] = cpu
        latest["live_connections"] = live_connections
        latest["cpu_idle_percent"] = cpu_idle


        for lag in [1, 2, 3, 4, 5]:
            latest[f"cpu_lag{lag}"] = df.iloc[-lag]["cpu_percentage"]
            latest[f"live_connection_lag{lag}"] = df.iloc[-lag]["live_connections"]


        window_df = df.tail(5)
        latest["cpu_roll_mean"] = window_df["cpu_percentage"].mean()
        latest["cpu_roll_std"] = window_df["cpu_percentage"].std()


        latest["cpu_delta_1"] = cpu - df.iloc[-1]["cpu_percentage"]
        latest["live_connection_delta_1"] = live_connections - df.iloc[-1]["live_connections"]

        X_now = pd.DataFrame([latest])

        for col in FEATURE_ORDER:
            if col not in X_now.columns:
                X_now[col] = 0.0
                logging.info(f"Model have recieved a buffer value {client_id} {req_id}")


        X_now = X_now[FEATURE_ORDER]

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

        rows = [cpu,cpu_idle, live_connections]

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
    cpu_idle = metrics.cpu_idle


    logging.info(
        "ml_api_insert request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    print(f"REQUEST ARRIVED {client_id} and generated requested id is {req_id}")


    base_file = os.getenv("FILE")

    client_file = Path(f"{base_file}/{client_id}/file.csv")

    try:

        rows = [cpu,cpu_idle, live_connections]

        with open(client_file, "a") as f:
            f.write(",".join(map(str, rows)) + "\n")

    except Exception:

        logging.exception("Error caused during data writing",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise

