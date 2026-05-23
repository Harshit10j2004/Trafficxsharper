import boto3
import logging
from deceng.setting.loggers import LoggerFactory
from deceng.setting.conifg import settings
ec2_client = None

logger = LoggerFactory.get_logger(
    name="aws_up",
    log_file=settings.LOG_FILE_AWS_U,
    level=logging.INFO
)

class get_ec2():

    @staticmethod
    async def get_ec2():
        global ec2_client
        try:
            if ec2_client is None:
                ec2_client = boto3.client("ec2", region_name="ap-south-1")
            return ec2_client

        except Exception as e:

            logger.exception(
                f"CODE caused issue during calling the helper function {e}",
            )

