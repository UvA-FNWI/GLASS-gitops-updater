"""Updater API authentication helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from flask import Request

# Mandatory Bearer-only on new clusters; query ?secret= removed after this date.
QUERY_SECRET_SUNSET_DATE = "2027-01-07"

DEPRECATION_MESSAGE = (
    "Query parameter secret is deprecated; use Authorization: Bearer <secret>. "
    f"Removal planned on {QUERY_SECRET_SUNSET_DATE}."
)


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
