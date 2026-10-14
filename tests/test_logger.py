from gitops_updater.logger import redact_access_environ


def test_redact_access_environ_masks_query_secret_and_authorization():
    environ = {
        "QUERY_STRING": "name=x&secret=abcdefghijklmnop",
        "RAW_URI": "/gitops-updater?name=x&secret=abcdefghijklmnop",
        "HTTP_AUTHORIZATION": "Bearer very-secret-token",
    }

    redact_access_environ(environ)

    assert environ["RAW_URI"] == "/gitops-updater?name=x&secret=[REDACTED]"
    assert environ["QUERY_STRING"] == "name=x&secret=[REDACTED]"
    assert "abcdefghijklmnop" not in environ["RAW_URI"]
    assert environ["HTTP_AUTHORIZATION"] == "[REDACTED]"


def test_redact_encoded_short_and_unrelated_secret_text():
    environ = {
        "QUERY_STRING": "secret=ab&name=secret",
        "RAW_URI": "/gitops-updater?s%65cret=a%2Fb&other=secret#keep",
    }

    redact_access_environ(environ)

    assert environ["QUERY_STRING"] == "secret=[REDACTED]&name=secret"
    assert environ["RAW_URI"] == "/gitops-updater?s%65cret=[REDACTED]&other=secret#keep"
