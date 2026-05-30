from fastapi import APIRouter,HTTPException,status,Depends,Request
from pydantic import BaseModel
import logging
import json
from datetime import datetime
from broker.functions.routers import for_ml
from broker.functions.routers import for_scaling
from broker.functions.supporters import check_incwindow
from broker.setting.loggers import LoggerFactory
from broker.setting.conifg import settings
from broker.setting.session import get_session
from broker.storage.database.database_connection import db_init,db_close, get_connection
from broker.storage.redis.redis_connection import startup_redis,shutdown_redis,redis_client
from broker.functions.supporters.timing_check import TimeCheck
from broker.storage.database.db_orm import Add_data,Retrive
from broker.functions.supporters.red_gray_check import Check
from broker.functions.supporters.freeze_file import Freez

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
def broker1func(metrics: Metrics, request: Request, conn=Depends(get_connection)):
    cpu = metrics.cpu_percentage
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
    timestamp = metrics.timestamp

    req_id = request.state.req_id

    headers = {
        "X-Request-ID": req_id
    }

    logger.info(
        "Broker request received",
        extra={
            "req_id": req_id,
            "client_id": client_id
        }
    )

    try:
        cursor = conn.cursor()

    except Exception:

        logger.exception("connection caused issue to sql")

        raise


    allowed_skew = TimeCheck.time_check(timestamp)

    if allowed_skew is False:
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

        db = Retrive.retrive_data_clint_info(client_id)

        threshold = db[1]
        buffer_z = db[2]
        buffer_lower = db[3]
        email = db[4]
        ami = db[5]
        server_type = db[6]
        security_group = db[7]
        manager_ip = db[8]

        db_cli = Retrive.retrive_data_system_info(client_id)


        last_scale_up_time = db_cli[0]
        last_scale_down_time = db_cli[1]
        total_cpu_window = db_cli[2]
        total_cur_fluc = db_cli[3]
        total_cur_ml_window = db_cli[4]
        total_cur_queue =db_cli[5]
        total_cur_rps =db_cli[6]
        last_queue = db_cli[7]
        last_rps = db_cli[8]
        last_cpu = db_cli[9]
        last_ml_window = db_cli[10]

    except Exception:

        logger.exception("Issue raised in data collection from db",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "db failure")

    try:
        if missing_server_count > int(server_expected / 10):
            for_scaling.For_scale.scaling("UP",email, ami, server_type, server_expected, client_id, req_id,security_group,headers,manager_ip)

    except Exception:

        logger.exception("Issue raised during scaling by missing servers",
                          extra={"req_id": req_id, "client_id": client_id}
                          )
        raise HTTPException(500, "scaling error")


    try:

        cur_time = int(datetime.utcnow().timestamp())

        in_gray_zone = Check.grey_check(threshold, buffer_lower, cpu, buffer_z)

        queue_increasing = check_incwindow.Window.increasing_window(queue_pressure, last_queue, total_cur_queue)
        rps_increasing = check_incwindow.Window.increasing_window(rps, last_rps, total_cur_rps)

        Add_data.update1(total_cur_queue=queue_increasing, last_queue=queue_pressure, total_cur_rps=rps_increasing, last_rps=rps, last_cpu=cpu, client_id=client_id)


        app_red_zone = Check.red_check(queue_increasing, rps_increasing)

        in_cooldown = Check.cooldown(last_scale_up_time)

        if not in_cooldown and app_red_zone is True:
            for_scaling.For_scale.scaling("UP", email, ami, server_type, server_expected, client_id, req_id,security_group,headers,manager_ip)

            Add_data.update2(total_cur_queue=0,total_cur_rps=0,client_id=client_id)

        if cpu >= threshold + buffer_z:

            new_total_cpu = total_cpu_window + 1

            Add_data.update3(total_cpu_window=new_total_cpu,client_id=client_id)

        else:
            cur_fluc = total_cur_fluc

            if cur_fluc > 2:

                Add_data.update3(total_cpu_window=0,client_id=client_id)

            else:

                data = cur_fluc + 1

                Add_data.update4(total_cur_fluc=data,client_id=client_id)

        if total_cpu_window >= 3 and not in_cooldown:

            for_scaling.For_scale.scaling("UP", email, ami, server_type, server_expected, client_id, req_id,security_group,headers,manager_ip)

            Add_data.update5(total_cpu_window=0,total_cur_ml_window=0,client_id=client_id)

            try:

                Add_data.update6(last_scale_up_time=cur_time,client_id=client_id)

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

                r = session.post(url, json=payload, headers=headers)
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
                timestamp,
                cpu,
                cpu_idle,
                live_connections,
                freeze_window,
                req_id,
                headers
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
                    timestamp,
                    cpu,
                    cpu_idle,
                    live_connections,
                    freeze_window,
                    req_id,
                    headers
                )

                if 0 <= resp_retry <= 100:
                    predicted_cpu = float(resp_retry)
                else:

                    logger.error(
                        "ML prediction failed twice for client",
                        extra={"req_id": req_id, "client_id": client_id, "window_id": resp_retry}
                    )
                    return


            Add_data.update7(total_cur_ml_window=new_cur_ml,last_ml_window=predicted_cpu,client_id=client_id)

            if (
                    new_cur_ml >= 3

            ):
                for_scaling.For_scale.scaling("ML", email, ami, server_type, server_expected, client_id, req_id,security_group,headers,manager_ip)

                Add_data.update8(total_cpu_window=0,total_cur_ml_window=0,client_id=client_id)

                try:

                    Add_data.update6(last_scale_up_time=cur_time,client_id=client_id)

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

    Freez.freeze(freeze_window, client_id, row, req_id)

    return {"status": "forwarded"}
