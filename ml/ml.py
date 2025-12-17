from fastapi import FastAPI
from pydantic import BaseModel
import time
import requests


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
    thresold: int

mlapi = FastAPI()

@mlapi.post("/clean")
async def mlfunc(metrics: Metrics):

    cpu = metrics.cpu_percantage
    cpu_idle = metrics.cpu_idle_percent
    totalram = metrics.total_ram
    ramused = metrics.ram_used
    diskusage = metrics.disk_usage_percent
    networkin = metrics.network_in
    networkout = metrics.network_out
    timestamp = metrics.timestamp
    window_id = metrics.window_id
    thresold = metrics.thresold



    if cpu>thresold:
        time.sleep(50)

        if(cpu >= 60):
            message = "NP"

        else:
            message = "P"

        payload = {
            "timestamp": timestamp,
            "cpu": cpu,
            "cpu_idle": cpu_idle,
            "total_ram": totalram,
            "ram_used": ramused,
            "disk_usage": diskusage,
            "network_in": networkin,
            "network_out": networkout,
            "message": message
        }

        url = ""
        requests.post(url,payload)






