"""db_config.py — the operator's system-DB DSN, encrypted at rest in this plugin's OWN kernel-state
file `postgres_connection` (auth-install Step 1: DB choice). Mirrors git_installer's `set_credential`
pattern: encrypt on save, decrypt on read, never plaintext on disk.

    docker compose exec backend pytest app/plugins/postgres/tests/test_db_config.py -v
"""
from __future__ import annotations

import pytest

from app.core import kernel_state
from app.plugins.postgres import db_config


@pytest.fixture
def tmp_state(tmp_path, monkeypatch):
    monkeypatch.setattr(kernel_state.settings, "kernel_state_dir", str(tmp_path))


def test_save_then_read_roundtrips_the_dsn(tmp_state):
    db_config.save("pg", "postgresql+asyncpg://u:p@h:5432/db")
    assert db_config.read_dsn() == "postgresql+asyncpg://u:p@h:5432/db"
    assert db_config.is_configured() is True


def test_read_dsn_is_none_when_unconfigured(tmp_state):
    assert db_config.read_dsn() is None
    assert db_config.is_configured() is False


def test_stored_dsn_is_ciphertext_not_plaintext(tmp_state):
    db_config.save("pg", "postgresql+asyncpg://u:secretpw@h:5432/db")
    blob = kernel_state.read_json("postgres_connection", {})
    assert "secretpw" not in str(blob)          # encrypted at rest


def test_saved_dsn_is_not_nested_under_a_value_wrapper(tmp_state):
    """The dedicated `postgres_connection` file IS the record — no `{"value": ...}` nesting like the
    shared `app_settings` blob uses (that nesting is what let the generic settings API reach reserved
    keys in the first place)."""
    db_config.save("bundled", "postgresql+asyncpg://pikaos:pikaos@db:5432/pikaos")
    blob = kernel_state.read_json("postgres_connection", {})
    assert set(blob.keys()) == {"provider", "dsn", "configured_at"}


def test_mark_env_sets_the_marker_without_a_secret(tmp_state):
    db_config.mark_env()
    assert db_config.is_configured() is True
    assert db_config.read_dsn() is None          # env source → no stored DSN, falls back to settings
