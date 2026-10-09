import logging

from gitops_updater.exceptions import UpdaterClientError

logger = logging.getLogger(__name__)


def public_error_message(exc: BaseException) -> str:
    """Map exceptions to client-safe messages; log details server-side only."""
    if isinstance(exc, UpdaterClientError):
        logger.info("Client error: %s", exc.message)
        return exc.message

    logger.error("Request failed", exc_info=exc)

    if isinstance(exc, ValueError):
        return "Invalid request"

    if isinstance(exc, FileNotFoundError):
        return "Configuration file or secret not found"

    if isinstance(exc, PermissionError):
        return "Configuration not accessible"

    if isinstance(exc, OSError):
        return "Configuration error"

    return "Request processing failed"
