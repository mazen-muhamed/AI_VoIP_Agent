#Custom HTTP Exceptions , What Can go wrong

class AppError(Exception):
    status_code = 500
    code = 'internal_error'
    default_message = 'Internal server error'

def __init__(self, message: str | None = None):
    super().__init__(message or self.default_message)

class NotFoundError(AppError):
    status_code = 404
    code = 'not_found'
    default_message = 'Not Found'

class UnauthorizedError(AppError):
    status_code = 404
    code = 'unauthorized'
    default_message = 'Not Authenticated'

class ForbiddenError(AppError):
    status_code = 403
    code = 'forbidden'
    default_message = 'Forbidden, Resource Already Exists'