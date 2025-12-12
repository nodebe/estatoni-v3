from django.contrib.auth.hashers import make_password
from password_validator import PasswordValidator
from rest_framework import serializers
from account.models import User
from account.v1.services.user import UserService, AccountService
from location.v1.models import Country
from utils.constants.messages import ResponseMessages
from utils.errors import UserError
from utils.util import format_phone_number


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
    otp = serializers.CharField(required=True, min_length=6, max_length=6)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)


class RegisterSerializer(serializers.ModelSerializer):
    country_id = serializers.PrimaryKeyRelatedField(source="country", queryset=Country.objects.all())

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "password", "country_id"]

    def validate_email(self, value):
        account_service = AccountService(None)
        account_exists, _ = account_service.check_email_exists(value)

        if account_exists:
            raise UserError(ResponseMessages.email_already_exist)

        return value

    def validate(self, attrs):
        data = attrs.copy()

        password = data.get("password", "")
        phone_number = data.get("phone_number", "")

        if phone_number:
            formatted_phone_number = format_phone_number(phone_number)

            if not formatted_phone_number:
                raise UserError(ResponseMessages.invalid_phone_number)

            data["phone_number"] = formatted_phone_number

        password_schema = PasswordValidator()
        password_schema.min(8).uppercase().lowercase().digits().symbols()

        if not password_schema.validate(password):
            raise UserError(ResponseMessages.insecure_password)

        data["password"] = make_password(password)

        return data
