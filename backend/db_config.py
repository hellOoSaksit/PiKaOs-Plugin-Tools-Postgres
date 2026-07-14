"""The system-DB connection chosen at install (auth-install Step 1). Encrypted DSN in this plugin's
OWN kernel-state file `postgres_connection` — NOT the shared `app_settings` blob other installer-owned
secrets use, so the generic `/api/settings/global/{key}` API can't reach it (no reserved-key entry
needed) and the kernel never has to know this key exists. Read before any DB exists (zero-datastore
kernel), so `register()` (see `__init__.py`) can source its engine from the operator's choice instead of
only `settings.database_url`. Mirrors `git_installer.set_credential`'s encrypt-on-save pattern.
"""
from __future__ import annotations
from datetime import datetime, timezone

from ...core import kernel_state
from ...core.crypto import decrypt, encrypt

_FILE = "postgres_connection"


def _value() -> dict | None:
    data = kernel_state.read_json(_FILE, {})
    return data if data else None


def save(provider: str, dsn: str) -> None:
    kernel_state.write_json(_FILE, {
        "provider": provider,
        "dsn": encrypt(dsn),
        "configured_at": datetime.now(timezone.utc).isoformat(),
    })


def read_dsn() -> str | None:
    value = _value()
    if not value or not value.get("dsn"):
        return None
    return decrypt(value["dsn"]) or None      # decrypt() returns "" on a bad/rotated token → None


def is_configured() -> bool:
    return _value() is not None


def mark_env() -> None:
    """Record that the DB comes from env (dev/deploy-baked) — suppresses `needsDbConfig` without
    storing a DSN. `read_dsn()` still returns None so `register()` falls back to `settings.database_url`.
    The dev-stack entrypoint calls this (see the R3 rework task); wiring it in is out of scope here."""
    kernel_state.write_json(_FILE, {
        "provider": "env",
        "dsn": "",
        "configured_at": datetime.now(timezone.utc).isoformat(),
    })
