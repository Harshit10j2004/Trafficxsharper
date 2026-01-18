#!/bin/bash
set -euo pipefail

echo "Starting TSX listeners..."

ncat -l -k -p 9000 --exec "/home/ubuntu/tsx/scripts/file_managing.sh" &

ncat -l -k -p 9001 --exec "/home/ubuntu/tsx/scripts/file_managing_nginx.sh" &

wait
