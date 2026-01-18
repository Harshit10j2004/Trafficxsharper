#!/bin/bash
set -euo pipefail

source /home/ubuntu/data.env

SERVER_ID="$(cat "$Server_id")"
timestamp=$(date +%s)

STATUS_URL="http://127.0.0.1/__nginx_status"
raw="$(curl -sf "$STATUS_URL")"

active=$(echo "$raw" | awk '/Active connections/ {print $3}')
accepts=$(echo "$raw" | awk 'NR==3 {print $1}')
handled=$(echo "$raw" | awk 'NR==3 {print $2}')
requests=$(echo "$raw" | awk 'NR==3 {print $3}')
reading=$(echo "$raw" | awk '/Reading:/ {print $2}')
writing=$(echo "$raw" | awk '/Writing:/ {print $4}')
waiting=$(echo "$raw" | awk '/Waiting:/ {print $6}')

line="$timestamp,$active,$accepts,$handled,$requests,$reading,$writing,$waiting,$SERVER_ID"

{
  echo "nginx_${SERVER_ID}.log"
  echo "$line"
} | ncat "$rec_ip" 9001