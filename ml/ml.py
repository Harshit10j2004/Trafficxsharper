from fastapi import FastAPI
from pydantic import BaseModel
import requests
import asyncio



class Metrics(BaseModel):
    timestamp : str
    cpu : float
    cpu_idle: float
    total_ram: float
    ram_used: float
    disk_usage: float
    network_in: float
    network_out: float
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



    message = None
    if cpu>70:
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






