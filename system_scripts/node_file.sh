#!/bin/bash
set -euo pipefail

source /home/ubuntu/tsx/data/data.env


cpu_thresold=20
mem_thresold=20
NODE_ID=$(docker info --format '{{.Swarm.NodeID}}')


INSTANCE_ID_FILE="/home/ubuntu/tsx/data/my-instance-id.txt"

if [ ! -f "$INSTANCE_ID_FILE" ]; then
    echo "Error: Instance ID file not found!" >&2
    exit 1
fi

INSTANCE_ID=$(cat "$INSTANCE_ID_FILE" | tr -d '[:space:]')

if [ -z "$INSTANCE_ID" ]; then
    echo "Error: Empty instance ID in file" >&2
    exit 1
fi

low_count=0

while true; do

  cpu_used=$(echo "100 - $cpu_idle" | bc)
  mem_used=$(free -m | awk '/Mem:/ {print $3}')

  if(((cpu_thresold > cpu_used) && (mem_thresold > mem_used))); then

    low_count=low_count+1

  else
    low_count = 0

  fi

  if((low_count>3)); then

    response=$(curl -s -X POST "$MANAGER_URL" -H "Content-Type: application/json" \
      -d "{\"node_id\": \"$NODE_ID\"}")

    if echo "$response" | grep -q '"approved": true'; then

      echo "Approved → leaving swarm"
      docker swarm leave --force

      response=$(curl -s -X POST "$dec_eng" -H "Content-Type: application/json" \
        -d "{\"node_id\": \"$NODE_ID\" , \"instance_id\": \"$INSTANCE_ID\"}")

    else

      low_count=0
    fi
  fi

  sleep 300

done

