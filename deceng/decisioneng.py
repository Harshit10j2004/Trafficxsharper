from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
import os
import logging
import requests
import boto3
import uuid
import time
import base64

load_dotenv(r"/home/ubuntu/tsx/data/data.env")


class SafeFormatter(logging.Formatter):
    def format(self, record):
        record.req_id = getattr(record, 'req_id', '')
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
    ami: list
    server_type: list
    client_id: str
    req_id: str
    joining_token: str
    security_group: list


class Scale_down(BaseModel):
    client_id: int
    instance_id: str
    node_id: str
    email: str
    provider: str


ec2_client = None


def get_ec2():
    global ec2_client
    if ec2_client is None:
        ec2_client = boto3.client("ec2", region_name="ap-south-1")
    return ec2_client


def start_instance_azure(image, total_instances, server_type, pending_file, req_id, client_id, joining_token,
                         security_group_id):
    try:

        userdata_template = """#!/bin/bash

                LOCAL_IP=$(curl -s -H "Metadata:true" "http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/privateIpAddress?api-version=2021-02-01&format=text")

                until systemctl is-active --quiet docker; do sleep 3; done

                docker swarm join \\
                  --token {joining_token} \\
                  --advertise-addr "${{LOCAL_IP}}" \\
                  --data-path-addr "${{LOCAL_IP}}" \\
                  172.31.2.184:2377 || echo "Join failed" >&2
                """

        userdata = userdata_template.format(joining_token=joining_token)
        custom_data = base64.b64encode(userdata.encode('utf-8')).decode('ascii')

        subscription_id = os.getenv("SUB_ID")
        resource_group = os.getenv("RES_GRP")
        location = "eastus"

        subnet_id = os.getenv("SUBNET_ID")

        admin_username = os.getenv("AZURE_NAME")
        admin_password = os.getenv("AZURE_PASS")
        base_vm_name = "TSX-WORKER"

        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        network_client = NetworkManagementClient(credential, subscription_id)

        instance_ids = []

        for i in range(1, total_instances + 1):
            vm_name = f"{base_vm_name}-{client_id}-{i:03d}"

            print(f"Creating VM: {vm_name}")

            nic_name = f"{vm_name}-nic"
            nic_poller = network_client.network_interfaces.begin_create_or_update(
                resource_group,
                nic_name,
                {
                    "location": location,
                    "network_security_group": {"id": security_group_id},
                    "ip_configurations": [{
                        "name": "ipconfig1",
                        "subnet": {"id": subnet_id},

                    }]
                }
            )
            nic = nic_poller.result()

            vm_params = {
                "location": location,
                "hardware_profile": {"vm_size": server_type},
                "storage_profile": {
                    "image_reference": {"id": image},
                    "os_disk": {
                        "create_option": "FromImage",
                        "managed_disk": {"storage_account_type": "Standard_LRS"}
                    }
                },
                "os_profile": {
                    "computer_name": vm_name,
                    "admin_username": admin_username,
                    "admin_password": admin_password,
                    "custom_data": custom_data,

                },
                "network_profile": {
                    "network_interfaces": [{"id": nic.id}]
                }
            }

            vm_poller = compute_client.virtual_machines.begin_create_or_update(
                resource_group, vm_name, vm_params
            )
            vm = vm_poller.result()

            print(f"  → Created: {vm.name}")
            instance_ids.append(vm.name)

            os.makedirs(os.path.dirname(pending_file), exist_ok=True)
            with open(pending_file, "a") as f:
                for name in instance_ids:
                    f.write(name + "\n")
            time.sleep(2)

        return instance_ids

    except Exception:

        logging.exception("Creating vm in azure caused issue",
                          extra={"client_id": client_id, "req_id": req_id})


def start_instance(ami, total_instances, server_type, pending_file, req_id, client_id, security_group, joining_token):
    try:

        userdata_template = """#!/bin/bash

        LOCAL_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)

        until systemctl is-active --quiet docker; do sleep 3; done

        docker swarm join \\
          --token {joining_token} \\
          --advertise-addr "${{LOCAL_IP}}" \\
          --data-path-addr "${{LOCAL_IP}}" \\
          172.31.2.184:2377 || echo "Join failed" >&2
        """

        security_group_main = [security_group]

        userdata = userdata_template.format(joining_token=joining_token)

        response = get_ec2().run_instances(
            ImageId=ami,
            MinCount=1,
            MaxCount=total_instances,
            InstanceType=server_type,
            KeyName=os.getenv("KEY"),
            SecurityGroupIds=security_group_main,
            SubnetId=os.getenv("SUBID"),
            UserData=userdata,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": f"tsx-worker-{client_id}"},

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
            extra={"Req_id": req_id, "client_id": client_id}
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="aws have issue during starting servers "
        )


def health_check(instance_id, req_id, client_id):
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


def pop_next_instance(pending_file, req_id, client_id, instance_id):
    if not os.path.exists(pending_file):
        logging.info(f"Pending file not found: {pending_file}",
                     extra={"Req_id": req_id, "client_id": client_id})
        return False

    with open(pending_file, "r") as f:
        all_ids = [line.strip() for line in f if line.strip()]

    original_count = len(all_ids)
    updated_ids = [iid for iid in all_ids if iid != instance_id]

    if len(updated_ids) == original_count:
        logging.info(f"Instance ID not found in file: {instance_id}",
                     extra={"Req_id": req_id, "client_id": client_id})
        return False

    if updated_ids:
        with open(pending_file, "w") as f:
            for iid in updated_ids:
                f.write(iid + "\n")
        logging.info(f"Removed {instance_id} — {len(updated_ids)} remaining",
                     extra={"Req_id": req_id, "client_id": client_id})

    return True

def removing_instance(id, client_id, req_id):
    try:

        InstanceIds = [id.strip()]
        get_ec2().terminate_instances(
            InstanceIds=InstanceIds
        )

        logging.info("instance is terminated sucessfully",
                     extra={"Req_id": req_id, "client_id": client_id, "instance_id": id}
                     )

    except Exception:
        logging.exception(
            "Issue raised during terminating the instances from aws",
            extra={"req_id": req_id, "client_id": client_id}
        )


def removing_instance_azure(id, client_id, req_id):
    try:

        credential = DefaultAzureCredential()
        subscription_id = os.getenv("SUB_ID")

        resource_client = ResourceManagementClient(credential, subscription_id)

        vm_resource_id = f"/subscriptions/{subscription_id}/resourceGroups/providers/Microsoft.Compute/virtualMachines/{id}"

        poller = resource_client.resources.begin_delete_by_id(
            resource_id=vm_resource_id
        )

        poller.wait()
    except Exception:
        logging.exception(
            "Issue raised during terminating the vm from azure",
            extra={"req_id": req_id, "client_id": client_id}
        )


def mail(email, client_id, req_id, scale_message, total_instances):
    try:
        payload = {
            "email": email,
            "client_id": client_id,
            "total_instances": total_instances,
            "req_id": req_id,
            "scale": scale_message

        }

        url = os.getenv("URL")

        r = session.post(url, json=payload, timeout=10)
        r.raise_for_status()

        return {
            "status": "requsted"
        }

    except Exception:

        logging.exception("mailing api failed",
                          extra={"client_id": client_id, "req_id": req_id})

        raise


@deceng.post("/deceng")
def decengfunc(metrics: Metrics, bg: BackgroundTasks):
    scale_message = metrics.scale_message
    email = metrics.email
    total_instances = metrics.total_instance
    ami = metrics.ami
    server_type = metrics.server_type
    client_id = metrics.client_id
    req_id = metrics.req_id
    joining_token = metrics.joining_token
    security_group = metrics.security_group

    base_path = f"/home/ubuntu/tsx/data/instances/{client_id}"
    pending_file = f"{base_path}/pending.txt"

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

    try:

        scale = "UP"

        instance_for_aws = int(total_instances/2)
        instance_for_azure = total_instances - instance_for_aws

        aws_ami = ami[0]
        azure_ami = ami[1]

        aws_sec = security_group[0]
        azure_sec = security_group[1]

        aws_st = server_type[0]
        azure_st = server_type[1]

        instance_id = start_instance(
            aws_ami,
            instance_for_aws,
            aws_st,
            pending_file,
            req_id,
            client_id,
            joining_token,
            aws_sec
        )

        instance_id_azure = start_instance_azure(
            azure_ami,
            instance_for_azure,
            azure_st,
            pending_file,
            req_id,
            client_id,
            joining_token,
            azure_sec
        )

        print(f"instance started {instance_id}")
        print(f"instance started {instance_id_azure}")

        email = mail(email, client_id, scale, req_id, scale_message, total_instances)



    except Exception:
        logging.exception(
            "AWS caused issue during scaling",
            extra={"req_id": req_id, "client_id": client_id}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="aws issue"
        )


@deceng.post("/deceng_down")
def scale_down(metrics: Scale_down):
    scale_message = "DOWN"
    client_id = metrics.client_id
    instance_id = metrics.instance_id
    node_id = metrics.node_id
    email = metrics.email
    provider = metrics.provider

    req_id = str(uuid.uuid4())
    base_path = f"/home/ubuntu/tsx/data/instances/{client_id}"
    pending_file = f"{base_path}/pending.txt"

    try:

        if provider == "AWS":

            offboard = removing_instance(instance_id, req_id, client_id)

            logging.info(f"The instances is deleted for client",
                     extra={"req_id": req_id, "client_id": client_id, "instance_id": instance_id, "node_id": node_id})

        if provider == "AZURE":

            offboard = removing_instance_azure(instance_id, req_id, client_id)

            logging.info(f"The instances is deleted for client",
                         extra={"req_id": req_id, "client_id": client_id, "instance_id": instance_id,
                                "node_id": node_id})

        file_del = pop_next_instance(pending_file, req_id, client_id, instance_id)

        logging.info(f"The instances is cleared from record",
                     extra={"req_id": req_id, "client_id": client_id, "instance_id": instance_id, "node_id": node_id})

        email = mail(email, client_id, req_id, scale_message, total_instances=1)

    except Exception:

        logging.exception(
            "AWS caused issue during offboard",
            extra={"req_id": req_id, "client_id": client_id}
        )