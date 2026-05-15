========================
Flight School Scheduling
========================

Purpose
=======

``fs_scheduling`` plans training flights before they are published to daily
operations. It manages scheduled flights, flight routes, cancellation reasons,
pilot functions, custom activities, the unified crew-member view, scheduling
wizards, conflict checks, and timeline grouping.

Main functionality
==================

* Creates and edits ``fs.scheduled.flight`` records with crew, aircraft,
  mission, route, time, and callsign data.
* Computes instructor and aircraft conflicts with configurable buffer times.
* Provides a unified ``fs.crew.member`` SQL view for students, instructors, and
  pilots.
* Generates schedules in a multi-step wizard from selected enrollments and
  instructors.
* Assigns start times, aircraft, and callsigns while respecting resource
  availability.
* Supplies timeline groups for aircraft and crew views.
* Adds scheduling-related settings and sequence defaults.

Dependencies
============

* ``fs_core`` for shared settings, menus, and security.
* ``fs_training`` for classes, enrollments, missions, and activities.
* ``fs_fleet`` for aircraft and aircraft types.
* ``fs_people`` for students, instructors, and pilots.
* ``mail`` for chatter and activity support.
* ``web_timeline`` for timeline views.

Related Flight School modules
=============================

``fs_flights`` consumes scheduled flights when publishing a day to operations.
``fs_training`` supplies missions and enrollments, while ``fs_fleet`` and
``fs_people`` supply assignable resources.

Public Python API
=================

``fs.scheduled.flight``
    Planned-flight model. Public methods include ``create()``, ``write()``,
    ``check_conflicts()``, ``get_timeline_groups()``, and timeline formatting
    helpers documented in source.

``fs.flight.mixin``
    Shared scheduling/flight helper mixin. Public helper methods generate
    callsigns, read scheduling configuration, format hours, derive pilot
    functions, and detect simulator missions.

``fs.crew.member``
    SQL-view model. Public methods include ``init()``, ``_name_search()``,
    ``get_source_record()``, ``get_enrollment_record()``, and qualification
    badge helpers.

``fs.scheduling.wizard``
    Batch scheduling wizard. Public actions include ``action_next_step()``,
    ``action_previous_step()``, ``action_add_mission()``,
    ``action_reschedule_time_only()``, ``action_reschedule()``,
    ``action_schedule()``, ``action_reset()``, and bulk-assignment actions.

``fs.scheduling.wizard.line``
    Generated line model with ordering actions such as ``action_move_up()``,
    ``action_move_down()``, ``action_move_first()``, ``action_move_last()``,
    ``toggle_lock()``, and ``action_save_and_close()``.

``fs.scheduling.wizard.bulk.action``
    Applies bulk route, aircraft type, or ADD-mission updates to wizard lines.

All public methods and complex private helpers include Google-style source
docstrings with parameters, return values, and exceptions.

Usage examples
==============

Create a scheduled flight directly::

    scheduled = env['fs.scheduled.flight'].create({
        'date': fields.Date.today(),
        'start_time': 8.0,
        'duration': 1.25,
        'pilot1_crew_id': student_crew.id,
        'pilot2_crew_id': instructor_crew.id,
        'aircraft_id': aircraft.id,
        'mission_id': mission.id,
        'route_id': route.id,
    })
    scheduled.check_conflicts()

Generate a batch schedule with the wizard::

    wizard = env['fs.scheduling.wizard'].create({
        'date': fields.Date.today(),
        'selected_enrollment_ids': [(6, 0, enrollment_ids)],
        'selected_instructor_ids': [(6, 0, instructor_ids)],
    })
    wizard.action_next_step()
    wizard.action_schedule()

Common workflow
---------------

1. Configure pilot functions, routes, cancellation reasons, and scheduling
   settings.
2. Select active enrollments and available instructors in the scheduling wizard.
3. Review generated lines, routes, aircraft types, and ADD missions.
4. Let the wizard assign times, aircraft, and callsigns.
5. Confirm the schedule and review timeline views.

Exceptions and validation
=========================

* ``UserError`` is raised when required crew, mission, route, aircraft type, or
  scheduling inputs are missing.
* ``ValidationError`` may be raised by Odoo constraints on related models.
* Conflict methods flag instructor and aircraft overlap states instead of always
  blocking the user, allowing managers to review and correct schedules.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
