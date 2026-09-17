# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Repair the SOLO seed record skipped by its noupdate XML definition."""
    cr.execute(
        'UPDATE fs_flight_type SET is_solo = TRUE WHERE code = %s AND NOT is_solo',
        ['SOLO'],
    )
