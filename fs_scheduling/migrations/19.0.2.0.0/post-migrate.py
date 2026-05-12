# -*- coding: utf-8 -*-
"""Post-migration script for flight crew refactoring.

This script migrates the flight_category from 4 values to 2:
- student_dual, student_solo → student_training
- pilot_training, staff → staff_training

It also preserves crew data by mapping old fields to new Pilot 1/Pilot 2 structure.
Runs AFTER ORM has created new columns.

IMPORTANT: Remove this migration script after all databases have been migrated.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate flight_category values and crew field data."""
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
