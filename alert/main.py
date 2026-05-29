from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import time
import uuid
from operations.gmail import router as mail
from health.health import router as health

@asynccontextmanager
async def lifespan(app:FastAPI):

    print("App is starting up")
    yield
    print("App is shutting down")

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def middleware(request:Request,callnext):

    starttime = time.time()
    print(f"request path {request.url.path}")

    req_id = request.headers.get("X-Request-ID")

    if not req_id:

        req_id = str(uuid.uuid4())

    request.state.req_id = req_id

    response = await callnext(request)

    process_time = time.time() - starttime
    print(f"Completed in {process_time}")

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Process-Time"] = str(process_time)

    return response


app.include_router(mail)
app.include_router(health)





