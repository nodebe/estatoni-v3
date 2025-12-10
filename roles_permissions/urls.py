from django.urls import path

from roles_permissions.views import ListPermissionsApiView, ListCreateRolesApiView, \
    UpdateOrDeleteRoleApiView

urlpatterns = [
    path('permissions', ListPermissionsApiView.as_view(), name="list_all_permissions"),
    path('', ListCreateRolesApiView.as_view(), name="list_all_roles"),
    path('<int:role_id>', UpdateOrDeleteRoleApiView.as_view(), name="get_update_delete_role")
]