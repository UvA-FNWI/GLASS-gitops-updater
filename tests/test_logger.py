from gitops_updater.logger import redact_access_environ


def test_redact_access_environ_masks_query_secret_and_authorization():
    environ = {
        "QUERY_STRING": "name=x&secret=abcdefghijklmnop",
        "RAW_URI": "/gitops-updater?name=x&secret=abcdefghijklmnop",
        "HTTP_AUTHORIZATION": "Bearer very-secret-token",
    }

    redact_access_environ(environ)

    assert "abcdefghijklmnop" not in environ["RAW_URI"]
    assert environ["HTTP_AUTHORIZATION"] == "[REDACTED]"
