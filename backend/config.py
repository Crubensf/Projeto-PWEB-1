from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Banco
    database_url: str = "sqlite:///./vanja.db"

    # JWT
    secret_key: str = "dev_secret_key_nao_usar_em_producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Cookies de autenticação
    cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"
    cookie_secure: bool = True  # HTTPS via Apache em produção
    cookie_samesite: str = "lax"

    # Rate limiting
    max_tentativas_login: int = 5
    janela_tentativas_login_s: int = 15 * 60
    max_registros_por_ip: int = 5
    janela_registro_s: int = 60 * 60

    # Validação
    min_senha: int = 8

    # Logs
    log_level: str = "INFO"
    log_pretty: bool = True  # console color em dev; False = JSON

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_rotas_ttl_s: int = 30


settings = Settings()
