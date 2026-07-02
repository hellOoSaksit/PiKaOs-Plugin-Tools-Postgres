"""Engine construction for the postgres Tool — the SQLAlchemy that used to live in the kernel's
`app/core/db.py`. The zero-datastore kernel owns no engine now; this Tool creates it (and the pgvector
asyncpg codec) and binds it under the `postgres.Connection` contract in `__init__.register()`.

Kept in its own module (not inline in `__init__`) so the engine helpers are importable on their own —
e.g. tests that build a throwaway engine call `register_pgvector` here, the same way they used to call
`app.core.db.register_pgvector`.
"""
from __future__ import annotations

from pgvector.asyncpg import register_vector
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


async def _register_vector_if_available(conn) -> None:
    """Register the pgvector codec on a connection, tolerating the `vector` type being absent.

    The `knowledge` plugin OWNS pgvector now — it creates `CREATE EXTENSION vector` in its migrate()
    step. So the type may not exist when a connection opens: the plugin is disabled (knowledge-off), or
    this connection was opened during boot before the plugin's migrate ran. In those cases we skip the
    codec instead of crashing every connection — a connection opened after the extension exists (e.g. at
    request time, once migrate has run) registers it. Connections without the codec are only used for
    non-vector work, so skipping is safe."""
    try:
        await register_vector(conn)
    except ValueError:
        pass  # `vector` type not installed on this connection yet — see docstring


def register_pgvector(eng: AsyncEngine) -> AsyncEngine:
    """Register pgvector's asyncpg codec on every connection this engine opens (leniently — see
    `_register_vector_if_available`), so the RAG repo binds/reads embeddings as `list[float]` directly
    instead of formatting a `'[..]'::vector` string literal (knowledge plugin's doc_chunks repo).

    Returns the engine so the call site can wrap creation in one expression. Tests that build their own
    engine call this too (the codec is per-engine)."""
    @event.listens_for(eng.sync_engine, "connect")
    def _on_connect(dbapi_connection, _record):  # noqa: ANN001 — SQLAlchemy event signature
        dbapi_connection.run_async(_register_vector_if_available)
    return eng


def create_engine(database_url: str) -> AsyncEngine:
    """The app engine: async, pool-pre-ping, with the pgvector codec registered."""
    return register_pgvector(create_async_engine(database_url, pool_pre_ping=True, future=True))


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """The session factory bound under `postgres.Connection` for every DB consumer."""
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
