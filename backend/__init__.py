"""postgres — provides the DB connection as a DI contract (kernel-redesign seam-first).

Seam-first scope: SQLAlchemy still lives in the Core image and db.py still creates the engine; this
plugin binds that engine + session factory into the container under `postgres.Connection`, the
same way knowledge binds `knowledge.Retriever` — so a consumer running in the plugin lifecycle context
(the worker today; the web app once it grows a container) resolves the connection through the contract
instead of importing db.py globals. When postgres is later fully externalized, only this register() changes.
"""
from __future__ import annotations


def register(ctx) -> None:
    from ...core.db import engine, SessionLocal          # Core still owns creation for now
    from ...core.contracts import POSTGRES_CONNECTION

    ctx.container.bind(POSTGRES_CONNECTION, {"engine": engine, "session_factory": SessionLocal})
