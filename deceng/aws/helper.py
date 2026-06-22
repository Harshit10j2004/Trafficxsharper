import boto3
import logging
from setting.loggers import LoggerFactory
from setting.conifg import settings

logger = LoggerFactory.get_logger(
    name="aws_up",
    log_file=settings.LOG_FILE_AWS_U,
    level=logging.INFO
)

_ec2_client = None

def get_ec2_client():
    global _ec2_client
    try:
        if _ec2_client is None:
            _ec2_client = boto3.client(
                "ec2",
                region_name="ap-south-1",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        return _ec2_client
    except Exception as e:
        logger.exception(
            f"CODE caused issue during calling the helper function {e}",
        )
        raise