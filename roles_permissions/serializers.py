from rest_framework import serializers
from models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "group_name"]


class CreateEditRoleSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    permission_ids = serializers.ListField(child=serializers.IntegerField())


class VerySimpleRoleSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)


class SimpleRoleSerializer(VerySimpleRoleSerializer):
    description = serializers.CharField(required=True)


class RoleSerializer(SimpleRoleSerializer):
    permissions = PermissionSerializer(many=True)
