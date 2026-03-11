#!/bin/bash
set -euo pipefail
HEADERS="Metadata: true"

API_VERSION="2025-04-07"


VM_ID=$(curl -s -H "$HEADERS" --noproxy "*" \
    "http://169.254.169.254/metadata/instance/compute/vmId?api-version=$API_VERSION&format=text")

if [ -z "$VM_ID" ]; then
    VM_ID=$(curl -s -H "$HEADERS" --noproxy "*" \
        "http://169.254.169.254/metadata/instance/compute?api-version=$API_VERSION" | \
        grep -oP '(?<="vmId": ")[^"]+')
fi

NODE_ID=$(docker info --format '{{.Swarm.NodeID}}')

echo "{$VM_ID , AZURE}"   > /home/ubuntu/tsx/data/my-instance-id.txt
echo "$NODE_ID" > /home/ubuntu/tsx/data/node_id.txt

