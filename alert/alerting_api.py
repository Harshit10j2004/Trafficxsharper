from fastapi import FastAPI,HTTPException,status
from dotenv import load_dotenv
from pydantic import BaseModel
from email.mime.text import MIMEText
import os
import smtplib
import logging


load_dotenv(r"/home/ubuntu/tsx/data/data.env")

logging.basicConfig(
    level= logging.INFO,
    format='%(asctime)s - %(levelname)s - req_id=%(req_id)s client_id=%(client_id)s - %(message)s',
    filename = os.getenv("LOG_FILE"),
    filemode='a'
)



sender = os.getenv("MAIL")
app_password = os.getenv("PASSWORD")

class AlertData(BaseModel):

    email: str
    total_instances: int
    scale: str
    client_id: int
    req_id:str
    message: str

emailapp = FastAPI()

@emailapp.post("/email")
def mainmail(data:AlertData):


    email = data.email
    total_instance = data.total_instances
    scale = data.scale
    client_id = data.client_id
    req_id = data.req_id


    logging.info(
        "alertapi request received",
        extra={
            "req_id": req_id,
            "client_id": client_id,
            "email": email,
            "total_instance": total_instance,
            "scale": scale
        }
    )

    subject = f"TSX Alert: Infrastructure Scaled {scale}"
    body = (f"Hello,This is an automated alert from TSX.Your infrastructure has been scaled {scale} due to observed or predicted load conditions crossing the configured threshold, total instances scaled {scale} are {total_instance}")

    message = MIMEText(body, "plain")
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, app_password)
            server.sendmail(sender, email, message.as_string())

        logging.info(
            "alert email sent",
            extra={
                "req_id": req_id,
                "client_id": client_id,
                "total_instance": total_instance,
                "scale": scale
            }
        )
    except smtplib.SMTPAuthenticationError:
        logging.exception("SMTP authentication failed",
                          extra={"client_id": client_id, "req_id": req_id, "email": email}
                          )
        raise HTTPException(status_code=503, detail="email auth failed")

    except smtplib.SMTPConnectError:
        logging.exception("SMTP connection failed",
                          extra={"client_id": client_id, "req_id": req_id, "email": email}
                          )
        raise HTTPException(status_code=503, detail="email server unreachable")

    except Exception:
        logging.exception("Unknown email error",
                          extra={"client_id": client_id, "req_id": req_id, "email": email}
                          )
        raise HTTPException(status_code=503, detail="email service failed")


