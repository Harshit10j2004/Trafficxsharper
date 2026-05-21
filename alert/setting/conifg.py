from pydantic_settings import BaseSettings
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class data(BaseSettings):

    MAIL: str
    PASSWORD: str
    LOG_FILE_MAIL:str

    class Config:

        env_file = PROJECT_ROOT / ".env"

settings = data()