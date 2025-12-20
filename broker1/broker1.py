from fastapi import FastAPI,HTTPException,status
import mysql.connector
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
import logging

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
    live_connections: int


broker1api = FastAPI()


load_dotenv(r"/home/ubuntu/tsx/data/data.env")


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE"),
    filemode='a'
)

@broker1api.post("/ingest")
async def broker1func(metrics: Metrics):



    try:

        con = mysql.connector.connect(
                host= os.getenv("DB_HOST"),
                user = os.getenv("USER"),
                password = os.getenv("PASSWORD"),
                database = os.getenv("DATABASE")

            )

        cursor = con.cursor()
    except Exception as e:

        logging.error(f"Connection to database caused issue!!! {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )




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
    live_connections = metrics.live_connections

    row = [timestamp, cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout,live_connections, client_id]

    file = os.getenv("TOTAL_AVG")
    test_file = os.getenv("TEST")

    try:

        query2 = "select client_name,thresold,l_buff,h_buff from client_info where client_id = %s"

        cursor.execute(query2, (client_id,))

        db = cursor.fetchone()

        if not db:
            logging.debug(f"loading client from db caused issue!! ")
            raise HTTPException(status_code=404, detail="Client not found")

        client_name = db[0]
        threshold = db[1]
        buffer_z = db[2]
        buffer_lower = db[3]

    finally:
        cursor.close()
        con.close()

    try:

        file_name = f"{freeze_window}.log"
        freeze_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/{file_name}"

        with open(freeze_window_file,"w") as f:
            f.write(",".join(map(str, row)) + "\n")

        with open(file,"a") as f:

           f.write(",".join(str(v) for v in row) + "\n")

        with open(test_file, "a") as f:

            f.write(client_name)

    except Exception as e:

        logging.debug(f"Writing the files caused issue!!! {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"File_writing_fails: {str(e)}"
        )


    if cpu >= threshold+buffer_z:

        try:

            message = "PANIC"

            payload = {
                "message": message
            }

            url = os.getenv("DEC_URL")

            r = requests.post(url, json=payload, timeout=1)
            r.raise_for_status()

        except Exception as e:

            logging.error(f"Sending request to dec_eng api caused issue!!! {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f" dec_eng api not responding: {str(e)}"
            )

    elif cpu >= threshold-buffer_lower:

        try:
            payload = {
                "timestamp": timestamp,
                "cpu": cpu,
                "cpu_idle": cpu_idle,
                "total_ram": totalram,
                "ram_used": ramused,
                "disk_usage": diskusage,
                "network_in": networkin,
                "network_out": networkout,
                "live_connections": live_connections,
                "window_id": freeze_window

            }

            url = os.getenv("ML_URL")

            r = requests.post(url, json=payload, timeout=1)
            r.raise_for_status()


        except Exception as e:

            logging.error(f"Sending request to ml api caused issue!!! {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f" ml api not responding: {str(e)}"

            )

    return {"status": "forwarded"}


