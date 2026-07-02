"""The postgres Tool ships a compose fragment that the kernel's compose renderer folds into the stack
when the tool is enabled — this pins that its `db` service is discoverable + loadable. Runs inside the
Core stack with the postgres plugin linked (app.plugin_loader / app.core.compose_render on the path).

    docker compose exec backend pytest app/plugins/postgres/tests/test_compose_fragment.py
"""
from __future__ import annotations


def test_real_postgres_fragment_loads():
    from app.plugin_loader import discover
    from app.core.compose_render import load_tool_fragments

    m = discover()
    frags = load_tool_fragments({"postgres"}, m)
    assert any("db" in (f.get("services") or {}) for f in frags)
