from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging
import joblib
from pathlib import Path
import pandas as pd
from setting.loggers import LoggerFactory
from setting.conifg import settings
from functions.supporters.file_handel import File

logger = LoggerFactory.get_logger(
    name="prediction",
    log_file=settings.LOG_FILE_PREDCITION,
    level=logging.INFO
)


router = APIRouter()


class CleanMetrics(BaseModel):
    timestamp: str
    cpu: float
    cpu_idle: float
    live_connections: int
    window_id: int
    client_id: str
    req_id: str




@router.post("/prediction")
async def mlfunc(metrics: CleanMetrics, request: Request):
    cpu = metrics.cpu
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = request.state.req_id
    cpu_idle = metrics.cpu_idle

    logger.info(
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

        base_file = settings.FILE

        client_file = Path(f"{base_file}/{client_id}/file.csv")

        df = pd.read_csv(client_file)

        ml = Path(f"{base_file}/{client_id}/model.pkl")
        model = joblib.load(ml)

    except Exception:

        logger.exception("Error caused during loading the model/files",
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

        logger.exception("Error caused during setting up the data for prediction",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise HTTPException(
            status_code=500,
            detail="ml_dataset_load_failed"
        )

    try:

        prediction = model.predict(X_now)[0]

    except Exception:

        logger.exception("Error caused during prediction",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise HTTPException(
            status_code=500,
            detail="prediction failed"
        )

    await File.file_write(logger,cpu, cpu_idle, live_connections,client_file,client_id,req_id)

    return prediction