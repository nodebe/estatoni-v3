from django.contrib import admin

from account.models import User, IDType, KYCVerificationService, KYCVerificationData
from base.admin import BaseAdmin


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = ["user_id", "first_name", "last_name", "email", "phone_number", "country", "last_login"]


@admin.register(IDType)
class IDTypeAdmin(BaseAdmin):
    list_display = ["name", "label", "country"]


@admin.register(KYCVerificationService)
class KYCVerificationServiceAdmin(BaseAdmin):
    list_display = ["name", "is_active"]


@admin.register(KYCVerificationData)
class KYCVerificationDataAdmin(BaseAdmin):
    list_display = ["user", "first_name", "last_name", "dob", "email", "phone_number", "status"]
