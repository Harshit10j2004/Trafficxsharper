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
# understand these lines
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

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)



def scaling(message,email,ami,server_type,server_expected,client_id):
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
            "total_instance": total_instance,
            "client_id": client_id

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

def prediction(timestamp,cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,live_connections,freeze_window,missing_server_count):
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
            "window_id": freeze_window,
            "missing_server_count": missing_server_count

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


    if(len(missing_server) == 0):
        missing_server_count = 0
    else:

        missing_server_count = len(missing_server)

    row = [timestamp, cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout,live_connections, client_id,server_expected,server_responded,missing_server_count]


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

            ml_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/ml_window.txt"
            window_file = f"/home/ubuntu/tsx/data/client/{client_id}/window.txt"
            cur_time = int(datetime.utcnow().timestamp())

            # reserch again
            real_state = load_json(window_file, {
                "high_cpu_count": 0
            })

            ml_state = load_json(ml_window_file, {
                "predictions": []
            })


            COOLDOWN = 300
            in_cooldown = False
            if last_scale_up_time:
                if cur_time - int(last_scale_up_time) < COOLDOWN:
                    in_cooldown = True


            if cpu >= threshold + buffer_z:
                real_state["high_cpu_count"] += 1
            else:
                real_state["high_cpu_count"] = 0

            if real_state["high_cpu_count"] >= 3 and not in_cooldown:
                scaling("UP", email, ami, server_type, server_expected,client_id)


                real_state["high_cpu_count"] = 0
                ml_state["predictions"] = []

                save_json(window_file, real_state)
                save_json(ml_window_file, ml_state)

                cursor.execute(
                    "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                    (cur_time, client_id)
                )
                con.commit()

                logging.info(f"REAL SCALE-UP triggered for client {client_id}")
                return {"status": "scaled_real"}


            in_gray_zone = (threshold - buffer_lower) <= cpu < threshold

            if not in_gray_zone:

                ml_state["predictions"] = []
                save_json(ml_window_file, ml_state)


            if in_gray_zone and not in_cooldown:
                prediction(
                    timestamp,
                    cpu,
                    cpu_idle,
                    totalram,
                    ramused,
                    diskusage,
                    networkin,
                    networkout,
                    live_connections,
                    freeze_window,
                    missing_server_count
                )

                # willbe replace with real ml output
                predicted_cpu = cpu + 5

                ml_state["predictions"].append(predicted_cpu)
                ml_state["predictions"] = ml_state["predictions"][-3:]

                preds = ml_state["predictions"]

                if (
                        len(preds) == 3
                        and preds[0] < preds[1] < preds[2]
                        and preds[2] >= threshold + buffer_z
                ):
                    scaling("ML", email, ami, server_type, server_expected,client_id)

                    real_state["high_cpu_count"] = 0
                    ml_state["predictions"] = []

                    save_json(window_file, real_state)
                    save_json(ml_window_file, ml_state)

                    cursor.execute(
                        "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                        (cur_time, client_id)
                    )
                    con.commit()

                    logging.info(f"ML SCALE-UP triggered for client {client_id}")
                    return {"status": "scaled_ml"}


            save_json(window_file, real_state)
            save_json(ml_window_file, ml_state)

            logging.debug(f"No scale-up action for client {client_id}")

    except Exception as e:
            logging.error(f"Scaling logic failed: {str(e)}")

    try:

        file_name = f"{freeze_window}.log"
        freeze_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/{file_name}"

        with open(freeze_window_file,"w") as f:
            f.write(",".join(map(str, row)) + "\n")

    except Exception as e:

        logging.debug(f"Writing the files caused issue!!! {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"File_writing_fails: {str(e)}"
        )

    return {"status": "forwarded"}


