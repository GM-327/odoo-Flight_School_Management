# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Access Control',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Dynamic role-level and department access control for Flight School modules',
    'author': 'Ghazi Marzouk, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'fs_core',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Base data loaded before views reference default levels and roles.
        'data/fs_access_control_data.xml',
        # Views and menus
        'views/fs_access_control_views.xml',
        'views/res_users_views.xml',
        'views/menu_views.xml',
        # Policies loaded after menus/actions exist.
        'data/fs_access_control_policy_data.xml',
    ],
    'application': False,
    'sequence': 5,
}
