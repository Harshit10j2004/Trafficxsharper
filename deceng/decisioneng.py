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

ec2 = boto3.client("ec2", region_name="ap-south-1")
elbv2 = boto3.client('elbv2')


def start_instance(ami,total_instances,server_type,pending_file):
    try:


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

        instance_ids = [i["InstanceId"] for i in response["Instances"]]

        os.makedirs(os.path.dirname(pending_file), exist_ok=True)
        with open(pending_file, "a") as f:
            for iid in instance_ids:
                f.write(iid + "\n")

        return instance_ids

        return instance_ids
    except Exception as e:

        logging.error(f"AWS caused issue during starting the server: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="aws have issue during starting servers "
        )

def health_check(instance_id):

    waiter = ec2.get_waiter("instance_status_ok")
    waiter.wait(
        InstanceIds=[instance_id],
        WaiterConfig={
            "Delay": 10,
            "MaxAttempts": 30
        }
    )

    return "healthy"

def register_to_alb(instance_id, port):
    elbv2.register_targets(
        TargetGroupArn=os.getenv("ALB"),
        Targets=[{"Id": instance_id, "Port": port}]
    )

def pop_next_instance(pending_file):
    if not os.path.exists(pending_file):
        return None

    with open(pending_file, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        return None

    iid = lines[0]

    with open(pending_file, "w") as f:
        for l in lines[1:]:
            f.write(l + "\n")

    return iid

def process_instances(pending_file, joined_file, port=80):
    while True:
        instance_id = pop_next_instance(pending_file)

        if not instance_id:
            break

        try:
            health_check(instance_id)

            register_to_alb(instance_id, port)

            with open(joined_file, "a") as f:
                f.write(instance_id + "\n")

            logging.info(f"{instance_id} joined ALB")

        except Exception as e:
            logging.error(f"{instance_id} failed onboarding: {str(e)}")



@deceng.post("/deceng")
def decengfunc(metrics: Metrics):


        message = metrics.message
        email = metrics.email
        total_instances = metrics.total_instance
        ami = metrics.ami
        server_type = metrics.server_type
        client_id = metrics.client_id

        file=os.getenv("FILE")
        base_path = f"/home/ubuntu/tsx/data/instances/{client_id}"
        pending_file = f"{base_path}/pending.txt"
        joined_file = f"{base_path}/joined.txt"

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

            logging.debug(f"Error occur during send data to alert api {str(e)}")


        try:

            instance_id = start_instance(
                ami,
                total_instances,
                server_type,
                pending_file
            )

            process_instances(pending_file, joined_file)

            return {
                "status": "scaled_up",
                "instances": instance_id
            }

        except Exception as e:
            logging.error(f"aws issue caused error {str(e)}")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="aws issue"
            )