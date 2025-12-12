from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from account.v1.serializers.profile import IdTypeSerializer
from account.v1.services.profile import IdTypeService
from crm.v1.services.others import OtherService
from utils.util import CustomApiRequest


class ListOptionsAPIView(ListAPIView, CustomApiRequest):
    permission_classes = []

    @extend_schema(tags=["Users"])
    def get(self, request, *args, **kwargs):
        service = OtherService(request)

        filter_params = self.get_request_filter_params("options")

        return self.process_request(request, service.fetch_options, filter_params=filter_params)


@extend_schema(tags=["Options"])
class ListIdTypesAPIView(ListAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        self.response_serializer = IdTypeSerializer
        self.response_serializer_requires_many = True
        service = IdTypeService(request)

        return self.process_request(request, service.fetch_list, filter_params={})
