from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class IngestionResult:
    client_id: str
    filename: str
    message_length: int
    timestamp: str


def utc_timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_atomic_text(target_path: Path, content: str) -> None:
    ensure_dir(target_path.parent)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, target_path)


def write_ingestion_message(
    base_dir: Path,
    client_id: str,
    message: str,
) -> IngestionResult:
    timestamp = utc_timestamp()
    filename = f"telegram_{timestamp}.txt"
    target_dir = base_dir / "Clients" / client_id / "IN_TXT"
    target_path = target_dir / filename
    write_atomic_text(target_path, message)
    return IngestionResult(
        client_id=client_id,
        filename=str(target_path),
        message_length=len(message),
        timestamp=timestamp,
    )


def load_chat_defaults(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def save_chat_defaults(path: Path, data: dict[str, str]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
