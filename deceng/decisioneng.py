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
    client_id: int


@deceng.post("/deceng")
def decengfunc(metrics: Metrics):


        message = metrics.message
        email = metrics.email
        total_instances = metrics.total_instance
        ami = metrics.ami
        server_type = metrics.server_type
        client_id = metrics.client_id

        file=os.getenv("FILE")
        ins_ids = f"/home/ubuntu/tsx/data/instances/{client_id}/instance.json"

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

            instance_ids = [
                inst["InstanceId"] for inst in response["Instances"]
            ]

            with open(ins_ids,"a") as f:

                f.write(",".join(map(str, instance_ids)) + "\n")

        except Exception as e:

            logging.error(f"AWS caused issue during starting the server: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="aws have issue during starting servers "
            )

        with open(file , "w") as f:

            f.write(f"scale {message}")
            f.write(f"instance {instance_ids}")

        try:
            client = boto3.client('elbv2')

            response = client.register_targets(
                TargetGroupArn=os.getenv("ALB"),
                Targets=[
                    {"Id": iid, "Port": 80} for iid in instance_ids
                ]
            )
        except Exception as e:

            logging.error(f"AWS caused issue during adding servers into the alb: {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="aws have issue during connecting to alb "
            )

        try:

            payload = {
                "email": email,
                "total_instances": total_instances,
                "scale": "UP"

            }

            url = os.getenv("URL")

            r = session.post(url,json=payload,timeout=1)
            r.raise_for_status()

        except Exception as e:

            logging.debug("Error occur during send data to alert api",{str(e)})

