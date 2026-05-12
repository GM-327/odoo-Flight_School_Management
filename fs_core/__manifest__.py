# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Settings',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Central settings and configuration for Flight School modules',
    'author': 'Ghazi Marzouk, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_setup',
        'auth_signup',
    ],
    'data': [
        # Security (must be loaded first)
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        # Data
        'data/fs_core_data.xml',
        'data/fs_department_data.xml',
        # Views
        'views/res_config_settings_views.xml',
        'views/fs_department_views.xml',
        'views/res_users_views.xml',
        'views/res_groups_privilege_views.xml',
        'views/menu_views.xml',
    ],
    'application': True,
    'sequence': 1,
    'images': ['static/description/icon.svg', 'static/description/icon.png'],
}
