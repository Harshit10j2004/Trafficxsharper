from pydantic_settings import BaseSettings
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class data(BaseSettings):

    LOG_FILE_MAIL: str
    LOG_FILE_FILE_M: str
    LOG_FILE_AWS_D: str
    LOG_FILE_AWS_U: str
    LOG_FILE_AZURE_U : str
    LOG_FILE_AZURE_D : str
    LOG_SCALE_UP: str
    LOG_SCALE_DOWN: str
    KEY: str
    SUBID: str
    URL: str
    SUB_ID: str
    RES_GRP: str
    SUBNET_ID: str
    ADM_PAS: str


    class Config:

        env_file = PROJECT_ROOT / ".env"

settings = data()