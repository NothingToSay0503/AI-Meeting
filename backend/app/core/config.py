from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "change-me-in-local-env"
    access_token_expire_minutes: int = 1440

    database_url: str = "mysql+pymysql://meeting:meeting_pwd@127.0.0.1:3306/meeting_minutes"
    redis_url: str = "redis://127.0.0.1:6379/0"
    kafka_bootstrap_servers: str = "127.0.0.1:9092"
    storage_audio_dir: str = "D:/demo/.storage/audio"

    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-pro"

    asr_provider: str = "mock"
    xfei_app_id: str = ""
    xfei_api_key: str = ""
    xfei_api_secret: str = ""
    xfei_asr_domain: str = "pro_ost_ed"
    xfei_asr_language: str = "zh_cn"
    xfei_asr_accent: str = "mandarin"
    xfei_asr_vspp_on: int = 1


settings = Settings()
