# -*- coding: utf-8 -*-
"""Post-migration script for unified crew member refactoring.

This script migrates from the old separate crew fields to the new unified
fs.crew.member fields (pilot1_crew_id, pilot2_crew_id).

Runs AFTER ORM has created new columns.

IMPORTANT: Remove this migration script after all databases have been migrated.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate old crew fields to unified crew member fields."""
    if not version:
        return
    
    _logger.info("Starting unified crew member migration...")
    
    # Check if old columns exist before attempting migration
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'fs_scheduled_flight' 
        AND column_name IN ('pilot1_enrollment_id', 'pilot1_instructor_id', 'pilot2_instructor_id');
    """)
    old_columns = [row[0] for row in cr.fetchall()]
    
    if not old_columns:
        _logger.info("No old crew columns found, skipping migration.")
        return
    
    # Step 1: Migrate student enrollment records to pilot1_crew_id
    # Enrollment ID is used directly as crew member ID for students
    if 'pilot1_enrollment_id' in old_columns:
        cr.execute("""
            UPDATE fs_scheduled_flight 
            SET pilot1_crew_id = pilot1_enrollment_id
            WHERE pilot1_enrollment_id IS NOT NULL
              AND pilot1_crew_id IS NULL;
        """)
        migrated_students = cr.rowcount
        _logger.info(f"Migrated {migrated_students} student enrollments to pilot1_crew_id")
    
    # Step 2: Migrate instructor/pilot records to pilot1_crew_id
    # Instructor ID + 1000000 = crew member ID for instructors
    if 'pilot1_instructor_id' in old_columns:
        cr.execute("""
            UPDATE fs_scheduled_flight 
            SET pilot1_crew_id = pilot1_instructor_id + 1000000
            WHERE pilot1_instructor_id IS NOT NULL
              AND pilot1_crew_id IS NULL;
        """)
        migrated_instructors = cr.rowcount
        _logger.info(f"Migrated {migrated_instructors} instructors to pilot1_crew_id")
    
    # Step 3: Migrate Pilot 2 instructor records
    # Instructor ID + 1000000 = crew member ID for instructors
    if 'pilot2_instructor_id' in old_columns:
        cr.execute("""
            UPDATE fs_scheduled_flight 
            SET pilot2_crew_id = pilot2_instructor_id + 1000000
            WHERE pilot2_instructor_id IS NOT NULL
              AND pilot2_crew_id IS NULL;
        """)
        migrated_p2_instructors = cr.rowcount
        _logger.info(f"Migrated {migrated_p2_instructors} Pilot 2 instructors to pilot2_crew_id")
    
    # Also migrate wizard lines if they exist
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'fs_scheduling_wizard_line' 
        AND column_name IN ('pilot1_enrollment_id', 'pilot2_instructor_id');
    """)
    wizard_old_columns = [row[0] for row in cr.fetchall()]
    
    if wizard_old_columns:
        _logger.info("Migrating wizard line crew fields...")
        
        if 'pilot1_enrollment_id' in wizard_old_columns:
            cr.execute("""
                UPDATE fs_scheduling_wizard_line 
                SET pilot1_crew_id = pilot1_enrollment_id
                WHERE pilot1_enrollment_id IS NOT NULL
                  AND pilot1_crew_id IS NULL;
            """)
        
        if 'pilot2_instructor_id' in wizard_old_columns:
            cr.execute("""
                UPDATE fs_scheduling_wizard_line 
                SET pilot2_crew_id = pilot2_instructor_id + 1000000
                WHERE pilot2_instructor_id IS NOT NULL
                  AND pilot2_crew_id IS NULL;
            """)
    
    _logger.info("Unified crew member migration completed successfully!")
