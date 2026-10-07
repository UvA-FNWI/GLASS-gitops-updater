from gitops_updater.main import app


def test_import_app():
    assert app is not None


def test_gitops_updater_requires_query_params(monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", "/nonexistent/config.yaml")
    client = app.test_client()
    response = client.get("/gitops-updater")
    assert response.status_code == 422
    assert response.json["error"] == "Missing GET-arguments"


def test_healthz_ok():
    client = app.test_client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_readyz_without_config(tmp_path, monkeypatch):
    missing = tmp_path / "missing.yaml"
    monkeypatch.setenv("CONFIG_PATH", str(missing))
    client = app.test_client()
    response = client.get("/readyz")
    assert response.status_code == 503


def test_readyz_with_config(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text("config: []\nproviders: []\n", encoding="utf-8")
    monkeypatch.setenv("CONFIG_PATH", str(config))
    client = app.test_client()
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json["status"] == "ready"


def test_gitops_updater_requires_config_path(monkeypatch):
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    client = app.test_client()
    response = client.get(
        "/gitops-updater",
        query_string={"name": "x", "secret": "y", "version": "1.0.0"},
    )
    assert response.status_code == 422
    assert response.json["error"] == "CONFIG_PATH not set"
