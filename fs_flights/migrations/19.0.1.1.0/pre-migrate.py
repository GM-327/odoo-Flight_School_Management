"""Pre-migration script for flight route-name normalization.

Purpose:
    Converts legacy JSONB ``route_name`` values on historical flight log rows to
    plain ``VARCHAR`` values before the upgraded flight operations models load.

Related Modules:
    Preserves route display data consumed by ``fs_flights`` operations boards
    and records published from ``fs_scheduling``.
"""

def migrate(cr, version):
    """Convert ``fs_flight_log.route_name`` from JSONB to VARCHAR when needed.

    Args:
        cr: Database cursor provided by Odoo during module migration.
        version: Installed module version provided by Odoo during migration.

    Returns:
        None: Updates database schema in place.
    """
    # Fix fs_flight_log.route_name if it is jsonb
    cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name='fs_flight_log' AND column_name='route_name'")
    res = cr.fetchone()
    if res and res[0] == 'jsonb':
        # Force conversion to varchar
        cr.execute("ALTER TABLE fs_flight_log ALTER COLUMN route_name TYPE VARCHAR USING COALESCE(route_name->>'en_US', route_name->>'en_GB', route_name::text)")
