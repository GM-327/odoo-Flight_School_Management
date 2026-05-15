====================
Flight School People
====================

Purpose
=======

``fs_people`` manages personnel records for a flight school. It covers the base
person model, students, instructors, pilots, administrative staff, ranks,
licenses, medical classes, qualifications, English levels, and instructor
availability.

Main functionality
==================

* Provides ``fs.person`` as the shared profile model for personnel data.
* Extends the base profile into ``fs.student``, ``fs.instructor``, and
  ``fs.pilot`` with role-specific fields and computed compliance statuses.
* Stores reusable configuration in rank, license type, qualification type,
  medical class, and English level models.
* Tracks qualifications and expiry status with ``fs.person.qualification``.
* Creates or opens linked Odoo users for personnel who need system access.
* Provides a People dashboard with student, instructor, and pilot KPIs.

Dependencies
============

* ``fs_core`` for shared settings, menus, and security.
* ``mail`` for chatter and activity tracking on personnel records.

Related Flight School modules
=============================

* ``fs_training`` enrolls students and assigns instructors.
* ``fs_scheduling`` exposes students, instructors, and pilots through the
  unified ``fs.crew.member`` SQL view.
* ``fs_documents`` attaches compliance documents and synchronizes expiry dates.
* ``fs_flights`` updates flight, instruction, solo, and simulator hour totals.

Public Python API
=================

``fs.person``
    Base profile. Public methods include ``action_create_user()``,
    ``action_view_user()``, and helper ``_suggest_login()`` for account login
    generation.

``fs.student``
    Student-specific compliance fields for licenses, insurance, security
    clearance, and medical status. Computed methods document their updated
    fields in source docstrings.

``fs.instructor``
    Instructor profile with qualification badges, rolling-hour computations,
    English status, and ``action_view_qualifications()``.

``fs.pilot``
    Pilot profile with qualification badges, English status, security clearance,
    insurance status, and ``action_view_qualifications()``.

``fs.admin.staff``
    Administrative staff records with linked-user actions.

``fs.people.dashboard``
    Dashboard model with public ``action_view_*`` methods returning Odoo action
    dictionaries for filtered personnel views.

All public classes and methods under ``models/`` and ``wizard/`` contain
Google-style docstrings with parameter, return, and exception sections.

Usage examples
==============

Create a student profile::

    rank = env['fs.rank'].search([('code', '=', 'LT')], limit=1)
    student = env['fs.student'].create({
        'name': 'Student Pilot',
        'callsign': 'SP01',
        'rank_id': rank.id,
        'email': 'student@example.invalid',
    })

Create a system user for a person::

    person = env['fs.person'].search([('email', '!=', False)], limit=1)
    action = person.action_create_user()

Open expired instructor qualifications from the dashboard::

    dashboard = env['fs.people.dashboard'].create({})
    action = dashboard.action_view_instructors_expired()

Common workflow
---------------

1. Configure ranks, license types, qualification types, English levels, and
   medical classes.
2. Create student, instructor, pilot, and administrative staff profiles.
3. Attach qualifications and expiry dates.
4. Link Odoo users for staff who require application access.
5. Use dashboards and document shortcuts to monitor compliance.

Exceptions and validation
=========================

* ``UserError`` may be raised when linked-user creation cannot proceed because
  required profile data is missing or a user already exists.
* ``ValidationError`` is raised when a qualification record is assigned to more
  than one owner.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
