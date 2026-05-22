import redis
import logging
from broker.setting.conifg import settings
from broker.setting.loggers import LoggerFactory

redis_client: redis.Redis | None = None

logger = LoggerFactory.get_logger(
    name="redis_status",
    log_file=settings.LOG_FILE_REDIS,
    level=logging.INFO
)

def startup_redis():
    global redis_client
    redis_client = redis.Redis(
        host='127.0.0.1',
        port=6379,
        decode_responses=True
    )

    try:
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None
        raise

    return redis_client

def shutdown_redis():
    global redis_client
    if redis_client:
        redis_client.close()
