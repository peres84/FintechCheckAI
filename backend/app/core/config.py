from pydantic import BaseModel


class Settings(BaseModel):
    app_env: str = "development"


settings = Settings()
