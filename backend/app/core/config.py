import os
import json
from typing import List, Union
from pydantic import field_validator, model_validator
from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Factory Manager - Ashok Textiles"
    COMPANY_NAME: str = "Ashok Textiles"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://10.150.249.110:5173"]

    # Target database is PostgreSQL. Either set DATABASE_URL, or set POSTGRES_* and it is built for you.
    # SQLite is still accepted for the legacy report-ingestion modules, but the weaving
    # analytics need PostgreSQL (see docs/database.md).
    DATABASE_URL: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "textile"
    POSTGRES_USER: str = "textile"
    POSTGRES_PASSWORD: str = ""

    # Run `alembic upgrade head` when the API starts. Convenient for development;
    # the Docker image runs migrations in its entrypoint instead and sets this to false.
    AUTO_MIGRATE: bool = True

    # Mill-local time zone: decides where a production day starts and ends.
    MILL_TIMEZONE: str = "Asia/Kolkata"

    SECRET_KEY: str = "ashok_textiles_dev_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Seeds one demo login per role. Never active when ENVIRONMENT=production, whatever this says.
    SEED_DEMO_USERS: bool = True

    LOG_LEVEL: str = "INFO"

    @property
    def demo_users_enabled(self) -> bool:
        return self.SEED_DEMO_USERS and self.ENVIRONMENT.lower() != "production"

    @model_validator(mode="after")
    def build_database_url(self):
        if not self.DATABASE_URL:
            if not self.POSTGRES_PASSWORD:
                raise ValueError(
                    "No database configured. Set DATABASE_URL, or POSTGRES_PASSWORD (plus POSTGRES_HOST/PORT/DB/USER). "
                    "See backend/.env.example."
                )
            self.DATABASE_URL = URL.create(
                "postgresql+psycopg", username=self.POSTGRES_USER, password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_HOST, port=self.POSTGRES_PORT, database=self.POSTGRES_DB,
            ).render_as_string(hide_password=False)
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        return self

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
