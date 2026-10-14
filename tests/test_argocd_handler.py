from http import HTTPStatus
from unittest.mock import MagicMock

import pytest

from gitops_updater.config import ConfigEntry
from gitops_updater.handlers.argocd import ArgoCD

ARGO_APP = """\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo
  namespace: argocd
spec:
  project: default
  source:
    repoURL: example.com
    chart: demo
    targetRevision: 2.0.0
  destination:
    server: https://kubernetes.default.svc
    namespace: demo
"""


@pytest.fixture
def provider():
    mock = MagicMock()
    file_mock = MagicMock()
    file_mock.content.return_value = ARGO_APP
    mock.get_file.return_value = file_mock
    return mock


@pytest.fixture
def config():
    return ConfigEntry(
        name="demo",
        path="apps/demo.yaml",
        secret_path="/secrets/x",
        handler="argocd",
        provider="github",
        mapping=None,
        paths=None,
        allow_downgrade=False,
    )


def test_downgrade_rejected_with_409(provider, config):
    result = ArgoCD(config, provider).handle("1.0.0")
    assert result.status == HTTPStatus.CONFLICT
    assert "not downgrading" in result.body["errors"][0]
    provider.update_file.assert_not_called()


def test_downgrade_allowed_via_flag(provider, config):
    result = ArgoCD(config, provider).handle("1.0.0", allow_downgrade=True)
    assert result.status == HTTPStatus.OK
    assert result.body["message"] == "updated successfully"
    provider.update_file.assert_called_once()


def test_downgrade_allowed_via_config(provider):
    config = ConfigEntry(
        name="demo",
        path="apps/demo.yaml",
        secret_path="/secrets/x",
        handler="argocd",
        provider="github",
        mapping=None,
        paths=None,
        allow_downgrade=True,
    )
    result = ArgoCD(config, provider).handle("1.0.0", allow_downgrade=True)
    assert result.status == HTTPStatus.OK
    provider.update_file.assert_called_once()


def test_already_up_to_date_returns_200(provider, config):
    result = ArgoCD(config, provider).handle("2.0.0")
    assert result.status == HTTPStatus.OK
    assert "already up-to-date" in result.body["errors"][0]
