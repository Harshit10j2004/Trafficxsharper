from fastapi import APIRouter,Request
from pydantic import BaseModel
import logging
from pathlib import Path
from setting.loggers import LoggerFactory
from setting.conifg import settings
from functions.supporters.file_handel import File

logger = LoggerFactory.get_logger(
    name="insertion",
    log_file=settings.LOG_FILE_INSERTION,
    level=logging.INFO
)


router = APIRouter()

class InsertMetrics(BaseModel):
    timestamp: str
    cpu: float
    cpu_idle: float
    live_connections: int
    window_id: int
    client_id: str
    req_id: str


@router.post("/insert")
async def inserting(metrics: InsertMetrics,request: Request):
    cpu = metrics.cpu
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    live_connections = metrics.live_connections
    client_id = metrics.client_id
    req_id = request.state.req_id
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

    await File.file_write(logger,cpu, cpu_idle, live_connections,client_file,client_id,req_id)
