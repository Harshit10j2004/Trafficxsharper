from fastapi import FastAPI, HTTPException,status
from pydantic import BaseModel
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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

retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET", "POST"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)


deceng = FastAPI()

class Metrics(BaseModel):

    message: str
    email: str
    total_instance: int
    ami: str
    server_type: str


@deceng.post("/deceng")
def decengfunc(metrics: Metrics):



        message = metrics.message
        email = metrics.email
        total_instances = metrics.total_instance
        ami = metrics.ami
        server_type = metrics.server_type

        file=os.getenv("FILE")

        try:


            ec2 = boto3.client("ec2",region_name="ap-south-1")
            response = ec2.run_instances(
                ImageId=ami,
                MinCount=1,
                MaxCount=total_instances,
                InstanceType=server_type,
                KeyName=os.getenv("KEY"),
                SecurityGroupIds=[os.getenv("SG")],
                SubnetId=os.getenv("SUBID"),
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": "tsx-worker-1"},

                        ]
                    }
                ]
            )

            instance_id = response["Instances"][0]["InstanceId"]

        except Exception as e:

            logging.error(f"AWS caused issue: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="aws have issue"
            )

        with open(file , "w") as f:

            f.write(f"scale {message}")
            f.write(f"instance {instance_id}")

        payload = {
            "email": email,
            "total_instances": total_instances,
            "scale": "UP"

        }

        url = os.getenv("URL")

        r = session.post(url,json=payload,timeout=1)
        r.raise_for_status()

