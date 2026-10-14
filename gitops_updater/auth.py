"""Updater API authentication helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from email.utils import format_datetime
from enum import Enum

from flask import Request

# Mandatory Bearer-only on new clusters; query ?secret= removed after this date (ISO).
QUERY_SECRET_SUNSET_DATE = "2027-01-07"

QUERY_SECRET_SUNSET_AT = datetime.combine(
    date.fromisoformat(QUERY_SECRET_SUNSET_DATE),
    time(23, 59, 59),
    tzinfo=UTC,
)
QUERY_SECRET_SUNSET_HTTPDATE = format_datetime(QUERY_SECRET_SUNSET_AT, usegmt=True)

DEPRECATION_MESSAGE = (
    "Query parameter secret is deprecated; use Authorization: Bearer <secret>. "
    f"Removal planned on {QUERY_SECRET_SUNSET_DATE}."
)


def deprecation_headers() -> dict[str, str]:
    """RFC 8594-style headers when query ?secret= is used."""
    return {
        "Deprecation": "true",
        "Sunset": QUERY_SECRET_SUNSET_HTTPDATE,
    }


class AuthMethod(str, Enum):
    BEARER = "bearer"
    QUERY = "query"


@dataclass(frozen=True)
class ResolvedAuth:
    secret: str
    method: AuthMethod


def parse_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def resolve_updater_secret(request: Request) -> ResolvedAuth | None:
    """Return credentials from Bearer header or legacy query parameter (Bearer wins)."""
    bearer = parse_bearer_token(request.headers.get("Authorization"))
    query = request.args.get("secret")

    if bearer:
        return ResolvedAuth(bearer, AuthMethod.BEARER)
    if query is not None:
        return ResolvedAuth(query, AuthMethod.QUERY)
    return None
