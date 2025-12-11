from .util import NotificationUtil
from .models import MessageTypes
from django.db.models import TextChoices
from core.celery import app


@app.task
def send_signup_otp(email, first_name, otp):
    util = NotificationUtil()
    return util.send_notification(
        recipients=[email],
        message_type=MessageTypes.signup_otp,
        data={
            "first_name": first_name,
            "otp": otp
        }
    )


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
