import os.path
from dataclasses import dataclass

import jinja2
from ruamel.yaml import YAML

from gitops_updater.config import ConfigEntry
from gitops_updater.providers.gitprovider import GitProvider, GitFile


class MappingYamlFile:
    def __init__(self, content: str):
        self.yaml_loader = YAML()
        self.yaml_content = self.yaml_loader.load(content)

    def has(self, source):
        return source in self.yaml_content

    def get(self, source):
        return self.yaml_content[source]

@dataclass
class Template:
    config: ConfigEntry
    provider: GitProvider

    def handle(self, id_: int, version: str, target: str = None) -> dict:

        target_path = self.get_target_path(self.config.path, id_)
        target_exists = self.provider.file_exists(target_path)

        template: GitFile
        template = self.provider.get_file(self.config.path)
        if self.config.mapping:
            file_content = self.provider.get_file(self.config.mapping).content()
            mapping = MappingYamlFile(file_content)
            if mapping.has(id_):
                target = mapping.get(id_)
            else:
                target = mapping.get('default')

        content = self.apply_template(template.content(), id_, version, target)

        if not target_exists:
            message = 'Create {}:{} with version {}'.format(self.config.name, id_, version)
            self.provider.create_file(target_path, content, message)
            return {'message': 'File created'}

        else:
            message = 'Update {}:{} to {}'.format(self.config.name, id_, version)
            file: GitFile
            file = self.provider.get_file(target_path)
            if file.content() == content:
                return {'message': 'Already up-to-date'}
            else:
                self.provider.update_file(file, message, content)
                return {'message': 'Version updated'}

    def apply_template(self, content: str, id_: int, version, target) -> str:
        tm = jinja2.Template(content)
        return tm.render(id=id_, version=version, target=target)

    def get_target_path(self, source_path: str, id_: int) -> str:

        directory = os.path.dirname(source_path)
        filename = os.path.basename(source_path)

        filename_segments = filename.split('.')
        filename_segments[0] = '{}-{}'.format(filename_segments[0], id_)

        return os.path.join(directory, '.'.join([segment for segment in filename_segments if segment != 'j2']))

    def handle_closed_pr(self, id_: int):
        target_path = self.get_target_path(self.config.path, id_)
        target_exists = self.provider.file_exists(target_path)

        if not target_exists:
            return {'message': 'target not deployed'}

        file: GitFile
        file = self.provider.get_file(target_path)
        message = 'Delete {}:{}'.format(self.config.name, id_)

        self.provider.delete_file(file, message)

        return {'message': 'removed feature deployment'}
