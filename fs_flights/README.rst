======================
Flight School Flights
======================

Purpose
=======

``fs_flights`` turns planned schedules into operational flight records. It
supports daily operations boards, simulator operations boards, flight execution
logging, cancellations, schedule import, ADD flights, deletion confirmation, and
hour recalculation.

Main functionality
==================

* Publishes scheduled flights into operational ``fs.flight`` records.
* Tracks planned and actual departure/arrival times, execution status,
  cancellation state, route, crew, aircraft, mission, and activity.
* Updates aircraft, personnel, and enrollment hours when flights are completed
  or adjusted.
* Provides daily and simulator operations boards with pagination, KPIs,
  aircraft availability, and board refresh actions.
* Supports operational wizards for adding flights, cancelling flights, deleting
  drafts, importing schedules, and recalculating hours.

Dependencies
============

* ``fs_scheduling`` for planned flights and scheduling helpers.
* ``fs_fleet`` for aircraft records and total-hour updates.
* ``fs_training`` for missions, activities, classes, and enrollment hours.
* ``fs_people`` for personnel hour totals.
* ``mail`` for chatter updates.
* ``bus`` for operations-board refresh integration.

Related Flight School modules
=============================

``fs_scheduling`` supplies planned flights. ``fs_training`` receives enrollment
hour updates. ``fs_fleet`` and ``fs_people`` receive total-hour updates from
completed operations.

Public Python API
=================

``fs.flight``
    Operational flight log. Public methods include ``create()``, ``write()``,
    ``unlink()``, ``action_open_form()``, ``action_save_and_close()``,
    ``action_start_flight()``, ``action_complete_flight()``,
    ``action_cancel_flight()``, and ``action_delete_flight()``. Hour
    distribution helpers document aircraft, crew, and enrollment updates.

``fs.daily.operations`` and ``fs.simulator.operations``
    Operations board models. Public methods include day navigation, refresh,
    pagination, board-opening, and add-flight/add-session actions.

``fs.scheduled.flight`` extension
    Adds publishing methods ``action_publish_day()`` and ``cron_publish_today()``
    plus conflict recalculation behavior for active operations.

Wizards
    ``fs.add.flight.wizard``, ``fs.add.sim.wizard``,
    ``fs.flight.cancel.wizard``, ``fs.flight.delete.wizard``,
    ``fs.import.schedule.wizard``, and ``fs.recalculate.hours.wizard`` expose
    documented public actions for common operational workflows.

All public classes and methods include Google-style source docstrings with
parameters, return values, and raised ``UserError`` or ``ValidationError``
exceptions where applicable.

Usage examples
==============

Publish a scheduled day to operations::

    scheduled_flights = env['fs.scheduled.flight'].search([
        ('date', '=', fields.Date.today()),
    ])
    scheduled_flights.action_publish_day()

Start and complete a flight::

    flight = env['fs.flight'].search([('status', '=', 'scheduled')], limit=1)
    flight.action_start_flight()
    flight.write({
        'actual_departure': 8.0,
        'actual_arrival': 9.2,
    })
    flight.action_complete_flight()

Open the daily operations board::

    board = env['fs.daily.operations'].create({'date': fields.Date.today()})
    action = board.action_open_operations_board()

Recalculate hour totals after historical corrections::

    wizard = env['fs.recalculate.hours.wizard'].create({})
    wizard.action_calculate()
    wizard.action_apply()

Common workflow
---------------

1. Publish the daily schedule from ``fs_scheduling``.
2. Monitor and update flights on the daily or simulator operations board.
3. Start, complete, or cancel flights as operational information changes.
4. Review hour distribution messages in chatter.
5. Use the recalculation wizard after bulk corrections or historical imports.

Exceptions and validation
=========================

* ``UserError`` is raised for duplicate callsigns, invalid state transitions,
  completed-flight deletion attempts, and missing required cancellation data.
* ``ValidationError`` may be raised by related model constraints.
* Hour distribution uses signed deltas so reversing or editing completed flights
  subtracts previous totals before applying corrected totals.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
