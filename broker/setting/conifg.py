from pydantic_settings import BaseSettings
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class data(BaseSettings):

    ML_URL: str
    ML_URL_INSERT: str
    DEC_URL: str
    LOG_FILE_FORML_R: str
    LOG_FILE_FORSCA_R: str
    LOG_FILE_BROKER: str
    DB_HOST: str
    DB_USER: str
    PASSWORD: str
    DATABASE: str
    LOG_FILE_DATABASE_S: str
    LOG_FILE_REDIS: str


    class Config:

        env_file = PROJECT_ROOT / ".env"

settings = data()