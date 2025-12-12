from abc import abstractmethod, ABC
import requests
import json

from django.conf import settings
from django.db.models import TextChoices
from utils.errors import ServerError
from utils.util import AppLogger


class HTTPMethods(TextChoices):
    get = "GET"
    post = "POST"
    patch = "PATCH"
    put = "PUT"
    options = "OPTIONS"
    delete = "DELETE"


def make_http_request(method, url, headers=None, data=None, json_data=None, params=None):
    methods_dict = {
        HTTPMethods.get: requests.get,
        HTTPMethods.post: requests.post,
        HTTPMethods.put: requests.put,
        HTTPMethods.patch: requests.patch,
        HTTPMethods.options: requests.options,
        HTTPMethods.delete: requests.delete,
    }

    try:
        request_method = methods_dict.get(method.upper())
        if not request_method:
            AppLogger.report(f"Unsupported method: {method}", "make_http_request")
            raise ServerError(error_position="make_http_request")

        if json_data is not None:
            response = request_method(url, headers=headers, json=json_data)
        elif data is not None:
            data = json.dumps(data)
            response = request_method(url, headers=headers, data=data)
        elif params is not None:
            data = json.dumps(data)
            response = request_method(url, headers=headers, params=params)
        else:
            response = request_method(url, headers=headers)

        return response

    except Exception as e:
        raise ServerError(error=e, error_position="make_http_request")


class APIService(ABC):
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.base_url = None
        self.headers = self.get_headers()

    def make_request(self, endpoint, method, data=None, json_data=None, params=None, save_data=True):
        if self.base_url is None:
            return False

        url = self.base_url + f"{endpoint}"

        response = make_http_request(
            url=url, method=method, headers=self.headers, data=data, json_data=json_data, params=params
        )

        if response.ok:
            return True, response
        else:
            return False, response

    @abstractmethod
    def get_headers(self):
        pass


class PremblyAPIService(APIService):
    def __init__(self, api_key=settings.PREMBLY_API_KEY):
        self.base_url = "https://api.prembly.com/verification"
        self.api_key = api_key

    def get_headers(self):
        return {
            "x-api-key": f"Bearer {self.api_key}",
            "app-id": settings.PREMBLY_APP_ID,
        }

    def verify_nin(self, id_number):
        # Test number: 12345678901
        data = {
            "number": id_number
        }

        status, response = self.make_request(
            endpoint="/vnin",
            method=HTTPMethods.post,
            data=data
        )

        response_data = response.json().get("data")

        if status:
            verified_data = response_data.get("data")
            verification_data = {
                "first_name": verified_data.get("firstname", ""),
                "last_name": verified_data.get("surname", ""),
                "dob": verified_data.get("birthdate", ""),
                "phone_number": verified_data.get("telephoneno", ""),
                "email": verified_data.get("email", ""),
                "gender": verified_data.get("gender", ""),
                "address": verified_data.get("residence_address", ""),
                "state_of_origin": verified_data.get("self_origin_state", ""),
                "state_of_residence": verified_data.get("residence_state", ""),
                "city_of_residence": verified_data.get("residence_town", ""),
                "image_string": verified_data.get("photo", "")
            }

            return verification_data, response_data

        return None, response_data

    def verify_bvn(self, id_number):
        # Test number: 54651333604
        data = {
            "number": id_number
        }

        status, response = self.make_request(
            endpoint="/bvn",
            method=HTTPMethods.post,
            data=data
        )

        response_data = response.json()

        if status:
            verified_data = response_data.get("data")
            verification_data = {
                "first_name": verified_data.get("firstName", ""),
                "last_name": verified_data.get("lastName", ""),
                "dob": verified_data.get("dateOfBirth", ""),
                "phone_number": verified_data.get("phoneNumber1") or verified_data.get("phoneNumber2"),
                "email": verified_data.get("email", ""),
                "gender": verified_data.get("gender", ""),
                "address": verified_data.get("residentialAddress", ""),
                "state_of_origin": verified_data.get("stateOfOrigin", ""),
                "state_of_residence": verified_data.get("stateOfResidence", ""),
                "city_of_residence": "",
                "image_string": verified_data.get("base64Image", "")
            }

            return verification_data, response_data

        return None, response_data
