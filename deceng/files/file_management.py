import os
import logging
from setting.loggers import LoggerFactory
from setting.conifg import settings

logger = LoggerFactory.get_logger(
    name="files_filemanagement",
    log_file=settings.LOG_FILE_MAIL,
    level=logging.INFO
)

class File():

    @staticmethod
    async def pop_next_instance(pending_file, req_id, client_id, instance_id):
        if not os.path.exists(pending_file):
            logger.info(f"Pending file not found: {pending_file}",
                         extra={"Req_id": req_id, "client_id": client_id})
            return False

        with open(pending_file, "r") as f:
            all_ids = [line.strip() for line in f if line.strip()]

        original_count = len(all_ids)
        updated_ids = [iid for iid in all_ids if iid != instance_id]

        if len(updated_ids) == original_count:
            logger.info(f"Instance ID not found in file: {instance_id}",
                         extra={"Req_id": req_id, "client_id": client_id})
            return False

        if updated_ids:
            with open(pending_file, "w") as f:
                for iid in updated_ids:
                    f.write(iid + "\n")
            logger.info(f"Removed {instance_id} — {len(updated_ids)} remaining",
                         extra={"Req_id": req_id, "client_id": client_id})

        return True
