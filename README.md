# PiKaOs-Plugin-Tools-Postgres

A **tool plugin** for [PiKaOs](https://github.com/hellOoSaksit/PiKaOs) — provides PostgreSQL as an
installable datastore. Part of the zero-datastore kernel model: the kernel ships no datastore; a tool
plugin brings the sidecar container + a thin connection contract the rest of the system consumes.

## What it provides

- **Contract:** `postgres.Connection` — the async SQLAlchemy engine + session factory, bound into the
  Core DI container by `backend/__init__.py`'s `register()`.
- **Sidecar:** `backend/compose.fragment.yml` — the `pgvector/pgvector:pg16` service, merged into the
  generated compose when this plugin is enabled.
- **Manifest:** `kind: tool`, id `postgres`, `secrets: [database_url]`.
- **DB-choice (auth-install Step 1):** this plugin owns the system-DB picker end to end, so the kernel
  stays SQLAlchemy-free. `backend/db_config.py` (encrypted DSN in the plugin's own kernel-state file
  `postgres_connection`, not the shared `app_settings` blob), `db_dsn.py` (asyncpg DSN normalization +
  Supabase-pooler rejection), `db_probe.py` (throwaway-engine connectivity test). Routes (`router.py`,
  bootstrap-token gated, generic client errors — see route docstrings):
  - `POST /api/postgres/db-test` — test a candidate connection, never persists.
  - `POST /api/postgres/db-config` — re-tests then persists (encrypted); 409 once already configured.
  - `GET /api/postgres/db-status` — `{needsDbConfig}` for the bootstrap flow to poll.
  - `db_config.mark_env()` — dev/CI marker (no stored DSN, `register()` keeps using the env fallback);
    wired by Core's `docker-entrypoint.sh` when `DB_CONFIG_SOURCE=env` is set (dev compose default).
  - **Frontend** (`frontend/`): `DbChoice.jsx` (the provider-picker screen), `db-choice.js`
    (`canSaveDb` helper), `i18n/{en,th,ja}-formal.json` (`dbchoice.*` keys). Exported via
    `index.jsx`'s `bootstrapScreens: { 'db-choice': ... }` — Core's plugin barrel renders it during
    the pre-login bootstrap window (the `bootstrapScreens` seam, not the normal in-app plugin routes).
  - Design: `PiKaOs-Docs/docs/superpowers/specs/2026-07-14-auth-install-step1-db-choice-design.md`.

## Install (in Core)

Linked into Core by the monorepo's `link-plugins.sh` (derives id `postgres` — the `Tools-` segment is
stripped so the id stays import-safe). Enabled through Core's Modules page → the install engine brings up
the sidecar and rebuilds.

## Status

Seam-first: SQLAlchemy still lives in the Core image while consumers (auth/rbac/knowledge) are extracted;
this plugin owns the connection seam so the later full externalization only changes `register()`.
See `PiKaOs-Docs/docs/architecture/kernel-redesign.md`.
