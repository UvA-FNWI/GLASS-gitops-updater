import os


def get_secret(path):
    if '/' in path:
        with open(path, 'r') as file:
            return file.read()
    return os.environ[path]
