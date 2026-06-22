from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent


class data(BaseSettings):

    LOG_FILE_MAIL: Optional[str] = None
    LOG_FILE_FILE_M: Optional[str] = None
    LOG_FILE_AWS_D: Optional[str] = None
    LOG_FILE_AWS_U: Optional[str] = None
    LOG_FILE_AZURE_U : Optional[str] = None
    LOG_FILE_AZURE_D : Optional[str] = None
    LOG_SCALE_UP: Optional[str] = None
    LOG_SCALE_DOWN: Optional[str] = None
    KEY: Optional[str] = None
    SUBID: Optional[str] = None
    URL: Optional[str] = None
    SUB_ID: Optional[str] = None
    RES_GRP: Optional[str] = None
    SUBNET_ID: Optional[str] = None
    ADM_PAS: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None


    class Config:

        env_file = PROJECT_ROOT / ".env"

settings = data()