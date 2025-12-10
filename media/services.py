from django.core.cache import cache
from .models import Media, UploadedMedia
from utils.errors import UserError, ServerError, NotFoundError
from utils.util import CustomApiRequest, FileUploader
from utils.constants.messages import ResponseMessages


class MediaService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def upload_media(self, payload):
        files = self.request.FILES.getlist("file")

        if not files:
            raise UserError(ResponseMessages.invalid_file)

        file_uploader = FileUploader(request=self.request)

        uploaded_file_list = []

        for file in files:
            uploaded_file = file_uploader.upload(file=file, description_payload=payload)
            uploaded_file_list.append(uploaded_file)

        return uploaded_file_list

    def delete_media(self, media_id):
        uploaded_media = UploadedMedia.objects.filter(id=media_id).first()

        if uploaded_media:
            self.check_resource_owner(uploaded_media)

            # Delete from Cloud storage
            file_uploader = FileUploader(request=self.request)
            file_uploader.delete(file_path=uploaded_media.url)

            uploaded_media.delete()

            return ResponseMessages.media_deleted_successfully

        raise NotFoundError(ResponseMessages.media_not_found)

    def find_media_type_by_id(self, media_type_id):
        if not str(media_type_id).isdigit():
            raise UserError(ResponseMessages.media_type_not_found)

        def __do_fetch_single():
            try:
                return Media.objects.get(pk=media_type_id)

            except Media.DoesNotExist:
                raise UserError(ResponseMessages.media_type_not_found)

            except Exception as e:
                raise ServerError(error=e, error_position="MediaService.find_media_type_by_id")

        cache_key = self.generate_cache_key("media_type", media_type_id)
        return cache.get_or_set(cache_key, __do_fetch_single)

    def find_uploaded_media_by_id(self, media_id, many=False):
        if not many and not str(media_id).isdigit():
            raise UserError(ResponseMessages.media_not_found)

        def __do_fetch_single():
            try:
                if many:
                    return UploadedMedia.objects.filter(pk__in=media_id).all()

                return UploadedMedia.objects.get(pk=media_id)

            except UploadedMedia.DoesNotExist:
                raise UserError(ResponseMessages.media_not_found)

            except Exception as e:
                raise ServerError(error=e, error_position="MediaService.find_uploaded_media_by_id")

        cache_key = self.generate_cache_key("uploaded_media", media_id)
        return cache.get_or_set(cache_key, __do_fetch_single)

    def fetch_media_types(self):
        def __do_fetch():
            try:
                return Media.objects.all()
            except Exception as e:
                raise ServerError(error=e, error_position="MediaService.fetch_media_types")

        cache_key = self.generate_cache_key("media_types")
        return cache.get_or_set(cache_key, __do_fetch)
