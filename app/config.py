"""Application settings, read from APP_* environment variables."""
import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "FastAPI Examples"
    # Development default only: set APP_SECRET_KEY to a long random value in any real deployment.
    secret_key: str = "dev-only-secret-change-me-0123456789abcdef"
    token_minutes: int = Field(30, gt=0)
    hash_iterations: int = Field(200_000, ge=1_000)
    seed_demo_data: bool = True
    max_upload_bytes: int = Field(1_000_000, gt=0)

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        values = {}
        if "APP_SECRET_KEY" in env:
            values["secret_key"] = env["APP_SECRET_KEY"]
        if "APP_TOKEN_MINUTES" in env:
            values["token_minutes"] = int(env["APP_TOKEN_MINUTES"])
        if "APP_SEED_DEMO_DATA" in env:
            values["seed_demo_data"] = env["APP_SEED_DEMO_DATA"].lower() in ("1", "true", "yes")
        return cls(**values)
