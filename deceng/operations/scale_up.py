from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Request
from pydantic import BaseModel
import logging
import asyncio
from setting.conifg import settings
from setting.loggers import LoggerFactory
from caller.caller_mail import Mail
from aws.aws_up import AWS_up
from azure.scale_up_azure import Azure_up

router = APIRouter()
logger = LoggerFactory.get_logger(
    name="scale_up_api",
    log_file=settings.LOG_SCALE_DOWN,
    level=logging.INFO
)


class Metrics(BaseModel):
    scale_message: str
    email: str
    total_instance: int
    ami: list
    server_type: list
    client_id: str
    req_id: str
    joining_token: str
    security_group: list
    manager_ip: str

@router.post("/deceng")
async def decengfunc(metrics: Metrics, bg: BackgroundTasks,request:Request):

    scale_message = metrics.scale_message
    email = metrics.email
    total_instances = metrics.total_instance
    ami = metrics.ami
    server_type = metrics.server_type
    client_id = metrics.client_id
    req_id = request.state.req_id
    joining_token = metrics.joining_token
    security_group = metrics.security_group
    manager_ip = metrics.manager_ip

    base_path = f"/home/ubuntu/tsx/data/instances/{client_id}"
    pending_file = f"{base_path}/pending.txt"

    logger.info(
        "DECENG request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
            "total_instances": total_instances,
            "ami": ami,
            "server_type": server_type,
            "scale_action": scale_message
        }
    )


    try:

        scale = "UP"

        instance_for_aws = max(1, int(total_instances / 2))
        instance_for_azure = total_instances - instance_for_aws

        aws_ami = ami[0]
        azure_ami = ami[1]

        aws_sec = security_group[0]
        azure_sec = security_group[1]

        aws_st = server_type[0]
        azure_st = server_type[1]

        aws_task = AWS_up.start_instance(
            aws_ami, instance_for_aws, aws_st, pending_file,
            req_id, client_id, aws_sec, joining_token, manager_ip
        )

        azure_task = Azure_up.start_instance_azure(
            azure_ami, instance_for_azure, azure_st, pending_file,
            req_id, client_id, joining_token, azure_sec, manager_ip
        )

        aws_result = await asyncio.gather(aws_task)


        email = Mail.mail(email, client_id, req_id, scale_message, total_instances=total_instances)


    except Exception:
        logger.exception(
            "Scaling caused issue",
            extra={"req_id": req_id, "client_id": client_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="aws issue"
        )

