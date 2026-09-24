from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger

class BaseAppException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)

class NotFoundException(BaseAppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=status.HTTP_404_NOT_FOUND, details=details)

class ValidationException(BaseAppException):
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=status.HTTP_400_BAD_REQUEST, details=details)

class UnauthorizedException(BaseAppException):
    def __init__(self, message: str = "Authentication required", details: Optional[Any] = None):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=status.HTTP_401_UNAUTHORIZED, details=details)

class ForbiddenException(BaseAppException):
    def __init__(self, message: str = "Access denied", details: Optional[Any] = None):
        super().__init__(message=message, code="FORBIDDEN", status_code=status.HTTP_403_FORBIDDEN, details=details)

class DatabaseException(BaseAppException):
    def __init__(self, message: str = "Database operation failed", details: Optional[Any] = None):
        super().__init__(message=message, code="DATABASE_ERROR", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)

def format_error_response(code: str, message: str, details: Optional[Any] = None) -> Dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        }
    }

async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    logger.warning(f"App Exception [{exc.code}] on {request.method} {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(code=exc.code, message=exc.message, details=exc.details)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(f"Validation Exception on {request.method} {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            code="UNPROCESSABLE_ENTITY",
            message="Input validation failed",
            details=exc.errors()
        )
    )

async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred."
        )
    )
