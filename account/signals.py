# users/signals.py
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from roles_permissions.models import Role
from .models import User


@receiver(m2m_changed, sender=User.roles.through)
def assign_role_permissions(sender, instance: User, action, reverse, model, pk_set, **kwargs):
    """
    When roles are added to a user, automatically sync permissions.
    """
    if action == "post_add":
        for role_id in pk_set:
            role = Role.objects.get(id=role_id)
            instance.permissions.add(*role.permissions.all())

    # OPTIONAL: If roles are removed, also remove role permissions
    if action == "post_remove":
        for role_id in pk_set:
            role = Role.objects.get(id=role_id)
            instance.permissions.remove(*role.permissions.all())
