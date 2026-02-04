def migrate(cr, version):
    # Fix fs_flight_log.route_name if it is jsonb
    cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name='fs_flight_log' AND column_name='route_name'")
    res = cr.fetchone()
    if res and res[0] == 'jsonb':
        # Force conversion to varchar
        cr.execute("ALTER TABLE fs_flight_log ALTER COLUMN route_name TYPE VARCHAR USING COALESCE(route_name->>'en_US', route_name->>'en_GB', route_name::text)")
