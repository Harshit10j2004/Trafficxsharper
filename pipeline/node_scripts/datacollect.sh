#!/bin/bash

set -x

data="/home/ubuntu/syslogs/sysscrlog/usage.log"
rec_ip=""

cpu=$(mpstat 1 1 | grep Average | awk '{print $12}')
cpu_used_percent=$(echo "100 - $cpu" | bc)

mem=$(free -m | grep Mem | awk '{print $2}')
mem_used=$(free -m | grep Mem | awk '{print $3}')
disk=$(df -h --total | grep total | awk '{print $5}' | tr -d '%')
network_stats=$(ifstat -b 1 1 2>/dev/null | awk 'NR==3 {print $1, $2}')
network_in_bytes=$(echo $network_stats | awk '{printf "%.0f", $1 * 1024}')
network_out_bytes=$(echo $network_stats | awk '{printf "%.0f", $2 * 1024}')

line="$cpu_used_percent,$cpu,$mem,$mem_used,$disk,$network_in_bytes,$network_out_bytes"

sleep 5

{
    echo "usage_$(hostname).log"
    echo "$line"
} | ncat $rec_ip 9000