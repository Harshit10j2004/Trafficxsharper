from broker.setting.session import get_session
from fastapi import HTTPException,status
import logging
from broker.setting.conifg import settings
from broker.setting.loggers import LoggerFactory

session = get_session()

logger = LoggerFactory.get_logger(
    name="router_for_ml",
    log_file=settings.LOG_FILE_FORML_R,
    level=logging.INFO
)


class For_ml():

    @staticmethod
    async def prediction(client_id, timestamp, cpu, cpu_idle, live_connections, freeze_window, req_id, rps, queue_pressure,
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

            url = settings.ML_URL

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