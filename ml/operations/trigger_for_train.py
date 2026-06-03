from fastapi import APIRouter,Request
from pydantic import BaseModel
import logging
from setting.loggers import LoggerFactory
from setting.conifg import settings
from train_model.train_model import Train

logger = LoggerFactory.get_logger(
    name="trigger_for_training",
    log_file=settings.LOG_FILE_INSERTION,
    level=logging.INFO
)


router = APIRouter()

class InsertMetrics(BaseModel):
    client_id: str

@router.post("/insert")
async def inserting(metrics: InsertMetrics,request: Request):

   client_id = metrics.client_id

   try:

        train_model_client = Train.train(client_id)

        logger.info(f"the model for {client_id} is being tranied")

   except Exception:

       logger.error(f"the model for {client_id} is being failed to train")

