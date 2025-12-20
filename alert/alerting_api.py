from fastapi import FastAPI,HTTPException,status
from dotenv import load_dotenv
from pydantic import BaseModel
from email.mime.text import MIMEText
import os
import smtplib
import logging


load_dotenv(r"C:\Users\harsh\OneDrive\Desktop\envs\healthcheck.env")

logging.basicConfig(
    level= logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename = os.getenv("LOG_FILE"),
    filemode='a'
)



sender = os.getenv("MAIL")
app_password = os.getenv("PASSWORD")

class AlertData(BaseModel):

    email: str
    total_instances: int
    scale: str

emailapp = FastAPI()

def mainmail(data=AlertData):

    email = data.email
    total_instance = data.total_ins
    scale = data.scale

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
    except Exception as e:
        print(e)

