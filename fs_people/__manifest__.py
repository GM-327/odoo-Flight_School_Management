# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'People',
    'version': '19.0.1.0.1',
    'category': 'Aviation/Flight School',
    'summary': 'Personnel management for flight schools',
    'description': """
People
======

Personnel management for Military Flight School Management System.

This module provides:
---------------------
* Military ranks configuration
* Instructors management
* Students management  
* Pilots management
* Administrative staff

All personnel can optionally have Odoo user accounts for system access.
    """,
    'author': 'Ghazi Marzouk',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'fs_core',
        'mail',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/fs_rank_data.xml',
        'data/fs_license_type_data.xml',
        'data/fs_qualification_type_data.xml',
        'data/fs_english_level_data.xml',
        'data/fs_medical_class_data.xml',
        # Views - Configuration
        'views/fs_rank_views.xml',
        'views/fs_license_type_views.xml',
        'views/fs_qualification_type_views.xml',
        'views/fs_english_level_views.xml',
        'views/fs_medical_class_views.xml',
        # Views - Personnel
        'views/fs_people_dashboard_views.xml',
        'views/fs_instructor_views.xml',
        'views/fs_student_views.xml',
        'views/fs_pilot_views.xml',
        'views/fs_person_qualification_views.xml',
        'views/fs_admin_staff_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/fs_instructor_demo.xml',
        'demo/fs_pilot_demo.xml',
        'demo/fs_student_demo.xml',
        'demo/fs_admin_staff_demo.xml',
        'demo/fs_personal_new_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'sequence': 20,
    'images': ['static/description/icon.svg'],
}
