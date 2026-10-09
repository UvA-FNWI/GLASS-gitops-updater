"""Client-facing errors that should not produce server stack traces in logs."""


class UpdaterClientError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class UnknownConfigError(UpdaterClientError):
    pass


class UnknownProviderError(UpdaterClientError):
    pass
