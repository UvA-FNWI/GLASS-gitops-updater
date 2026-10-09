import hmac
from dataclasses import dataclass

from ruamel.yaml import YAML

from gitops_updater.exceptions import UnknownConfigError, UnknownProviderError
from gitops_updater.providers.github import GitHubProvider
from gitops_updater.providers.gitlab import GitLabProvider
from gitops_updater.utils import get_secret


@dataclass
class ConfigEntry:
    name: str
    path: str
    secret_path: str
    handler: str
    provider: str
    mapping: str
    paths: list[str]
    allow_downgrade: bool = False

    def valid_secret(self, secret: str) -> bool:
        expected = self.secret().strip().encode("utf-8")
        provided = secret.strip().encode("utf-8")
        return hmac.compare_digest(expected, provided)

    def secret(self) -> str:
        return get_secret(self.secret_path)


class ConfigReader:
    def find(self, filename: str, name: str) -> ConfigEntry:
        yaml = YAML()
        with open(filename, "r") as file:
            yamlfile = yaml.load(file)
            for row in yamlfile["config"]:
                if row["name"] == name:
                    return ConfigEntry(
                        row["name"],
                        row.get("path", None),
                        row["secretPath"],
                        row["handler"],
                        row["provider"],
                        row.get("mapping", None),
                        row.get("paths", None),
                        bool(row.get("allowDowngrade", False)),
                    )

        raise UnknownConfigError(f'Unknown configuration name "{name}"')

    def find_provider(self, filename: str, name: str):
        yaml = YAML()
        with open(filename, "r") as file:
            yamlfile = yaml.load(file)
            for row in yamlfile["providers"]:
                if row["name"] == name and row["type"] == "GitHub":
                    return GitHubProvider(
                        row["tokenPath"], row["branch"], row["repository"]
                    )
                if row["name"] == name and row["type"] == "GitLab":
                    return GitLabProvider(
                        row["url"], row["tokenPath"], row["branch"], row["project"]
                    )

        raise UnknownProviderError(f'Unknown provider "{name}"')
