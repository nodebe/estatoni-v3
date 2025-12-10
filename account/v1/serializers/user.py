from rest_framework import serializers
from account.models import User
from media.models import UploadedMedia
from roles_permissions.models import Role

base_user_serializer_fields = ["first_name", "last_name", "phone_number", "profile_photo_id", "role_ids"]


class BaseUserSerializer(serializers.ModelSerializer):
    profile_photo_id = serializers.PrimaryKeyRelatedField(source="profile_photo", queryset=UploadedMedia.objects.all(),
                                                          required=False, allow_null=True)
    role_ids = serializers.PrimaryKeyRelatedField(source="roles", queryset=Role.objects.all(), many=True, required=True)


class UserSerializer(BaseUserSerializer):

    class Meta:
        model = User
        fields = base_user_serializer_fields + ["email"]


class UpdateUserSerializer(BaseUserSerializer):
    class Meta:

        model = User
        fields = base_user_serializer_fields
