from pathlib import Path

import pytest

from scripts.release_targets import parse_release_targets

TARGETS = Path(__file__).parents[1] / ".github" / "release-targets.yaml"


def test_release_targets_list_both_rollouts_independently():
    parsed = parse_release_targets(TARGETS.read_text(encoding="utf-8"))
    registries = {row["name"]: row["host"] for row in parsed["registries"]}
    rollouts = {row["name"]: row for row in parsed["rollout"]}

    assert registries == {
        "datanose": "datanosecr.azurecr.io",
        "fnwi": "fnwicr.azurecr.io",
    }
    assert set(rollouts) == {"datanose", "k8s"}
    assert rollouts["datanose"]["registry"] == "datanose"
    assert rollouts["datanose"]["secret"] == "UPDATER_SECRET_DN"
    assert rollouts["k8s"]["registry"] == "fnwi"
    assert rollouts["k8s"]["url"] == "https://k8s.datanose.nl/gitops-updater"
    assert rollouts["k8s"]["secret"] == "UPDATER_SECRET_K8S"


def test_release_targets_reject_unknown_registry():
    text = """\
registries:
  - name: datanose
    host: datanosecr.azurecr.io
rollout:
  - name: k8s
    registry: missing
    url: https://k8s.datanose.nl/gitops-updater
    config: gitops-updater
    secret: UPDATER_SECRET_K8S
"""
    with pytest.raises(ValueError, match="unknown registry"):
        parse_release_targets(text)
