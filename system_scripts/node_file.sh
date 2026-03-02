#!/bin/bash
set -x

source /home/ubuntu/tsx/data/data.env


cpu_thresold=20
mem_thresold=20

NODE_ID_FILE="/home/ubuntu/tsx/data/node_id.txt"
NODE_ID=$(cat "$NODE_ID_FILE" | tr -d '[:space:]')

echo "hitpoint 1"
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

  echo "hitpoint2"

  cpu_idle=$(mpstat 1 1 | awk '/Average/ {print $12}')
  cpu_used=$(echo "100 - $cpu_idle" | bc)
  mem_used=$(free -m | awk '/Mem:/ {print $3}')

  cpu_used_int=${cpu_used%%.*}
  mem_used_int=${mem_used%%.*}

  if (( cpu_thresold > cpu_used_int )); then

    ((low_count++))

    echo "hitpoint3"

  else
    low_count=0
    echo "hitpoint4"

  fi

  if((low_count>3)); then

    echo "hitpoint5"

    response=$(curl -s -X POST "$MANAGER_URL" -H "Content-Type: application/json" \
      -d "{\"node_id\": \"$NODE_ID\"}")

    if echo "$response" | grep -q '"approved": true'; then

      echo "Approved → leaving swarm"
      ./leaving.sh /home/ubuntu/tsx/codes

      response=$(curl -s -X POST "$dec_eng" -H "Content-Type: application/json" \
        -d "{\"node_id\": \"$NODE_ID\" , \"instance_id\": \"$INSTANCE_ID\", \"email\": \"$EMAIL\",\"client_id\": \"$CLIENT_ID\" }")

    else

      low_count=0
    fi
  fi

  sleep 10

done

