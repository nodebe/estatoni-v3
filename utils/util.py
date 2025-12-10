import logging
import random
import secrets
import time
from datetime import datetime
from math import ceil
from django.shortcuts import render
from django.contrib.auth.models import AnonymousUser
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.timezone import is_aware, make_aware
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from typing import TypeVar
from rest_framework import status
from django.contrib.auth.hashers import make_password
from base.tasks import make_api_request_log, update_api_request_log, report_activity
from media.models import UploadedMedia, UploadToChoices
from utils.constants.messages import ResponseMessages
from utils.decorators import CustomApiPermissionRequired
from utils.errors import UserError, PermissionDeniedError
from utils.uploaders import CloudinaryUploader, AmazonUploader
from utils.encryption_util import AESCipher

T = TypeVar("T")


class AppLogger:
    @staticmethod
    def report(error, error_position=None):
        # TODO: Implement better Logging in here
        logging.error(error)

    @staticmethod
    def print(*message):
        print(message)


class DefaultPagination(PageNumberPagination):
    max_page_size = 20
    page_size = int(settings.DEFAULT_PAGE_SIZE)
    page_query_param = "page"
    page_size_query_param = 'page_size'


class CustomApiResponse:
    response_payload_requires_encryption = False
    response_message_on_success = None

    def __init__(self):
        self.encrypt_response = None

    def response_with_json(self, data, status_code=None):
        if not data:
            data = {}
        elif not isinstance(data, dict):
            data = {"data": data}

        if self.response_message_on_success:
            data["message"] = self.response_message_on_success

        if settings.APP_ENC_ENABLED and self.response_payload_requires_encryption:
            cipher = AESCipher(settings.APP_ENC_KEY, settings.APP_ENC_VEC)
            data = cipher.encrypt_nested(data)

        return Response(data, status=status_code)

    def error_response(self, e):
        from utils.errors import ServerError

        if hasattr(e, "status_code"):
            if hasattr(e, "message"):
                message = e.message
            elif hasattr(e, "detail"):
                message = e.detail
            else:
                message = "Operation Error"
            response_data = {
                "error": message,
                "data": None
            }

            if response_data.get("error"):
                self.response_message_on_success = None

            return self.response_with_json(data=response_data, status_code=e.status_code)
        else:
            raise ServerError(error=e, error_position="CustomApiResponse.error_response")


class CustomApiRequest(CustomApiPermissionRequired, CustomApiResponse, DefaultPagination):
    serializer_class = None
    permission_classes = []
    response_serializer = None
    logging_enabled = settings.API_REQUEST_LOGGING_ENABLED
    response_serializer_requires_many = False
    request_serializer_requires_many = False
    wrap_response_in_data_object = True
    request_payload_requires_decryption = False
    status_code_on_success = status.HTTP_200_OK
    context = None
    extra_context_data = None
    response_is_template_view = False
    context_object_name = None
    template_name = None
    payload = {}
    ref_id = None
    AUTHORIZATION_KEYS = ["X-API-KEY", "HTTP_AUTHORIZATION", "X-Api-Key", "Authorization"]

    def __init__(self, request=None):
        super().__init__()
        self.page_size = int(settings.DEFAULT_PAGE_SIZE)
        self.current_page = 1
        self.request = request

    @property
    def auth_user(self):
        user = self.request.user if self.request and self.request.user else None
        if isinstance(user, AnonymousUser):
            user = None

        return user

    def report_activity(self, activity_type, data, description=None):
        if not description:
            description = str(activity_type) + " records related to " + str(data)

        report_activity.delay(self.auth_user, activity_type, description)

    def digify_number(self, digit, name):
        try:
            return int(digit)
        except Exception as e:
            raise UserError(f"{name} is not a number")

    def check_profile_owner(self, profile):
        """Check if the person performing any activity on the profile is the owner of the profile"""
        if profile.user != self.auth_user:
            raise PermissionDeniedError()

    def check_resource_owner(self, resource, *additional_user_attr):
        user_attrs = list(additional_user_attr)

        user_attrs.append("user")

        pass_checks = []

        for attr in user_attrs:
            if hasattr(resource, attr):
                if getattr(resource, attr) == self.auth_user:
                    return True
                else:
                    pass_checks.append(False)

        if not any(pass_checks):
            raise PermissionDeniedError()

        return False

    def process_request(self, request, target_function, **extra_args):
        try:
            self.check_required_roles_and_permissions()

            self.encrypt_response = self.response_payload_requires_encryption

            if self.request_payload_requires_decryption and settings.APP_ENC_ENABLED:
                encryption_util = AESCipher(settings.APP_ENC_KEY, settings.APP_ENC_VEC)
                request_data = encryption_util.decrypt_body(request.data)
            else:
                request_data = request.data

            if self.logging_enabled:
                self.ref_id = get_unique_id(length=18)
                try:
                    make_api_request_log(
                        request.user.id if request.user else "",
                        request.data, request.get_full_path(), self.ref_id,
                        headers={k: v for k, v in request.headers.items() if k not in self.AUTHORIZATION_KEYS}
                    )
                except Exception as e:
                    AppLogger.report(e, "CustomApiRequest.process_request.self.logging_enable")

            if not self.context:
                self.context = dict()

            self.context['request'] = request

            if self.extra_context_data:
                for key, val in self.extra_context_data.items():
                    self.context[key] = val

            if self.serializer_class and request.method in {"PUT", "POST"}:
                serializer = self.serializer_class(
                    data=request_data or dict(),
                    context=self.context,
                    many=self.request_serializer_requires_many
                )

                serializer.is_valid(raise_exception=True)

                response_raw_data = target_function(serializer.validated_data, **extra_args)

            else:
                if self.payload:
                    response_raw_data = target_function(self.payload, **extra_args)
                else:
                    response_raw_data = target_function(**extra_args)

            return self.__handle_request_response(response_raw_data)

        except Exception as e:
            AppLogger.report(e)

            response_data = {"error": str(e), "message": "Server error"}

            if self.ref_id:
                try:
                    update_api_request_log.delay(self.ref_id, response_status="Error", response_body=response_data)
                except Exception as e:
                    AppLogger.report(e)

            return self.error_response(e)

    def __handle_request_response(self, response_raw_data):
        response_data = response_raw_data

        if isinstance(response_data, str):
            self.response_message_on_success = response_data
            response_data = {}

        # Code for if there's a template needed as the response
        if self.response_is_template_view:
            if self.context_object_name is None:
                self.context_object_name = "data"

            self.context[self.context_object_name] = response_data
            return render(self.request, self.template_name, self.context)

        if self.response_serializer is not None:
            response_data = self.response_serializer(response_data, many=self.response_serializer_requires_many).data

        if self.wrap_response_in_data_object:
            response_data = {"data": response_data}

        if self.ref_id:
            try:
                update_api_request_log.delay(self.ref_id, response_status="Success", response_body=response_data)
            except Exception as e:
                AppLogger.report(e)

        return self.response_with_json(response_data, self.status_code_on_success)

    def generate_cache_key(self, *args, **kwargs):
        model = kwargs.get("model") or None
        list_args = list(args)
        if model:
            try:
                name = model().model_name()
            except Exception:
                try:
                    name = model()._meta.model_name
                except Exception:
                    name = model.model_name()

            list_args.insert(0, name)

        return ":".join(list(slugify(arg) for arg in list_args))

    def get_request_filter_params(self, *additional_params):
        if additional_params is None:
            additional_params = []

        data = {}

        filter_bucket = self.request.query_params
        general_params = ['keyword', 'search', 'filter', 'from_date', 'to_date', 'page', 'page_size', 'ordering',
                          "is_active"] + list(additional_params)

        for param in general_params:
            field_value = filter_bucket.get(param, None)
            if field_value is not None:
                if str(field_value).lower() in ['true', 'false']:
                    data[param] = str(filter_bucket.get(param))
                else:
                    data[param] = filter_bucket.get(param) or ''
            else:
                data[param] = None

        if data['filter'] and not data['keyword']:
            data['keyword'] = data['filter']
        if data['search'] and not data['keyword']:
            data['keyword'] = data['search']

        try:
            data['page'] = int(data.get('page') or 1)

        except Exception as e:
            AppLogger.report(e, "CustomApiRequest.get_request_filter_params")
            data['page'] = 1

        try:
            data['page_size'] = int(data.get('page_size') or 10)
        except Exception as e:
            AppLogger.report(e, "CustomApiRequest.get_request_filter_params")
            data['page_size'] = int(settings.DEFAULT_PAGE_SIZE)

        self.current_page = data.get("page")
        self.page_size = data.get("page_size")

        return data

    def get_paginated_list_response(self, data, count_all):
        return self.__make_pages(self.__get_pagination_data(count_all, data))

    def fetch_list(self, filter_params, **extra_args):
        raise Exception("Not implemented")

    def fetch_paginated_list(self, **extra_args):
        queryset = self.fetch_list(**extra_args)
        page = self.paginate_queryset(queryset, request=self.request)
        data = self.serializer_class(page, many=True, context={"request": self.request}).data

        return self.get_paginated_list_response(data, queryset.count())

    def __get_pagination_data(self, total, data):
        query_params = self.request.query_params

        try:
            self.current_page = int(query_params.get("page", self.current_page)) or self.current_page
            self.page_size = int(query_params.get("page_size", self.page_size)) or self.page_size
        except Exception:
            print("Incorrect page number")

        prev_page_no = int(self.current_page) - 1
        last_page = ceil(total / self.page_size) if self.page_size > 0 else 0
        has_next_page = total > 0 and len(data) > 0 and total > ((self.page_size * prev_page_no) + len(data))
        has_previous_page = (prev_page_no > 0) and (total >= (self.page_size * prev_page_no))

        return prev_page_no, data, total, last_page, has_next_page, has_previous_page

    def __make_pages(self, pagination_data):
        prev_page_no, data, total, last_page, has_next_page, has_prev_page = pagination_data

        prev_page_url = None
        next_page_url = None

        request_url = self.request.path

        q_list = []
        if has_next_page or has_prev_page:
            query_list = self.request.query_params or {}
            for key in query_list:
                if key != "page":
                    q_list.append(f"{key}={query_list[key]}")

        if has_next_page:
            new_list = q_list.copy()
            new_list.append("page=" + str((+self.current_page + 1)))
            q = "&".join(new_list)
            next_page_url = f"{request_url}?{q}"

        if has_prev_page:
            new_list = q_list.copy()
            new_list.append("page=" + str((+self.current_page - 1)))
            q = "&".join(new_list)
            prev_page_url = f"{request_url}?{q}"

        return {
            "page_size": self.page_size,
            "current_page": self.current_page if self.current_page <= last_page else last_page,
            "last_page": last_page,
            "total": total,
            "next_page_url": next_page_url,
            "prev_page_url": prev_page_url,
            "data": data
        }


def get_unique_id(prefix="", suffix="", length=None):
    rand_no = ""
    for i in range(0, 3):
        rand_no += random.choice("0123456789")

    date_to_string = (
            datetime.strftime(timezone.now(), "%Y%m%d%H%M%S") +
            get_random_string(4, allowed_chars='0123456789')
    )
    generated_id = f'{prefix}{date_to_string[3:-2]}'

    if length:
        length = min(20, length)
        generated_id = generated_id[:length]

    generated_id = f"{generated_id}{rand_no}{suffix}"

    return generated_id


def generate_password():
    if settings.DEBUG:
        password = settings.DEFAULT_PASSWORD
    else:
        password = secrets.token_hex(6)

    return password


def generate_otp():
    if settings.DEBUG:
        otp = settings.DEFAULT_OTP
    else:
        otp = str(random.randint(1, 9999)).zfill(4)

    hashed_otp = make_password(otp)

    return otp, hashed_otp


def generate_random_username():
    # List of words to combine for the username
    adjectives = ['fast', 'bright', 'cool', 'brave', 'happy', 'silent', 'lucky']
    nouns = ['lion', 'tiger', 'eagle', 'panda', 'shark', 'falcon', 'wolf']

    # Choose a random adjective and noun
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)

    # Generate a random number
    number = random.randint(1, 999)

    # Combine the parts to form the username
    username = f"{adjective.capitalize()}{noun.capitalize()}{number}"

    return username


def check_time_expired(time_to_check, duration=10) -> bool:
    """
    Returns True if the otp has expired and False if the otp is still valid.
    Returns True if the current time is greater than the time_to_check by the number of duration.
    """

    if not is_aware(time_to_check):
        time_to_check = make_aware(time_to_check)

    created_at = time_to_check
    current_time = timezone.now()

    time_difference = current_time - created_at
    time_difference_minutes = time_difference.total_seconds() / 60

    return time_difference_minutes > duration


class FileUploader(CustomApiRequest):
    DEFAULT_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png"]

    def __init__(self, request):
        super().__init__(request)
        self.request = request
        self.upload_to = UploadToChoices.general

    def upload(self, file, description_payload):
        original_file_name = file.name.lower()
        file_extension = original_file_name.split('.')[-1].lower()
        file_size = self.get_file_size(file)

        media_type = description_payload.get("media_type")

        if not media_type:
            raise UserError(ResponseMessages.media_type_not_found)

        allowed_file_types = [aft.strip(".") for aft in media_type.allowed_file_types]

        if file_extension not in allowed_file_types:
            raise UserError(ResponseMessages.invalid_file_extension)

        if file_size > (media_type.max_file_size_in_kb * 1024):
            raise UserError(ResponseMessages.file_too_large)

        self.upload_to = media_type.upload_to

        file_path = f"{self.upload_to}/{self.generate_file_name(file_extension)}"
        file_content = ContentFile(file.read())

        uploader = CloudinaryUploader(file_path, file_content, file_extension)

        full_url = uploader.upload()

        uploaded_file = UploadedMedia.objects.create(
            media=media_type,
            user=self.auth_user,
            url=full_url,
            name=original_file_name.strip(f".{file_extension}"),
            size=file_size,
            file_type=self.get_content_type_from_extension(file_extension)
        )

        return uploaded_file

    def generate_file_name(self, ext):
        file_name = f"{str(time.time()).replace('.', '')}{str(time.time()).replace('.', '')}"
        return file_name

    def delete(self, file_path):
        uploader = CloudinaryUploader(file_path)
        return uploader.delete()

    def get_file_size(self, file):
        original_position = file.tell()  # Store the original position
        file.seek(0, 2)  # Move the file pointer to the end of the file
        file_size = file.tell()  # Get the current position (file size)
        file.seek(original_position)  # Return to the original position
        return file_size

    def get_content_type_from_extension(self, file_extension):
        extension_mapping = {
            'txt': 'text/plain',
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'mp4': 'video/mp4',
            'mp3': 'audio/mp3',
            'html': 'text/html',
            'css': 'text/css',
        }

        return extension_mapping.get(file_extension, 'application/octet-stream')
