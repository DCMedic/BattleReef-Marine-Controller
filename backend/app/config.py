from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BattleReef Marine Controller"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    postgres_db: str = "battlereef"
    postgres_user: str = "battlereef"
    postgres_password: str = "changeme"
    database_url: str = "postgresql+psycopg://battlereef:changeme@postgres:5432/battlereef"
    sql_echo: bool = False

    mqtt_host: str = "mosquitto"
    mqtt_port: int = 8883
    mqtt_client_id: str = "battlereef-backend"
    mqtt_tls_enabled: bool = True
    mqtt_tls_ca_cert: str = "/run/battlereef-mqtt/ca.crt"
    mqtt_tls_client_cert: str = "/run/battlereef-mqtt/battlereef-backend.crt"
    mqtt_tls_client_key: str = "/run/battlereef-mqtt/battlereef-backend.key"
    mqtt_tls_check_hostname: bool = True
    mqtt_username: str = ""
    mqtt_password: str = ""

    auth_jwt_secret: str = "development-only-change-me-development-only"
    auth_token_issuer: str = "battlereef-controller"
    auth_token_audience: str = "battlereef-api"
    auth_token_ttl_minutes: int = 30
    auth_max_failed_attempts: int = 5
    auth_lockout_minutes: int = 15
    auth_bootstrap_admin_username: str = ""
    auth_bootstrap_admin_password: str = ""

    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
