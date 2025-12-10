from rest_framework import status
from utils.constants.messages import ErrorMessages


class CustomError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = ErrorMessages.internal_server_error

    def __init__(self, message=None, status_code=None):
        if message is not None:
            self.message = message

        if status_code is not None:
            self.status_code = status_code

        super().__init__(self.message)


class ServerError(CustomError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = ErrorMessages.internal_server_error

    def __init__(self, error=None, error_position=None):
        from utils.util import AppLogger

        if error:
            AppLogger.report(error, error_position)


class UserError(CustomError):
    status_code = status.HTTP_400_BAD_REQUEST
    message = ErrorMessages.bad_request


class NotFoundError(CustomError):
    status_code = status.HTTP_404_NOT_FOUND
    message = ErrorMessages.resource_not_found


class PermissionDeniedError(CustomError):
    status_code = status.HTTP_403_FORBIDDEN
    message = ErrorMessages.permission_denied


class AccessDeniedError(CustomError):
    status_code = status.HTTP_403_FORBIDDEN
    message = ErrorMessages.access_denied


class NotAuthorizedError(CustomError):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = ErrorMessages.access_denied


class CustomServerError(CustomError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = ErrorMessages.internal_server_error


class RateLimitException(CustomError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = ErrorMessages.too_many_requests


class UnprocessableEntityError(CustomError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = ErrorMessages.unprocessable_entity
