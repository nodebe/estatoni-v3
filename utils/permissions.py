from rest_framework.permissions import BasePermission

from utils.constants.messages import ErrorMessages

#
# class IsXOnlyView(BasePermission):
#     """
#     Allows access only to clients.
#     """
#
#     message = {
#         "error": ErrorMessages.permission_denied
#     }
#
#     def has_permission(self, request, view):
#
#         return bool(True)
