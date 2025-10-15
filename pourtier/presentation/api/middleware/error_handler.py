"""
Global error handling middleware.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from pourtier.domain.exceptions import PourtierException


async def pourtier_exception_handler(
    request: Request, exc: PourtierException
) -> JSONResponse:
    """
    Handle Pourtier domain exceptions.

    Converts domain exceptions to appropriate HTTP responses.
    """
    status_code_map = {
        "ENTITY_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DUPLICATE_ENTITY": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "SUBSCRIPTION_EXPIRED": status.HTTP_403_FORBIDDEN,
        "LIMIT_EXCEEDED": status.HTTP_403_FORBIDDEN,
        "NO_ACTIVE_SUBSCRIPTION": status.HTTP_403_FORBIDDEN,
        "PAYMENT_FAILED": status.HTTP_402_PAYMENT_REQUIRED,
        "INVALID_PAYMENT_METHOD": status.HTTP_400_BAD_REQUEST,
        "INSUFFICIENT_FUNDS": status.HTTP_402_PAYMENT_REQUIRED,
        "STRATEGY_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "DEPLOYMENT_ALREADY_ACTIVE": status.HTTP_409_CONFLICT,
        "INVALID_DEPLOYMENT_STATE": status.HTTP_400_BAD_REQUEST,
    }

    status_code = status_code_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.code,
            "message": exc.message,
        },
    )
