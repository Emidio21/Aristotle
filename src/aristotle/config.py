from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurazione da variabili d'ambiente / file .env (prefisso ARISTOTLE_)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ARISTOTLE_", extra="ignore")

    telegram_token: SecretStr
    erep_api_key: SecretStr
    erep_api_base: str = "https://api.erepublik.tools"
    # Socrates usa una versione configurabile per /citizen/{id} e "v0" fisso per la ricerca.
    erep_api_version: str = "v0"
    erep_search_version: str = "v0"
    cache_ttl: float = 60.0
    admin_chat_id: int | None = None
    log_level: str = "INFO"
