"""Pre-migration script for flight-route name normalization.

Purpose:
    Converts translated JSONB route names to plain ``VARCHAR`` values before
    the upgraded ``fs.flight.route`` model is loaded.

Related Modules:
    Protects route labels used by scheduled flights, operations boards, and
    timeline grouping.
"""

def migrate(cr, version):
    """Convert ``fs_flight_route.name`` from JSONB to VARCHAR when needed.

    Args:
        cr: Database cursor provided by Odoo during module migration.
        version: Installed module version provided by Odoo during migration.

    Returns:
        None: Updates database schema in place.
    """
    # Check if table exists
    cr.execute("SELECT 1 FROM information_schema.tables WHERE table_name = 'fs_flight_route'")
    if cr.fetchone():
        # Check column type
        cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name='fs_flight_route' AND column_name='name'")
        res = cr.fetchone()
        if res and res[0] == 'jsonb':
            # Convert JSONB to VARCHAR, extracting the english value or casting to text
            cr.execute(
                "ALTER TABLE fs_flight_route ALTER COLUMN name TYPE VARCHAR USING COALESCE(name->>'en_US', name->>'en_GB', name::text)")
