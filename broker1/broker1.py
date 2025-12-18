from fastapi import FastAPI,Form
import mysql.connector
from pydantic import BaseModel
import requests


class Metrics(BaseModel):

    timestamp : str
    cpu_percantage : float
    cpu_idle_percent: float
    total_ram: float
    ram_used: float
    disk_usage_percent: float
    network_in: float
    network_out: float
    client_id : int
    freeze_window: int


broker1api = FastAPI()

@broker1api.post("/ingest")
async def broker1func(metrics: Metrics):

    con = mysql.connector.connect(
            host= "",
            user = "admin",
            password = "",
            database = "tsx"

        )

    cursor = con.cursor()


    cpu = metrics.cpu_percantage
    cpu_idle = metrics.cpu_idle_percent
    totalram = metrics.total_ram
    ramused = metrics.ram_used
    diskusage = metrics.disk_usage_percent
    networkin = metrics.network_in
    networkout = metrics.network_out
    client_id = metrics.client_id
    timestamp = metrics.timestamp
    freeze_window = metrics.freeze_window

    print(cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,client_id,freeze_window)
    row = [timestamp, cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout, client_id]

    file = "/home/ubuntu/tsx/data/totalavg.txt"
    test_file = "/home/ubuntu/tsx/data/test.txt"

    file_name = f"{freeze_window}.log"
    freeze_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/{file_name}"

    with open(freeze_window_file,"w") as f:
        f.write(",".join(map(str, row)) + "\n")

    with open(file,"a") as f:

       f.write(",".join(str(v) for v in row) + "\n")


    query2 = "select client_name,thresold,l_buff,h_buff from client_info where client_id = %s"


    cursor.execute(query2, (client_id,))

    row = cursor.fetchone()

    client_name = row[0]
    threshold = row[1]
    buffer_z = row[2]
    buffer_lower = row[3]



    with open(test_file,"a") as f:

       f.write(client_name)

    if cpu >= threshold-buffer_lower:

        payload = {
            "timestamp": timestamp,
            "cpu": cpu,
            "cpu_idle": cpu_idle,
            "total_ram": totalram,
            "ram_used": ramused,
            "disk_usage": diskusage,
            "network_in": networkin,
            "network_out": networkout,
            "window_id": freeze_window

        }

        url = ""

        requests.post(url,json=payload)

    elif cpu >= threshold+buffer_z:

        message = "PANIC"

        payload = {


            "message": message

        }

        url = ""

        requests.post(url, json=payload)

    return {"status": "accepted"}
