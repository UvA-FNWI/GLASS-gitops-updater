from urllib.parse import unquote_plus

from gunicorn.glogging import Logger as GunicornBaseLogger

_REDACTED = "[REDACTED]"


def redact_uri(raw_uri: str) -> str:
    path, separator, query = raw_uri.partition("?")
    if not separator:
        return raw_uri

    # Preserve any fragment, although HTTP request targets normally have none.
    query, fragment_separator, fragment = query.partition("#")

    redacted_parts = []
    for part in query.split("&"):
        key, _equals, _value = part.partition("=")
        if unquote_plus(key) == "secret":
            part = f"{key}={_REDACTED}"
        redacted_parts.append(part)

    return path + separator + "&".join(redacted_parts) + fragment_separator + fragment


def redact_access_environ(environ: dict) -> None:
    raw_uri = environ.get("RAW_URI")
    if raw_uri:
        environ["RAW_URI"] = redact_uri(raw_uri)

    query = environ.get("QUERY_STRING")
    if query:
        environ["QUERY_STRING"] = redact_uri("?" + query)[1:]

    if environ.get("HTTP_AUTHORIZATION"):
        environ["HTTP_AUTHORIZATION"] = _REDACTED


class CustomGunicornLogger(GunicornBaseLogger):
    def access(self, resp, req, environ, request_time):
        redact_access_environ(environ)
        super().access(resp, req, environ, request_time)
