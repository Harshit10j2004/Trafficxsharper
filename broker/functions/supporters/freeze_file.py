from fastapi import HTTPException,status
from broker.setting.loggers import LoggerFactory
from broker.setting.conifg import settings
import logging

logger = LoggerFactory.get_logger(
    name="extra",
    log_file=settings.LOG_FILE_EXTRA,
    level=logging.INFO
)

class Freez():

    @staticmethod
    async def freeze(freeze_window,client_id,row,req_id):

        try:

            file_name = f"{freeze_window}.log"
            freeze_window_file = f"/home/ubuntu/tsx/data/client/{client_id}/{file_name}"

            with open(freeze_window_file, "w") as f:
                f.write(",".join(map(str, row)) + "\n")

        except Exception:

            logger.exception(f"Writing the files caused issue",
                              extra={"req_id": req_id, "client_id": client_id})

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"File_writing_fails"
            )