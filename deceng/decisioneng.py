from fastapi import FastAPI, HTTPException,status
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

load_dotenv(r"")


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE"),
    filemode='a'
)


deceng = FastAPI()

class Metrics(BaseModel):

    message: str

@deceng.post("/deceng")
def decengfunc(metrics: Metrics):

    try:

        message = metrics.message

        file=os.getenv("FILE")

        with open(file , "w") as f:

            f.write(f"scale {message}")

        print("deccision engine")

    except Exception as e:

        logging.debug(f"error occured in decision engine {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"issue {str(e)}"
        )