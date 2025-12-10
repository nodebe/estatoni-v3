from .util import NotificationUtil
from .models import MessageTypes
from django.db.models import TextChoices
from core.celery import app


class SendToOptions(TextChoices):
    email = "Email"


class DynamicNotificationType(TextChoices):
    transaction_update = "Transaction Update"
    platform_update = "Platform Update"


@app.task
def send_password_reset(email, first_name, otp):
    util = NotificationUtil()
    return util.send_notification(
        recipients=[email],
        message_type=MessageTypes.password_reset,
        data={
            "first_name": first_name,
            "otp": otp
        }
    )


@app.task
def send_dynamic_notification(recipients, first_name, message):
    util = NotificationUtil()

    util.send_notification(
        recipients=recipients,
        message_type=MessageTypes.dynamic_notification,
        data={
            "first_name": first_name,
            "message": message
        }
    )
