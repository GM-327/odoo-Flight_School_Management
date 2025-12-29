# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Flight School Documents',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Document management with versioning and expiry tracking',
    'description': """
Flight School Documents
=======================

Document management for Military Flight School Management System.

This module provides:
---------------------
* Document types configuration (flexible, user-defined)
* Document management with file uploads (images, PDFs)
* Version control for documents
* Expiry tracking with status indicators
* Links to students, instructors, pilots, and training classes
* Sync document expiry to related model fields
    """,
    'author': 'Ghazi Marzouk',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'web',
        'fs_core',
        'fs_people',
        'fs_training',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/fs_document_entity_type_data.xml',
        'data/fs_document_type_data.xml',
        # Wizards
        'wizard/fs_document_upload_wizard_views.xml',
        # Views
        'views/fs_documents_dashboard_views.xml',
        'views/fs_document_type_views.xml',
        'views/fs_document_views.xml',
        'views/fs_student_views.xml',
        'views/fs_instructor_views.xml',
        'views/fs_pilot_views.xml',
        'views/fs_training_class_views.xml',
        'views/fs_class_type_views.xml',
        'views/fs_admin_task_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fs_documents/static/src/css/document_view.css',
            'fs_documents/static/src/js/document_resizer.js',
        ],
    },
    'demo': [
        'demo/fs_documents_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'sequence': 40,
    'images': ['static/description/icon.svg'],
}
