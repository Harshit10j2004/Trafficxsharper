from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import requests
import os
import logging

load_dotenv(r"/home/ubuntu/tsx/data/data.env")


logging.basicConfig(
    level=logging.DEBUG,
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
            email = "onxy.harsh123@gmail.com"

            if(cpu >= 80):
                message = "P"

            else:

                message = "NP"

            payload = {

                "message": message,
                "email": email,
                "total_inc": 1
            }

            url = os.getenv("URL")
            session.post(url,json=payload)

        except Exception as e:

            logging.debug("ML api caused a error")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{str(e)}"
            )










