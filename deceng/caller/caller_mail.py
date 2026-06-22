import logging
from setting.session import get_session
from setting.conifg import settings
from setting.loggers import LoggerFactory


logger = LoggerFactory.get_logger(
    name="caller_mail",
    log_file=settings.LOG_FILE_MAIL,
    level=logging.INFO
)


session = get_session()

class Mail():

    @staticmethod
    async def mail(email, client_id, req_id, scale_message, total_instances):
        try:
            payload = {
                "email": email,
                "client_id": client_id,
                "total_instances": total_instances,
                "req_id": req_id,
                "scale": scale_message

            }

            url = settings.URL

            headers = {"X-Request-ID": req_id}

            r = session.post(url, json=payload, timeout=10, headers=headers)
            r.raise_for_status()

            return {
                "status": "requsted"
            }

        except Exception:

            logging.exception("mailing api failed",
                              extra={"client_id": client_id, "req_id": req_id})

            raise