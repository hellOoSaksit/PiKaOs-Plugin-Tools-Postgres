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

## Install (in Core)

Linked into Core by the monorepo's `link-plugins.sh` (derives id `postgres` — the `Tools-` segment is
stripped so the id stays import-safe). Enabled through Core's Modules page → the install engine brings up
the sidecar and rebuilds.

## Status

Seam-first: SQLAlchemy still lives in the Core image while consumers (auth/rbac/knowledge) are extracted;
this plugin owns the connection seam so the later full externalization only changes `register()`.
See `PiKaOs-Docs/docs/architecture/kernel-redesign.md`.
