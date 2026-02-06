#!/bin/bash
set -euo pipefail

source /home/ubuntu/tsx/data/data.env

BASE_DIR="$window_file"
NOW=$(date +%s)
MAX_AGE=600   # seconds

for client_dir in "$BASE_DIR"/*; do
    [[ -d "$client_dir" ]] || continue

    for log_file in "$client_dir"/*.log; do
        [[ -e "$log_file" ]] || continue

        name=$(basename "$log_file")
        epoch="${name%.log}"

        # Only delete epoch-based logs
        [[ "$epoch" =~ ^[0-9]+$ ]] || continue

        diff=$(( NOW - epoch ))

        if (( diff > MAX_AGE )); then
            rm -f "$log_file"
            echo "DELETED LOG: $log_file (${diff}s old)"
        fi
    done
done