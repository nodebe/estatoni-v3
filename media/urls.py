from django.urls import path

from .views import MediaTypeAPIView, UploadMediaAPIView

urlpatterns = [
    path("types", MediaTypeAPIView.as_view(), name='media_type'),
    path("upload", UploadMediaAPIView.as_view(), name='upload_media'),
]
