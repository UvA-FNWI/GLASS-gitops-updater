import hashlib
import hmac
import os

from flask import Flask, json, request

from gitops_updater.auth import (
    DEPRECATION_MESSAGE,
    AuthMethod,
    deprecation_headers,
    resolve_updater_secret,
)
from gitops_updater.config import ConfigReader
from gitops_updater.errors import public_error_message
from gitops_updater.handlers.argocd import ArgoCD
from gitops_updater.handlers.result import HandlerResult
from gitops_updater.handlers.template import Template

app = Flask(__name__)


def __json_response(status: int, payload, extra_headers=None):
    headers = extra_headers or {}
    return app.response_class(
        response=json.dumps(payload),
        status=status,
        mimetype="application/json",
        headers=headers,
    )


def __with_deprecation(payload: dict, auth_method: AuthMethod):
    if auth_method != AuthMethod.QUERY:
        return payload, None
    body = {**payload, "deprecation": DEPRECATION_MESSAGE}
    return body, deprecation_headers()


def __parse_allow_downgrade() -> bool:
    value = request.args.get("allowDowngrade")
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes")


def __respond_handler(response: HandlerResult | dict, auth_method: AuthMethod):
    if isinstance(response, HandlerResult):
        status, payload = response.status, response.body
    else:
        status, payload = 200, response
    body, headers = __with_deprecation(payload, auth_method)
    return __json_response(status, body, headers)


@app.get("/healthz")
def healthz():
    return __json_response(200, {"status": "ok"})


@app.get("/readyz")
def readyz():
    config_path = os.environ.get("CONFIG_PATH")
    if not config_path or not os.path.isfile(config_path):
        return __json_response(
            503, {"status": "not ready", "reason": "config unavailable"}
        )
    return __json_response(200, {"status": "ready"})


@app.route("/gitops-updater")
def handle():
    if "CONFIG_PATH" not in os.environ:
        return __json_response(422, {"error": "CONFIG_PATH not set"})

    name = request.args.get("name")
    version = request.args.get("version")

    if name is None or version is None:
        return __json_response(422, {"error": "Missing GET-arguments"})

    resolved = resolve_updater_secret(request)
    if resolved is None:
        return __json_response(
            401,
            {
                "error": (
                    "Missing authentication; send Authorization: Bearer <secret> "
                    "(query parameter secret is deprecated)."
                )
            },
        )

    try:
        config = ConfigReader().find(os.environ["CONFIG_PATH"], name)
        if not config.valid_secret(resolved.secret):
            return __json_response(401, {"error": "Invalid secret"})

        provider = ConfigReader().find_provider(
            os.environ["CONFIG_PATH"], config.provider
        )

        if config.handler == "template":
            id_ = request.args.get("id")
            if id_ is None:
                return __json_response(422, {"error": "Missing GET-arguments"})

            id_ = int(id_)
            handler = Template(config, provider)

            if version == "delete":
                response = handler.handle_closed_pr(id_)
            else:
                response = handler.handle(id_, version, request.args.get("target"))

            return __respond_handler(response, resolved.method)

        if config.handler == "argocd":
            handler = ArgoCD(config, provider)
            allow_downgrade = config.allow_downgrade or __parse_allow_downgrade()
            response = handler.handle(version, allow_downgrade=allow_downgrade)
            return __respond_handler(response, resolved.method)
    except Exception as e:
        return __json_response(422, {"error": public_error_message(e)})


@app.route("/gitops-updater/webhooks/github", methods=["POST"])
def github_webhook():
    body = request.get_json()

    if "action" not in body or "number" not in body:
        return __json_response(422, {"error": "Missing JSON-arguments"})

    if "X-Hub-Signature-256" not in request.headers:
        return __json_response(422, {"error": "Missing X-Hub-Signature-256 header"})

    if body["action"] != "closed":
        return __json_response(200, {"message": "action not closed, skipping"})

    if "CONFIG_PATH" not in os.environ:
        return __json_response(422, {"error": "CONFIG_PATH not set"})

    name = request.args.get("name")
    id_ = body["number"]

    if name is None:
        return __json_response(422, {"error": "Missing GET-arguments"})

    try:
        config = ConfigReader().find(os.environ["CONFIG_PATH"], name)

        expected = hmac.new(
            bytes(config.secret(), "UTF-8"), request.data, hashlib.sha256
        ).hexdigest()
        incoming = (
            request.headers.get("X-Hub-Signature-256").split("sha256=")[-1].strip()
        )
        if not hmac.compare_digest(incoming, expected):
            return __json_response(
                401, {"error": "Invalid secret in X-Hub-Signature-256 header"}
            )

        provider = ConfigReader().find_provider(
            os.environ["CONFIG_PATH"], config.provider
        )
        handler = Template(config, provider)
        response = handler.handle_closed_pr(id_)

        return __json_response(200, response)
    except Exception as e:
        return __json_response(422, {"error": public_error_message(e)})


if __name__ == "__main__":
    app.run()
