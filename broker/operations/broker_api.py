from fastapi import APIRouter,HTTPException,status,Depends
from pydantic import BaseModel
import logging
import uuid
import json
import redis
from datetime import datetime, timezone
from broker.functions.routers import for_ml
from broker.functions.routers import for_scaling
from broker.functions.supporters import check_incwindow
from broker.setting.loggers import LoggerFactory
from broker.setting.conifg import settings
from broker.setting.session import get_session
from broker.storage.database.database_connection import db_init,db_close, get_connection
from broker.storage.redis.redis_connection import startup_redis,shutdown_redis,redis_client

session = get_session()


logger = LoggerFactory.get_logger(
    name="broker",
    log_file=settings.LOG_FILE_BROKER,
    level=logging.INFO
)

router = APIRouter()

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

@router.on_event("startup")
def startup_event():

    db_init()
    startup_redis()

@router.on_event("shutdown")
def shutdown_event():

    db_close()
    shutdown_redis()


@router.post("/ingest")
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

    logger.info(
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

        logger.exception("connection caused issue to sql")

        raise


    timestamp = metrics.timestamp
    client_ts = datetime.strptime(metrics.timestamp, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = abs((now - client_ts).total_seconds())

    ALLOWED_SKEW = 60

    if delta > ALLOWED_SKEW:
        logger.error("data arrived late",
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

    redis_client.publish("metrics", json.dumps(row))

    try:

        query2 = "select client_name,thresold,l_buff,h_buff,email,ami,server_type,security_group from client_info where client_id = %s"

        cursor.execute(query2, (client_id,))

        db = cursor.fetchone()

        if not db:
            logger.warning("loading client from db caused issue",
                            extra={"req_id": req_id, "client_id": client_id, "table": "client_info"}
                            )
            raise HTTPException(status_code=404, detail="Client not found")

        threshold = db[1]
        buffer_z = db[2]
        buffer_lower = db[3]
        email = db[4]
        ami = db[5]
        server_type = db[6]
        security_group = db[7]

        query = "select last_scale_up_time,last_scale_down_time,total_cpu_window,total_cur_fluc ,total_cur_ml_window,total_cur_queue,total_cur_rps,total_cur_rps,last_queue,last_rps,last_cpu,last_ml_window from system_info where client_id = %s"

        cursor.execute(query, (client_id,))

        db = cursor.fetchone()

        if not db:
            logger.info("loading data from db caused issue",
                         extra={"req_id": req_id, "client_id": client_id, "table": "system_info"}
                         )
            raise HTTPException(status_code=404, detail="data not found")

        last_scale_up_time = db[0]
        last_scale_down_time = db[1]
        total_cpu_window = db[2]
        total_cur_fluc = db[3]
        total_cur_ml_window = db[4]
        total_cur_queue =db[5]
        total_cur_rps =db[6]
        last_queue = db[7]
        last_rps = db[8]
        last_cpu = db[9]
        last_ml_window = db[10]

    except Exception:

        logger.exception("Issue raised in data collection from db",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "db failure")

    try:
        if missing_server_count > int(server_expected / 10):
            for_scaling.For_scale.scaling("UP",email, ami, server_type, server_expected, client_id, req_id,security_group)

    except Exception:

        logger.exception("Issue raised during scaling by missing servers",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "db failure")


    try:

        cur_time = int(datetime.utcnow().timestamp())

        in_gray_zone = (threshold - buffer_lower) <= cpu < (threshold + buffer_z)

        queue_increasing = check_incwindow.Window.increasing_window(queue_pressure, last_queue, total_cur_queue)
        rps_increasing = check_incwindow.Window.increasing_window(rps, last_rps, total_cur_rps)


        sql_query1 = f"update system_info set total_cur_queue =%s , last_queue = %s  , total_cur_rps =%s , last_rps =%s , last_cpu = %s  where client_id = %s"
        values1 = (queue_increasing, queue_pressure, rps_increasing, rps, cpu ,client_id)

        cursor.execute(sql_query1,values1)

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


        if not in_cooldown and app_red_zone is True:
            for_scaling.For_scale.scaling("UP", email, ami, server_type, server_expected, client_id, req_id,security_group)


            sql_query5 = f"update local_state set total_cur_queue = ?, total_cur_rps = ? where client_id = ?"
            values2 = (0, 0, client_id)
            cursor.execute(sql_query5,values2)

        if cpu >= threshold + buffer_z:

            new_total_cpu = total_cpu_window + 1

            sql_query2 = f"update local_state set total_cpu_window = ? where client_id = ?"
            values3 = (new_total_cpu,client_id,)

            cursor.execute(sql_query2,values3)

        else:
            cur_fluc = total_cur_fluc

            if cur_fluc > 2:

                sql_query3 = f"update local_state set total_cpu_window = ? where client_id = ?"
                values4 = (0, client_id,)

                cursor.execute(sql_query3,values4)


            else:

                data = cur_fluc + 1

                sql_query4 = f"update local_state set total_cur_fluc = ? where client_id = ?"
                values5 = (data, client_id,)

                cursor.execute(sql_query4,values5)

        if total_cpu_window >= 3 and not in_cooldown:
            for_scaling.For_scale.scaling("UP", email, ami, server_type, server_expected, client_id, req_id,security_group)



            sql_query6 = f"update local_state set total_cpu_window = ?, total_cur_ml_window = ? where client_id = ?"
            values6 = (0, 0, client_id)

            cursor.execute(sql_query6, values6)

            try:

                cursor.execute(
                    "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                    (cur_time, client_id)
                )
                conn.commit()

            except Exception:

                logger.exception("updating the db last_scale_up_time caused issue",
                                  extra={"req_id": req_id, "client_id": client_id}

                                  )
                raise

            logger.info(f" SCALE-UP triggered",
                         extra={"req_id": req_id, "client_id": client_id}
                         )
            return {"status": "scaled_real"}

        if not in_gray_zone:

            url = settings.ML_URL_INSERT

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

                logger.exception("inserting api of ml caused issue",
                                  extra={"req_id": req_id, "client_id": client_id})

            logger.info("insert api of ml data send",
                         extra={"req_id": req_id, "client_id": client_id})

        if in_gray_zone and not in_cooldown:

            new_cur_ml = None

            resp = for_ml.For_ml.prediction(
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

                resp_retry = for_ml.For_ml.prediction(
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

                    logger.error(
                        "ML prediction failed twice for client",
                        extra={"req_id": req_id, "client_id": client_id, "window_id": resp_retry}
                    )
                    return

            sql_query8 = "update local_state set total_cur_ml_window = ?,last_ml_window = ? where client_id = ?"
            values6 =  (new_cur_ml, predicted_cpu, client_id)

            cursor.execute(sql_query8, values6)

            if (
                    new_cur_ml >= 3

            ):
                for_scaling.For_scale.scaling("ML", email, ami, server_type, server_expected, client_id, req_id,security_group)

                sql_query9 = "update local_state set total_cpu_window = ?, total_cur_ml_window = ? where client_id = ?"
                values7 =  (0, 0, client_id)

                cursor.execute(sql_query9, values7)

                try:

                    cursor.execute(
                        "UPDATE system_info SET last_scale_up_time = %s WHERE client_id = %s",
                        (cur_time, client_id)
                    )
                    conn.commit()

                except Exception:

                    logger.exception("writing in db caused issue",
                                      extra={"req_id": req_id, "client_id": client_id}
                                      )

                logger.info("SCALE-UP triggered by ml preds",
                             extra={"req_id": req_id, "client_id": client_id})
                return {"status": "scaled_ml"}


    except Exception as e:
        logger.exception(f"Scaling logic failed",
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


    return {"status": "forwarded"}
