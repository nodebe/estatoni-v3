from django.contrib.auth.hashers import make_password
from password_validator import PasswordValidator
from rest_framework import serializers
from account.models import User
from roles_permissions.serializers import SimpleRoleSerializer
from media.models import UploadedMedia
from utils.constants.messages import ResponseMessages
from utils.errors import UserError


class VerySimpleProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_id", "first_name", "last_name", "email", "phone_number"]


base_profile_serializer_fields = ['user_id', 'first_name', 'last_name', 'phone_number', 'email', "profile_photo",
                                  "roles", "created_at", "created_by", "components", "states", "lgas", "is_active"]


class BaseProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    profile_photo = serializers.URLField(source="profile_photo.url", read_only=True)
    created_by = VerySimpleProfileSerializer(read_only=True)


class ProfileSerializer(BaseProfileSerializer):
    profile_photo_id = serializers.PrimaryKeyRelatedField(source="profile_photo", queryset=UploadedMedia.objects.all(),
                                                          required=False, write_only=True)
    updated_by = VerySimpleProfileSerializer(read_only=True)
    deactivated_by = VerySimpleProfileSerializer(read_only=True)
    roles = SimpleRoleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = base_profile_serializer_fields + ["is_active", "profile_photo_id", "updated_by", "updated_at",
                                                   "deactivated_by", "deactivated_at"]


class SimpleProfileSerializer(BaseProfileSerializer):
    roles = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)

    class Meta:
        model = User
        fields = base_profile_serializer_fields


class PasswordResetSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        data = attrs.copy()

        password = attrs.get("new_password", "")

        password_schema = PasswordValidator()
        password_schema.min(8).uppercase().lowercase().digits().symbols()

        if not password_schema.validate(password):
            raise UserError(ResponseMessages.insecure_password)

        data["new_password"] = make_password(password)

        return data
