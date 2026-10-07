from urllib.parse import parse_qsl

from gunicorn.glogging import Logger as GunicornBaseLogger

_REDACTED = "[REDACTED]"


def redact_access_environ(environ: dict) -> None:
    parsed_query = parse_qsl(environ.get("QUERY_STRING", ""))

    for key, value in parsed_query:
        if key == "secret":
            redacted_secret = (
                value[0:2] + ("*" * (len(value) - 3)) + value[-1]
                if len(value) > 3
                else value
            )
            raw_uri = environ.get("RAW_URI")
            if raw_uri:
                environ["RAW_URI"] = raw_uri.replace(value, redacted_secret, 1)

    if environ.get("HTTP_AUTHORIZATION"):
        environ["HTTP_AUTHORIZATION"] = _REDACTED


class CustomGunicornLogger(GunicornBaseLogger):
    def access(self, resp, req, environ, request_time):
        redact_access_environ(environ)
        super().access(resp, req, environ, request_time)
