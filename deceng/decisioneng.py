from fastapi import FastAPI, HTTPException,status,BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import logging
import requests
import boto3

load_dotenv(r"/home/ubuntu/tsx/data/data.env")

class SafeFormatter(logging.Formatter):
    def format(self, record):
        record.req_id    = getattr(record, 'req_id',    '')
        record.client_id = getattr(record, 'client_id', '')
        return super().format(record)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

file_handler = logging.FileHandler(
    os.getenv("LOG_FILE"),
    mode='a',
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(SafeFormatter(
    '%(asctime)s - %(levelname)s - req_id=%(req_id)s client_id=%(client_id)s - %(message)s'
))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(SafeFormatter(
    '[%(asctime)s] %(levelname)-5s req_id=%(req_id)s client=%(client_id)s %(message)s'
))

root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

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

    scale_message: str
    email: str
    total_instance: int
    ami: str
    server_type: str
    client_id: str
    req_id: str

ec2_client = None
elbv2_client = None

def get_ec2():
    global ec2_client
    if ec2_client is None:
        ec2_client = boto3.client("ec2", region_name="ap-south-1")
    return ec2_client

def get_elbv2():
    global elbv2_client
    if elbv2_client is None:
        elbv2_client = boto3.client("elbv2", region_name="ap-south-1")
    return elbv2_client


def start_instance(ami,total_instances,server_type,pending_file,req_id,client_id):
    try:


        response = get_ec2().run_instances(
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


    except Exception:

        logging.exception(
            "AWS caused issue during starting the server",
            extra={"Req_id":req_id,"client_id":client_id}
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="aws have issue during starting servers "
        )

def health_check(instance_id,req_id,client_id):

    try:

        waiter = get_ec2().get_waiter("instance_status_ok")
        waiter.wait(
            InstanceIds=[instance_id],
            WaiterConfig={
                "Delay": 10,
                "MaxAttempts": 30
            }
        )

        return "healthy"
    except Exception:

        logging.exception("EC2 waiting time caused error",
                          extra={"Req_id": req_id, "client_id": client_id}
                          )
        raise

def register_to_alb(instance_id, port,req_id,client_id):
    try:

        get_elbv2().register_targets(
            TargetGroupArn=os.getenv("ALB"),
            Targets=[{"Id": instance_id, "Port": port}]
        )
        logging.info("instance connected to ALB",
                     extra={"Instance_id":instance_id,"Req_id": req_id, "client_id": client_id}
                     )
    except Exception:

        logging.exception("AWS caused during registering during alb")
        raise

def pop_next_instance(pending_file,req_id,client_id):
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
    logging.info(
        "Popped instance from pending queue",
        extra={"instance_id": iid, "remaining": len(lines),"req_id":req_id,"client_id":client_id}
    )

    return iid

def process_instances(pending_file, joined_file,req_id, client_id,port=80):
    while True:
        instance_id = pop_next_instance(pending_file,req_id,client_id)

        if not instance_id:
            break

        try:
            health_check(instance_id,req_id,client_id)

            register_to_alb(instance_id, port,req_id,client_id)

            with open(joined_file, "a") as f:
                f.write(instance_id + "\n")


        except Exception:
            logging.exception(
                "Issue raised during onboarding",
                extra={"Instance": instance_id,"req_id":req_id,"client_id":client_id}
            )

def removing_instance(id,client_id,req_id):

    try:
        targets = [{"Id": iid} for iid in id]

        get_ec2().terminate_instances(
            InstanceIds=targets
        )

        logging.info("instance disconnected to ALB are terminated sucessfully",
                     extra={"Req_id": req_id, "client_id": client_id}
                     )

    except Exception:
        logging.exception(
            "Issue raised during terminating the instances",
            extra={"req_id": req_id, "client_id": client_id}
        )

def unregistring(joined_file ,req_id,client_id):

    try:

        with open(joined_file, "r") as f:
            instance_ids = [line.strip() for line in f if line.strip()]

        total = len(instance_ids)
        remove_count = max(1, total // 4)

        ids_to_remove = instance_ids[:remove_count]
        remaining_ids = instance_ids[remove_count:]

        with open(joined_file, "w") as f:
            if remaining_ids:
                f.write("\n".join(remaining_ids) + "\n")

        targets = [{"Id": iid} for iid in ids_to_remove]

        get_elbv2().deregister_targets(
            TargetGroupArn=os.getenv("ALB"),
            Targets=targets
        )
        logging.info("instance disconnected to ALB",
                     extra={"Req_id": req_id, "client_id": client_id}
        )

        terminating = removing_instance(ids_to_remove,client_id, req_id)
        print("Scale down sucessfull")

    except Exception:

        logging.exception(
            "Issue raised during offboarding",
            extra={"req_id": req_id, "client_id": client_id}
        )


@deceng.post("/deceng")
def decengfunc(metrics: Metrics,bg:BackgroundTasks):


        scale_message = metrics.scale_message
        email = metrics.email
        total_instances = metrics.total_instance
        ami = metrics.ami
        server_type = metrics.server_type
        client_id = metrics.client_id
        req_id = metrics.req_id

        base_path = f"/home/ubuntu/tsx/data/instances/{client_id}"
        pending_file = f"{base_path}/pending.txt"
        joined_file = f"{base_path}/joined.txt"

        scale = None


        logging.info(
            "DECENG request received",
            extra={
                "req_id": req_id,
                "client_id": client_id,
                "total_instances": total_instances,
                "ami": ami,
                "server_type": server_type,
                "scale_action": scale_message
            }
        )

        print(f"REQUEST ARRIVED {client_id} and generated requested id is {req_id} for server {scale_message}")

        if(scale_message == "UP"):

            try:

                scale = "UP"


                instance_id = start_instance(
                    ami,
                    total_instances,
                    server_type,
                    pending_file,
                    req_id,
                    client_id
                )

                print(f"instance started {instance_id}")

                bg.add_task(process_instances, pending_file, joined_file,req_id,client_id)

            except Exception:
                logging.exception(
                    "AWS caused issue during scaling",
                    extra={"req_id": req_id, "client_id": client_id}
                )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="aws issue"
                )

        elif(scale_message == "DOWN"):

            scale = "DOWN"

            try:

                offboard = unregistring(joined_file, req_id, client_id)

            except Exception:

                logging.exception(
                    "AWS caused issue during offboard",
                    extra={"req_id": req_id, "client_id": client_id}
                )

        try:

            payload = {
                    "email": email,
                    "client_id": client_id,
                    "total_instances": total_instances,
                    "scale": scale,
                    "req_id": req_id,
                    "message": scale_message

            }

            url = os.getenv("URL")

            r = session.post(url,json=payload,timeout=10)
            r.raise_for_status()

            return {
                    "status": "requsted"
            }

        except Exception:

            logging.exception("Failed to notify alert service",
                                  extra={"client_id":client_id,"req_id":req_id}
                                  )
