"""Validate publish hosts and rollout environments for the publish workflow."""

import json
import os
import re
import sys

_HOST = re.compile(r"^[A-Za-z0-9.-]+$")
_ENVIRONMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,254}$")


def parse_entries(value: str) -> list[str]:
    return [part for part in re.split(r"[\s,]+", value.strip()) if part]


def parse_release_targets(hosts: str, environments: str) -> dict[str, list[str]]:
    host_list = parse_entries(hosts)
    environment_list = parse_entries(environments)
    if not host_list:
        raise ValueError("RELEASE_HOSTS must list at least one host")
    if not environment_list:
        raise ValueError("ROLLOUT_ENVIRONMENTS must list at least one environment")

    for host in host_list:
        if _HOST.fullmatch(host) is None:
            raise ValueError(f"host: {host!r} is not a registry host")
    for name in environment_list:
        if _ENVIRONMENT.fullmatch(name) is None:
            raise ValueError(f"environment: {name!r} is not a GitHub Environment name")

    if len(host_list) != len(set(host_list)):
        raise ValueError("hosts must be unique")
    if len(environment_list) != len(set(environment_list)):
        raise ValueError("rollout environments must be unique")

    return {"hosts": host_list, "rollouts": environment_list}


def write_github_output(name: str, value: str) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    marker = f"EOF_{name}"
    with open(output, "a", encoding="utf-8") as handle:
        handle.write(f"{name}<<{marker}\n{value}\n{marker}\n")


def plan(hosts: str, environments: str) -> dict[str, str]:
    parsed = parse_release_targets(hosts, environments)
    payload = {
        "rollouts": json.dumps(parsed["rollouts"], separators=(",", ":")),
        "hosts": "\n".join(parsed["hosts"]),
    }
    for name, value in payload.items():
        write_github_output(name, value)
    return payload


def main() -> None:
    try:
        payload = plan(
            os.environ.get("RELEASE_HOSTS", ""),
            os.environ.get("ROLLOUT_ENVIRONMENTS", ""),
        )
    except ValueError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1) from error
    if not os.environ.get("GITHUB_OUTPUT"):
        json.dump(payload, sys.stdout)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
