from abc import abstractmethod, ABC
import requests
import json
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
            return True, response.json()
        else:
            return False, response.json()

    @abstractmethod
    def get_headers(self):
        pass
