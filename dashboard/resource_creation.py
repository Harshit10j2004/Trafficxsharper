from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import boto3

class Information(BaseModel):

    cpu: str
    ram: str
    storage: int
    network: str
    workload: str
    inbound: list[int]
    outbound: list[int]
    tools: list[str]


app = FastAPI()

CATALOG_PATH = Path("/home/ubuntu/tsx/catalog/aws_instance_catalog.json")
ec2 = boto3.client("ec2", region_name="ap-south-1")

def load_catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)["instances"]

def parse_range(value: str):

    try:
        low, high = value.split("-")
        return int(low), int(high)
    except Exception:
        raise ValueError(f"Invalid range format: {value}")

def filter_instances(instances, cpu_min, cpu_max, ram_min, ram_max, network, workload):
    candidates = []

    for inst in instances:
        if not (cpu_min <= inst["vcpu"] <= cpu_max):
            continue

        if not (ram_min <= inst["memory_gb"] <= ram_max):
            continue

        if inst["network_class"] != network:
            continue

        if workload not in inst["workload_fit"]:
            continue

        candidates.append(inst)

    return candidates

def build_user_data(tools: list[str]):
    try:
        script = [
            "#!/bin/bash",
            "set -e",
            "apt-get update -y"
        ]

        if tools:
            joined_tools = " ".join(tools)
            script.append(f"apt-get install -y {joined_tools}")


        return "\n".join(script)
    except Exception as e:
        print(e)
        print("from script")


def create_sg(inbound,outbound):

    response = ec2.create_security_group(
        GroupName="tsx-client-1-sg",
        Description="TSX managed security group for client 1",
        VpcId="vpc-090749b4fff3f9d4e"
    )

    sg_id = response["GroupId"]

    ip_permissions = []

    for port in inbound:
        ip_permissions.append({
            "IpProtocol": "tcp",
            "FromPort": int(port),
            "ToPort": int(port),
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        })
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=ip_permissions
    )

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ]
    )

    out_ip_permission = []

    for port in outbound:

        if port == "all":
            out_ip_permission.append({
                "IpProtocol": -1,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            })

        else:
            out_ip_permission.append({
                "IpProtocol": "tcp",
                "FromPort": int(port),
                "ToPort": int(port),
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            })

    if out_ip_permission:
        ec2.authorize_security_group_egress(
            GroupId=sg_id,
            IpPermissions=out_ip_permission
        )

    return sg_id


def start_instance(server_type,security_group,tools):

    try:

        userdata = build_user_data(tools)


        response = ec2.run_instances(
            ImageId="ami-07d0c4554fe3e78ec",
            MinCount=1,
            MaxCount=1,
            InstanceType=server_type,
            KeyName="new_key",
            SecurityGroupIds=[security_group],
            SubnetId="subnet-064758303e390dd6b",
            UserData = userdata,
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
        return instance_id


    except Exception as e:

        print(e)
        raise

def image_creation(instance_id):

    response = ec2.create_image(
        InstanceId=instance_id,
        Name="tsx-client-1-base-ami",
        Description="TSX client base AMI with tools preinstalled",
        NoReboot=True
    )

    return response

@app.post("/creation")

def main(data:Information):

    workload = data.workload
    cpu = data.cpu
    ram = data.ram
    storage = data.storage
    network = data.network
    inbound = data.inbound
    outbound = data.outbound
    tools = data.tools

    cpu_min, cpu_max = parse_range(cpu)
    ram_min, ram_max = parse_range(ram)

    # instances = load_catalog()
    #
    # matches = filter_instances(
    #     instances,
    #     cpu_min, cpu_max,
    #     ram_min, ram_max,
    #     network,
    #     workload
    # )
    #
    # if not matches:
    #     return ("issues with config best")

    best = "t3.micro"

    security_group = create_sg(inbound,outbound)

    instances = start_instance(best,security_group,tools)

    ami = image_creation(instances)

    return {
        "security_group": security_group,
        "ami": ami
    }

    


