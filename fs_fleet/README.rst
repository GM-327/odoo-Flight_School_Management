===================
Flight School Fleet
===================

Purpose
=======

``fs_fleet`` manages the aircraft inventory used by the Flight School
Management suite. It stores aircraft categories, aircraft types, individual
aircraft, airworthiness state, maintenance thresholds, certificate dates, and
fleet dashboard indicators.

Main functionality
==================

* Classifies aircraft with ``fs.aircraft.category`` and ``fs.aircraft.type``.
* Tracks individual aircraft in ``fs.aircraft`` with registration, serial
  number, type, status, hours, maintenance due dates, and certificate expiries.
* Computes airworthiness, maintenance warning states, and status colors for UI
  dashboards and Kanban views.
* Provides a fleet dashboard with operational, maintenance, and certificate
  KPIs.
* Adds fleet-related settings to ``res.config.settings``.

Dependencies
============

* ``fs_core`` for shared settings, menus, and security.
* ``mail`` for chatter and activity tracking on aircraft records.

Related Flight School modules
=============================

* ``fs_training`` uses aircraft types to define class and mission requirements.
* ``fs_scheduling`` searches available aircraft when assigning planned flights.
* ``fs_flights`` updates aircraft totals and last-flight dates after completed
  operations.

Public Python API
=================

``fs.aircraft``
    Main fleet record. Public actions include ``action_set_available()``,
    ``action_set_maintenance()``, and ``action_set_grounded()``. ``unlink()``
    prevents deleting aircraft that already have flight history.

``fs.aircraft.type``
    Defines make/model metadata and allowed capabilities. ``name_get()`` returns
    user-friendly labels and ``unlink()`` protects types that are in use.

``fs.aircraft.category``
    Groups aircraft types and stores category flags such as simulator status.
    ``unlink()`` protects categories linked to aircraft types.

``fs.fleet.dashboard``
    Transient dashboard model. Public ``action_view_*`` methods return Odoo
    action dictionaries for filtered aircraft, maintenance, and certificate
    views.

All compute, onchange, constraint, and action methods are documented with
Google-style docstrings in ``models/``. The docstrings include parameters,
return values, and raised ``UserError`` exceptions where applicable.

Usage examples
==============

Create an aircraft type and aircraft::

    category = env['fs.aircraft.category'].search([('code', '=', 'SEP')], limit=1)
    aircraft_type = env['fs.aircraft.type'].create({
        'name': 'Cessna 172S',
        'manufacturer': 'Cessna',
        'category_id': category.id,
    })
    aircraft = env['fs.aircraft'].create({
        'registration': 'TS-ABC',
        'aircraft_type_id': aircraft_type.id,
        'total_hours': 1250.0,
        'maintenance_due_at_hours': 1260.0,
    })

Move an aircraft into maintenance::

    aircraft.action_set_maintenance()

Open aircraft due for maintenance from the dashboard::

    dashboard = env['fs.fleet.dashboard'].create({})
    action = dashboard.action_view_maintenance_due_soon()

Common workflow
---------------

1. Configure categories and aircraft types.
2. Register each aircraft and set its current total hours.
3. Configure warning thresholds in Fleet settings.
4. Use scheduling and operations modules to consume aircraft availability and
   update total hours.

Exceptions and validation
=========================

* ``UserError`` is raised when a registration contains unsupported characters,
  a manufactured year is not four digits, or a user attempts to delete an
  aircraft with flight history.
* SQL constraints prevent duplicate aircraft registrations.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
