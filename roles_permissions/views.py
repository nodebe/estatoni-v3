from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated

from utils.constants.roles_permissions import PermissionEnum
from roles_permissions.serializers import CreateEditRoleSerializer, RoleSerializer
from roles_permissions.services import RoleService, PermissionService
from utils.util import CustomApiRequest


class ListPermissionsApiView(ListAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **k):
        filter_params = self.get_request_filter_params()

        service = PermissionService(request)
        return self.process_request(request, service.fetch_list, filter_params=filter_params)


class ListCreateRolesApiView(ListCreateAPIView, CustomApiRequest):
    serializer_class = CreateEditRoleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **k):
        filter_params = self.get_request_filter_params()
        self.permission_required = PermissionEnum.view_roles

        service = RoleService(request)
        return self.process_request(request, service.fetch_list, filter_params=filter_params)

    def post(self, request, *args, **kwargs):
        self.permission_required = PermissionEnum.create_roles
        self.response_serializer = RoleSerializer

        service = RoleService(request)
        return self.process_request(request, service.create)


class UpdateOrDeleteRoleApiView(RetrieveUpdateDestroyAPIView, CustomApiRequest):
    serializer_class = CreateEditRoleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        self.permission_required = PermissionEnum.view_roles
        self.response_serializer = RoleSerializer

        service = RoleService(request)
        role_id = kwargs.get("role_id")
        return self.process_request(request, service.fetch_single, role_id=role_id)

    def put(self, request, *args, **kwargs):
        self.permission_required = PermissionEnum.update_roles
        self.response_serializer = RoleSerializer

        service = RoleService(request)
        role_id = kwargs.get("role_id")
        return self.process_request(request, service.update, role_id=role_id)

    def delete(self, request, *args, **kwargs):
        role_id = kwargs.get("role_id")
        self.permission_required = PermissionEnum.delete_roles

        service = RoleService(request)
        return self.process_request(request, service.delete, role_id=role_id)
