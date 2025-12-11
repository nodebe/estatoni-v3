from rest_framework.generics import CreateAPIView, DestroyAPIView
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from ..serializers.auth import (LoginSerializer, EmailSerializer, ResetPasswordSerializer, VerifyUserOTPSerializer,
                                RefreshTokenSerializer, RegisterSerializer)
from ..services.auth import AuthService, OTPIntent
from utils.util import CustomApiRequest


class RegisterAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = RegisterSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.register)


class VerifyRegisterOTPAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = VerifyUserOTPSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.verify_register_otp)


class ResendRegisterOTPAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = EmailSerializer
    permission_classes = []

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.send_otp, otp_intent=OTPIntent.signup_otp)


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
        return self.process_request(request, service.send_otp, otp_intent=OTPIntent.reset_password)


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


class CustomBlacklistTokenAPIView(CreateAPIView, CustomApiRequest):
    serializer_class = RefreshTokenSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Auth"])
    def post(self, request, *args, **kwargs):
        service = AuthService(request)
        return self.process_request(request, service.logout)
