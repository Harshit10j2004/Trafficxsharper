import logging
from deceng.aws.helper import get_ec2
from deceng.setting.loggers import LoggerFactory
from deceng.setting.conifg import settings

logger = LoggerFactory.get_logger(
    name="aws_down",
    log_file=settings.LOG_FILE_AWS_D,
    level=logging.INFO
)

class AWS_down():

    @staticmethod
    async def removing_instance(id, client_id, req_id):
        try:

            InstanceIds = [id.strip()]
            get_ec2().terminate_instances(
                InstanceIds=InstanceIds
            )

            logger.info("instance is terminated sucessfully",
                         extra={"Req_id": req_id, "client_id": client_id, "instance_id": id}
                         )

        except Exception:
            logger.exception(
                "Issue raised during terminating the instances from aws",
                extra={"req_id": req_id, "client_id": client_id}
            )