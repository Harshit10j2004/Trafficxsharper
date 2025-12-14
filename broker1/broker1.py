from fastapi import FastAPI,Form
import mysql.connector
import logging
from pydantic import BaseModel
import os



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


broker1api = FastAPI()

@broker1api.post("/ingest")
async def broker1func(metrics: Metrics):

    con = mysql.connector.connect(
            host= "",
            user = "",
            password = "",
            database = ""

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
    print(cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,client_id)
    file = "/home/ubuntu/tsx/data/totalavg.txt"
    test_file = "/home/ubuntu/tsx/data/test.txt"

    row = [timestamp,cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,client_id]

    with open(file,"a") as f:

       f.write(",".join(str(v) for v in row) + "\n")


    query = "SELECT client_name FROM client_info WHERE client_id = %s"
    cursor.execute(query, (client_id,))
    answer = cursor.fetchone()


    with open(test_file,"a") as f:

       f.write(str(answer[0]) + "\n")