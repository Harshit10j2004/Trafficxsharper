from pydantic_settings import BaseSettings
from pathlib import Path

# config file to get data from .env and export to the other files to use it

#Navigate two levels up from this file to reach the project root where .env resides
PROJECT_ROOT = Path(__file__).parent.parent


class data(BaseSettings):

    MAIL: str
    PASSWORD: str
    LOG_FILE_MAIL:str

    class Config:

        env_file = PROJECT_ROOT / ".env"

settings = data()