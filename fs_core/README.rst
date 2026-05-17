======================
Flight School Settings
======================

Purpose
=======

``fs_core`` is the foundation module for the Flight School Management addon
suite. It defines shared security groups, the Flight School application menu
structure, department records, and central configuration fields used by the
other modules.

Main functionality
==================

* Creates the Flight School application category and shared menu roots.
* Defines the baseline security groups and access-control records consumed by
  fleet, people, training, documents, scheduling, and operations modules.
* Provides ``fs.department`` for organizing users or staff by flight-school
  department.
* Extends ``res.config.settings`` with global Flight School settings.

Security model
==============

``fs_core`` defines a hierarchical Flight School role set: User, Instructor,
Manager, and Administrator. User and role administration is intentionally
restricted to Flight School Administrators. Managers retain only the access
explicitly granted by the functional modules and cannot administer ``res.users``,
``res.groups``, ``res.groups.privilege``, departments, or global settings from
``fs_core``.

The module is currently designed for a single-company/single-school deployment.
Settings are stored globally through ``ir.config_parameter`` and departments are
not company-specific.

Dependencies
============

Runtime dependencies are declared in ``__manifest__.py``:

* ``base`` and ``base_setup`` for Odoo settings and user management.
* ``auth_signup`` for user-account provisioning support.

Related Flight School modules
=============================

Every Flight School addon depends on or integrates with ``fs_core`` for shared
settings, security, and navigation. Install this module before installing the
other Flight School modules.

Public Python API
=================

``fs.department``
    Stores department metadata used to classify organizational units. The model
    enforces mandatory unique department codes, prevents recursive hierarchies,
    and requires department managers to be active Flight School users.

``res.config.settings`` extension
    Exposes central settings through Odoo's Settings interface. Configuration
    values are stored with Odoo's ``ir.config_parameter`` mechanism where
    appropriate.

All public classes and methods include Google-style docstrings in the source
files under ``models/``. Private Odoo compute and onchange methods document the
fields they update and the exceptions they can raise.

Usage examples
==============

Create a department from an Odoo shell or server action::

    department = env['fs.department'].create({
        'name': 'Flight Operations',
        'code': 'OPS',
    })

Department codes are normalized to uppercase and must contain 2 to 12
characters using only uppercase letters, numbers, hyphens, or underscores.

Open the Flight School settings form from Python::

    action = env['ir.actions.act_window']._for_xml_id(
        'fs_core.action_flight_school_settings'
    )

Common workflow
---------------

1. Install ``fs_core``.
2. Assign users to the Flight School security groups.
3. Configure shared settings from the Flight School Settings menu.
4. Install the functional modules required by the school.

Exceptions and validation
=========================

This module uses Odoo ORM validation and raises ``ValidationError`` for invalid
department codes, recursive department hierarchies, invalid department manager
assignments, and invalid default home-base ICAO codes. Related modules may raise
``UserError`` or ``ValidationError`` when their business rules depend on settings
defined here.

Known limitations
=================

* Settings and departments are global and are not scoped by company.
* The default home base is stored as a validated ICAO-style text value rather
  than a relation to an airport/base model.
* Rest and daily-flight-hour policy parameters are not defined in ``fs_core``;
  they should be implemented in the operational module that consumes them.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
