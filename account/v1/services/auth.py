from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db.models import TextChoices
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from notification.tasks import send_password_reset, send_signup_otp
from roles_permissions.constants import RoleEnum
from roles_permissions.services import RoleService
from utils.constants.messages import ResponseMessages, ErrorMessages
from utils.errors import UserError, AccessDeniedError, NotAuthorizedError
from utils.models import ModelService
from .user import AccountService
from utils.util import CustomApiRequest, generate_otp, check_time_expired, get_unique_id
from ...models import Otp, User
from django.utils import timezone


class OTPIntent(TextChoices):
    reset_password = "Reset Password"
    signup_otp = "Signup OTP"


class AuthService(CustomApiRequest):

    def __init__(self, request):
        super().__init__(request)
        self.model_service = ModelService(request)

    def send_otp(self, payload, otp_intent=None):
        email = payload.get("email")
        account_service = AccountService(self.request)

        user_exists, user = account_service.check_email_exists(email)

        if user_exists:
            user_email_verified = user.email_verified
            otp_service = OTPService(self.request)

            if otp_intent == OTPIntent.signup_otp and not user_email_verified or otp_intent == OTPIntent.reset_password:
                otp = otp_service.get_or_set_user_otp(user)
            else:
                otp = None

            if otp_intent == OTPIntent.reset_password:
                _ = send_password_reset.delay(email=email, first_name=user.first_name, otp=otp)
            elif otp_intent == OTPIntent.signup_otp:
                if not user_email_verified:
                    _ = send_signup_otp.delay(email=email, first_name=user.first_name, otp=otp)

        return ResponseMessages.otp_sent_to_email

    def register(self, payload):
        phone_number = payload.get("phone_number")

        account_service = AccountService(self.request)
        account = account_service.fetch_user_by_phone_number(phone_number, is_fresh=True)

        if account:
            raise UserError(ResponseMessages.phone_already_exist)

        payload["user_id"] = get_unique_id(length=10)

        user = self.model_service.create_model_instance(model=User, payload=payload)

        # Send OTP to email
        otp_service = OTPService(self.request)
        otp = otp_service.get_or_set_user_otp(user)

        #  Setup User Roles and Permissions
        role_service = RoleService(self.request)
        role = role_service.fetch_single_by_label(role_label=RoleEnum.user.label)

        user.roles.add(role.id)

        _ = send_signup_otp.delay(email=user.email, first_name=user.first_name, otp=otp)

        return ResponseMessages.otp_sent_to_email

    def logout(self, payload):
        auth_header = self.request.headers.get("Authorization")
        refresh_token = payload.get("refresh_token")
        # TODO: Fix the logout

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            access_token_str = auth_header.split(" ")[1]
            access_token = AccessToken(access_token_str)

            token_obj, created = OutstandingToken.objects.get_or_create(
                user=self.auth_user,
                jti=access_token["jti"],
                token=access_token_str,
                expires_at=timezone.make_aware(access_token["exp"]),
            )

            BlacklistedToken.objects.get_or_create(token=token_obj)

            return ResponseMessages.logout_successful

        except TokenError:
            raise UserError(ResponseMessages.invalid_token)

    def refresh_token(self, payload):
        token = payload.get('refresh_token')

        if not token:
            raise AccessDeniedError()

        try:
            refresh = RefreshToken(token)

        except Exception:
            raise NotAuthorizedError(ResponseMessages.token_expired)

        return {"access_token": str(refresh.access_token)}

    def reset_password(self, payload):
        email = payload.get("email")
        password = payload.get("password")

        account_service = AccountService(self.request)

        user_exists, user = account_service.check_email_exists(email)

        if user_exists:
            if not user.can_reset_password:
                raise AccessDeniedError()

            user.password = password
            user.can_reset_password = False
            user.save(update_fields=["password", "can_reset_password"])

            return ResponseMessages.successful_password_change

        raise UserError(message=ResponseMessages.user_not_recognized)

    def forgot_password(self, payload):
        email = payload.get("email")
        account_service = AccountService(self.request)

        user_exists, user = account_service.check_email_exists(email)

        if user_exists:
            otp_service = OTPService(self.request)
            otp = otp_service.get_or_set_user_otp(user)

            _ = send_password_reset.delay(email=email, first_name=user.first_name, otp=otp)

        return ResponseMessages.reset_password_email_sent

    def verify_otp_via_email(self, payload, otp_intent=None):
        """
        :param otp_intent: used to determine what happens after verifying otp
        :param payload: {
            otp: 4-digit code,
            email: "email@emaildomain.com"
        }
        :return: User or Message
        """
        otp = payload.get("otp")
        email = payload.get("email")

        account_service = AccountService(self.request)
        user_exists, user = account_service.check_email_exists(email)

        if user_exists and hasattr(user, "otp"):
            otp_service = OTPService(self.request)

            if otp_service.verify_otp(user, otp):
                if otp_intent == OTPIntent.reset_password:
                    user.can_reset_password = True
                    user.save(update_fields=["can_reset_password"])
                    return ResponseMessages.valid_otp

                elif otp_intent == OTPIntent.signup_otp:
                    if not user.email_verified:
                        user.email_verified = True
                        user.save(update_fields=["email_verified"])

                        return account_service.get_user_data(user)
                    else:
                        raise UserError(ResponseMessages.user_email_already_verified)

                return ResponseMessages.valid_otp

            raise UserError(message=ResponseMessages.invalid_or_expired_otp)

        raise UserError(message=ResponseMessages.user_not_recognized)

    def verify_password_otp(self, payload):
        return self.verify_otp_via_email(payload, otp_intent=OTPIntent.reset_password)

    def verify_register_otp(self, payload):
        return self.verify_otp_via_email(payload, otp_intent=OTPIntent.signup_otp)

    def login(self, payload):
        username = payload.get("email").lower()
        password = payload.get("password")

        account_service = AccountService(self.request)
        user_exists, user = account_service.check_email_exists(username)

        if user and not user.is_active:
            raise AccessDeniedError(ErrorMessages.inactive_account)

        authenticate_kwargs = {
            "username": username,
            "password": password
        }

        login_count_cache_key = self.generate_cache_key("login_count", username)

        login_count = cache.get(key=login_count_cache_key)

        if login_count and login_count >= 5:
            raise AccessDeniedError(message=ResponseMessages.too_many_attempts_account_blocked)

        user = authenticate(**authenticate_kwargs)

        if user is None:
            login_count = 1 if login_count is None else login_count + 1
            cache.set(login_count_cache_key, login_count, timeout=1200)

            raise UserError(message=ResponseMessages.invalid_credentials)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        account_service = AccountService(request=self.request)

        return account_service.get_user_data(user)


class OTPService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def create(self, data):
        model_service = ModelService(self.request)

        _ = model_service.create_model_instance(model=Otp, payload=data)

        return True

    def get_or_set_user_otp(self, user):
        """Creates the OTP one-to-one relationship for the user if not existing or creates a new OTP and attaches it
        to the already existing relationship"""
        otp, hashed_otp = generate_otp()

        data = {
            "user": user,
            "otp": hashed_otp,
            "otp_requested_at": timezone.now()
        }

        if not hasattr(user, "otp"):
            _ = self.create(data)

        else:
            _ = self.update_user_otp(user, hashed_otp)

        return otp

    def update_user_otp(self, user, hashed_otp):
        user_otp = user.otp
        user_otp.otp = hashed_otp
        user_otp.trials = 0
        user_otp.otp_requested_at = timezone.now()
        user_otp.otp_verified_at = None
        user_otp.is_otp_verified = False
        user_otp.save(update_fields=["otp", "otp_requested_at", "trials", "is_otp_verified", "otp_verified_at"])

        return True

    def verify_otp(self, user, incoming_otp):
        user_otp = user.otp

        if user_otp.trials >= 3:
            raise UserError(message=ResponseMessages.too_many_failed_otp_verification_attempts)

        if user_otp.is_otp_verified:
            raise UserError(message=ResponseMessages.invalid_or_expired_otp)

        otp_requested_at = user_otp.otp_requested_at
        hashed_otp = user_otp.otp

        if check_password(incoming_otp, hashed_otp) and not check_time_expired(otp_requested_at):
            user_otp.is_otp_verified = True
            user_otp.otp_verified_at = timezone.now()
            user_otp.save(update_fields=["is_otp_verified", "otp_verified_at"])

            return True

        user_otp.trials += 1
        user_otp.save(update_fields=["trials"])

        return False
