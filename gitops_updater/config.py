import os

from dataclasses import dataclass

from ruamel.yaml import YAML

from gitops_updater.providers.github import GitHubProvider
from gitops_updater.providers.gitlab import GitLabProvider

from typing import List

from gitops_updater.utils import get_secret


@dataclass
class ConfigEntry:
    name: str
    path: str
    secret_path: str
    handler: str
    provider: str
    mapping: str
    paths: List[str]

    def valid_secret(self, secret: str) -> bool:
        return self.secret() == secret

    def secret(self) -> str:
        return get_secret(self.secret_path)


class ConfigReader:
    def find(self, filename: str, name: str) -> ConfigEntry:
        yaml = YAML()
        with open(filename, 'r') as file:
            yamlfile = yaml.load(file)
            for row in yamlfile['config']:
                if row['name'] == name:
                    return ConfigEntry(
                        row['name'],
                        row['path'] if 'path' in row else None,
                        row['secretPath'],
                        row['handler'],
                        row['provider'],
                        row['mapping'] if 'mapping' in row else None,
                        row['paths'] if 'paths' in row else None
                    )

        raise Exception("Couldn't read config")

    def find_provider(self, filename: str, name: str):
        yaml = YAML()
        with open(filename, 'r') as file:
            yamlfile = yaml.load(file)
            for row in yamlfile['providers']:
                if row['name'] == name and row['type'] == 'GitHub':
                    return GitHubProvider(row['tokenPath'], row['branch'], row['repository'])
                if row['name'] == name and row['type'] == 'GitLab':
                    return GitLabProvider(row['url'], row['tokenPath'], row['branch'], row['project'])

        raise Exception("Couldn't read config")
