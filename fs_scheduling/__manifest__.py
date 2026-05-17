# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Scheduling',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Flight mission scheduling and timeline management',
    'author': 'Ghazi Marzouk, Odoo Community Association (OCA)',
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
        'data/fs_pilot_function_data.xml',
        'data/fs_scheduling_data.xml',
        'data/fs_flight_route_data.xml',
        'views/fs_cancellation_reason_views.xml',
        'views/fs_crew_member_views.xml',
        'views/fs_custom_flight_type_views.xml',
        'views/fs_pilot_function_views.xml',
        'views/fs_scheduled_flight_views.xml',
        'views/fs_flight_route_views.xml',
        'views/fs_scheduling_inherits_views.xml',
        'views/fs_scheduling_selection_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/fs_selection_views.xml',
        'wizard/fs_scheduling_wizard_line_views.xml',
        'wizard/fs_scheduling_wizard_bulk_action_views.xml',
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
    'application': True,
    'auto_install': True,
    'sequence': 50,
    'images': ['static/description/icon.svg', 'static/description/icon.png'],
}
