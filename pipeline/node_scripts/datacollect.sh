#!/bin/bash
set -euo pipefail

source /home/ubuntu/data.env

ID_FILE="$Server_id"
mkdir -p "$(dirname "$ID_FILE")"

if [ ! -f "$ID_FILE" ]; then
  uuidgen > "$ID_FILE"
fi

SERVER_ID="$(cat "$ID_FILE")"
export SERVER_ID

timestamp=$(date +%s)

cpu_idle=$(mpstat 1 1 | awk '/Average/ {print $12}')
cpu_used=$(echo "100 - $cpu_idle" | bc)

mem_total=$(free -m | awk '/Mem:/ {print $2}')
mem_used=$(free -m | awk '/Mem:/ {print $3}')

disk_used=$(df -h --total | awk '/total/ {gsub("%","",$5); print $5}')

IFACE=$(ip route get 1.1.1.1 | awk '{print $5; exit}')
read net_in net_out < <(
  awk -v iface="$IFACE" '$1 ~ iface":" {print $2, $10}' /proc/net/dev
)

connections=$(ss -H state established | wc -l)

line="$timestamp,$cpu_used,$cpu_idle,$mem_total,$mem_used,$disk_used,$net_in,$net_out,$connections,$SERVER_ID"

{
  echo "usage_${SERVER_ID}.log"
  echo "$line"
} | ncat "$rec_ip" 9000