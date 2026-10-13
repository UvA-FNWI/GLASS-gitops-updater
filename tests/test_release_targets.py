import pytest

from scripts.release_targets import parse_release_targets


def test_release_targets_accept_hosts_and_environments():
    parsed = parse_release_targets(
        "registry.example.com",
        "staging, production",
    )

    assert parsed["hosts"] == ["registry.example.com"]
    assert parsed["rollouts"] == ["staging", "production"]


def test_release_targets_split_on_whitespace_and_commas():
    parsed = parse_release_targets(
        "one.example.com\ntwo.example.com",
        "staging production",
    )

    assert parsed["hosts"] == ["one.example.com", "two.example.com"]
    assert parsed["rollouts"] == ["staging", "production"]


def test_release_targets_reject_missing_host():
    with pytest.raises(ValueError, match="RELEASE_HOSTS"):
        parse_release_targets("  ", "staging")


def test_release_targets_reject_duplicate_environment():
    with pytest.raises(ValueError, match="rollout environments must be unique"):
        parse_release_targets("registry.example.com", "staging staging")


def test_release_targets_reject_invalid_host():
    with pytest.raises(ValueError, match="host"):
        parse_release_targets("bad_host", "staging")
