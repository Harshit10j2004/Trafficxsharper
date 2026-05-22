from mysql.connector import pooling
import logging
from contextlib import contextmanager
from broker.setting.conifg import settings
from broker.setting.loggers import LoggerFactory

logger = LoggerFactory.get_logger(
    name="database_status",
    log_file=settings.LOG_FILE_DATABASE_S,
    level=logging.INFO
)

db_pool = None

def get_db_pool():
    global db_pool
    if db_pool is None:
        raise RuntimeError("Database pool not initialized")
    return db_pool

@contextmanager
def get_connection():
    conn = None
    try:
        conn = get_db_pool().get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

async def db_init():
    global db_pool
    try:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="fastapi_pool",
            pool_size=20,
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.PASSWORD,
            database=settings.DATABASE,
            connect_timeout=10000
        )
        print("Database connection pool created")
    except Exception as e:

        logger.error("THE DATABASE CONNECTION DURING STARTUP FAILED")

        raise


async def db_close():

    try:
        global db_pool
        if db_pool is not None:
            db_pool._remove_connections()
            logger.info("Database connection pool closed successfully")

    except Exception as e:

        logger.error("THE DATABASE CLOSEUP DURING SHUTDOWN FAILED")

        raise

