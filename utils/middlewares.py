from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import AuthenticationFailed

from utils.constants.messages import ErrorMessages
from utils.errors import CustomError
from rest_framework_simplejwt.authentication import JWTAuthentication


class CustomExceptionMiddleware(MiddlewareMixin):
    """
        Import this in the middleware list in your settings.py file
        MIDDLEWARE = [
            # Other middlewares
            'utils.middlewares.CustomExceptionMiddleware',
            # Other middlewares
        ]
    """

    def process_exception(self, request, exception):
        if isinstance(exception, CustomError):
            response_data = {
                'error': exception.message
            }

            return JsonResponse(response_data, status=exception.status_code)

        return None


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if not user.is_active:
            raise AuthenticationFailed(
                detail={
                    "error": ErrorMessages.inactive_account,
                }
            )

        return user
