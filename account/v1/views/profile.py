from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from account.v1.serializers.profile import ProfileSerializer, PasswordResetSerializer
from account.v1.services.user import AccountService
from utils.constants.messages import ResponseMessages
from utils.util import CustomApiRequest


class ProfileAPIView(RetrieveUpdateDestroyAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]
    response_serializer = ProfileSerializer

    @extend_schema(tags=["Profile"])
    def put(self, request, *args, **kwargs):
        self.serializer_class = ProfileSerializer
        self.response_message_on_success = ResponseMessages.update_successful

        service = AccountService(request)

        return self.process_request(request, service.update)

    @extend_schema(tags=["Profile"])
    def get(self, request, *args, **kwargs):
        service = AccountService(request)

        return self.process_request(request, service.fetch)


class ProfileUserDataAPIView(RetrieveAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=["Profile"])
    def get(self, request, *args, **kwargs):
        service = AccountService(request)

        return self.process_request(request, service.fetch_user_data)


class PasswordResetAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordResetSerializer

    @extend_schema(tags=["Profile"])
    def post(self, request, *args, **kwargs):
        service = AccountService(request)
        return self.process_request(request, service.reset_password)
