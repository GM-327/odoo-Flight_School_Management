======================
Flight School Training
======================

Purpose
=======

``fs_training`` manages the training syllabus and class lifecycle. It defines
class types, requirements, flight disciplines, flight types, activities,
missions, training classes, student enrollments, mission completion records,
admin tasks, and training dashboards.

Main functionality
==================

* Builds reusable curricula with class types, hour requirements, missions, and
  administrative task templates.
* Manages active training classes with planned and expected dates.
* Enrolls students, instructors, and licensed personnel in training classes.
* Tracks required, logged, remaining, solo, simulator, and extra hours.
* Records mission completion and administrative task completion.
* Provides training dashboards and filtered actions for class and enrollment
  monitoring.

Dependencies
============

* ``fs_core`` for shared settings, menus, and security.
* ``fs_people`` for students, instructors, pilots, and qualifications.
* ``fs_fleet`` for aircraft types used by class and mission requirements.
* ``mail`` for chatter and activity tracking.

Related Flight School modules
=============================

* ``fs_scheduling`` uses missions and enrollment data to generate schedules.
* ``fs_flights`` updates enrollment hour totals after completed operations.
* ``fs_documents`` links required documents to classes, class types, and admin
  tasks.

Public Python API
=================

``fs.training.class``
    Training class lifecycle model. Public methods include ``create()``,
    ``write()``, ``action_start_class()``, ``action_set_draft()``,
    ``action_complete_class()``, and ``action_cancel_class()``.

``fs.student.enrollment``
    Enrollment and hour-progress model. Public actions include
    ``action_graduate()``, ``action_drop()``, ``action_reinstate()``,
    ``action_view_student()``, and ``action_open_enrollment()``.

``fs.enrollment.hours``
    Per-activity hour ledger used to compute progress and remaining hours.

``fs.flight.mission``
    Mission definition model with ``action_duplicate_mission()`` and onchange
    helpers for activity defaults.

``fs.mission.completion``
    Mission completion state with ``action_mark_complete()`` and
    ``action_mark_incomplete()``.

``fs.training.dashboard``
    Dashboard model with public ``action_view_*`` methods for classes,
    enrollments, and admin tasks.

All compute, onchange, constraint, and action methods include Google-style
source docstrings with parameter, return, and exception details.

Usage examples
==============

Create a class from a configured class type::

    class_type = env['fs.class.type'].search([], limit=1)
    training_class = env['fs.training.class'].create({
        'name': 'Initial Flight Training 2026-A',
        'class_type_id': class_type.id,
        'start_date': fields.Date.today(),
    })
    training_class.action_start_class()

Enroll a student::

    enrollment = env['fs.student.enrollment'].create({
        'student_id': student.id,
        'training_class_id': training_class.id,
        'instructor_id': instructor.id,
        'status': 'active',
    })

Graduate an enrollment after requirements are satisfied::

    enrollment.action_graduate()

Common workflow
---------------

1. Configure disciplines, flight types, activities, class requirements, and
   missions.
2. Create a class type and its minimum-hour matrix.
3. Create a training class and enroll students.
4. Use scheduling and operations modules to log flights.
5. Review dashboards and graduate, drop, or reinstate enrollments as needed.

Exceptions and validation
=========================

* ``UserError`` is raised when lifecycle actions are not valid for the current
  class or enrollment state.
* ``ValidationError`` is raised for invalid dates, duplicate active enrollments,
  or an enrolled person that does not match the selected enrollment type.

Credits
=======

Authors
-------

* Ghazi Marzouk
* Odoo Community Association (OCA)

Maintainers
-----------

This module is maintained by the Flight School Management contributors.
