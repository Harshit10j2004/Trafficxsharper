from fastapi import FastAPI, HTTPException,status
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging
import requests
import boto3

load_dotenv(r"/home/ubuntu/tsx/data/data.env")


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.getenv("LOG_FILE"),
    filemode='a'
)


deceng = FastAPI()

class Metrics(BaseModel):

    message: str
    email: str
    total_inc: int


@deceng.post("/deceng")
def decengfunc(metrics: Metrics):

    try:

        message = metrics.message
        email = metrics.email
        total_instances = metrics.total_inc

        file=os.getenv("FILE")



        ec2 = boto3.client("ec2",region_name="ap-south-1")
        instances = ec2.create_instances(
            ImageId="ami-0978e5f7af7072347",
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName="mainkey",
            SecurityGroupIds=["sg-0664a235a9ca9ca86"],
            SubnetId="subnet-0b157a1fb9dcbaf2e",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": "tsx-worker-1"},

                    ]
                }
            ]
        )

        instance = instances[0]

        with open(file , "w") as f:

            f.write(f"scale {message}")
            f.write(f"instance {instance}")

        payload = {
            "email": email,
            "total_instances": total_instances,
            "scale": "UP"

        }

        url = os.getenv("URL")

        r = requests.post(url,json=payload,timeout=1)
        r.raise_for_status()

    except Exception as e:

        logging.debug(f"error occured in decision engine {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"issue {str(e)}"
        )