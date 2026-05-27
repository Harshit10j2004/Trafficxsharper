from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import time
from operations.scale_down import router as sdr
from operations.scale_up import router as sur
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

    response = await callnext(request)

    process_time = time.time() - starttime
    print(f"Completed in {process_time}")

    return response



app.include_router(sdr)
app.include_router(sur)
app.include_router(health)





