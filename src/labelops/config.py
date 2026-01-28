from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    allowlisted_chat_ids: set[int]
    allowlisted_usernames: set[str]
    default_client_id: str
    clients: list[str]
    chat_defaults_path: Path


@dataclass(frozen=True)
class ClickDropConfig:
    api_base_url: str
    api_key: str
    retry_schedule_minutes: list[int]


@dataclass(frozen=True)
class AppConfig:
    telegram: TelegramConfig
    clickdrop: ClickDropConfig


class ConfigError(RuntimeError):
    pass


def _require(value: Any, field: str) -> Any:
    if value in (None, ""):
        raise ConfigError(f"Missing required config field: {field}")
    return value


def load_config(path: Path) -> AppConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    telegram = data.get("telegram", {})
    clickdrop = data.get("clickdrop", {})

    token = _require(telegram.get("token"), "telegram.token")
    allowlisted_chat_ids = {
        int(chat_id) for chat_id in telegram.get("allowlisted_chat_ids", [])
    }
    allowlisted_usernames = {
        str(username).lstrip("@").lower()
        for username in telegram.get("allowlisted_usernames", [])
    }
    default_client_id = _require(
        telegram.get("default_client_id"), "telegram.default_client_id"
    )
    clients = [str(client) for client in telegram.get("clients", [])]
    chat_defaults_path = Path(
        telegram.get("chat_defaults_path", "data/chat_defaults.json")
    )

    telegram_cfg = TelegramConfig(
        token=token,
        allowlisted_chat_ids=allowlisted_chat_ids,
        allowlisted_usernames=allowlisted_usernames,
        default_client_id=default_client_id,
        clients=clients,
        chat_defaults_path=chat_defaults_path,
    )

    clickdrop_cfg = ClickDropConfig(
        api_base_url=_require(
            clickdrop.get("api_base_url"), "clickdrop.api_base_url"
        ),
        api_key=_require(clickdrop.get("api_key"), "clickdrop.api_key"),
        retry_schedule_minutes=[
            int(value) for value in clickdrop.get("retry_schedule_minutes", [])
        ],
    )

    return AppConfig(telegram=telegram_cfg, clickdrop=clickdrop_cfg)
