from django.db.models import TextChoices


class PermissionEnum(TextChoices):
    # Roles
    view_roles = "View Roles"
    create_roles = "Create Roles"
    update_roles = "Update Roles"
    delete_roles = "Delete Roles"

    # M & E
    create_m_and_e = "Create M/E"
    view_m_and_e = "View M/E"
    update_m_and_e = "Update M/E"
    activate_or_deactivate_m_and_e = "Activate/Deactivate M/E"

    # Dashboard
    view_dashboards = "View Dashboards"

    # Components
    create_components = "Create Components"
    view_components = "View Components"
    update_components = "Update Components"
    delete_components = "Delete Components"
    assign_components_to_states = "Assign Components to States"

    # Sub Components
    create_sub_components = "Create Sub Components"
    view_sub_components = "View Sub Components"
    update_sub_components = "Update Sub Components"
    delete_sub_components = "Delete Sub Components"

    # PDOs
    create_pdo = "Create PDO"
    view_pdo = "View PDO"
    update_pdo = "Update PDO"
    delete_pdo = "Delete PDO"

    # Query
    create_query = "Create Query"
    view_query = "View Query"
    update_query = "Update Query"
    reply_query = "Reply Query"

    # Federal Component Lead (FCL)
    create_fcl = "Create Federal Component Lead"
    view_fcl = "View Federal Component Lead"
    update_fcl = "Update Federal Component Lead"
    activate_or_deactivate_fcl = "Activate/Deactivate Federal Component Lead"

    # State Component Lead (SCL)
    create_scl = "Create State Component Lead"
    view_scl = "View State Component Lead"
    update_scl = "Update State Component Lead"
    activate_or_deactivate_scl = "Activate/Deactivate State Component Lead"

    # Data Collector (DC)
    create_dc = "Create Data Collector"
    view_dc = "View Data Collector"
    update_dc = "Update Data Collector"
    activate_or_deactivate_dc = "Activate/Deactivate Data Collector"

    # Data
    create_data = "Create Data"

    # State
    activate_or_deactivate_state = "Activate/Deactivate State"

    # Users
    view_users = "View Users"
    create_users = "Create Users"
    update_users = "Update Users"
    activate_or_deactivate_users = "Activate/Deactivate Users"


class RoleEnum(TextChoices):
    sysadmin = "System Administrator"
    npc = "National Project Coordinator"
    m_and_e = "Monitoring and Evaluation Personnel"
    fcl = "Federal Component Lead"
    spc = "State Project Coordinator"
    scl = "State Component Lead"
    dc = "Data Collector"


PermissionGroups = {
    "Role Management": [
        PermissionEnum.view_roles,
        PermissionEnum.create_roles,
        PermissionEnum.update_roles,
        PermissionEnum.delete_roles
    ],
    "M and E Management": [
        PermissionEnum.create_m_and_e,
        PermissionEnum.view_m_and_e,
        PermissionEnum.update_m_and_e,
        PermissionEnum.activate_or_deactivate_m_and_e
    ],
    "Dashboard Management": [
        PermissionEnum.view_dashboards,
    ],
    "Component Management": [
        PermissionEnum.create_components,
        PermissionEnum.view_components,
        PermissionEnum.update_components,
        PermissionEnum.delete_components
    ],
    "State Management": [
        PermissionEnum.activate_or_deactivate_state
    ],
    "Sub Component Management": [
        PermissionEnum.create_sub_components,
        PermissionEnum.view_sub_components,
        PermissionEnum.update_sub_components,
        PermissionEnum.delete_sub_components
    ],
    "PDO Management": [
        PermissionEnum.create_pdo,
        PermissionEnum.view_pdo,
        PermissionEnum.update_pdo,
        PermissionEnum.delete_pdo
    ],
    "Query Management": [
        PermissionEnum.create_query,
        PermissionEnum.view_query,
        PermissionEnum.update_query,
        PermissionEnum.reply_query
    ],
    "FCL Management": [
        PermissionEnum.create_fcl,
        PermissionEnum.view_fcl,
        PermissionEnum.update_fcl,
        PermissionEnum.activate_or_deactivate_fcl
    ],
    "SCL Management": [
        PermissionEnum.create_scl,
        PermissionEnum.view_scl,
        PermissionEnum.update_scl,
        PermissionEnum.activate_or_deactivate_scl
    ],
    "DC Management": [
        PermissionEnum.create_dc,
        PermissionEnum.view_dc,
        PermissionEnum.update_dc,
        PermissionEnum.activate_or_deactivate_dc
    ],
    "Data Management": [
        PermissionEnum.create_data
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
        PermissionGroups.get("M and E Management"),
        PermissionGroups.get("Dashboard Management"),
        PermissionGroups.get("Component Management"),
        PermissionGroups.get("State Management"),
        PermissionGroups.get("Sub Component Management"),
        PermissionGroups.get("PDO Management"),
        PermissionGroups.get("Query Management"),
        PermissionGroups.get("FCL Management"),
        PermissionGroups.get("SCL Management"),
        PermissionGroups.get("DC Management"),
        PermissionGroups.get("Data Management"),
        PermissionGroups.get("User Management"),
    ],
    RoleEnum.npc: [
        PermissionGroups.get("Roles Management"),
        PermissionGroups.get("M and E Management"),
        PermissionGroups.get("Dashboard Management"),
        PermissionGroups.get("Component Management"),
        PermissionGroups.get("State Management"),
        PermissionGroups.get("Query Management"),
        PermissionGroups.get("User Management"),
        PermissionGroups.get("User Management"),
    ],
    RoleEnum.m_and_e: [
        PermissionGroups.get("Roles Management"),
        PermissionGroups.get("Dashboard Management"),
        PermissionGroups.get("Component Management"),
        PermissionGroups.get("Sub Component Management"),
        PermissionGroups.get("State Management"),
        PermissionGroups.get("PDO Management"),
        PermissionGroups.get("Query Management"),
        PermissionGroups.get("User Management"),
    ],
    RoleEnum.fcl: [
        PermissionGroups.get("Dashboard Management"),
        PermissionGroups.get("User Management"),
        PermissionEnum.create_query
    ],
    RoleEnum.spc: [
        PermissionGroups.get("SCL Management"),
        PermissionGroups.get("Dashboard Management"),
        PermissionGroups.get("DC Management"),
        PermissionGroups.get("User Management"),
        PermissionEnum.assign_components_to_states,
        PermissionEnum.reply_query,
        PermissionEnum.view_query
    ],
    RoleEnum.scl: [
        PermissionGroups.get("Dashboard Management"),
    ],
    RoleEnum.dc: [
        PermissionGroups.get("Data Management"),
    ]
}

# Hierarchy
DC_ABOVE = []
SCL_ABOVE = [RoleEnum.dc]
SPC_ABOVE = SCL_ABOVE + [RoleEnum.scl]
FCL_ABOVE = SPC_ABOVE + [RoleEnum.spc]
M_AND_E_ABOVE = FCL_ABOVE + [RoleEnum.fcl]
NPC_ABOVE = M_AND_E_ABOVE + [RoleEnum.m_and_e]
SYSADMIN_ABOVE = NPC_ABOVE + [RoleEnum.npc]

RoleHierarchy = {
    RoleEnum.sysadmin: SYSADMIN_ABOVE,
    RoleEnum.npc: NPC_ABOVE,
    RoleEnum.m_and_e: M_AND_E_ABOVE,
    RoleEnum.fcl: FCL_ABOVE,
    RoleEnum.spc: SCL_ABOVE,
    RoleEnum.scl: SCL_ABOVE,
    RoleEnum.dc: DC_ABOVE
}