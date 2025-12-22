# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Settings',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Central settings and configuration for Flight School modules',
    'description': """
Flight School Settings
======================

Central configuration module for the Military Flight School Management System 
following EU JAR-FCL (EASA) regulations.

This module provides:
---------------------
* Security groups (User, Instructor, Manager, Admin)
* Central configuration settings
* Module category definition

Other Flight School modules depend on this for security and settings.
Available modules: Fleet, People, Training, etc.
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
        # Data
        'data/fs_core_data.xml',
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
