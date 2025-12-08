#!/bin/bash

set -x

data="/home/ubuntu/syslogs/sysscrlog/usage.log"

timestamp=$(date "+%Y-%m-%d %H:%M:%S.%3N")

cpu=$(mpstat 1 1 | grep Average | awk '{print $12}')
cpu_used_percent=$(echo "100 - $cpu" | bc)

mem=$(free -m | grep Mem | awk '{print $2}')
mem_used=$(free -m | grep Mem | awk '{print $3}')
disk=$(df -h --total | grep total | awk '{print $5}')
network_stats=$(ifstat -b 1 1 2>/dev/null | awk 'NR==3 {print $1, $2}')
network_in_bytes=$(echo $network_stats | awk '{printf "%.0f", $1 * 1024}')
network_out_bytes=$(echo $network_stats | awk '{printf "%.0f", $2 * 1024}')

echo "${timestamp},${cpu_used_percent},${cpu},${mem},${mem_used},${disk},${network_in_bytes},${network_out_bytes}" >> "${data}"

sleep 5

#rsync -avz --progress -e "ssh -i -o StrictHostKeyChecking=accept"