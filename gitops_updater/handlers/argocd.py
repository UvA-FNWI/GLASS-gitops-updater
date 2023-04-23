from dataclasses import dataclass

from gitops_updater.config import ConfigEntry
from gitops_updater.providers.gitprovider import GitProvider, GitFile

import semver
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO

@dataclass
class ArgoCD:
    config: ConfigEntry
    provider: GitProvider

    def handle(self, version: str) -> dict:
        multiple = self.config.paths
        paths = self.config.paths if multiple else [self.config.path]

        errors = []

        for path in paths:
            file: GitFile
            file = self.provider.get_file(path)

            yaml_file = ArgoCDYamlFile(file.content(), None if multiple else self.config.name)
            current_version = yaml_file.current_version()
            target_version = semver.VersionInfo.parse(version)

            if target_version == current_version:
                errors.append(f'{path}: already up-to-date')
            elif current_version > target_version:
                errors.append(f'{path}: not downgrading')
            else:
                updated_content = yaml_file.update(version)
                message = f'Update {path} to {target_version}'
                self.provider.update_file(file, message, updated_content)

        if len(errors) > 0:
            return {
                'message': f'error',
                'errors': errors
            }

        return {
            'message': f'updated successfully',
            'old_version': str(current_version),
            'new_version': version
        }


class ArgoCDYamlFile:
    def __init__(self, content: str, name: str):
        self.yaml_loader = YAML()
        self.yaml_content = list(self.yaml_loader.load_all(content))

        for segment in self.yaml_content:
            if segment['metadata'] is None or (name is not None and segment['metadata']['name'] != name):
                continue

            self.version = segment['spec']['source']['targetRevision']
            self.segment = segment
            return

        raise Exception("Couldn't locate segment in yaml file")

    def current_version(self) -> semver.VersionInfo:
        return semver.VersionInfo.parse(self.version)

    def update(self, version: str) -> str:
        self.segment['spec']['source']['targetRevision'] = version
        stream = StringIO()
        self.yaml_loader.dump_all(self.yaml_content, stream)
        return stream.getvalue()
