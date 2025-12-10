from django.db.models import TextChoices


class PermissionEnum(TextChoices):
    # Roles
    view_roles = "view_roles", "View Roles"
    create_roles = "create_roles", "Create Roles"
    update_roles = "update_roles", "Update Roles"
    delete_roles = "delete_roles", "Delete Roles"

    # Users
    view_users = "view_users", "View Users"
    create_users = "create_users", "Create Users"
    update_users = "update_users", "Update Users"
    activate_or_deactivate_users = "activate_deactivate_users", "Activate/Deactivate Users"


class RoleEnum(TextChoices):
    sysadmin = "sys_admin", "System Administrator"
    admin = "admin", "Administrator"
    moderator = "moderator", "Moderator"
    accountant = "accountant", "Accountant"
    user = "user", "User"
    estate_developer = "estate_developer", "Estate Developer"


PermissionGroups = {
    "Role Management": [
        PermissionEnum.view_roles,
        PermissionEnum.create_roles,
        PermissionEnum.update_roles,
        PermissionEnum.delete_roles
    ],
    "User Management": [
        PermissionEnum.create_users,
        PermissionEnum.view_users,
        PermissionEnum.update_users,
        PermissionEnum.activate_or_deactivate_users
    ],
}

DefaultRolesPermissions = {
    RoleEnum.sysadmin: [
        PermissionGroups.get("Roles Management"),
        PermissionGroups.get("User Management"),
    ],
    RoleEnum.admin: [],
    RoleEnum.moderator: [],
    RoleEnum.accountant: [],
    RoleEnum.user: [],
    RoleEnum.estate_developer: []
}


USER_ABOVE = []
ESTATE_DEVELOPER_ABOVE = []
ACCOUNTANT_ABOVE = []
MODERATOR_ABOVE = []
ADMIN_ABOVE = [RoleEnum.moderator, RoleEnum.accountant, RoleEnum.user, RoleEnum.estate_developer]
SYSADMIN_ABOVE = [RoleEnum.admin] + ADMIN_ABOVE

RoleHierarchy = {
    RoleEnum.sysadmin: SYSADMIN_ABOVE,
    RoleEnum.admin: ADMIN_ABOVE,
    RoleEnum.moderator: MODERATOR_ABOVE,
    RoleEnum.accountant: ACCOUNTANT_ABOVE,
    RoleEnum.user: USER_ABOVE,
    RoleEnum.estate_developer: ESTATE_DEVELOPER_ABOVE
}

