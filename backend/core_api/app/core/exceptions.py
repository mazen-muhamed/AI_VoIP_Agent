#Custom HTTP Exceptions , What Can go wrong

from __future__ import annotations


class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"
    default_message: str = "Internal server error"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.default_message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Not Found"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    default_message = "Invalid Credentials"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    default_message = "Forbidden"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "Resource already exists"


class ValidationError(AppError):
    status_code = 422
    code = "unprocessable_content"
    default_message = "Validation failed"


class TokenExpired(UnauthorizedError):
    def __init__(self):
        super().__init__(message="Token expired")


class TokenInvalid(UnauthorizedError):
    def __init__(self):
        super().__init__(message="Invalid token")


class AccountDisabled(UnauthorizedError):
    def __init__(self):
        super().__init__(message="Account disabled. Contact your system administrator.")