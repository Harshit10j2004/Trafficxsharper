from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import time
from operations.prediction import router as pred
from operations.inserting import router as inse
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



app.include_router(pred)
app.include_router(inse)
app.include_router(health)





