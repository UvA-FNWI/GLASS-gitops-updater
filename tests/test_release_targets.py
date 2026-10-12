from pathlib import Path

import pytest

from scripts.release_targets import parse_release_targets

TARGETS = Path(__file__).parents[1] / ".github" / "release-targets.yaml"


def _write_targets(tmp_path: Path, text: str) -> Path:
    path = tmp_path / TARGETS.name
    path.write_text(text, encoding="utf-8")
    schema = TARGETS.with_suffix(".schema.json")
    path.with_suffix(".schema.json").write_text(
        schema.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return path


def test_release_targets_list_both_rollouts_independently():
    parsed = parse_release_targets(TARGETS)
    registries = {row["name"]: row["host"] for row in parsed["registries"]}
    rollouts = {row["name"]: row for row in parsed["rollout"]}

    assert registries == {"datanose": "datanosecr.azurecr.io"}
    assert set(rollouts) == {"datanose", "k8s"}
    assert rollouts["datanose"]["secret"] == "UPDATER_SECRET_DN"
    assert rollouts["k8s"]["url"] == "https://k8s.datanose.nl/gitops-updater"
    assert rollouts["k8s"]["secret"] == "UPDATER_SECRET_K8S"


def test_release_targets_reject_missing_host(tmp_path: Path):
    path = _write_targets(
        tmp_path,
        """\
registries:
  - name: datanose
rollout:
  - name: datanose
    url: https://api-v2-tst.datanose.nl/gitops-updater
    config: gitops-updater
    secret: UPDATER_SECRET_DN
""",
    )
    with pytest.raises(ValueError, match="host"):
        parse_release_targets(path)


def test_release_targets_reject_duplicate_rollout_name(tmp_path: Path):
    path = _write_targets(
        tmp_path,
        """\
registries:
  - name: datanose
    host: datanosecr.azurecr.io
rollout:
  - name: datanose
    url: https://api-v2-tst.datanose.nl/gitops-updater
    config: gitops-updater
    secret: UPDATER_SECRET_DN
  - name: datanose
    url: https://k8s.datanose.nl/gitops-updater
    config: gitops-updater
    secret: UPDATER_SECRET_K8S
""",
    )
    with pytest.raises(ValueError, match="rollout names must be unique"):
        parse_release_targets(path)
