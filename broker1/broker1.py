from fastapi import FastAPI,HTTPException,status
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime , timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import logging
import mysql.connector
import requests
import json



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


def scaling(message,email,ami,server_type,server_expected):
    try:



        if (server_expected < 10):
            total_instance = 1
        else:
            total_instance = int(server_expected / 10)

        payload = {
            "message": message,
            "email": email,
            "ami": ami,
            "server_type": server_type,
            "total_instance": total_instance

        }

        url = os.getenv("DEC_URL")

        r = session.post(url, json=payload, timeout=1)
        r.raise_for_status()

    except Exception as e:

        logging.error(f"Sending request to decision engine api caused issue!!! {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f" deceng api not responding: {str(e)}"

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
    global_scale_up_cooldown_seconds = 90

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



        query = "select last_scale_up_time from system_info where client_id = %s"

        cursor.execute(query, (client_id,))

        db = cursor.fetchone()

        if not db:
            logging.debug(f"loading data from db caused issue!! ")
            raise HTTPException(status_code=404, detail="data not found")

        last_scale_up_time = db[0]

    except Exception as e:
        print(e)

    try:

        try:
            window_file = f"/home/ubuntu/tsx/data/client/{client_id}/window.txt"
            cur_time = int(datetime.utcnow().timestamp())


            if os.path.exists(window_file):
                with open(window_file, "r") as f:
                    state = json.load(f)
            else:
                state = {
                    "high_cpu_count": 0,
                    "low_cpu_count": 0,
                    "last_cpu": None,
                    "last_ts": 0
                }

            PANIC_DELTA = 20
            panic_scale = False

            if state["last_cpu"] is not None:
                cpu_delta = cpu - state["last_cpu"]
                if cpu_delta >= PANIC_DELTA:
                    panic_scale = True

            if cpu > threshold + buffer_z:
                state["high_cpu_count"] += 1
                state["low_cpu_count"] = 0

            elif cpu < threshold - buffer_lower:
                state["low_cpu_count"] += 1
                state["high_cpu_count"] = 0


            COOLDOWN = 300
            in_cooldown = False

            if last_scale_up_time:
                if cur_time - int(last_scale_up_time) < COOLDOWN:
                    in_cooldown = True

            SCALE_TRIGGERED = False


            if panic_scale and not in_cooldown:
                message = "PANIC"
                scaling(message, email, ami, server_type, server_expected)
                SCALE_TRIGGERED = True


            elif state["high_cpu_count"] >= 3 and not in_cooldown:
                message = "UP"
                scaling(message, email, ami, server_type, server_expected)
                SCALE_TRIGGERED = True

            state["last_cpu"] = cpu
            state["last_ts"] = cur_time

            with open(window_file, "w") as f:
                json.dump(state, f, indent=2)

            if SCALE_TRIGGERED:
                con = mysql.connector.connect(
                    host=os.getenv("DB_HOST"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("PASSWORD"),
                    database=os.getenv("DATABASE")
                )
                cursor = con.cursor()
                cursor.execute(
                    "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                    (cur_time, client_id)
                )
                con.commit()
                cursor.close()
                con.close()


            if SCALE_TRIGGERED:
                logging.info(f"SCALE-UP triggered for client {client_id}")
            else:
                logging.debug(f"No scale-up action for client {client_id}")

        except Exception as e:
            logging.error(f"Scaling logic failed: {str(e)}")



    except Exception as e:
        print(e)

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




    if cpu >= threshold-buffer_lower:

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

            r = session.post(url, json=payload, timeout=1)
            r.raise_for_status()


        except Exception as e:

            logging.error(f"Sending request to ml api caused issue!!! {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f" ml api not responding: {str(e)}"

            )

    return {"status": "forwarded"}


