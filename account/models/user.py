from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from base.models import AppDbModel, BaseModel
from roles_permissions.constants import RoleEnum


class LanguageOptions(models.TextChoices):
    english = 'en'


class IDTypeLabelOptions(models.TextChoices):
    bvn = "bvn"
    nin = "nin"


class VerificationStatusOption(models.TextChoices):
    not_started = "Not Started"
    processing = "Processing"
    pending = "Pending"
    verified = "Verified"
    failed = "Failed"


class KYCVerificationServiceOptions(models.TextChoices):
    prembly = "Prembly"


class OtpBase(AppDbModel):
    otp = models.CharField(max_length=255, null=False)
    otp_requested_at = models.DateTimeField(null=False)
    is_otp_verified = models.BooleanField(default=False)
    otp_verified_at = models.DateTimeField(null=True)
    trials = models.IntegerField(default=0)

    class Meta:
        abstract = True


class Otp(OtpBase):
    user = models.OneToOneField("account.User", on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.user.email


class IDType(BaseModel):
    name = models.CharField(max_length=255, null=False, unique=True)
    label = models.CharField(max_length=255, null=False, unique=True, choices=IDTypeLabelOptions.choices)
    country = models.ForeignKey("location.Country", on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class User(AbstractUser, BaseModel):
    user_id = models.CharField(max_length=50, unique=True, null=False, db_index=True)
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(unique=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    can_reset_password = models.BooleanField(default=False)
    profile_photo = models.OneToOneField(to="media.UploadedMedia", null=True, on_delete=models.SET_NULL,
                                         related_name="owner", blank=True)
    roles = models.ManyToManyField("roles_permissions.Role", related_query_name="roles", blank=True)
    permissions = models.ManyToManyField("roles_permissions.Permission", related_query_name="permissions", blank=True)
    id_type = models.ForeignKey("IDType", on_delete=models.SET_NULL, null=True)
    id_number = models.CharField(max_length=50, null=True, blank=True, unique=True)
    dob = models.DateField(null=True, blank=True)
    kyc_verification_status = models.CharField(max_length=30, choices=VerificationStatusOption.choices,
                                               default=VerificationStatusOption.not_started)
    kyc_verification_response_data = models.JSONField(null=True, blank=True)
    kyc_verification_comment = models.TextField(null=True, blank=True)
    language = models.CharField(max_length=10, default=LanguageOptions.english, choices=LanguageOptions.choices)
    country = models.ForeignKey("location.Country", on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(f"{self.first_name}::{self.user_id}")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    groups = None
    user_permissions = None

    @property
    def tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
            'token_type': "Bearer"
        }

    def has_permission(self, perm_name):
        if self.is_superuser:
            return True

        q = Q(permissions__name=perm_name)

        return self.roles.filter(Q(name__exact=RoleEnum.sysadmin)).exists() or self.permissions.filter(q).exists()

    def has_role(self, role_name):
        q = Q(name=role_name)

        return self.roles.filter(q).exists()

    def has_any_of_roles(self, role_names):
        q = Q(name__in=role_names)

        return self.roles.filter(q).exists()


class ApiRequestLogger(AppDbModel):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, null=True, related_name="+")
    path = models.CharField(max_length=255)
    ref_id = models.CharField(null=False, db_index=True, max_length=255)
    headers = models.JSONField(default=dict)
    request_data = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = "API Request Logs"


class KYCVerificationService(BaseModel):
    name = models.CharField(max_length=255, choices=KYCVerificationServiceOptions.choices, null=False, unique=True)


class KYCVerificationData(BaseModel):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="+")
    first_name = models.CharField(max_length=255, null=False, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    dob = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=False, blank=True)
    email = models.EmailField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    state_of_origin = models.CharField(max_length=100, null=True, blank=True)
    state_of_residence = models.CharField(max_length=100, null=True, blank=True)
    city_of_residence = models.CharField(max_length=100, null=True, blank=True)
    image_string = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=False)
