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
    def __init__(self, api_key="", base_url=""):
        self.api_key = api_key
        self.base_url = base_url
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
        base_url = "https://api.prembly.com/verification"
        super().__init__(api_key=api_key, base_url=base_url)

    def get_headers(self):
        return {
            "x-api-key": f"{self.api_key}",
            "app-id": settings.PREMBLY_APP_ID,
        }

    def verify_nin(self, id_number):
        # Test number: 12345678901
        data = {
            "number_nin": id_number
        }

        status, response = self.make_request(
            endpoint="/vnin",
            method=HTTPMethods.post,
            data=data
        )

        response_data = response.json()

        response_code = response_data.get("response_code")

        if response_code == "00":
            verified_data = response_data.get("nin_data")
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

        elif response_code == "01":
            return None, response_data

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

        response_code = response_data.get("response_code")

        if response_code == "00":
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

        elif response_code == "01":
            return None, response_data

        return None, response_data


class PaystackAPIService(APIService):
    def __init__(self):
        self.api_key = settings.PAYSTACK_SECRET_KEY
        super().__init__(api_key=self.api_key)
        self.base_url = "https://api.paystack.co"

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}"
        }

    def verify_transaction(self, reference):
        endpoint = f"/transaction/verify/{reference}"

        response = self.make_request(method=HTTPMethods.get, endpoint=endpoint)

        return response

    def create_transfer_recipient(self, payload):
        endpoint = f"/transferrecipient"

        data = {
            "type": "nuban",
            "name": payload.get("name"),
            "account_number": payload.get("account_number"),
            "bank_code": payload.get("bank_code"),
            "currency": "NGN"
        }

        response = self.make_request(method=HTTPMethods.post, endpoint=endpoint, data=data)

        return response

    def initiate_transfer(self, recipient, amount, reference, **kwargs):
        endpoint = "/transfer"

        amount = float(amount * 100)

        data = {
            "source": "balance",
            "amount": amount,
            "recipient": recipient,
            "reference": reference,
            "reason": kwargs.get("reason", "")
        }

        response = self.make_request(method=HTTPMethods.post, endpoint=endpoint, data=data)

        return response

    def fetch_bank_list(self):
        endpoint = f"/bank"

        response = self.make_request(method=HTTPMethods.get, endpoint=endpoint)

        return response

    def verify_account_number(self, account_number, bank_code):
        endpoint = f"/bank/resolve?account_number={account_number}&bank_code={bank_code}"

        response = self.make_request(method=HTTPMethods.get, endpoint=endpoint)

        return response
