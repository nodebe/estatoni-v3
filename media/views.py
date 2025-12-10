from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from .serializers import MediaTypeSerializer, UploadMediaSerializer, UploadMediaResponseSerializer
from .services import MediaService
from utils.util import CustomApiRequest


class MediaTypeAPIView(ListAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        self.response_serializer = MediaTypeSerializer
        self.response_serializer_requires_many = True

        service = MediaService(request)
        return self.process_request(request, target_function=service.fetch_media_types)


class UploadMediaAPIView(CreateAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]
    serializer_class = UploadMediaSerializer

    def post(self, request, *args, **kwargs):
        self.logging_enabled = False
        self.response_serializer = UploadMediaResponseSerializer
        self.response_serializer_requires_many = True
        service = MediaService(request)

        return self.process_request(request, target_function=service.upload_media)


class DeleteMediaAPIView(DestroyAPIView, CustomApiRequest):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        service = MediaService(request)

        media_id = kwargs.get('media_id')

        return self.process_request(request, target_function=service.delete_media, media_id=media_id)
