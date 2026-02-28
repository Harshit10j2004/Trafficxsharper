from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import random
import time

class Data(BaseModel):

    node_id: str

app = FastAPI()

def get_all_node_ids():
    output = subprocess.check_output(
        ["docker", "node", "ls", "--format", "{{.ID}} {{.Status}}"]
    ).decode()
    lines = output.strip().split("\n")
    return [line.split()[0] for line in lines if "Ready" in line]

def get_node_load(node_id: str):
    try:

        stats = subprocess.check_output(
            ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}} {{.MemPerc}}"]
        ).decode().strip().split()
        if len(stats) >= 2:
            cpu_str, mem_str = stats[0], stats[1]
            cpu = float(cpu_str.rstrip('%'))
            mem = float(mem_str.rstrip('%'))
            return cpu, mem
    except:
        pass
    return 0.0, 0.0

def wait_for_drain(node_id, timeout, interval):
    start = time.time()
    while time.time() - start < timeout:
        try:

            result = subprocess.run(
                ["docker", "node", "ps", node_id, "--format", "{{.ID}}"],
                capture_output=True, text=True, check=True
            )
            if not result.stdout.strip():
                print(f"Node {node_id} fully drained")
                return True
            print(f"Still {len(result.stdout.splitlines())} tasks on {node_id}...")
        except subprocess.CalledProcessError:
            pass
        time.sleep(interval)

    raise TimeoutError(f"Timeout waiting for {node_id} to drain after {timeout}s")

@app.post("/manager")
def removing_node(data:Data):

    node_id = Data.node_id

    node_status = subprocess.check_output(["docker", "node", "inspect", node_id, "--format", "{{.Status.State}}"]).decode().strip()

    if node_status != "ready":

        return {"approved": False}

    nodes = get_all_node_ids()
    other_nodes = [n for n in nodes if n != node_id]

    if len(other_nodes) == 0:
        return {"approved": False}

    sample_size = min(5, len(other_nodes))
    sampled_nodes = random.sample(other_nodes, sample_size)

    busy_count = 0
    MAX_ALLOWED_LOAD = 65

    for node in sampled_nodes:
        cpu, mem = get_node_load(node)
        if cpu > MAX_ALLOWED_LOAD or mem > MAX_ALLOWED_LOAD:
            busy_count += 1

    if busy_count >= sample_size // 2 + 1:
        return {
            "approved": False,
            "reason": f"{busy_count}/{sample_size} other nodes are too busy (> {MAX_ALLOWED_LOAD}%)"
        }
    subprocess.run(["docker", "node", "update", "--availability", "drain", node_id], check=True)

    wait_for_drain(node_id,timeout=900,interval=30)

    return {
        "approved": True,
        "reason": f"draining started — {len(sampled_nodes)} other nodes checked, load looks OK"
    }
