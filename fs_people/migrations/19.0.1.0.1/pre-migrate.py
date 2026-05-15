"""Pre-migration script for administrative staff service numbers.

Purpose:
    Renames the legacy ``employee_number`` column and unique constraint to the
    current ``service_number`` naming used by ``fs.admin.staff``.

Related Modules:
    Keeps personnel identifiers consistent for ``fs_people`` records that are
    referenced by training, scheduling, documents, and operations modules.
"""

def migrate(cr, version):
    """Rename employee_number to service_number in fs_admin_staff table.

    Args:
        cr: Database cursor provided by Odoo during module migration.
        version: Installed module version provided by Odoo during migration.

    Returns:
        None: Updates Odoo records, computed fields, or wizard state in place.
    """
    # Check if the old column exists
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='fs_admin_staff'
        AND column_name='employee_number'
    """)
    if cr.fetchone():
        # Rename the column
        cr.execute("""
            ALTER TABLE fs_admin_staff
            RENAME COLUMN employee_number TO service_number
        """)

        # Rename the constraint if it exists
        cr.execute("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name='fs_admin_staff'
            AND constraint_name='fs_admin_staff_employee_number_unique'
        """)
        if cr.fetchone():
            cr.execute("""
                ALTER TABLE fs_admin_staff
                RENAME CONSTRAINT fs_admin_staff_employee_number_unique
                TO fs_admin_staff_service_number_unique
            """)
