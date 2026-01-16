# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Scheduling',
    'version': '19.0.3.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Flight mission scheduling and timeline management',
    'description': """
Scheduling
==========

This module provides tools for scheduling flight missions for students and instructors.

Key Features:
-------------
* Timeline view for aircraft and instructor schedules.
* Batch scheduling wizard for tomorrow's missions.
* Instructor and aircraft availability management.
* Automatic eligibility checks (expiries, qualifications).
* Configurable buffer times and scheduling sequences.
    """,
    'author': 'Ghazi Marzouk',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'fs_core',
        'fs_training',
        'fs_fleet',
        'fs_people',
        'mail',
        'web_timeline',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/fs_scheduling_data.xml',
        'views/fs_cancellation_reason_views.xml',
        'views/fs_crew_member_views.xml',
        'views/fs_custom_flight_type_views.xml',
        'views/fs_scheduled_flight_views.xml',
        'views/fs_flight_route_views.xml',
        'views/fs_scheduling_inherits_views.xml',
        'views/fs_scheduling_selection_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/fs_selection_views.xml',
        'wizard/fs_scheduling_wizard_line_views.xml',
        'wizard/fs_scheduling_wizard_views.xml',
        'views/fs_scheduling_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_scheduling/static/src/views/fs_timeline_controller.esm.js',
            'fs_scheduling/static/src/views/fs_timeline_controller.xml',
            'fs_scheduling/static/src/views/fs_timeline_renderer.esm.js',
            'fs_scheduling/static/src/views/fs_timeline_renderer.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': True,
    'sequence': 50,
    'images': ['static/description/icon.png'],
}
