from dataclasses import dataclass


@dataclass(frozen=True)
class HandlerResult:
    body: dict
    status: int = 200
