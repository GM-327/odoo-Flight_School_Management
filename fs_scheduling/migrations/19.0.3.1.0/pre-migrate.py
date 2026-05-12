def migrate(cr, version):
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
