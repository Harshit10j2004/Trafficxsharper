from pydantic_settings import BaseSettings
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class data(BaseSettings):

    LOG_FILE_PREDCITION: str
    LOG_FILE_INSERTION: str
    LOG_FILE_TRANNING: str
    FILE: str


    class Config:

        env_file = PROJECT_ROOT / ".env"

settings = data()