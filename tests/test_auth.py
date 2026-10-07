from pathlib import Path

import pytest

from gitops_updater.auth import QUERY_SECRET_SUNSET_DATE, resolve_updater_secret
from gitops_updater.config import ConfigReader
from gitops_updater.main import app

FIXTURE_CONFIG = Path(__file__).parent / "fixtures" / "updater_config.yaml"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CONFIG_PATH", str(FIXTURE_CONFIG))
    monkeypatch.setattr(
        "gitops_updater.config.get_secret",
        lambda _path: "top-secret\n",
    )
    return app.test_client()


def test_resolve_bearer_preferred_over_query():
    with app.test_request_context(
        "/gitops-updater?secret=query-value",
        headers={"Authorization": "Bearer header-value"},
    ):
        from flask import request

        resolved = resolve_updater_secret(request)
        assert resolved.secret == "header-value"
        assert resolved.method.value == "bearer"


def test_missing_authentication(client):
    response = client.get(
        "/gitops-updater",
        query_string={"name": "test-app", "version": "1.0.0"},
    )
    assert response.status_code == 422
    assert "Bearer" in response.json["error"]


def test_invalid_bearer_secret(client):
    response = client.get(
        "/gitops-updater",
        query_string={"name": "test-app", "version": "1.0.0"},
        headers={"Authorization": "Bearer wrong"},
    )
    assert response.status_code == 422
    assert response.json["error"] == "Invalid secret"


def test_bearer_auth_success_without_deprecation(client, monkeypatch):
    monkeypatch.setattr(
        ConfigReader,
        "find_provider",
        lambda self, _filename, _name: object(),
    )
    monkeypatch.setattr(
        "gitops_updater.handlers.argocd.ArgoCD.handle",
        lambda self, version: {"message": "ok"},
    )
    response = client.get(
        "/gitops-updater",
        query_string={"name": "test-app", "version": "1.0.0"},
        headers={"Authorization": "Bearer top-secret"},
    )
    assert response.status_code == 200
    assert response.json["message"] == "ok"
    assert "deprecation" not in response.json
    assert "Deprecation" not in response.headers


def test_query_secret_success_includes_deprecation(client, monkeypatch):
    monkeypatch.setattr(
        ConfigReader,
        "find_provider",
        lambda self, _filename, _name: object(),
    )
    monkeypatch.setattr(
        "gitops_updater.handlers.argocd.ArgoCD.handle",
        lambda self, version: {"message": "ok"},
    )
    response = client.get(
        "/gitops-updater",
        query_string={
            "name": "test-app",
            "version": "1.0.0",
            "secret": "top-secret",
        },
    )
    assert response.status_code == 200
    assert response.json["message"] == "ok"
    assert QUERY_SECRET_SUNSET_DATE in response.json["deprecation"]
    assert response.headers.get("Deprecation") == "true"
