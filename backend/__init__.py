"""postgres — the Tool that CREATES the DB engine and provides it as a DI contract, and (since the
auth-install Step-1 rework) OWNS the DB-choice HTTP surface — `/api/postgres/db-test|db-config|db-status`,
see `router.py` + `db_config.py`/`db_dsn.py`/`db_probe.py`.

The zero-datastore kernel owns no engine: SQLAlchemy left `app/core/db.py`, which is now just a
sqlalchemy-free `get_db` seam resolving this contract. Here `register()` builds the async engine + session
factory + pgvector codec (moved from the kernel, see `engine.py`) and binds them — plus an async `ping`
probe so the kernel health router needs no sqlalchemy — under `postgres.Connection`. It sources its DSN
from the operator's Step-1 choice (`db_config.read_dsn()`, this plugin's own kernel-state file) first,
falling back to `settings.database_url` when unconfigured.

Every composition root (web lifespan · redis worker · scripts.migrate_plugins) registers this Tool and
resolves `postgres.Connection` after registration; DB-owning plugins (auth/ai/knowledge/chat/telegram)
declare `dependencies: ["postgres"]` so it registers first. Nothing has a DB unless this Tool is enabled.
"""
from __future__ import annotations

from .router import router


def register(ctx) -> None:
    from ...core.config import settings
    from ...core.contracts import POSTGRES_CONNECTION
    from . import db_config
    from .engine import create_engine, create_session_factory

    dsn = db_config.read_dsn() or settings.database_url      # Step-1 choice first → env fallback
    engine = create_engine(dsn)
    sf = create_session_factory(engine)

    async def ping() -> bool:
        """Health probe — SELECT 1 through the pool. Lets the kernel health router check the DB via the
        contract instead of importing sqlalchemy."""
        from sqlalchemy import text
        async with sf() as s:
            await s.execute(text("SELECT 1"))
        return True

    ctx.container.bind(POSTGRES_CONNECTION, {"engine": engine, "session_factory": sf, "ping": ping})


__all__ = ["router", "register"]
