# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Core',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Core module for Military Flight School Management System',
    'description': """
Flight School Core Module
=========================

Foundation module for a Military Flight School Management System 
following EU JAR-FCL (EASA) regulations.

This module provides:
---------------------
* Security groups (User, Instructor, Manager, Admin)
* Base configuration settings
* Module category definition

Other fs_* modules depend on this core module.
    """,
    'author': 'Ghazi Marzouk',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_setup',
    ],
    'data': [
        # Security (must be loaded first)
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        # Views
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
