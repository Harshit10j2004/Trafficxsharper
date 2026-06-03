from fastapi import APIRouter

router = APIRouter()

#The health check api for checking health of the service

@router.get("/health")
def health():

    #if all things are good return ok

    return{
        "status" : "ok"
    }
