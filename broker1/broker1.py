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
import uuid



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
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - req_id=%(req_id)s client_id=%(client_id)s - %(message)s',
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

def load_json(path, default,client_id,req_id):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return default

    except Exception:

        logging.exception("loding json caused issue",
                          extra={"req_id":req_id,"client_id":client_id})

def save_json(path, data,client_id,req_id):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    except Exception:

        logging.exception("writing json caused issue",
                          extra={"req_id":req_id,"client_id":client_id})



def scaling(message,email,ami,server_type,server_expected,client_id,req_id):
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
            "client_id": client_id,
            "req_id": req_id

        }

        url = os.getenv("DEC_URL")

        r = requests.post(url, json=payload, timeout=1)
        r.raise_for_status()

    except Exception:

        logging.error("Sending request to decision engine api caused issue",
                      extra={"req_id":req_id,"client_id":client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f" deceng api not responding"

        )

def prediction(client_id,timestamp,cpu,cpu_idle,totalram,ramused,diskusage,networkin,networkout,live_connections,freeze_window,missing_server_count,req_id):
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
            "missing_server_count": missing_server_count,
            "client_id": client_id,
            "req_id": req_id

        }

        url = os.getenv("ML_URL")

        r = session.post(url, json=payload)
        r.raise_for_status()

        resp = r.json()

        if 0 <= resp <= 100:
            next_cpu = float(resp)

            logging.info("Predicted cpu from ml",
                         extra={"req_id":req_id,"client_id":client_id,"predicted_cpu": next_cpu})

            return next_cpu


        else:

            window_id = int(resp)
            return window_id


    except Exception:

        logging.error(f"Sending request to ml api caused issue",
                      extra={"req_id":req_id,"client_id":client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f" ml api not responding"

        )


@broker1api.post("/ingest")
def broker1func(metrics: Metrics):


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

    req_id = str(uuid.uuid4())

    logging.info(
        "Broker request received",
        extra={
            "req_id": req_id,
            "client_id": client_id
        }
    )



    try:

        con = mysql.connector.connect(
                host= os.getenv("DB_HOST"),
                user = os.getenv("DB_USER"),
                password = os.getenv("PASSWORD"),
                database = os.getenv("DATABASE")

            )

        cursor = con.cursor()
    except Exception:

        logging.exception("Connection to database caused issue",
                          extra={"req_id":req_id,"client_id":client_id}
                          )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )



    timestamp = metrics.timestamp
    client_ts = datetime.strptime(metrics.timestamp,"%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = abs((now - client_ts).total_seconds())

    ALLOWED_SKEW = 60

    if delta > ALLOWED_SKEW:
        logging.error("data arrived late",
                      extra={"req_id": req_id, "client_id": client_id}
                      )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Timestamp out of sync"
        )


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
            logging.warning("loading client from db caused issue",
                          extra={"req_id": req_id, "client_id": client_id,"table":"client_info"}
                          )
            raise HTTPException(status_code=404, detail="Client not found")

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
            logging.info("loading data from db caused issue",
                         extra={"req_id": req_id, "client_id": client_id,"table":"system_info"}
                         )
            raise HTTPException(status_code=404, detail="data not found")

        last_scale_up_time = db[0]

    except Exception:

        logging.exception("Issue raised in data collection from db",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "db failure")


    try:

            ml_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/ml_window.txt"
            window_file = f"/home/ubuntu/tsx/data/client/{client_id}/window.txt"
            cur_time = int(datetime.utcnow().timestamp())


            real_state = load_json(window_file, {
                "high_cpu_count": 0
            },client_id,req_id)

            ml_state = load_json(ml_window_file, {
                "predictions": []
            },client_id,req_id)

            in_gray_zone = (threshold - buffer_lower) <= cpu < (threshold + buffer_z)


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
                scaling("UP", email, ami, server_type, server_expected,client_id,req_id)


                real_state["high_cpu_count"] = 0
                ml_state["predictions"] = []

                save_json(window_file, real_state)
                save_json(ml_window_file, ml_state)

                try:

                    cursor.execute(
                        "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                        (cur_time, client_id)
                    )
                    con.commit()

                except Exception:

                    logging.exception("updating the db last_scale_up_time caused issue",
                                      extra={"req_id":req_id,"client_id":client_id}

                                      )
                    raise

                logging.info(f" SCALE-UP triggered",
                             extra={"req_id": req_id, "client_id": client_id}
                             )
                return {"status": "scaled_real"}


            if not in_gray_zone:


                save_json(ml_window_file, ml_state)
                url = os.getenv("ML_URL/insert")

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
                    "missing_server_count": missing_server_count,
                    "client_id": client_id

                }

                try:

                    r = session.post(url, json=payload)
                    r.raise_for_status()

                except Exception:

                    logging.exception("inserting api of ml caused issue",
                                      extra={"req_id":req_id,"client_id":client_id})

                logging.info("insert api of ml data send",
                             extra={"req_id":req_id,"client_id":client_id})


            if in_gray_zone and not in_cooldown:


                resp = prediction(
                    client_id,
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
                    missing_server_count,
                    req_id
                )

                if 0 <= resp <= 100:
                    predicted_cpu = float(resp)

                    if predicted_cpu > (threshold + buffer_z):

                        ml_state["predictions"].append({
                            "predicted_cpu": predicted_cpu
                        })

                    save_json(ml_window_file, ml_state,client_id,req_id)

                else:
                    resp_retry = prediction(
                        client_id,
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
                        missing_server_count,
                        req_id
                    )

                    if 0 <= resp_retry <= 100:
                        predicted_cpu = float(resp_retry)
                    else:

                        logging.error(
                            "ML prediction failed twice for client",
                            extra={"req_id": req_id, "client_id": client_id,"window_id": resp_retry}
                        )
                        return

                ml_state["predictions"].append(predicted_cpu)
                ml_state["predictions"] = ml_state["predictions"][-3:]

                preds = ml_state["predictions"]

                if (
                        len(preds) == 3
                        and preds[0] < preds[1] < preds[2]
                        and preds[2] >= threshold + buffer_z
                ):
                    scaling("ML", email, ami, server_type, server_expected,client_id,req_id)

                    real_state["high_cpu_count"] = 0
                    ml_state["predictions"] = []

                    save_json(window_file, real_state)
                    save_json(ml_window_file, ml_state)

                    try:

                        cursor.execute(
                            "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                            (cur_time, client_id)
                        )
                        con.commit()

                    except Exception:

                        logging.exception("writing in db caused issue",
                                          extra={"req_id": req_id, "client_id": client_id}
                                          )



                    logging.info("SCALE-UP triggered by ml preds",
                                 extra={"req_id":req_id,"client_id":client_id})
                    return {"status": "scaled_ml"}



            save_json(window_file, real_state,client_id,req_id)
            save_json(ml_window_file, ml_state,client_id,req_id)


    except Exception as e:
            logging.exception(f"Scaling logic failed",
                              extra={"req_id":req_id,"client_id":client_id})
            raise HTTPException(500, "scaling logic failed")

    try:

        file_name = f"{freeze_window}.log"
        freeze_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/{file_name}"

        with open(freeze_window_file,"w") as f:
            f.write(",".join(map(str, row)) + "\n")

    except Exception:

        logging.exception(f"Writing the files caused issue",
                          extra={"req_id":req_id,"client_id":client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"File_writing_fails"
        )

    finally:
        cursor.close()
        con.close()

    return {"status": "forwarded"}


