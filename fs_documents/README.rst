=======================
Flight School Documents
=======================

Purpose
=======

``fs_documents`` centralizes document management for people, training classes,
class types, and administrative tasks. It supports document categories, entity
links, file uploads, version history, previews, expiry tracking, and dashboard
shortcuts.

Main functionality
==================

* Defines document entity types and document types.
* Stores one ``fs.document`` per document type and related entity.
* Stores file history in ``fs.document.version`` and marks one version as
  current.
* Computes expiry status and synchronizes expiry dates back to related records
  such as personnel compliance fields.
* Provides a multi-step upload wizard for creating or updating documents.
* Extends student, instructor, pilot, class, class type, and admin task forms
  with document counters and shortcut actions.

Dependencies
============

* ``web`` for preview and backend asset integration.
* ``fs_core`` for shared settings, menus, and security.
* ``fs_people`` for student, instructor, and pilot entities.
* ``fs_training`` for training classes, class types, and administrative tasks.

Related Flight School modules
=============================

``fs_people`` and ``fs_training`` provide the business records whose documents
are managed by this module. Expiry synchronization updates those related records
when document versions change.

Public Python API
=================

``fs.document``
    Main document record. Public methods include ``write()``,
    ``sync_expiry_to_related()``, ``action_view_versions()``,
    ``action_add_version()``, ``get_or_create_for_entity()``,
    ``action_open_upload_wizard()``, and ``action_open_preview()``.

``fs.document.version``
    Version ledger for uploaded files. Public methods include ``create()``,
    ``write()``, ``action_set_as_current()``, and ``action_open_preview()``.

``fs.document.upload.wizard``
    Multi-step upload workflow. Public methods include ``default_get()``,
    ``action_next()``, ``action_previous()``, and ``action_submit()``.

Entity extensions
    Student, instructor, pilot, class, class type, and admin-task extensions
    expose ``action_view_documents()``, ``action_upload_document()``, and
    shortcut preview actions where relevant.

All public classes and methods include Google-style source docstrings with
parameters, return values, and raised exceptions.

Usage examples
==============

Create or retrieve a document for a student::

    document_type = env['fs.document.type'].search([('code', '=', 'MEDICAL')], limit=1)
    document = env['fs.document'].get_or_create_for_entity(
        document_type=document_type,
        entity_model='fs.student',
        entity_id=student.id,
    )

Open the upload wizard for an existing document::

    action = document.action_open_upload_wizard()

Add a new version programmatically::

    version = env['fs.document.version'].create({
        'document_id': document.id,
        'file': encoded_file,
        'filename': 'medical.pdf',
        'issue_date': fields.Date.today(),
        'expiry_date': fields.Date.add(fields.Date.today(), years=1),
    })
    version.action_set_as_current()

Common workflow
---------------

1. Configure entity types and document types.
2. Open a person, class, class type, or admin task and use Upload Document.
3. Select the document type and upload the file.
4. Enter reference, issue, and expiry details.
5. Monitor expiring and expired documents from the dashboard.

Exceptions and validation
=========================

* ``ValidationError`` is raised when a document is linked to more than one
  entity or when uniqueness rules are violated.
* ``UserError`` is raised by the upload wizard when required wizard steps or
  files are missing.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
