"""Error handling middleware."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.services.providers.exceptions import (
    ExternalServiceError,
    PriceProviderError,
    ServiceUnavailableError,
    SettlementProviderError,
    TradingProviderError,
)


async def error_handler_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Global error handler middleware."""
    try:
        return await call_next(request)
    except ServiceUnavailableError as exc:
        logger.error(
            f"Service unavailable: {exc.service_name} - {exc}",
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": str(exc),
                "service": exc.service_name,
                "error_type": "service_unavailable",
            },
        )
    except (TradingProviderError, SettlementProviderError, PriceProviderError) as exc:
        logger.error(
            f"Provider error: {exc.service_name} - {exc}",
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "detail": str(exc),
                "service": exc.service_name,
                "error_type": "provider_error",
            },
        )
    except ExternalServiceError as exc:
        logger.error(
            f"External service error: {exc.service_name} - {exc}",
            exc_info=exc,
        )
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "detail": str(exc),
                "service": exc.service_name,
                "error_type": "external_service_error",
            },
        )
    except Exception as exc:
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
