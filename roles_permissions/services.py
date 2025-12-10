from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from utils.constants.messages import ResponseMessages
from utils.constants.others import ActivityType
from utils.errors import UserError, NotFoundError
from utils.util import CustomApiRequest
from .constants import PermissionGroups, DefaultRolesPermissions
from .models import Permission, Role


class PermissionService(CustomApiRequest):
    # TODO: Insert fetch list and fetch paginated list response

    @staticmethod
    def create_default_permissions():
        permission_ids = []
        for group, permissions in PermissionGroups.items():
            for permission in permissions:
                permission_name = permission.value
                permission_label = permission.label

                permission_obj, is_created = Permission.objects.update_or_create(
                    label=permission_label,
                    defaults={
                        "group_name": group,
                        "name": permission_name,
                    }
                )
                permission_ids.append(permission_obj.pk)
                print(f"Permission '{permission_obj}'", "created" if is_created else "updated")

        Permission.objects.exclude(pk__in=permission_ids).delete()

    @classmethod
    def get_permissions_by_ids(cls, permission_ids):
        if isinstance(permission_ids, str):
            permission_ids = [permission_ids]
        return Permission.objects.filter(pk__in=permission_ids)

    @classmethod
    def get_permissions_by_names(cls, permission_names):
        if isinstance(permission_names, str):
            permission_names = [permission_names]
        return Permission.objects.filter(name__in=permission_names)

    @classmethod
    def get_permission_by_id(cls, permission_id):
        return Permission.objects.filter(pk=permission_id)

    @classmethod
    def get_permission_by_name(cls, permission_name):
        return Permission.objects.filter(name=permission_name)

    def fetch_list(self, filter_params, **kwargs):
        filter_keyword = filter_params.get("keyword")

        q = Q()
        if filter_keyword:
            q = Q(name__icontains=filter_keyword)

        queryset = Permission.objects.filter(q).order_by("name")

        return queryset


class RoleService(CustomApiRequest):

    @staticmethod
    def create_default_roles():
        permission_service = PermissionService()

        for key, value in DefaultRolesPermissions.items():
            role = key
            role_name = role.value
            role_label = role.label

            permission_groups = value

            role, is_created = Role.objects.update_or_create(
                label=role_label,
                defaults={
                    "name": role_name,
                    "description": role_name
                }
            )

            role.permissions.clear()

            for permission in permission_groups:
                if not isinstance(permission, list):
                    permission = [permission]

                role_permissions = permission_service.get_permissions_by_names(permission)
                role.permissions.add(*role_permissions)
                role.save()

            print("Permissions added for role '{}'".format(role_name))

    def create(self, payload):
        permission_service = PermissionService(self.request)
        permissions = permission_service.get_permissions_by_ids(payload.get("permission_ids"))

        name = payload.get("name")
        description = payload.get("description")
        user_can_be_created_by = payload.get("user_can_be_created_by")

        role, is_created = Role.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
                "user_can_be_created_by": user_can_be_created_by
            }
        )

        if not is_created:
            raise UserError(ResponseMessages.role_already_exists.format(name))

        role.permissions.add(*permissions)
        role.save()

        self.report_activity(ActivityType.create, role)

        return role

    def delete(self, role_id):
        role = self.fetch_single(role_id)

        role.deleted_at = timezone.now()
        role.deleted_by = self.auth_user
        role.save()

        cache_key = self.generate_cache_key(role.id, model=Role)
        cache.delete(cache_key)

        self.report_activity(ActivityType.delete, role)

        return role

    @classmethod
    def check_if_role_exists(cls, new_role_name, existing_role_id):
        return Role.objects.filter(name=new_role_name).exclude(id=existing_role_id).exists()

    def update(self, payload, role_id):
        role = self.fetch_single(role_id)

        permission_service = PermissionService(self.request)
        permissions = permission_service.get_permissions_by_ids(payload.get("permission_ids"))

        name = payload.get("name")
        if self.check_if_role_exists(name, role_id):
            raise UserError(ResponseMessages.role_already_exists.format(name))

        role.name = name
        role.description = payload.get("description")
        role.user_can_be_created_by = payload.get("user_can_be_created_by")
        role.permissions.clear()
        role.permissions.add(*permissions)
        role.save()

        self.report_activity(ActivityType.update, role)

        cache_key = self.generate_cache_key(role_id, model=Role)
        cache.delete(cache_key)

        return role

    def fetch_single(self, role_id):
        def fetch():
            role = Role.available_objects.prefetch_related("permissions").filter(pk=role_id).first()

            if not role:
                raise NotFoundError(ResponseMessages.role_not_found)

            return role

        cache_key = self.generate_cache_key(role_id, model=Role)
        return cache.get_or_set(cache_key, fetch)

    @classmethod
    def fetch_by_ids(cls, role_ids):
        return Role.available_objects.filter(pk__in=role_ids)

    def fetch_by_names(self, role_names):
        return Role.available_objects.filter(name__in=role_names)

    def fetch_list(self, filter_params, **kwargs):
        filter_keyword = filter_params.get("keyword")

        q = Q()
        if filter_keyword:
            q = Q(name__icontains=filter_keyword) | Q(description__icontains=filter_keyword)

        queryset = Role.available_objects.prefetch_related("permissions").filter(q).order_by("name")

        return queryset
