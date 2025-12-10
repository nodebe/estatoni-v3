from django.contrib.auth.hashers import make_password
from password_validator import PasswordValidator
from rest_framework import serializers
from utils.constants.messages import ResponseMessages
from utils.errors import UserError


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        data = attrs.copy()

        password = attrs.get("password", "")

        password_schema = PasswordValidator()
        password_schema.min(8).uppercase().lowercase().digits().symbols()

        if not password_schema.validate(password):
            raise UserError(ResponseMessages.insecure_password)

        data["password"] = make_password(password)

        return data


class VerifyUserOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, min_length=4, max_length=4)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)
