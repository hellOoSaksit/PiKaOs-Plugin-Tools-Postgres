"""register() sources its DSN from the operator's Step-1 choice (kernel-state db_config) first,
falling back to env (settings.database_url) when unconfigured — proves the precedence without a
live DB by monkeypatching create_engine/create_session_factory and db_config.read_dsn."""


def _ctx_stub():
    class Ctx:  # minimal PluginContext stand-in, matches test_postgres_register.py's style
        container = type("C", (), {"bind": staticmethod(lambda *a, **k: None)})()

    return Ctx


def test_register_prefers_kernel_state_dsn_over_env(monkeypatch):
    seen = {}
    monkeypatch.setattr("app.core.db_config.read_dsn", lambda: "postgresql+asyncpg://k:k@kernel:5432/k")
    monkeypatch.setattr("app.plugins.postgres.engine.create_engine", lambda dsn: seen.setdefault("dsn", dsn))
    monkeypatch.setattr("app.plugins.postgres.engine.create_session_factory", lambda e: None)
    from app.plugins.postgres import register

    register(_ctx_stub())
    assert seen["dsn"] == "postgresql+asyncpg://k:k@kernel:5432/k"


def test_register_falls_back_to_env_when_unconfigured(monkeypatch):
    seen = {}
    monkeypatch.setattr("app.core.db_config.read_dsn", lambda: None)
    monkeypatch.setattr("app.core.config.settings.database_url", "postgresql+asyncpg://e:e@env:5432/e", raising=False)
    monkeypatch.setattr("app.plugins.postgres.engine.create_engine", lambda dsn: seen.setdefault("dsn", dsn))
    monkeypatch.setattr("app.plugins.postgres.engine.create_session_factory", lambda e: None)
    from app.plugins.postgres import register

    register(_ctx_stub())
    assert seen["dsn"].endswith("@env:5432/e")
