# -*- coding: utf-8 -*-
"""Post-migration script for the scheduled-flight crew refactor.

Purpose:
    Migrates legacy flight categories and crew columns to the current
    ``student_training`` / ``staff_training`` category model and Pilot 1 / Pilot
    2 field structure after Odoo creates the new columns.

Related Modules:
    Depends on ``fs_scheduling`` models and preserves data consumed by
    ``fs_flights`` when planned flights are published to operations.

Notes:
    Keep this script until every deployed database has been migrated past
    version 19.0.2.0.0.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate flight_category values and crew field data.

    Args:
        cr: Database cursor provided by Odoo during module migration.
        version: Installed module version provided by Odoo during migration.

    Returns:
        None: Updates Odoo records, computed fields, or wizard state in place.
    """
    if not version:
        return

    _logger.info("Starting flight crew refactoring migration...")

    # Step 1: Update flight_category in fs_scheduled_flight table
    cr.execute("""
        UPDATE fs_scheduled_flight
        SET flight_category = CASE
            WHEN flight_category IN ('student_dual', 'student_solo') THEN 'student_training'
            WHEN flight_category IN ('pilot_training', 'staff') THEN 'staff_training'
            ELSE flight_category
        END
        WHERE flight_category IN ('student_dual', 'student_solo', 'pilot_training', 'staff');
    """)
    updated_flights = cr.rowcount
    _logger.info(f"Updated flight_category for {updated_flights} scheduled flights")

    # Step 2: Migrate crew fields for student training flights
    # Map enrollment_id → pilot1_enrollment_id
    # Map instructor_id → pilot2_instructor_id and pilot2_function = 'instructor'
    # Map supervisor_id → pilot2_instructor_id and pilot2_function = 'supervisor'
    cr.execute("""
        UPDATE fs_scheduled_flight
        SET
            pilot1_enrollment_id = enrollment_id,
            pilot1_function = CASE
                WHEN is_solo = true THEN 'solo'
                ELSE 'student'
            END,
            pilot2_instructor_id = COALESCE(instructor_id, supervisor_id),
            pilot2_function = CASE
                WHEN is_solo = true THEN 'supervisor'
                WHEN instructor_id IS NOT NULL THEN 'instructor'
                WHEN supervisor_id IS NOT NULL THEN 'supervisor'
                ELSE NULL
            END
        WHERE flight_category = 'student_training'
          AND enrollment_id IS NOT NULL
          AND pilot1_enrollment_id IS NULL;
    """)
    migrated_student = cr.rowcount
    _logger.info(f"Migrated crew data for {migrated_student} student training flights")

    # Step 3: Migrate crew fields for staff training flights
    # Map pilot_id or instructor_id → pilot1_instructor_id
    # Map instructor2_id or pilot2_id → pilot2_instructor_id or pilot2_pilot_id
    cr.execute("""
        UPDATE fs_scheduled_flight
        SET
            pilot1_instructor_id = COALESCE(pilot_id, instructor_id),
            pilot1_function = 'pilot',
            pilot2_instructor_id = instructor2_id,
            pilot2_pilot_id = pilot2_id,
            pilot2_function = CASE
                WHEN instructor2_id IS NOT NULL THEN 'instructor'
                WHEN pilot2_id IS NOT NULL THEN 'pilot'
                ELSE NULL
            END
        WHERE flight_category = 'staff_training'
          AND pilot1_instructor_id IS NULL
          AND (pilot_id IS NOT NULL OR instructor_id IS NOT NULL);
    """)
    migrated_staff = cr.rowcount
    _logger.info(f"Migrated crew data for {migrated_staff} staff training flights")

    _logger.info("Flight crew refactoring migration completed successfully!")
