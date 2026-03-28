from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis
import json
import threading

app = FastAPI

@app.on_event("startup")
def start_listener():
    thread = threading.Thread(target=redis_listener, daemon=True)
    thread.start()

def redis_listener():
    pubsub = r.pubsub()
    pubsub.subscribe("metrics")

    for message in pubsub.listen():
        if message["type"] == "message":
            data = message["data"]

            # broadcast to all clients
            for client in list(clients):
                try:
                    import asyncio
                    asyncio.run(client.send_text(data))
                except:
                    clients.remove(client)


r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    clients.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)


