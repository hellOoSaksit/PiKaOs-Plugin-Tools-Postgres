"""`/api/postgres/db-test` + `/api/postgres/db-config` + `/api/postgres/db-status` — the setup-code-gated
DB-choice routes (Step 1 of install), owned by this plugin so the kernel stays SQLAlchemy-free.

All three routes require a valid bootstrap Bearer (the token `verify-code` hands back — see
PiKaOs-Core's `test_setup_code.py`) and never leak the real driver exception or DSN to the client: only
a generic "database connection failed" crosses the wire, the real detail stays server-side in
`db_probe`'s log. `/db-status` is gated the same way for consistency even though it only reveals a
boolean — an unauthenticated caller should never learn whether the system DB is configured yet, same
rule the old `/api/setup/status.needsDbConfig` field followed.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...core import setup_state
from . import db_config, db_dsn, db_probe

router = APIRouter(prefix="/api/postgres", tags=["postgres"])


class DbIn(BaseModel):
    """The operator's DB choice (Step 1 of install) — same shape for db-test and db-config so the
    frontend can "test then save" against one payload. `db_dsn.build` picks which fields matter."""
    provider: str
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    dbname: str | None = None
    connectionString: str | None = None


class DbStatusOut(BaseModel):
    needsDbConfig: bool


def _bearer(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth[7:].strip() or None


def _require_bootstrap(request: Request) -> None:
    if not setup_state.verify_session_token(_bearer(request)):
        raise HTTPException(status_code=401, detail="bootstrap authorization required")


def _dsn_from(body: DbIn) -> str:
    dsn = db_dsn.build(body.provider, body.model_dump(exclude_none=True))
    db_dsn.reject_pooler(dsn)
    return dsn


@router.post("/db-test")
async def db_test(body: DbIn, request: Request) -> dict:
    """Connectivity check only — never persists. The client sends this before db-config so the
    operator gets pass/fail feedback without committing a bad DSN. Errors are GENERIC to the client
    (the real driver exception is logged server-side only by `db_probe.probe` — never the DSN or
    password crosses the wire in either direction on failure)."""
    _require_bootstrap(request)
    try:
        dsn = _dsn_from(body)                 # KeyError here = an incomplete `pg` payload (missing host/user/…)
        await db_probe.probe(dsn)
    except (db_dsn.DbDsnError, db_probe.DbProbeError, KeyError) as exc:
        raise HTTPException(status_code=400, detail="database connection failed") from exc
    return {"ok": True}


@router.post("/db-config")
async def db_config_save(body: DbIn, request: Request) -> dict:
    """Re-probes (never trusts a prior /db-test without re-checking) then persists the DSN via
    `db_config.save` — encrypted at rest, see db_config.py. 409 once a DB is already configured: this
    is a one-shot Step-1 choice, not an update endpoint. `restart_required` tells the frontend the
    kernel needs a restart before the new DSN takes effect (the running process keeps its old engine)."""
    _require_bootstrap(request)
    if db_config.is_configured():
        raise HTTPException(status_code=409, detail="a database is already configured")
    try:
        dsn = _dsn_from(body)                 # KeyError here = an incomplete `pg` payload (missing host/user/…)
        await db_probe.probe(dsn)
    except (db_dsn.DbDsnError, db_probe.DbProbeError, KeyError) as exc:
        raise HTTPException(status_code=400, detail="database connection failed") from exc
    db_config.save(body.provider, dsn)
    return {"ok": True, "restart_required": True}


@router.get("/db-status", response_model=DbStatusOut)
async def db_status(request: Request) -> DbStatusOut:
    """Whether the operator still needs to complete Step 1 (DB choice) — the frontend polls this
    instead of the kernel's `/api/setup/status`, since only this plugin knows about `db_config`."""
    _require_bootstrap(request)
    return DbStatusOut(needsDbConfig=not db_config.is_configured())
