# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Flights',
    'version': '19.0.1.1.0',
    'category': 'Aviation/Flight School',
    'summary': 'Daily flight operations monitoring and execution logging',
    'description': """
Flights - Daily Operations (Odoo 19)
====================================

Monitor and manage flight operations for the current day.

Key Features:
* Full-screen operations board for TV display
* Real-time flight status tracking with live updates
* ATD/ATA inline entry with automatic hour distribution
* Color-coded status with cancellation reason display
* Available aircraft footer display
    """,
    'author': 'Ghazi Marzouk',
    'license': 'LGPL-3',
    'depends': [
        'fs_scheduling',
        'fs_fleet',
        'fs_training',
        'fs_people',
        'mail',
        'bus',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/fs_flight_cancel_wizard_views.xml',
        'wizards/fs_add_flight_wizard_views.xml',
        'wizards/fs_flight_delete_wizard_views.xml',
        'wizards/fs_import_schedule_wizard_views.xml',
        'wizards/fs_recalculate_hours_wizard_views.xml',
        'views/fs_flight_views.xml',
        'views/fs_daily_operations_views.xml',
        'views/fs_simulator_operations_views.xml',
        'views/fs_scheduled_flight_views.xml',
        'views/fs_initial_experience_views.xml',
        'views/fs_flights_menus.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_flights/static/src/css/operations_board.css',
            'fs_flights/static/src/js/operations_board.js',
            'fs_flights/static/src/js/fullscreen_toggle_field.js',
            'fs_flights/static/src/xml/fullscreen_toggle_field.xml',
            'fs_flights/static/src/js/soft_refresh_field.js',
            'fs_flights/static/src/xml/soft_refresh_field.xml',
            'fs_flights/static/src/js/carousel_control.js',
            'fs_flights/static/src/xml/carousel_control.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 60,
    'images': ['static/description/icon.svg', 'static/description/icon.png'],
}
