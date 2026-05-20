from fastapi import APIRouter
from pydantic import BaseModel
import logging
from pathlib import Path
from ml.setting.loggers import LoggerFactory
from ml.setting.conifg import settings


logger = LoggerFactory.get_logger(
    name="insertion",
    log_file=settings.LOG_FILE_INSERTION,
    level=logging.INFO
)


router = APIRouter

class InsertMetrics(BaseModel):
    timestamp: str
    cpu: float
    cpu_idle: float
    live_connections: int
    window_id: int
    client_id: str
    req_id: str


@router.post("/insert")
async def inserting(metrics: InsertMetrics):
    cpu = metrics.cpu
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = metrics.req_id
    cpu_idle = metrics.cpu_idle


    logger.info(
        "ml_api_insert request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
        }
    )

    print(f"REQUEST ARRIVED {client_id} and generated requested id is {req_id}")


    base_file = settings.FILE

    client_file = Path(f"{base_file}/{client_id}/file.csv")

    try:

        rows = [cpu,cpu_idle, live_connections]

        with open(client_file, "a") as f:
            f.write(",".join(map(str, rows)) + "\n")

    except Exception:

        logger.exception("Error caused during data writing",
                          extra={"client_id": client_id, "req_id": req_id}
                          )

        raise

