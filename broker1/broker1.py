from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import logging
import mysql.connector
from mysql.connector import pooling
import requests
import uuid
import sqlite3


class Metrics(BaseModel):
    timestamp: str
    cpu_percentage: float
    cpu_idle_percent: float
    total_ram: float
    ram_used: float
    disk_usage_percent: float
    network_in: float
    network_out: float
    client_id: str
    freeze_window: int
    live_connections: int
    server_expected: int
    server_responded: int
    missing_server: list[str]
    rps: float
    conn_rate: float
    queue_pressure: float
    rps_per_node: float


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

db_pool = None


def get_db_pool():
    global db_pool
    if db_pool is None:
        raise RuntimeError("Database pool not initialized")
    return db_pool


@broker1api.on_event("startup")
def startup_event():
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="fastapi_pool",
            pool_size=20,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("PASSWORD"),
            database=os.getenv("DATABASE"),
            connect_timeout=10000
        )
        print("Database connection pool created")
    except Exception as e:
        print(f"Failed to create DB pool: {e}")
        raise


@broker1api.on_event("shutdown")
def shutdown_event():
    global db_pool
    if db_pool is not None:
        db_pool._remove_connections()
        print("Database connection pool closed")


def get_connection():
    conn = get_db_pool().get_connection()
    try:
        yield conn
    finally:
        conn.close()


def if_down(total_cpu, total_rps, total_queue, req_id, client_id):
    try:

        if (
                total_cpu <= 1 and
                total_rps <= 1 and
                total_queue <= 1
        ):
            return 1
        return 0

    except Exception:

        logging.exception("function if_down failed",
                          extra={"req_id": req_id, "client_id": client_id})


def increasing_window(cur_value, last_value, total):
    if (
            cur_value > last_value
    ):
        total = total + 1

    else:

        total = max(0, total - 1)

    return total


def scaling(message, email, ami, server_type, server_expected, client_id, req_id):
    try:

        if (server_expected < 10):
            total_instance = 1
        else:
            total_instance = int(server_expected / 10)

        payload = {
            "scale_message": message,
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
                      extra={"req_id": req_id, "client_id": client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f" deceng api not responding"

        )


def scaling_down(client_id, req_id, email, message):
    try:

        payload = {
            "client_id": client_id,
            "req_id": req_id,
            "email": email,
            "scale_message": message,
            "total_instance": 0,
            "ami": "NA",
            "server_type": "NA"

        }

        url = os.getenv("DEC_URL")

        r = requests.post(url, json=payload, timeout=1)
        r.raise_for_status()


    except Exception:

        logging.exception("scaling down api caused issue",
                          extra={"req_id": req_id, "client_id": client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f" deceng api not responding"

        )


def prediction(client_id, timestamp, cpu, cpu_idle, live_connections, freeze_window, req_id, rps, queue_pressure,
               conn_rate):
    try:

        payload = {
            "timestamp": timestamp,
            "cpu": cpu,
            "cpu_idle": cpu_idle,
            "live_connections": live_connections,
            "window_id": freeze_window,
            "client_id": client_id,
            "req_id": req_id,
        }

        url = os.getenv("ML_URL")

        r = session.post(url, json=payload)
        r.raise_for_status()

        resp = r.json()

        if 0 <= resp <= 100:
            next_cpu = float(resp)

            logging.info("Predicted cpu from ml",
                         extra={"req_id": req_id, "client_id": client_id, "predicted_cpu": next_cpu})

            return next_cpu


        else:

            window_id = int(resp)
            return window_id


    except Exception:

        logging.error(f"Sending request to ml api caused issue",
                      extra={"req_id": req_id, "client_id": client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f" ml api not responding"

        )


@broker1api.post("/ingest")
def broker1func(metrics: Metrics, conn=Depends(get_connection)):
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
    rps = metrics.rps
    rps_per_node = metrics.rps_per_node
    conn_rate = metrics.conn_rate
    queue_pressure = metrics.queue_pressure

    req_id = str(uuid.uuid4())

    logging.info(
        "Broker request received",
        extra={
            "req_id": req_id,
            "client_id": client_id
        }
    )

    print(f"REQUEST ARRIVED {client_id} and generated requested id is {req_id}")

    try:
        cursor = conn.cursor()

    except Exception:

        logging.exception("connection caused issue to sql")

        raise

    try:
        sqll_conn = sqlite3.connect("/home/ubuntu/tsx/data/client_data.db")
        sqll_cursor = sqll_conn.cursor()


    except Exception:

        logging.exception("connection caused issue to sqllite")

    timestamp = metrics.timestamp
    client_ts = datetime.strptime(metrics.timestamp, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
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

    if (len(missing_server) == 0):
        missing_server_count = 0
    else:
        missing_server_count = len(missing_server)

    row = [timestamp, cpu, cpu_idle, totalram, ramused, diskusage, networkin, networkout, live_connections, client_id,
           server_expected, server_responded, missing_server_count]

    try:

        query2 = "select client_name,thresold,l_buff,h_buff,email,ami,server_type from client_info where client_id = %s"

        cursor.execute(query2, (client_id,))

        db = cursor.fetchone()

        if not db:
            logging.warning("loading client from db caused issue",
                            extra={"req_id": req_id, "client_id": client_id, "table": "client_info"}
                            )
            raise HTTPException(status_code=404, detail="Client not found")

        threshold = db[1]
        buffer_z = db[2]
        buffer_lower = db[3]
        email = db[4]
        ami = db[5]
        server_type = db[6]

        query = "select last_scale_up_time,last_scale_down_time from system_info where client_id = %s"

        cursor.execute(query, (client_id,))

        db = cursor.fetchone()

        if not db:
            logging.info("loading data from db caused issue",
                         extra={"req_id": req_id, "client_id": client_id, "table": "system_info"}
                         )
            raise HTTPException(status_code=404, detail="data not found")

        last_scale_up_time = db[0]
        last_scale_down_time = db[1]

    except Exception:

        logging.exception("Issue raised in data collection from db",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "db failure")

    try:

        total_cpu_window = None
        total_cur_fluc = None
        total_cur_ml_window = None
        total_cur_queue = None
        total_cur_rps = None
        last_queue = None
        last_rps = None
        last_cpu = None
        last_ml_window = None

        sqll_query = "select total_cpu_window,total_cur_fluc,total_cur_ml_window,total_cur_queue,total_cur_rps,last_queue,last_rps,last_cpu,last_ml_window from local_state where client_id = ?"

        sqll_cursor.execute(sqll_query, (client_id,))

        local_data = sqll_cursor.fetchone()

        if(local_data is None):
            sqll_query10 = "insert into local_state (client_id, total_cpu_window,total_cur_fluc,total_cur_ml_window,total_cur_queue,total_cur_rps,last_queue,last_rps,last_cpu,last_ml_window) values (?,?,?,?,?,?,?,?,?,?)"
            values = (client_id,0,0,0,0,0,0,0,0,0)

            sqll_cursor.execute(sqll_query10,values)
            sqll_conn.commit()

            total_cpu_window = 0
            total_cur_fluc = 0
            total_cur_ml_window = 0
            total_cur_queue = 0
            total_cur_rps = 0
            last_queue = 0
            last_rps = 0
            last_cpu = 0
            last_ml_window = 0

        else:

            total_cpu_window = local_data[0]
            total_cur_fluc = local_data[1]
            total_cur_ml_window = local_data[2]
            total_cur_queue = local_data[3]
            total_cur_rps = local_data[4]
            last_queue = local_data[5]
            last_rps = local_data[6]
            last_cpu = local_data[7]
            last_ml_window = local_data[8]


    except Exception:

        logging.exception("Issue raised in data collection from db",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "db failure")

    try:

        cur_time = int(datetime.utcnow().timestamp())

        in_gray_zone = (threshold - buffer_lower) <= cpu < (threshold + buffer_z)

        queue_increasing = increasing_window(queue_pressure, last_queue, total_cur_queue)
        rps_increasing = increasing_window(rps, last_rps, total_cur_rps)


        sql_query1 = f"update local_state set total_cur_queue = ? , last_queue = ? , total_cur_rps = ? , last_rps = ?, last_cpu = ? where client_id = ?"

        sqll_cursor.execute(
            sql_query1,
            (queue_increasing, queue_pressure, rps_increasing, rps, cpu ,client_id)
        )

        sqll_conn.commit()

        app_red_zone = False

        if (queue_increasing >= 3 and rps_increasing >= 3):
            app_red_zone = True

        D_COOLDOWN = 240
        COOLDOWN = 300
        in_cooldown = False
        in_d_cooldown = False
        if last_scale_up_time:
            if cur_time - int(last_scale_up_time) < COOLDOWN:
                in_cooldown = True

        if last_scale_down_time:
            if cur_time - int(last_scale_down_time) < D_COOLDOWN:
                in_d_cooldown = True

        do_scale_down = if_down(total_cpu_window, total_cur_queue, total_cur_rps, req_id, client_id)

        if not in_cooldown and app_red_zone is True:
            scaling("UP", email, ami, server_type, server_expected, client_id, req_id)


            sql_query5 = f"update local_state set total_cur_queue = ?, total_cur_rps = ? where client_id = ?"
            sqll_cursor.execute(sql_query5, (0, 0, client_id))

            sqll_conn.commit()

        if cpu >= threshold + buffer_z:

            new_total_cpu = total_cpu_window + 1

            sql_query2 = f"update local_state set total_cpu_window = ? where client_id = ?"
            sqll_cursor.execute(sql_query2, (new_total_cpu,client_id,))

            sqll_conn.commit()


        else:
            cur_fluc = total_cur_fluc

            if cur_fluc > 2:

                sql_query3 = f"update local_state set total_cpu_window = ? where client_id = ?"
                sqll_cursor.execute(sql_query3, (0, client_id,))

                sqll_conn.commit()


            else:

                data = cur_fluc + 1

                sql_query4 = f"update local_state set total_cur_fluc = ? where client_id = ?"
                sqll_cursor.execute(sql_query4, (data, client_id,))

                sqll_conn.commit()

        if total_cpu_window >= 3 and not in_cooldown:
            scaling("UP", email, ami, server_type, server_expected, client_id, req_id)



            sql_query6 = f"update local_state set total_cpu_window = ?, total_cur_ml_window = ? where client_id = ?"
            sqll_cursor.execute(sql_query6, (0, 0, client_id))

            sqll_conn.commit()

            try:

                cursor.execute(
                    "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                    (cur_time, client_id)
                )
                conn.commit()

            except Exception:

                logging.exception("updating the db last_scale_up_time caused issue",
                                  extra={"req_id": req_id, "client_id": client_id}

                                  )
                raise

            logging.info(f" SCALE-UP triggered",
                         extra={"req_id": req_id, "client_id": client_id}
                         )
            return {"status": "scaled_real"}

        if not in_gray_zone:

            url = os.getenv("ML_URL_INSERT")

            payload = {
                "timestamp": timestamp,
                "cpu": cpu,
                "cpu_idle": cpu_idle,
                "live_connections": live_connections,
                "window_id": freeze_window,
                "client_id": client_id,
                "req_id": req_id

            }

            try:

                r = session.post(url, json=payload)
                r.raise_for_status()

            except Exception:

                logging.exception("inserting api of ml caused issue",
                                  extra={"req_id": req_id, "client_id": client_id})

            logging.info("insert api of ml data send",
                         extra={"req_id": req_id, "client_id": client_id})

        if in_gray_zone and not in_cooldown:

            new_cur_ml = None

            resp = prediction(
                client_id,
                freeze_window,
                timestamp,
                cpu,
                live_connections,
                req_id,
                rps,
                queue_pressure
            )

            if 0 <= resp <= 100:
                predicted_cpu = float(resp)

                if predicted_cpu > (threshold + buffer_z):
                    new_cur_ml = total_cur_ml_window + 1
                else:
                    new_cur_ml = max(0, total_cur_ml_window - 1)


            else:

                resp_retry = prediction(
                    client_id,
                    freeze_window,
                    timestamp,
                    cpu,
                    live_connections,
                    req_id
                )

                if 0 <= resp_retry <= 100:
                    predicted_cpu = float(resp_retry)
                else:

                    logging.error(
                        "ML prediction failed twice for client",
                        extra={"req_id": req_id, "client_id": client_id, "window_id": resp_retry}
                    )
                    return

            sql_query8 = "update local_state set total_cur_ml_window = ?,last_ml_window = ? where client_id = ?"
            sqll_cursor.execute(sql_query8, (new_cur_ml, predicted_cpu, client_id))

            sqll_conn.commit()

            if (
                    new_cur_ml >= 3

            ):
                scaling("ML", email, ami, server_type, server_expected, client_id, req_id)

                sql_query9 = "update local_state set total_cpu_window = ?, total_cur_ml_window = ? where client_id = ?"
                sqll_cursor.execute(sql_query9, (0, 0, client_id))

                sqll_conn.commit()

                try:

                    cursor.execute(
                        "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                        (cur_time, client_id)
                    )
                    conn.commit()

                except Exception:

                    logging.exception("writing in db caused issue",
                                      extra={"req_id": req_id, "client_id": client_id}
                                      )

                logging.info("SCALE-UP triggered by ml preds",
                             extra={"req_id": req_id, "client_id": client_id})
                return {"status": "scaled_ml"}

        if not in_d_cooldown and do_scale_down == 1:

            scaling_down(client_id, req_id, email, "DOWN")

            try:

                cursor.execute(
                    "UPDATE system_info SET last_scale_down_time = %s WHERE client_id = %s",
                    (cur_time, client_id)
                )
                conn.commit()

            except Exception:

                logging.exception("writing in db caused issue",
                                  extra={"req_id": req_id, "client_id": client_id}
                                  )

    except Exception as e:
        logging.exception(f"Scaling logic failed",
                          extra={"req_id": req_id, "client_id": client_id})
        raise HTTPException(500, "scaling logic failed")

    try:

        file_name = f"{freeze_window}.log"
        freeze_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/{file_name}"

        with open(freeze_window_file, "w") as f:
            f.write(",".join(map(str, row)) + "\n")

    except Exception:

        logging.exception(f"Writing the files caused issue",
                          extra={"req_id": req_id, "client_id": client_id})

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"File_writing_fails"
        )

    sqll_conn.close()

    return {"status": "forwarded"}


