from gitops_updater.main import app


def test_import_app():
    assert app is not None


def test_gitops_updater_requires_query_params(monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", "/nonexistent/config.yaml")
    client = app.test_client()
    response = client.get("/gitops-updater")
    assert response.status_code == 422
    assert response.json["error"] == "Missing GET-arguments"


def test_gitops_updater_requires_config_path(monkeypatch):
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    client = app.test_client()
    response = client.get(
        "/gitops-updater",
        query_string={"name": "x", "secret": "y", "version": "1.0.0"},
    )
    assert response.status_code == 422
    assert response.json["error"] == "CONFIG_PATH not set"
