from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from account.models import User
from account.v1.serializers.profile import SimpleProfileSerializer
from roles_permissions.models import Permission, Role
from roles_permissions.services import RoleService
from utils.constants.messages import ResponseMessages
from roles_permissions.constants import RoleEnum, RoleHierarchy
from utils.errors import ServerError, NotFoundError, UserError, PermissionDeniedError
from utils.models import ModelService
from utils.util import CustomApiRequest, get_unique_id, generate_password


class AccountService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def fetch(self):
        return self.auth_user

    def check_email_exists(self, email):
        user = User.objects.filter(Q(email__iexact=email))

        return user.exists(), user.first()

    def set_profile_photo(self, profile_photo_media):
        self.auth_user.profile_photo = profile_photo_media
        self.auth_user.save(update_fields=['profile_photo'])

    def update(self, payload):
        model_service = ModelService(self.request)

        profile_photo = payload.pop("profile_photo", None)

        user_update = model_service.update_model_instance(model_instance=self.auth_user, **payload)

        if profile_photo:
            self.set_profile_photo(profile_photo)

        cache_key = self.generate_cache_key(self.auth_user.user_id, model=User)
        cache.delete(cache_key)

        return user_update

    def fetch_user_by_user_id(self, user_id, is_background=False):
        def __do_fetch_single():
            try:
                user = User.objects.get(user_id=user_id)
                return user

            except User.DoesNotExist:
                if is_background:
                    return None

                raise NotFoundError(ResponseMessages.user_with_id_not_found.format(user_id))

            except Exception as e:
                raise ServerError(error=e, error_position="UserService.fetch_user_by_user_id")

        if is_background:
            return __do_fetch_single()

        cache_key = self.generate_cache_key(user_id, model=User)
        return cache.get_or_set(cache_key, __do_fetch_single)

    def fetch_user_by_phone_number(self, phone_number, is_fresh=False):
        """
        is_fresh: True for when you're searching for a signup, to allow you to continue with the flow instead of raising error
        """

        def __do_fetch_single():
            try:
                user = User.objects.get(phone_number=phone_number)
                return user

            except User.DoesNotExist:
                if is_fresh:
                    return None
                else:
                    raise NotFoundError(ResponseMessages.user_with_phone_number_not_found.format(phone_number))

            except Exception as e:
                raise ServerError(error=e, error_position="UserService.fetch_user_by_user_id")

        cache_key = self.generate_cache_key(phone_number, model=User)
        return cache.get_or_set(cache_key, __do_fetch_single)

    def check_username_exists(self, username):
        user = User.objects.filter(Q(username__iexact=username))

        return user.exists(), user.first()

    def fetch_user_data(self):
        user_data = self.get_user_data(self.auth_user)

        poppable_data = ["refresh_token", "access_token", "token_type"]
        for key in poppable_data:
            user_data.pop(key, None)

        return user_data

    def get_user_data(self, user):

        user_service = UserService(self.request)

        permissions = user_service.get_user_permissions(user)
        roles = user_service.get_user_role_names(user)

        return {
            **user.tokens,
            "token_type": "Bearer",
            "user": {
                "id": user.user_id,
                "email": user.email,
                "phone_number": user.phone_number,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_photo": user.profile_photo.url if user.profile_photo else None,
                "roles": roles,
                "permissions": permissions,
                "is_email_verified": user.email_verified
            }
        }

    def reset_password(self, payload):
        user = self.auth_user
        old_password = payload.get("old_password")
        new_password = payload.get("new_password")

        if not check_password(old_password, user.password):
            raise UserError(ResponseMessages.incorrect_password)

        user.password = new_password
        user.save(update_fields=["password"])

        return ResponseMessages.successful_password_change


class UserService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)
        self.serializer_class = SimpleProfileSerializer

    def active_or_deactivate(self, payload, user_id):
        account_service = AccountService(self.request)
        user = account_service.fetch_user_by_user_id(user_id)

        # Check for user's current roles
        self.check_permission_to_act_based_on_role_hierarchy(user.roles.all())

        status = payload.get("status", True)

        if status:
            user.is_active = True
            user.deactivated_by = None
            user.deactivated_at = None
        else:
            user.is_active = False
            user.deactivated_by = self.auth_user
            user.deactivated_at = timezone.now()

        user.save(update_fields=["is_active", "deactivated_by", "deactivated_at"])

        verb = "activated" if status else "deactivated"

        self.report_activity(activity_type=verb, data=user)

        return user

    def update(self, payload, user_id):
        account_service = AccountService(self.request)
        user = account_service.fetch_user_by_user_id(user_id)

        # Check the roles of the user to be updated
        self.check_permission_to_act_based_on_role_hierarchy(user.roles.all())

        # Check for incoming roles to be added to user
        roles = payload.pop("roles", None) or user.roles
        self.check_permission_to_act_based_on_role_hierarchy(roles)

        permissions = payload.pop("permissions", None) or user.permissions

        model_service = ModelService(self.request)

        user = model_service.update_model_instance(user, **payload)

        # Attach roles and permissions to user
        user.roles.set(roles)
        user.permissions.set(permissions)

        return user

    def check_permission_to_act_based_on_role_hierarchy(self, roles):
        roles_hierarchy_list = self.merge_user_roles_below_hierarchy()

        for role in roles:
            if role.name not in roles_hierarchy_list:
                raise PermissionDeniedError(ResponseMessages.no_permission_to_assign_role.format(role))

    def create(self, payload):
        roles = payload.pop("roles", None)

        if not roles:
            raise UserError(ResponseMessages.role_is_required)

        self.check_permission_to_act_based_on_role_hierarchy(roles)

        model_service = ModelService(self.request)

        payload["user_id"] = get_unique_id()

        password = generate_password()
        payload["password"] = make_password(password)

        with transaction.atomic():
            user = model_service.create_model_instance(model=User, payload=payload)

            # Attach roles to user
            user.roles.add(*roles)

        return user

    def merge_user_roles_below_hierarchy(self):
        roles = self.get_user_role_names(self.auth_user)

        role_hierarchy_list = []

        for role in roles:
            roles_below = RoleHierarchy.get(role)
            if roles_below:
                role_hierarchy_list = role_hierarchy_list + roles_below

        # Fetch the new roles from DB that can be created by this user
        role_ids = self.get_user_role_ids(self.auth_user)
        new_roles = (Role.active_available_objects.filter(user_can_be_created_by__icontains=role_ids)
                     .values_list("name", flat=True))

        role_hierarchy_list.extend(new_roles)

        return list(set(role_hierarchy_list))

    def fetch_creatable_users_roles(self):
        role_hierarchy_list = self.merge_user_roles_below_hierarchy()

        role_service = RoleService(self.request)
        roles = role_service.fetch_by_names(role_hierarchy_list)

        return roles

    def fetch_list(self, filter_params, **kwargs):
        keyword = filter_params.get("keyword")
        roles = filter_params.get("roles")

        q = Q()

        if keyword:
            q &= (Q(first_name__icontains=keyword) | Q(last_name__icontains=keyword) |
                  Q(email__icontains=keyword) | Q(phone_number__icontains=keyword) |
                  Q(user_id__icontains=keyword))

        if roles:
            roles = roles.split(",")
            q &= Q(roles__id__in=roles)

        queryset = User.available_objects.filter(q).prefetch_related("roles").order_by("-created_at")

        return queryset

    def get_user_permissions(self, user):
        def __do_get_permissions():
            if user.is_superuser or user.roles.filter(name__exact=RoleEnum.sysadmin).exists():
                permissions = Permission.objects.values("name", "label").order_by("name")
            else:
                permissions = user.permissions.values("name", "label").order_by("name")

            return permissions

        cache_key = self.generate_cache_key("permissions", user.user_id)
        return cache.get_or_set(cache_key, __do_get_permissions)

    def get_user_role_names(self, user):
        def __do_get_role_names():
            roles = user.roles.values_list("name", flat=True).order_by("name")
            return roles

        cache_key = self.generate_cache_key("role_names", user.user_id)
        return cache.get_or_set(cache_key, __do_get_role_names)

    def get_user_role_ids(self, user):
        def __do_get_role_ids():
            roles = user.roles.values_list("id", flat=True)
            return list(roles)

        cache_key = self.generate_cache_key("role_ids", user.user_id)
        perms = cache.get_or_set(cache_key, __do_get_role_ids)

        return perms
