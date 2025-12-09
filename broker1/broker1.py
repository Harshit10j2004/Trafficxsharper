from fastapi import FastAPI,Form
import mysql.connector
import logging
from pydantic import BaseModel
import os

# con = mysql.connector.connect(
#             host= "localhost",
#             user = "root",
#             password = "Harshit@1234",
#             database = "client_info"
#
#         )
#
# cursor = con.cursor()

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

    row = [timestamp,cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,client_id]

    with open(file,"a") as f:

       f.write(",".join(str(v) for v in row) + "\n")


    # query = f"select name from client_info where client is = %s",(client_id,)
    #
    # cursor.execute(query)
    # answer = cursor.fetchone()
    # print(answer)