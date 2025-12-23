# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Training',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Training classes, enrollments, and flight missions',
    'description': """
Flight School Training
======================

Training management for Military Flight School Management System.

This module provides:
---------------------
* Training class types with configurable requirements
* Flight disciplines (MAN, NAV, IFR, VSV) and types (Solo, Dual)
* Training classes with student enrollments
* Flight missions syllabus
* Student progress tracking
* Administrative task checklists
    """,
    'author': 'Ghazi Marzouk',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'fs_core',
        'fs_people',
        'fs_fleet',
        'mail',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/fs_flight_discipline_data.xml',
        'data/fs_flight_type_data.xml',
        'data/fs_flight_activity_data.xml',
        'data/fs_class_type_data.xml',
        'data/fs_class_type_hours_data.xml',
        # Views - Configuration
        'views/fs_flight_discipline_views.xml',
        'views/fs_flight_type_views.xml',
        'views/fs_flight_activity_views.xml',
        'views/fs_class_requirement_views.xml',
        'views/fs_class_type_views.xml',
        'views/fs_flight_mission_views.xml',
        'views/fs_admin_task_views.xml',
        # Views - Training
        'views/fs_training_class_views.xml',
        'views/fs_student_enrollment_views.xml',
        'views/fs_student_views.xml',
        'views/fs_instructor_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_training/static/src/js/progress_bar_patch.js',
        ],
    },
    'demo': [
        'demo/fs_training_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'sequence': 30,
}
