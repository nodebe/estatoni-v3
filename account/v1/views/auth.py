from rest_framework.generics import CreateAPIView
from drf_spectacular.utils import extend_schema

from ..serializers.auth import (LoginSerializer, EmailSerializer, ResetPasswordSerializer, VerifyUserOTPSerializer,
                                RefreshTokenSerializer)
from ..services.auth import AuthService
from utils.util import CustomApiRequest


class LoginAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = LoginSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.login)


class ForgotPasswordAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = EmailSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.forgot_password)


class VerifyPasswordOTPAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = VerifyUserOTPSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.verify_password_otp)


class PasswordResetOTPAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = ResetPasswordSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.reset_password)


class CustomTokenRefreshAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = RefreshTokenSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.refresh_token)
