"""Credential isolation helpers for live evaluation."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .errors import LiveEvalError


SECRET_ENV_NAMES = {"CODEX_API_KEY", "OPENAI_API_KEY", "CODEX_ACCESS_TOKEN"}


def sanitized_env(*, include_credentials: bool, extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    if not include_credentials:
        for name in SECRET_ENV_NAMES:
            environment.pop(name, None)
    if extra:
        environment.update(extra)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def default_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def seed_saved_auth(source_home: Path, target_home: Path) -> None:
    source = source_home / "auth.json"
    if source.is_symlink() or not source.is_file():
        raise LiveEvalError(f"saved Codex authentication is unavailable at {source}")
    target_home.mkdir(parents=True, exist_ok=True)
    target_home.chmod(0o700)
    target = target_home / "auth.json"
    shutil.copyfile(source, target)
    target.chmod(0o600)


def codex_execution_env(
    *, auth_mode: str, codex_home: Path, extra: dict[str, str] | None = None
) -> dict[str, str]:
    environment_extra = {"CODEX_HOME": str(codex_home)}
    if extra:
        environment_extra.update(extra)
    environment = sanitized_env(
        include_credentials=auth_mode == "api-key",
        extra=environment_extra,
    )
    if auth_mode == "api-key":
        environment.pop("CODEX_ACCESS_TOKEN", None)
    return environment
