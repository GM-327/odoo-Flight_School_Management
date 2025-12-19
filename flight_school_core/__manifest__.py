# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Core',
    'version': '0.1',
    'category': 'Aviation/Flight School',
    'summary': 'Core module for Military Flight School Management System',
    'description': """
Flight School Core Module
=========================

This is the core/foundation module for a Military Flight School Management System 
following EU JAR-FCL (EASA) regulations.

Key Features:
-------------
* Training Class Type Management (PPL, CPL, IR, etc.)
* Training Class Management (student batches/cohorts)
* Student Management with military ranks and callsigns
* Instructor Management (military and civilian)
* Aircraft Fleet Management
* Rank Hierarchy Configuration
* Person Type Configuration
* Full security with role-based access control

This module provides the foundational data models that other flight school 
modules will depend on.
    """,
    'author': 'Ghazi Marzouk',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'base_setup',
    ],
    'data': [
        # Security (must be loaded first)
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        # Data (pre-populated records)
        'data/class_type_data.xml',

        'data/rank_data.xml',
        # Views
        'views/action_views.xml',
        'views/class_type_views.xml',

        'views/rank_views.xml',
        'views/pilot_views.xml',
        'views/student_views.xml',
        'views/instructor_views.xml',
        'views/instructor_qualification_views.xml',
        'views/aircraft_category_views.xml',
        'views/aircraft_type_views.xml',
        'views/training_class_views.xml',
        'views/res_config_settings_views.xml',
        'views/aircraft_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
