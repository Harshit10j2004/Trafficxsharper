from fastapi import HTTPException,status
import logging
import requests
from broker.setting.conifg import settings
from broker.setting.loggers import LoggerFactory

logger = LoggerFactory.get_logger(
    name="router_for_scaling",
    log_file=settings.LOG_FILE_FORSCA_R,
    level=logging.INFO
)

class For_scale():

    @staticmethod

    async def scaling(message, email, ami, server_type, server_expected, client_id, req_id,security_group,headers,manager_ip,joining_token):
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
                "req_id": req_id,
                "security_group": security_group,
                "manager_ip": manager_ip,
                "joining_token": joining_token

            }

            url = settings.DEC_URL

            r = requests.post(url, json=payload, timeout=1, headers=headers)
            r.raise_for_status()

        except Exception:

            logger.error("Sending request to decision engine api caused issue",
                          extra={"req_id": req_id, "client_id": client_id})

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f" deceng api not responding"

            )
