from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
import requests
import asyncio
from dotenv import load_dotenv
import os
import logging

load_dotenv(r"")


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE"),
    filemode='a'
)



class Metrics(BaseModel):
    timestamp : str
    cpu : float
    cpu_idle: float
    total_ram: float
    ram_used: float
    disk_usage: float
    network_in: float
    network_out: float
    live_connections: int
    window_id: int

mlapi = FastAPI()

@mlapi.post("/clean")
async def mlfunc(metrics: Metrics):

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




    if cpu>70:

        try:
            await asyncio.sleep(50)

            if(cpu >= 80):
                message = "P"

            else:

                message = "NP"

            payload = {

                "message": message
            }

            url = ""
            requests.post(url,json=payload)

        except Exception as e:

            logging.debug("ML api caused a error")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{str(e)}"
            )










