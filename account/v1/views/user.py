from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated

from account.v1.serializers.profile import SimpleProfileSerializer, ProfileSerializer
from roles_permissions.serializers import VerySimpleRoleSerializer
from account.v1.serializers.user import UserSerializer, UpdateUserSerializer
from account.v1.services.user import UserService, AccountService
from api.serializers.others import ActivateDeactivateSerializer
from utils.constants.messages import ResponseMessages
from utils.constants.roles_permissions import PermissionEnum
from utils.util import CustomApiRequest


class ListCreateUsersAPIView(ListAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        self.permission_required = [PermissionEnum.view_users]
        filter_params = self.get_request_filter_params("roles")

        service = UserService(request)

        return self.process_request(request, service.fetch_paginated_list, filter_params=filter_params)

    @extend_schema(tags=["Users"])
    def post(self, request, *args, **kwargs):
        self.serializer_class = UserSerializer
        self.response_serializer = SimpleProfileSerializer
        self.response_message_on_success = ResponseMessages.user_created_successfully
        self.permission_required = [PermissionEnum.create_users]

        service = UserService(request)

        return self.process_request(request, service.create)


class RetrieveUpdateUserAPIView(RetrieveUpdateAPIView, CustomApiRequest):
    response_serializer = ProfileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Users"])
    def put(self, request, *args, **kwargs):
        self.serializer_class = UpdateUserSerializer
        self.response_message_on_success = ResponseMessages.user_updated_successfully
        self.permission_required = [PermissionEnum.update_users]

        user_id = kwargs.get("user_id")

        service = UserService(request)

        return self.process_request(request, service.update, user_id=user_id)

    @extend_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        self.permission_required = [PermissionEnum.view_users]

        user_id = kwargs.get("user_id")
        service = AccountService(request)

        return self.process_request(request, service.fetch_user_by_user_id, user_id=user_id)


class ActivateDeactivateUserAPIView(UpdateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Users"])
    def put(self, request, *args, **kwargs):
        self.serializer_class = ActivateDeactivateSerializer
        self.response_serializer = ProfileSerializer
        self.permission_required = [PermissionEnum.activate_or_deactivate_users]

        status = request.data.get("status", True)

        verb = "activated" if status else "deactivated"

        self.response_message_on_success = ResponseMessages.user_acted_on_successfully.format(verb)

        user_id = kwargs.get("user_id")
        service = UserService(request)

        return self.process_request(request, service.active_or_deactivate, user_id=user_id)


class ListCreatableUsersRoles(ListAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        self.response_serializer = VerySimpleRoleSerializer
        self.response_serializer_requires_many = True
        self.permission_required = PermissionEnum.create_users

        service = UserService(request)

        return self.process_request(request, service.fetch_creatable_users_roles)
