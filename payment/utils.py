import hashlib
import hmac
from rest_framework.permissions import BasePermission
from django.conf import settings


class IsPaystackAuthenticated(BasePermission):
    secret_key = settings.PAYSTACK_SECRET_KEY

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True

        body_str = request.body
        signature = hmac.new(
            key=self.secret_key.encode(),
            msg=body_str,
            digestmod=hashlib.sha512
        ).hexdigest()

        return signature == request.headers.get('x-paystack-signature')
