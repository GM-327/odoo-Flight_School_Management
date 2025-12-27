# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Fleet',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Aircraft fleet management for flight schools',
    'description': """
Flight School Fleet
===================

Aircraft fleet management for Military Flight School Management System.

This module provides:
---------------------
* Aircraft categories (single-engine, multi-engine, complex, simulator)
* Aircraft types (Cessna 172, Diamond DA40, etc.)
* Individual aircraft tracking with registration
* Status management (available, maintenance, grounded)
* Hobbs/airframe hours tracking
* Maintenance scheduling awareness

Depends on Flight School Core for security groups.
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
        'data/aircraft_category_data.xml',
        'data/aircraft_type_data.xml',
        # Views
        'views/aircraft_category_views.xml',
        'views/aircraft_type_views.xml',
        'views/aircraft_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/aircraft_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'sequence': 10,
    'images': ['static/description/icon.svg'],
}
