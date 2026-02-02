#!/bin/bash

set -x

source /home/ubuntu/tsx/data/data.env

file=$window_file

timestamp_ms=$(date +%s%3N)

for i in "${file}"/*.log;do

  name=$(basename "$i")
  epoch=${name%.log}


  [[ "$epoch" =~ ^[0-9]+$ ]] || continue

  diff=$(( NOW - epoch ))

  if (( diff > 600 )); then
        rm -f "$i"

        echo "OLD FILE: $i ($diff sec old)"

  fi
done