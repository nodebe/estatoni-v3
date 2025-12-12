from django.db.models import TextChoices


class ActivityType(TextChoices):
    delete = "delete"
    update = "update"
    create = "create"
    approve = "approve"
    reject = "reject"
    revert = "revert"
    activate = "activate"
    verify = "verify"
    deactivate = "deactivate"
    application = "application"


class ActivityTypeVerb(TextChoices):
    delete = "deleted"
    update = "updated"
    create = "created"
    approve = "approved"
    reject = "rejected"
    revert = "reverted"
    activate = "activated"
    verify = "verified"
    deactivate = "deactivated"
    application = "applied"


class CeleryTaskQueue(TextChoices):
    email = "email"
    logging = "logging"
    default = "default"
