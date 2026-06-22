from fastapi import APIRouter,Request
from pydantic import BaseModel
import uuid
import logging
from setting.conifg import settings
from setting.loggers import LoggerFactory
from caller.caller_mail import Mail
from aws.aws_down import AWS_down
from azure.scale_down_azure import Azure_down
from files.file_management import File

router = APIRouter()

class Scale_down(BaseModel):
    client_id: int
    instance_id: str
    node_id: str
    email: str
    provider: str



logger = LoggerFactory.get_logger(
    name="scale_down_api",
    log_file=settings.LOG_SCALE_DOWN,
    level=logging.INFO
)

@router.post("/deceng_down")
async def scale_down(metrics: Scale_down):
    scale_message = "DOWN"
    client_id = metrics.client_id
    instance_id = metrics.instance_id
    node_id = metrics.node_id
    email = metrics.email
    provider = metrics.provider

    req_id = str(uuid.uuid4())
    base_path = f"/home/ubuntu/tsx/data/instances/{client_id}"
    pending_file = f"{base_path}/pending.txt"

    try:

        if provider == "AWS":

            offboard = AWS_down.removing_instance(instance_id, req_id, client_id)

            logging.info(f"The instances is deleted for client",
                     extra={"req_id": req_id, "client_id": client_id, "instance_id": instance_id, "node_id": node_id})

        if provider == "AZURE":

            offboard = Azure_down.removing_instance_azure(instance_id, req_id, client_id)

            logging.info(f"The instances is deleted for client",
                         extra={"req_id": req_id, "client_id": client_id, "instance_id": instance_id,
                                "node_id": node_id})

        file_del = File.pop_next_instance(pending_file, req_id, client_id, instance_id)

        logging.info(f"The instances is cleared from record",
                     extra={"req_id": req_id, "client_id": client_id, "instance_id": instance_id, "node_id": node_id})

        email = Mail.mail(email, client_id, req_id, scale_message, total_instances=2)

    except Exception:

        logging.exception(
            "AWS caused issue during offboard",
            extra={"req_id": req_id, "client_id": client_id}
        )