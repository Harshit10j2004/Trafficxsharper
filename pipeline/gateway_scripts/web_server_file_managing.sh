#!/bin/bash
set -euo pipefail

read -r fname

if [[ -z "$fname" ]]; then
  echo "ERROR: empty filename" > "${file}"
  exit 1
fi

TARGET="/home/ubuntu/tsx/n_data/$fname"

cat > "$TARGET"