ID_FILE="/home/ubuntu/tsx/data/server_id"

if [ ! -f "$ID_FILE" ]; then
  uuidgen > "$ID_FILE"
fi

SERVER_ID=$(cat "$ID_FILE")
