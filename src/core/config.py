from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Chat Zelda"
    debug: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
