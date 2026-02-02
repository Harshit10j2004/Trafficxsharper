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

    instances = load_catalog()

    matches = filter_instances(
        instances,
        cpu_min, cpu_max,
        ram_min, ram_max,
        network,
        workload
    )

    if not matches:
        return ("issues with config best")

    best = matches[0]

    


