from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime , timezone
import os
import logging
import mysql.connector
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
    live_connections: int
    server_expected: int
    server_responded: int
    missing_server: list[str]


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
                user = os.getenv("DB_USER"),
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



    timestamp = metrics.timestamp
    client_ts = datetime.strptime(metrics.timestamp,"%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = abs((now - client_ts).total_seconds())

    ALLOWED_SKEW = 60

    if delta > ALLOWED_SKEW:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Timestamp out of sync"
        )



    cpu = metrics.cpu_percantage
    cpu_idle = metrics.cpu_idle_percent
    totalram = metrics.total_ram
    ramused = metrics.ram_used
    diskusage = metrics.disk_usage_percent
    networkin = metrics.network_in
    networkout = metrics.network_out
    client_id = metrics.client_id
    freeze_window = metrics.freeze_window
    live_connections = metrics.live_connections
    server_expected = metrics.server_expected
    server_responded = metrics.server_responded
    missing_server = metrics.missing_server

    missing_server_count = None

    if(len(missing_server) == 0):
        missing_server_count = 0
    else:

        missing_server_count = len(missing_server)

    row = [timestamp, cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout,live_connections, client_id,server_expected,server_responded,missing_server]

    file = os.getenv("TOTAL_AVG")
    test_file = os.getenv("TEST")

    try:

        query2 = "select client_name,thresold,l_buff,h_buff,email,ami,server_type from client_info where client_id = %s"

        cursor.execute(query2, (client_id,))

        db = cursor.fetchone()

        if not db:
            logging.debug(f"loading client from db caused issue!! ")
            raise HTTPException(status_code=404, detail="Client not found")

        client_name = db[0]
        threshold = db[1]
        buffer_z = db[2]
        buffer_lower = db[3]
        email = db[4]
        ami = db[5]
        server_type = db[6]


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

            if(server_expected < 10):
                total_instance = 1
            else:
                total_instance = int(server_expected/10)

            payload = {
                "message": message,
                "email": email,
                "ami": ami,
                "server_type": server_type,
                "total_instance": total_instance


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


