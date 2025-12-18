from fastapi import FastAPI
from pydantic import BaseModel

deceng = FastAPI()

class Metrics(BaseModel):

    message: str

@deceng.post("/deceng")
def decengfunc(metrics: Metrics):

    message = metrics.message

    file="/home/ubuntu/tsx/data/test.txt"

    with open(file , "w") as f:

        f.write(f"scale {message}")

    print("deccision engine")