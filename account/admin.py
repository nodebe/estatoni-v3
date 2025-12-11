from django.contrib import admin

from account.models import User
from base.admin import BaseAdmin


@admin.register(User)
class UserAdmin(BaseAdmin):
    list_display = ["user_id", "first_name", "last_name", "email", "phone_number", "last_login"]
