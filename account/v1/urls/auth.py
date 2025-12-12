from django.urls import path
from rest_framework_simplejwt.views import TokenBlacklistView

from account.v1.views.auth import (LoginAPIView, ForgotPasswordAPIView, VerifyPasswordOTPAPIView, RegisterAPIView,
                                   PasswordResetOTPAPIView, CustomTokenRefreshAPIView, VerifyRegisterOTPAPIView,
                                   ResendRegisterOTPAPIView, LogoutAPIView)

urlpatterns = [
    path("register", RegisterAPIView.as_view(), name='register'),
    path("register/verify", VerifyRegisterOTPAPIView.as_view(), name='register_verify'),
    path("register/resend-otp", ResendRegisterOTPAPIView.as_view(), name='register_resend_otp'),
    path("login", LoginAPIView.as_view(), name='login'),
    path("password/forgot", ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path("password/reset", PasswordResetOTPAPIView.as_view(), name='reset_password'),
    path("password/verify-otp", VerifyPasswordOTPAPIView.as_view(), name='verify_password_otp'),
    path('token/refresh', CustomTokenRefreshAPIView.as_view(), name='token_refresh'),
    path('logout', LogoutAPIView.as_view(), name='logout'),
]
