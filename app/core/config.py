from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Config(BaseSettings):
    ORIGINS:list[str] = ["http://localhost:3000"]
    PROJECT_NAME:str = "fast-api-template"
    VERSION:str = "v1"
    DATABASE_URI:str = os.getenv("DATABASE_URI", "")

config = Config()