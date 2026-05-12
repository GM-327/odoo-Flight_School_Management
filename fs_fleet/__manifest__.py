# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Fleet',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Aircraft fleet management for flight schools',
    'author': 'Ghazi Marzouk, Odoo Community Association (OCA)',
    'license': 'LGPL-3',
    'depends': [
        'fs_core',
        'mail',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/aircraft_category_data.xml',
        'data/aircraft_type_data.xml',
        'data/aircraft_data.xml',
        # Views
        'views/fs_fleet_dashboard_views.xml',
        'views/aircraft_category_views.xml',
        'views/aircraft_type_views.xml',
        'views/aircraft_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    # 'demo': [
    #     'demo/aircraft_demo.xml',
    # ],
    'application': True,
    'auto_install': True,
    'sequence': 10,
    'images': ['static/description/icon.svg', 'static/description/icon.png'],
}
